# commands/stats_cmds.py
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
import time

import discord
from discord.ext import commands as ext_commands

from bot_config import (
    GUILD_ID,
    KVK_PLAYER_STATS_CHANNEL_ID,
    STATS_ALERT_CHANNEL_ID,
)
from build_KVKrankings_embed import build_kvkrankings_embed
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
from embed_utils import build_stats_embed
from gsheet_module import run_kvk_export_test, run_kvk_proc_exports_with_alerts
from honor_rankings_view import HonorRankingView, build_honor_rankings_embed
from kvk.services import kvk_admin_service
from profile_cache import autocomplete_choices
from registry.account_slots import ACCOUNT_ORDER
from services import (
    governor_account_service,
    kvk_history_service,
    stats_export_service,
)
from stats_alerts.embeds.kvk import send_kvk_embed
from stats_alerts.honors import get_latest_honor_top, purge_latest_honor_scan
from stats_alerts.interface import send_stats_update_embed
from stats_alerts.kvk_meta import is_currently_kvk
from stats_cache_helpers import load_last_kvk_map
from stats_service import get_stats_payload
from ui.views.kvk_history_view import KVKHistoryView
from ui.views.kvk_personal_views import MyKVKStatsSelectView
from ui.views.registry_views import MyRegsActionView
from ui.views.stats_views import KVKRankingView
from utils import load_stat_cache, load_stat_row, normalize_governor_id
from versioning import versioned

logger = logging.getLogger(__name__)
bot: ext_commands.Bot | None = None
# ACCOUNT_ORDER imported from account_picker — single canonical definition.


