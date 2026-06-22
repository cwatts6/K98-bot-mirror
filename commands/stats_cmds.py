# commands/stats_cmds.py
from __future__ import annotations

import asyncio
import logging
import time

import discord
from discord.ext import commands as ext_commands

from bot_config import (
    GUILD_ID,
    KVK_PLAYER_STATS_CHANNEL_ID,
    STATS_ALERT_CHANNEL_ID,
)
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from constants import CREDENTIALS_FILE, DATABASE, KVK_SHEET_NAME, PASSWORD, SERVER, USERNAME
from core.interaction_safety import safe_command, safe_defer
from decoraters import (
    _actor_from_ctx,
    channel_only,
    is_admin_and_notify_channel,
    is_admin_or_leadership,
    track_usage,
)
from embed_my_stats import SliceButtons, build_embeds
from gsheet_module import run_kvk_export_test, run_kvk_proc_exports_with_alerts
from kvk.services import kvk_admin_service
from profile_cache import autocomplete_choices
from services import (
    governor_account_service,
    stats_export_service,
)
from stats_alerts.embeds.kvk import send_kvk_embed
from stats_alerts.honors import purge_latest_honor_scan
from stats_alerts.interface import send_stats_update_embed
from stats_alerts.kvk_meta import is_currently_kvk
from stats_service import get_stats_payload
from versioning import versioned

logger = logging.getLogger(__name__)
bot: ext_commands.Bot | None = None


def _split_discord_content(content: str, *, max_chars: int = 1900) -> list[str]:
    """Split command output into Discord-safe content chunks."""
    if len(content) <= max_chars:
        return [content]

    chunks: list[str] = []
    current = ""
    for line in content.splitlines():
        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        while len(line) > max_chars:
            chunks.append(line[:max_chars])
            line = line[max_chars:]
        current = line

    if current:
        chunks.append(current)

    return chunks or [""]