# MyKVKStatsSelectView is defined canonically in ui.views.kvk_personal_views and imported above.


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
        logger.info("[COMMAND] /test_kvk_export invoked by %s (kvk_no=%s)", ctx.user, kvk_no)

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
                logger.exception("[COMMAND] /test_kvk_export could not resolve KVK")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Could not resolve the current KVK window: `{type(e).__name__}: {e}`"
                )
                return

        sheet_name = (sheet_name or KVK_SHEET_NAME).strip() or KVK_SHEET_NAME

        # Let the invoker know we're starting
        try:
            await ctx.interaction.edit_original_response(
                content=f"⏳ Running KVK export TEST for KVK `{kvk_no}` (primary sheet: **{sheet_name}**)…"
            )
        except Exception:
            pass

        start_ts = datetime.utcnow()

        try:
            # Run the test export in a thread (blocking IO / network)
            meta = await asyncio.to_thread(
                run_kvk_export_test,
                SERVER,
                DATABASE,
                USERNAME,
                PASSWORD,
                int(kvk_no),
                sheet_name,
                CREDENTIALS_FILE,
                create_primary,
                export_pass4,
                export_altar,
                export_pass7,
            )
        except Exception as e:
            logger.exception("[COMMAND] /test_kvk_export crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 Test export failed unexpectedly: `{type(e).__name__}: {e}`"
            )
            return

        dur = (datetime.utcnow() - start_ts).total_seconds()

        # Build a helpful embed summarising the metadata returned by run_kvk_export_test()
        try:
            embed = discord.Embed(
                title=f"🧪 KVK Export Test — KVK {kvk_no}",
                description=f"Test run completed in `{dur:.1f}s`.",
                color=discord.Color.green(),
            )

            embed.add_field(name="KVK", value=str(kvk_no), inline=True)
            embed.add_field(name="Primary sheet", value=sheet_name, inline=True)
            embed.add_field(name="Triggered by", value=f"<@{ctx.user.id}>", inline=True)

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
                logger.exception("[COMMAND] /test_kvk_export failed to send result embed")

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
        # We always keep the selector private to the caller
        await safe_defer(ctx, ephemeral=True)

        account_summary = await governor_account_service.get_account_summary_for_user(ctx.user.id)
        if not account_summary.ok:
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not load registry: `{account_summary.error}`"
            )
            return

        if not account_summary.governor_ids:
            # Reuse your existing action view as a nice fallback
            view = MyRegsActionView(author_id=ctx.user.id, has_regs=False)
            msg = await ctx.interaction.edit_original_response(
                content="You don’t have any Governor accounts registered yet. Use the options below:",
                view=view,
            )
            view.set_message_ref(msg)
            return

        accounts = account_summary.ordered_accounts

        # Best-effort: load last-KVK cache via the TTL-backed in-process cache helper.
        last_kvk_map = {}
        try:
            last_kvk_map = await load_last_kvk_map()
            if not isinstance(last_kvk_map, dict):
                last_kvk_map = {}
        except Exception:
            logger.exception("[/mykvkstats] load_last_kvk_map failed")
            last_kvk_map = {}

        # Single-account path → post PUBLIC embed immediately
        if len(accounts) == 1:
            ((_, info),) = accounts.items()
            gid = normalize_governor_id(info.get("GovernorID"))
            if not gid:
                await ctx.interaction.edit_original_response(
                    content="❌ Your registration has no valid Governor ID."
                )
                return

            try:
                # Offload potential IO-bound stat row load
                row = await asyncio.to_thread(load_stat_row, gid)
            except Exception as e:
                logger.exception("[/mykvkstats] load_stat_row failed")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Could not load stats: `{type(e).__name__}: {e}`"
                )
                return

            if not row:
                await ctx.interaction.edit_original_response(
                    content=f"❌ Stats not found for Governor ID `{gid}`."
                )
                return

            # Attach last-KVK row (if available) to the loaded stat row so embed builders can use it
            try:
                lk = last_kvk_map.get(str(gid))
                if lk:
                    # shallow attach; embed builders expect governor_data['last_kvk']
                    row["last_kvk"] = lk
            except Exception:
                logger.exception("[/mykvkstats] Failed to attach last_kvk for %s", gid)

            try:
                embeds, file = build_stats_embed(row, ctx.user)
                # build_stats_embed returns (list[discord.Embed], discord.File)
            except Exception as e:
                logger.exception("[/mykvkstats] build_stats_embed failed")
                await ctx.interaction.edit_original_response(
                    content=f"❌ Failed to build stats: `{type(e).__name__}: {e}`"
                )
                return

            # PUBLIC post (send all embeds together)
            try:
                if file is not None:
                    await ctx.channel.send(embeds=embeds, files=[file])
                else:
                    await ctx.channel.send(embeds=embeds)
            except Exception:
                # fallback: send embeds only if file send fails
                try:
                    await ctx.channel.send(embeds=embeds)
                except Exception:
                    logger.exception("[/mykvkstats] failed to send stats embed(s) to channel")

            # Silence the ephemeral placeholder instead of confirming
            try:
                await ctx.interaction.edit_original_response(content=" ", view=None)
            except Exception:
                pass
            return

        # Multi-account path → ephemeral dropdown + helper buttons
        try:
            # Keep preferred ordering first, then append any remaining slots deterministically
            ordered_accounts = {slot: accounts[slot] for slot in ACCOUNT_ORDER if slot in accounts}
            # append remaining keys not in ACCOUNT_ORDER in sorted order
            remaining = [s for s in sorted(accounts.keys()) if s not in ordered_accounts]
            for s in remaining:
                ordered_accounts[s] = accounts[s]
            view = MyKVKStatsSelectView(ctx=ctx, accounts=ordered_accounts, author_id=ctx.user.id)
            # Attach last_kvk_map to the view so callbacks can reuse it when they load stat rows.
            # (The view callback should check for `self._last_kvk_map` and attach when building embeds.)
            try:
                view._last_kvk_map = last_kvk_map
            except Exception:
                # non-fatal; view may not accept new attrs in some contexts, but that's unlikely
                pass
        except Exception as e:
            logger.exception("[/mykvkstats] MyKVKStatsSelectView init failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build account selector: `{type(e).__name__}: {e}`"
            )
            return

        await ctx.interaction.edit_original_response(
            # architecture-check: allow
            content="Select an account below to view your stats:",
            view=view,
        )

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
            # Build the main player stats cache (existing behaviour)
            main_started = datetime.now(UTC)
            from player_stats_cache import (
                build_lastkvk_player_stats_cache,
                build_player_stats_cache,
            )

            main_result = None
            main_count = None
            main_error = None
            try:
                main_result = await build_player_stats_cache()
                if isinstance(main_result, int):
                    main_count = main_result
                elif isinstance(main_result, dict):
                    # prefer top-level "_meta".count if present, otherwise "count"
                    main_count = (main_result.get("_meta") or {}).get("count") or main_result.get(
                        "count"
                    )
            except Exception as e:
                main_error = f"{type(e).__name__}: {e}"
                logger.exception("[/refresh_stats_cache] build_player_stats_cache failed")

            main_dur = (datetime.now(UTC) - main_started).total_seconds()

            # Build the last-KVK cache (best-effort, report separately)
            last_started = datetime.now(UTC)
            last_result = None
            last_count = None
            last_error = None
            try:
                last_result = await build_lastkvk_player_stats_cache()
                if isinstance(last_result, dict):
                    # last_result expected shape: { "_meta": {...}, "<GovernorID>": {...}, ... }
                    last_count = (last_result.get("_meta") or {}).get("count") or last_result.get(
                        "count"
                    )
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.exception("[/refresh_stats_cache] build_lastkvk_player_stats_cache failed")

            last_dur = (datetime.now(UTC) - last_started).total_seconds()

            # Compose human-friendly message summarising both builds
            parts = []
            if main_error:
                parts.append(f"❌ Player stats cache build failed: `{main_error}`")
            else:
                if main_count is not None:
                    parts.append(
                        f"✅ Player stats cache refreshed ({main_count} records) ⏱ {main_dur:.1f}s"
                    )
                else:
                    parts.append(f"✅ Player stats cache refreshed ⏱ {main_dur:.1f}s")

            if last_error:
                parts.append(
                    f"⚠️ Last-KVK cache build failed (non-fatal): `{last_error}` — the main cache is available."
                )
            else:
                if last_count is not None:
                    parts.append(
                        f"✅ Last-KVK cache refreshed ({last_count} records) ⏱ {last_dur:.1f}s"
                    )
                else:
                    parts.append(f"✅ Last-KVK cache refreshed ⏱ {last_dur:.1f}s")

            # Final combined message
            msg = " \n".join(parts)
            logger.info("[/refresh_stats_cache] %s", msg.replace("\n", " | "))

            await ctx.interaction.edit_original_response(content=msg)

        except Exception as e:
            logger.exception("[/refresh_stats_cache] failed")
            try:
                await ctx.interaction.edit_original_response(
                    content=f"❌ Failed to refresh cache:\n```{type(e).__name__}: {e}```"
                )
            except Exception:
                # If editing the original response failed, try to send a followup
                try:
                    await ctx.followup.send(
                        f"❌ Failed to refresh cache: `{type(e).__name__}: {e}`", ephemeral=True
                    )
                except Exception:
                    logger.exception("[/refresh_stats_cache] failed to report error to user")

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
        await safe_defer(ctx, ephemeral=ephemeral)

        account_summary = await governor_account_service.get_account_summary_for_user(ctx.user.id)
        if not account_summary.ok and not governor_id:
            await ctx.followup.send(
                f"Registry is temporarily unavailable: `{account_summary.error}`",
                ephemeral=True,
            )
            return
        account_map = kvk_history_service.build_ordered_account_map(
            account_summary.ordered_accounts
        )  # {label: {GovernorID, GovernorName}}

        # If a Governor ID is provided, build a minimal map for it (works even with no registry)
        if governor_id:
            # Best-effort name discovery; fall back to the ID string
            try:
                from kvk_history_utils import fetch_history_for_governors

                df_lookup = fetch_history_for_governors([governor_id])
                gov_name = None
                for col in ("GovernorName", "Gov_Name", "Name"):
                    if col in df_lookup.columns and not df_lookup[col].dropna().empty:
                        gov_name = str(df_lookup[col].dropna().iloc[0])
                        break
                gov_name = gov_name or str(governor_id)
            except Exception:
                gov_name = str(governor_id)
            account_map = {"Lookup": {"GovernorID": int(governor_id), "GovernorName": gov_name}}
        elif not account_map:
            await ctx.followup.send(
                "❌ You haven't registered any accounts yet. Use `/register_governor` or pass a Governor ID here.",
                ephemeral=True,
            )
            return

        # Start on the provided governor_id when present, else Main/first
        default_id = (
            str(governor_id)
            if governor_id
            else kvk_history_service.pick_default_governor_id(account_map)
        )
        if not default_id:
            await ctx.followup.send(
                "❌ I couldn't find a valid Governor ID in your registered accounts.",
                ephemeral=True,
            )
            return

        view = KVKHistoryView(
            user=ctx.user,
            account_map=account_map,
            selected_ids=[default_id],  # start with just Main (or first)
            allow_all=True,
            ephemeral=ephemeral,  # <- pass through the user's choice
        )
        await view.initial_send(ctx)

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
        """
        Show KVK leaderboard with multi-column view.

        Default: Power (highest to lowest), Top 10, Page 1

        Features:
        - 5 sort metrics: Power, Kills, % Kill Target, Deads, DKP
        - 4 limit options: Top 10, 25, 50, 100
        - Automatic pagination for Top 100 (50 per page)
        - Excel-style sort indicator (▼) on active column

        Users can change sort metric and limit via dropdown/buttons.
        """
        await safe_defer(ctx, ephemeral=False)

        cache = load_stat_cache()
        rows = [r for k, r in cache.items() if k != "_meta"]
        if not rows:
            await ctx.followup.send(
                "⚠️ No stats cache available yet. Try again after the next scan/export."
            )
            return

        # Default: Power sort, Top 10, Page 1
        view = KVKRankingView(cache, metric="power", limit=10, timeout=120.0)
        embed = build_kvkrankings_embed(rows, "power", 10, page=1)

        # Fallback footer if helper didn't set one
        if not embed.footer or not embed.footer.text:
            last_ref = cache.get("_meta", {}).get("generated_at") or "unknown"
            embed.set_footer(text=f"Last refreshed: {last_ref}")

        resp = await ctx.followup.send(embed=embed, view=view)
        try:
            view.message = await ctx.interaction.original_response()
        except Exception:
            try:
                view.message = await resp.original_response()
            except Exception:
                view.message = None

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

        # Resolve current KVK if not provided
        if kvk_no == 0:
            try:
                kvk_no = await asyncio.to_thread(kvk_admin_service.resolve_kvk_no, kvk_no)
            except Exception:
                logger.exception("[/kvk_export_all] Could not resolve current KVK")
                kvk_no = 0
            if kvk_no == 0:
                await ctx.followup.send(
                    "❌ Could not resolve the current KVK window.", ephemeral=True
                )
                return

        # Default sheet name from constants (allows slash arg override)
        sheet_name = (sheet_name or KVK_SHEET_NAME).strip() or KVK_SHEET_NAME

        await ctx.followup.send(f"⏳ Exporting KVK `{kvk_no}` to **{sheet_name}**…", ephemeral=True)

        try:
            ok = await asyncio.to_thread(
                run_kvk_proc_exports_with_alerts,
                SERVER,
                DATABASE,
                USERNAME,
                PASSWORD,
                kvk_no,
                sheet_name,
                CREDENTIALS_FILE,
                ctx.channel,
                ctx.bot.loop,
            )
        except Exception as e:
            logger.exception("[/kvk_export_all] export failed")
            await ctx.followup.send(
                f"💥 Export failed for KVK `{kvk_no}`: `{type(e).__name__}: {e}`",
                ephemeral=True,
            )
            return

        if ok:
            await ctx.followup.send(
                f"✅ Exported KVK `{kvk_no}` to **{sheet_name}**.", ephemeral=True
            )
        else:
            await ctx.followup.send(
                f"💥 Export failed for KVK `{kvk_no}`. Check logs.", ephemeral=True
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

        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # Whether the season is currently KVK (for the send_stats_update_embed path)
        is_kvk = await asyncio.to_thread(is_currently_kvk, SERVER, DATABASE, USERNAME, PASSWORD)

        try:
            if post_here:
                # Directly call the internal builder to post in the invoking channel, test-mode (no ping)
                await send_kvk_embed(ctx.bot, ctx.channel, ts, is_test=True)
                where = ctx.channel.mention
            else:
                # Use the public entrypoint; test-mode skips daily-send guards and pings, posts to Stats channel
                await send_stats_update_embed(ctx.bot, ts, True, is_test=True)
                where = f"<#{STATS_ALERT_CHANNEL_ID}>"

            await ctx.followup.send(
                f"✅ Sent KVK test embed to {where} (is_kvk={is_kvk}).", ephemeral=True
            )
        except Exception as e:
            logger.exception("[/test_kvk_embed] failed")
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
        """
        /honor_rankings - show Top 10 honor by default and let user switch Top 10/25/50/100 with buttons.
        """
        # Defer to allow DB fetch
        await safe_defer(ctx, ephemeral=False)

        initial_limit = 10

        try:
            rows = await get_latest_honor_top(initial_limit)
        except Exception:
            logger.exception("[HONOR] get_latest_honor_top failed")
            rows = []

        if not rows:
            # graceful response if DB has no honor data
            await ctx.followup.send("No honor data found for the latest KVK.", ephemeral=False)
            return

        embed = build_honor_rankings_embed(rows, limit=initial_limit)
        view = HonorRankingView()
        await ctx.followup.send(embed=embed, view=view, ephemeral=False)

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