def register_stats(bot_instance: ext_commands.Bot) -> None:
    global bot
    bot = bot_instance
    kvk_admin_group = discord.SlashCommandGroup(
        "kvk_admin",
        "KVK admin controls",
        guild_ids=[GUILD_ID],
    )
    stats_group = discord.SlashCommandGroup(
        "stats",
        "Stats leadership controls",
        guild_ids=[GUILD_ID],
    )
    honor_group = discord.SlashCommandGroup(
        "honor",
        "Honor admin controls",
        guild_ids=[GUILD_ID],
    )

    @kvk_admin_group.command(
        name="test_export",
        description="🧪 Admin: Test KVK Google Sheets export without performing an import",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_kvk_export(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
        sheet_name: str = discord.Option(
            str,
            "Primary Google Sheet name",
            required=False,
            default=KVK_SHEET_NAME,
        ),
        create_primary: bool = discord.Option(
            bool,
            # architecture-check: allow
            "Create/write the primary KVK sheet",
            required=False,
            default=True,
        ),
        export_pass4: bool = discord.Option(
            bool,
            "Export Pass 4 data",
            required=False,
            default=True,
        ),
        export_altar: bool = discord.Option(
            bool,
            "Export Altar data",
            required=False,
            default=True,
        ),
        export_pass7: bool = discord.Option(
            bool,
            "Export Pass 7 data",
            required=False,
            default=True,
        ),
    ):
        """
        Admin-only command to run the export pipeline for a KVK without requiring an import.
        Returns structured metadata about which spreadsheets/tabs would be created/written.
        """
        logger.info("[COMMAND] /kvk_admin test_export invoked by %s (kvk_no=%s)", ctx.user, kvk_no)

        # Single ack (ephemeral)
        try:
            await safe_defer(ctx, ephemeral=True)
        except Exception:
            pass

        # Resolve current KVK if not provided (reuse existing helper)
        if kvk_no == 0:
            try:
                kvk_no = await asyncio.to_thread(kvk_admin_service.resolve_kvk_no, None)
            except Exception as e:
                logger.exception("[COMMAND] /kvk_admin test_export could not resolve KVK")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Could not resolve the current KVK window: `{type(e).__name__}: {e}`"
                )
                return

        sheet_name = kvk_admin_service.normalize_sheet_name(sheet_name, KVK_SHEET_NAME)

        # Let the invoker know we're starting
        try:
            await ctx.interaction.edit_original_response(
                content=f"⏳ Running KVK export TEST for KVK `{kvk_no}` (primary sheet: **{sheet_name}**)…"
            )
        except Exception:
            pass

        try:
            # Run the test export in a thread (blocking IO / network)
            result = await asyncio.to_thread(
                kvk_admin_service.run_export_test,
                kvk_no=kvk_no,
                sheet_name=sheet_name,
                server=SERVER,
                database=DATABASE,
                username=USERNAME,
                password=PASSWORD,
                credentials_file=CREDENTIALS_FILE,
                create_primary=create_primary,
                export_pass4=export_pass4,
                export_altar=export_altar,
                export_pass7=export_pass7,
                runner=run_kvk_export_test,
            )
        except Exception as e:
            logger.exception("[COMMAND] /kvk_admin test_export crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 Test export failed unexpectedly: `{type(e).__name__}: {e}`"
            )
            return

        dur = result.duration_seconds

        # Build a helpful embed summarising the metadata returned by run_kvk_export_test()
        try:
            embed = discord.Embed(
                title=f"🧪 KVK Export Test — KVK {kvk_no}",
                description=f"Test run completed in `{result.duration_seconds:.1f}s`.",
                color=discord.Color.green(),
            )

            embed.add_field(name="KVK", value=str(result.kvk_no), inline=True)
            embed.add_field(name="Primary sheet", value=result.sheet_name, inline=True)
            embed.add_field(name="Triggered by", value=f"<@{ctx.user.id}>", inline=True)

            meta = result.meta
            # Primary metadata (if present)
            primary = meta.get("primary") if isinstance(meta, dict) else None
            if primary:
                p_written = primary.get("written_tabs", []) or []
                p_skipped = primary.get("skipped_tabs", []) or []
                p_url = primary.get("spreadsheet_url")
                lines = []
                if p_written:
                    lines.append(f"Written tabs: {len(p_written)}")
                if p_skipped:
                    lines.append(f"Empty tabs (created empty): {len(p_skipped)}")
                if p_url:
                    lines.append(f"[Open primary sheet]({p_url})")
                embed.add_field(
                    name="Primary result",
                    value="\n".join(lines) or "No primary metadata",
                    inline=False,
                )

            # Additional spreadsheets (PASS4 / 1st Altar / PASS7)
            additional = meta.get("additional") if isinstance(meta, dict) else {}
            if additional:
                for ss_name, ss_meta in additional.items():
                    created = ss_meta.get("created", False)
                    written = ss_meta.get("written_tabs", []) or []
                    skipped = ss_meta.get("skipped_tabs", []) or []
                    url = ss_meta.get("spreadsheet_url") or ""
                    status = (
                        "✅ Created"
                        if created
                        else "ℹ️ Skipped" if ss_meta.get("reason") == "no_data" else "❌ Failed"
                    )
                    value_lines = [status]
                    if written:
                        value_lines.append(f"Written: {len(written)}")
                    if skipped:
                        value_lines.append(f"Skipped: {len(skipped)}")
                    if url:
                        value_lines.append(f"[Open]({url})")
                    embed.add_field(name=ss_name, value="\n".join(value_lines), inline=False)
        except Exception:
            # Fallback summary if embed construction fails
            try:
                await ctx.interaction.edit_original_response(
                    content=f"✅ Test export finished in `{dur:.1f}s`. Inspect logs for details."
                )
            except Exception:
                pass
            return

        try:
            await ctx.interaction.edit_original_response(content=None, embed=embed)
        except Exception:
            try:
                await ctx.followup.send(embed=embed, ephemeral=True)
            except Exception:
                logger.exception("[COMMAND] /kvk_admin test_export failed to send result embed")

    @bot.slash_command(
        name="mykvkstats",
        description="View your personal KVK stats for each registered game account.",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v2.21")
    @safe_command
    @track_usage()
    async def mykvkstats(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/mykvkstats",
                new_path="/kvk stats",
                detail="The new command uses the modern KVK stats card and account selector.",
            ),
            ephemeral=True,
        )
        return

    @kvk_admin_group.command(
        name="refresh_stats_cache",
        description="Admin only: Refresh player stats cache",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_stats_cache(ctx):

        await safe_defer(ctx, ephemeral=True)

        try:
            from player_stats_cache import (
                build_lastkvk_player_stats_cache,
                build_player_stats_cache,
            )

            result = await kvk_admin_service.refresh_stats_caches(
                build_player_stats_cache=build_player_stats_cache,
                build_lastkvk_player_stats_cache=build_lastkvk_player_stats_cache,
            )
            msg = kvk_admin_service.format_cache_refresh_message(result)
            logger.info("[/kvk_admin refresh_stats_cache] %s", msg.replace("\n", " | "))
            await ctx.interaction.edit_original_response(content=msg)
            return
        except Exception as e:
            logger.exception("[/kvk_admin refresh_stats_cache] failed")
            try:
                await ctx.interaction.edit_original_response(
                    content=f"Failed to refresh cache: `{type(e).__name__}: {e}`"
                )
            except Exception:
                try:
                    await ctx.followup.send(
                        f"Failed to refresh cache: `{type(e).__name__}: {e}`", ephemeral=True
                    )
                except Exception:
                    logger.exception(
                        "[/kvk_admin refresh_stats_cache] failed to report error to user"
                    )
            return

    @bot.slash_command(
        name="my_stats",
        description="View your Rise of Kingdoms stats across your registered accounts",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v1.14")
    @safe_command
    @track_usage()
    async def my_stats_command(ctx):
        # Defer so the token stays alive (ephemeral)
        await safe_defer(ctx, ephemeral=True)

        # Resolve user/guild safely
        user_obj, guild_obj = _actor_from_ctx(ctx)
        user_id = user_obj.id

        account_summary = await governor_account_service.get_account_summary_for_user(user_id)
        if not account_summary.ok:
            await ctx.followup.send(
                f"Registry is temporarily unavailable: `{account_summary.error}`",
                ephemeral=True,
            )
            return

        gov_ids = list(account_summary.governor_ids)
        if not gov_ids:
            await ctx.followup.send(
                "I don’t see any governor accounts linked to you. Use `/link_account` first.",
                ephemeral=True,
            )
            return

        # Friendly account names for the dropdown
        account_names = list(account_summary.account_names)
        name_to_id = account_summary.name_to_id

        # Initial slice & payload
        slice_key = "wtd"

        # Find the user's Main from the same registry block
        default_choice = account_summary.default_choice

        # Governor IDs to load for the initial render
        if default_choice == "ALL":
            initial_gov_ids = gov_ids
        else:
            gid = name_to_id.get(default_choice)
            initial_gov_ids = [gid] if gid else gov_ids  # fallback if mapping missing

        payload = await get_stats_payload(user_id, initial_gov_ids, slice_key)
        rows = (payload or {}).get("rows") or []
        if not rows:
            await ctx.followup.send(
                "No stats available yet for your linked accounts. Try again after the next scan.",
                ephemeral=True,
            )
            return

        # If registry names are missing, derive from payload (PER rows)
        if not account_names:
            per_names = sorted(
                {
                    str(r.get("GovernorName") or "").strip()
                    for r in rows
                    if r.get("Grouping") == "PER" and r.get("GovernorName")
                }
            )
            account_names = per_names

        # ---- NEW: build view + embeds, send message, and store handles ----
        view = SliceButtons(
            requester_id=user_id,
            initial_slice=slice_key,
            account_options=account_names,
            current_choice=default_choice,
            governor_ids=gov_ids,
            name_to_id=name_to_id,
            # timeout defaults to STATS_VIEW_TIMEOUT
        )

        gid_for_choice = None if default_choice == "ALL" else name_to_id.get(default_choice)

        # Performance monitoring: track initial load time

        start = time.time()

        embeds, files = await build_embeds(
            slice_key, default_choice, payload, governor_id_for_choice=gid_for_choice
        )

        elapsed = time.time() - start
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "my_stats_initial_load",
                    "user_id": user_id,
                    "slice": slice_key,
                    "num_governors": len(gov_ids),
                    "num_accounts": len(account_names),
                    "elapsed_seconds": round(elapsed, 3),
                    "num_embeds": len(embeds),
                    "num_charts": len(files),
                }
            )
        except Exception:
            pass

        # Send ephemerally; store message + followup on the view so callbacks/timeout can edit/clean up
        try:
            msg = await ctx.followup.send(embeds=embeds, files=files, view=view, ephemeral=True)
        except Exception:
            # If something goes wrong sending with files, retry without attachments
            msg = await ctx.followup.send(embeds=embeds, view=view, ephemeral=True)

        view.message = msg
        view.followup = ctx.followup
        view.mark_live()

    @bot.slash_command(
        name="my_stats_export",
        description="Export your registered accounts’ stats to Excel, CSV, or Google Sheets format",
        guild_ids=[GUILD_ID],
    )
    @versioned("v3.02")  # bump version
    @safe_command
    @track_usage()
    async def my_stats_export(
        ctx: discord.ApplicationContext,
        format: str = discord.Option(
            str,
            name="format",
            description="Choose export format",
            choices=["Excel", "CSV", "GoogleSheets"],
            default="Excel",
            required=False,
        ),
        days: int = discord.Option(
            int,
            name="days",
            description="Number of days to include (min: 30, max: 360)",
            min_value=30,
            max_value=360,
            default=90,
            required=False,
        ),
    ):
        """
        Export your stats to a downloadable file.

        Supports Excel (.xlsx), CSV, and Google Sheets-compatible formats.
        """
        await safe_defer(ctx, ephemeral=True)

        export_file = None

        try:
            user_id = ctx.author.id
            username = ctx.author.display_name or ctx.author.name

            outcome = await stats_export_service.build_personal_stats_export(
                discord_user_id=user_id,
                display_name=username,
                requested_format=format,
                days=days,
            )
            if outcome.status != "ok" or outcome.export_file is None:
                await ctx.followup.send(
                    f"Error: {outcome.message or 'Export could not be prepared.'}",
                    ephemeral=True,
                )
                return

            export_file = outcome.export_file
            file_obj = discord.File(export_file.file_path, filename=export_file.filename)

            embed = discord.Embed(
                title=f"{export_file.format_emoji} Stats Export ({export_file.format_name})",
                description=export_file.description,
                color=0x2ECC71,
            )
            embed.add_field(
                name="File Info",
                value=(
                    f"**Accounts:** {len(export_file.governor_ids)}\n"
                    f"**Daily Records:** {export_file.row_count:,}\n"
                    f"**Date Range:** {export_file.days} days"
                ),
                inline=False,
            )
            embed.add_field(
                name="How to Open",
                value=export_file.instructions,
                inline=False,
            )
            embed.set_footer(
                text=(
                    f"Exported {export_file.row_count:,} records for "
                    f"{len(export_file.governor_ids)} account(s) - "
                    "Data refreshed daily at ~06:00 UTC"
                )
            )

            await ctx.followup.send(embed=embed, file=file_obj, ephemeral=True)

            try:
                from file_utils import emit_telemetry_event

                emit_telemetry_event(export_file.telemetry)
            except Exception:
                pass

        except Exception as exc:
            logger.exception("Failed to export stats for user %s", ctx.author.id)
            await ctx.followup.send(
                f"Export failed: {type(exc).__name__}\n\nPlease try again or contact support.",
                ephemeral=True,
            )

        finally:
            stats_export_service.cleanup_export_file(export_file)

    @stats_group.command(
        name="player",
        description="(Leadership) View stats for a player by GovernorID or fuzzy name",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
    @safe_command
    @is_admin_or_leadership()
    @track_usage()
    async def player_stats_command(
        ctx,
        governor_id: int = discord.Option(
            int,
            "Governor ID (optional if using name)",
            required=False,
            default=0,
        ),
        name: str = discord.Option(
            str,
            "Partial governor name (optional if using ID)",
            required=False,
            default="",
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        # Resolve actor (robust across forks)
        user_obj, _ = _actor_from_ctx(ctx)
        requester_id = user_obj.id

        # Resolve GovernorID(s)
        gov_ids: list[int] = []
        if governor_id:
            gov_ids = [int(governor_id)]
        elif name.strip():
            # Fuzzy match from your cached helper (label, value=str(gid)) pairs expected
            try:
                matches = autocomplete_choices(name.strip(), limit=5)  # -> List[Tuple[str, str]]
            except Exception:
                matches = []
            # Dedupe and coerce to int
            seen = set()
            for _, val in matches:
                try:
                    gid = int(val)
                except (TypeError, ValueError):
                    continue
                if gid not in seen:
                    seen.add(gid)
                    gov_ids.append(gid)
        else:
            await ctx.followup.send(
                "Provide a **GovernorID** or a **partial name**.", ephemeral=True
            )
            return

        if not gov_ids:
            await ctx.followup.send("No matching governors found.", ephemeral=True)
            return

        # Initial slice & payload
        slice_key = "wtd"
        payload = await get_stats_payload(requester_id, gov_ids, slice_key)
        rows = (payload or {}).get("rows") or []
        if not rows:
            await ctx.followup.send(
                "No stats available yet for that player/selection.", ephemeral=True
            )
            return

        # Build account names & name->id map
        # Prefer PER rows for names; fall back to fuzzy labels if needed
        per_names = sorted(
            {
                r.get("GovernorName", "")
                for r in rows
                if r.get("Grouping") == "PER" and r.get("GovernorName")
            }
        )
        account_options = per_names[:]  # dropdown labels

        name_to_id: dict[str, int] = {}
        # From payload (authoritative)
        for r in rows:
            if r.get("Grouping") == "PER":
                gname = str(r.get("GovernorName") or "").strip()
                try:
                    gid = int(r.get("GovernorID"))
                except (TypeError, ValueError):
                    continue
                if gname and gid:
                    name_to_id[gname] = gid
        # If empty (e.g., ALL rows only), seed from fuzzy match labels if available
        if not name_to_id and name.strip():
            try:
                matches = autocomplete_choices(name.strip(), limit=5)
            except Exception:
                matches = []
            for label, val in matches:
                try:
                    name_to_id[str(label).strip()] = int(val)
                except (TypeError, ValueError):
                    continue
            if not account_options:
                account_options = list(name_to_id.keys())

        # Decide initial choice
        choice = "ALL" if len(gov_ids) > 1 else (account_options[0] if account_options else "ALL")

        # Build embed & view
        embeds, files = await build_embeds(slice_key, choice, payload)
        view = SliceButtons(
            requester_id=requester_id,
            initial_slice=slice_key,
            account_options=account_options,  # names for dropdown
            current_choice=choice,
            governor_ids=gov_ids,
            name_to_id=name_to_id or None,  # enables per-account switching
            timeout=14 * 60,
        )

        if files:
            msg = await ctx.followup.send(embeds=embeds, files=files, view=view, ephemeral=True)
        else:
            msg = await ctx.followup.send(embeds=embeds, view=view, ephemeral=True)

        # Let the View edit this message on timeout
        try:
            view.message = msg
        except Exception:
            pass

    @bot.slash_command(
        name="mykvkhistory",
        description="View your KVK-by-KVK history as a chart and table.",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)
    @versioned("v1.09")
    @safe_command
    @track_usage()
    async def mykvkhistory(
        ctx: discord.ApplicationContext,
        ephemeral: bool = discord.Option(bool, "Only show to me", required=False, default=False),
        governor_id: int = discord.Option(
            int, "Governor ID (optional)", required=False, default=None
        ),
    ):
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/mykvkhistory",
                new_path="/kvk history",
                detail="The new command includes History, Summary, Trends, and CSV export controls.",
            ),
            ephemeral=True,
        )
        return

    @bot.slash_command(
        name="kvk_rankings",
        description="Leaderboard for current KVK: Power, Kills, % Kill Target, Deads, or DKP.",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v2.00")  # Updated version for PR3
    @safe_command
    @track_usage()
    async def kvk_rankings(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=False)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/kvk_rankings",
                new_path="/kvk rankings type:kvk",
                detail="The new rankings browser includes visual Top 10 cards, Top 25/50 views, My Rank, and CSV export.",
            ),
            ephemeral=False,
        )
        return

    @kvk_admin_group.command(
        name="export_all",
        description="Export all-kingdom KVK tabs",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_export_all(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
        sheet_name: str = discord.Option(
            str,
            "Primary Google Sheet name",
            required=False,
            default=KVK_SHEET_NAME,
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        # Default sheet name from constants (allows slash arg override)
        sheet_name = kvk_admin_service.normalize_sheet_name(sheet_name, KVK_SHEET_NAME)

        try:
            resolved_kvk_no = await asyncio.to_thread(kvk_admin_service.resolve_kvk_no, kvk_no)
        except Exception as e:
            logger.exception("[/kvk_admin export_all] could not resolve KVK")
            await ctx.followup.send(
                f"Could not resolve KVK `{kvk_no}`: `{type(e).__name__}: {e}`",
                ephemeral=True,
            )
            return

        await ctx.followup.send(
            f"Exporting KVK `{resolved_kvk_no}` to **{sheet_name}**...", ephemeral=True
        )

        try:
            result = await asyncio.to_thread(
                kvk_admin_service.run_export_all,
                kvk_no=resolved_kvk_no,
                sheet_name=sheet_name,
                server=SERVER,
                database=DATABASE,
                username=USERNAME,
                password=PASSWORD,
                credentials_file=CREDENTIALS_FILE,
                alert_channel=ctx.channel,
                event_loop=ctx.bot.loop,
                runner=run_kvk_proc_exports_with_alerts,
            )
        except Exception as e:
            logger.exception("[/kvk_admin export_all] export failed")
            await ctx.followup.send(
                f"💥 Export failed for KVK `{kvk_no}`: `{type(e).__name__}: {e}`",
                ephemeral=True,
            )
            return

        if result.ok:
            await ctx.followup.send(
                f"✅ Exported KVK `{result.kvk_no}` to **{result.sheet_name}**.", ephemeral=True
            )
        else:
            await ctx.followup.send(
                f"💥 Export failed for KVK `{result.kvk_no}`. Check logs.", ephemeral=True
            )

    @kvk_admin_group.command(
        name="recompute",
        description="Recompute windowed outputs for the current KVK",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_recompute(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
    ):
        await safe_defer(ctx, ephemeral=True)
        try:
            result = await asyncio.to_thread(kvk_admin_service.recompute_kvk_windows, kvk_no)
            await ctx.followup.send(
                f"✅ Recomputed KVK `{result.kvk_no}` in `{result.duration_seconds:.2f}s`.",
                ephemeral=True,
            )
        except Exception as e:
            await ctx.followup.send(f"💥 {type(e).__name__}: {e}", ephemeral=True)

    @kvk_admin_group.command(
        name="list_scans",
        description="List recent scans for a KVK",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_list_scans(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
        limit: int = discord.Option(
            int,
            "How many recent scans to show",
            required=False,
            default=20,
        ),
    ):
        await safe_defer(ctx, ephemeral=True)
        try:
            result = await asyncio.to_thread(kvk_admin_service.list_recent_scans, kvk_no, limit)

            chunks = _split_discord_content(kvk_admin_service.format_recent_scans_message(result))
            for chunk in chunks:
                await ctx.followup.send(content=chunk, ephemeral=True)
        except Exception as e:
            await ctx.followup.send(f"❌ {type(e).__name__}: {e}", ephemeral=True)

    @kvk_admin_group.command(
        name="test_embed",
        description="🧪 Post the KVK daily embed in test mode",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")  # bump to force re-register
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_kvk_embed(
        ctx: discord.ApplicationContext,
        post_here: bool = discord.Option(  # <-- TYPE first, not default
            bool,
            "Post in THIS channel? (False → Stats Alert channel)",
            required=False,
            default=True,
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        context = await asyncio.to_thread(
            kvk_admin_service.load_embed_test_context,
            is_currently_kvk_checker=is_currently_kvk,
            server=SERVER,
            database=DATABASE,
            username=USERNAME,
            password=PASSWORD,
        )
        ts = context.timestamp_label
        is_kvk = context.is_kvk

        try:
            if post_here:
                # Directly call the internal builder to post in the invoking channel, test-mode (no ping)
                await send_kvk_embed(ctx.bot, ctx.channel, ts, is_test=True)
                where = ctx.channel.mention
            else:
                # Use the public entrypoint; test-mode skips daily-send guards and pings, posts to Stats channel
                await send_stats_update_embed(ctx.bot, ts, is_kvk, is_test=True)
                where = f"<#{STATS_ALERT_CHANNEL_ID}>"

            await ctx.followup.send(
                f"✅ Sent KVK test embed to {where} (is_kvk={is_kvk}).", ephemeral=True
            )
        except Exception as e:
            logger.exception("[/kvk_admin test_embed] failed")
            await ctx.followup.send(
                f"❌ Failed to send test embed:\n`{type(e).__name__}: {e}`", ephemeral=True
            )

    @kvk_admin_group.command(
        name="window_preview",
        description="Show KVK windows with scan edges, scan counts, and row counts",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.08")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def kvk_window_preview(
        ctx,
        kvk_no: int = discord.Option(int, "KVK number (0 = current)", required=False, default=0),
    ):
        await safe_defer(ctx, ephemeral=True)

        result = await asyncio.to_thread(kvk_admin_service.load_window_preview, kvk_no)
        body = kvk_admin_service.format_window_preview_table(result)

        desc = (
            f"KVK **{result.kvk_no}** — window preview at "
            f"{result.generated_at_utc.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        if result.bad_ranges:
            desc += f"\n⚠️ {len(result.bad_ranges)} window(s) have End < Start."

        embed = discord.Embed(
            title="KVK Window Preview", description=desc, color=discord.Color.blurple()
        )
        embed.add_field(name="Windows", value=body, inline=False)

        await ctx.followup.send(embed=embed, ephemeral=True)

    def _format_validate_embed(report) -> discord.Embed:
        embed = discord.Embed(
            title="CrystalTech Validation",
            description=report.summary(),
            color=discord.Color.green() if report.ok else discord.Color.red(),
        )
        # Show up to 10 issues for brevity
        shown = 0
        for issue in report.issues:
            if shown >= 10:
                remaining = len(report.issues) - shown
                if remaining > 0:
                    embed.add_field(
                        name="…", value=f"+{remaining} more issues not shown", inline=False
                    )
                break
            loc = []
            if issue.path_id:
                loc.append(f"path={issue.path_id}")
            if issue.step_uid:
                loc.append(f"step={issue.step_uid}")
            where = f" ({', '.join(loc)})" if loc else ""
            embed.add_field(
                name=f"[{issue.level}] {issue.code}{where}",
                value=(issue.message[:512] + ("…" if len(issue.message) > 512 else "")) or "—",
                inline=False,
            )
            shown += 1
        return embed

    @bot.slash_command(
        name="honor_rankings",
        description="Show the latest Honour Top-N (default 10, max 50).",
        guild_ids=[GUILD_ID],
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def honor_rankings(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=False)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/honor_rankings",
                new_path="/kvk rankings type:honor",
                detail="Honor rankings now live in the unified KVK rankings browser.",
            ),
            ephemeral=False,
        )
        return

    @honor_group.command(
        name="purge_last",
        description="Purge the latest Honour scan (test cleanup).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def honor_purge_last(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)

        deleted = await asyncio.to_thread(purge_latest_honor_scan)

        if deleted > 0:
            title = "✅ Purged latest Honour scan"
            desc = f"Deleted **{deleted}** player rows and the scan header."
            color = discord.Color.orange()
        else:
            title = "ℹ️ Nothing to purge"
            desc = "No KVK or scan was found."
            color = discord.Color.dark_grey()

        embed = discord.Embed(title=title, description=desc, color=color)
        await ctx.followup.send(embed=embed, ephemeral=True)

    bot.add_application_command(kvk_admin_group)
    bot.add_application_command(stats_group)
    bot.add_application_command(honor_group)
