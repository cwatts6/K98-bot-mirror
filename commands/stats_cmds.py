# commands/stats_cmds.py
from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import (
    GUILD_ID,
    KVK_PLAYER_STATS_CHANNEL_ID,
    STATS_ALERT_CHANNEL_ID,
)
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from constants import CREDENTIALS_FILE, DATABASE, KVK_SHEET_NAME, PASSWORD, SERVER, USERNAME
from core.discord_embed_limits import require_valid_embed_payload
from core.interaction_safety import safe_command, safe_defer
from core.operator_diagnostic_payloads import (
    safe_diagnostic_content as _safe_diagnostic_error,
)
from decoraters import (
    channel_only,
    is_admin_and_notify_channel,
    track_usage,
)
from gsheet_module import run_kvk_export_test, run_kvk_proc_exports_with_alerts
from kvk.services import kvk_admin_service
from stats_alerts.honors import purge_latest_honor_scan
from ui.views.leadership_player_review_views import send_leadership_player_review
from versioning import versioned

logger = logging.getLogger(__name__)
bot: ext_commands.Bot | None = None


def _split_discord_content(content: str, *, max_chars: int = 1900) -> list[str]:
    """Split command output into Discord-safe complete-line chunks."""
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

        if len(line) > max_chars:
            chunks.append("… 1 complete diagnostic row not shown.")
        else:
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
                    content=_safe_diagnostic_error(
                        "❌ Could not resolve the current KVK window:",
                        f"{type(e).__name__}: {e}",
                    )
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
                content=_safe_diagnostic_error(
                    "💥 Test export failed unexpectedly:", f"{type(e).__name__}: {e}"
                )
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
                    content=_safe_diagnostic_error(
                        "Failed to refresh cache:", f"{type(e).__name__}: {e}"
                    )
                )
            except Exception:
                try:
                    await ctx.followup.send(
                        _safe_diagnostic_error(
                            "Failed to refresh cache:", f"{type(e).__name__}: {e}"
                        ),
                        ephemeral=True,
                    )
                except Exception:
                    logger.exception(
                        "[/kvk_admin refresh_stats_cache] failed to report error to user"
                    )
            return

    @stats_group.command(
        name="player",
        description="Privately review one governor's leadership stats",
        guild_ids=[GUILD_ID],
    )
    @versioned("v2.00")
    @safe_command
    @track_usage()
    async def player_stats_command(
        ctx: discord.ApplicationContext,
        governor_id: int | None = discord.Option(
            int,
            "Exact Governor ID (use either ID or name)",
            required=False,
        ),
        name: str | None = discord.Option(
            str,
            "Governor name (use either name or ID)",
            required=False,
            max_length=100,
        ),
    ):
        await send_leadership_player_review(ctx, governor_id=governor_id, name=name)

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
                _safe_diagnostic_error(
                    f"Could not resolve KVK `{kvk_no}`:", f"{type(e).__name__}: {e}"
                ),
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
                _safe_diagnostic_error(
                    f"💥 Export failed for KVK `{kvk_no}`:", f"{type(e).__name__}: {e}"
                ),
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
            await ctx.followup.send(
                _safe_diagnostic_error("💥 Recompute failed:", f"{type(e).__name__}: {e}"),
                ephemeral=True,
            )

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
            await ctx.followup.send(
                _safe_diagnostic_error("❌ Failed to list scans:", f"{type(e).__name__}: {e}"),
                ephemeral=True,
            )

    @kvk_admin_group.command(
        name="test_embed",
        description="Preview the fighting-KVK embed in an isolated destination",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_kvk_embed(
        ctx,
        destination=discord.Option(discord.TextChannel, "Explicit diagnostic text destination"),
        action=discord.Option(
            str, "Run or inspect a preview", choices=["run", "status"], default="run"
        ),
        session=discord.Option(str, "Issued preview session token", required=False, default=None),
    ):
        from bot_config import ADMIN_USER_ID, NOTIFY_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID
        from core.interaction_safety import send_ephemeral
        from stats_alerts.diagnostics import validate_destination
        from stats_alerts.embeds.kvk import build_kvk_preview, publish_kvk_preview
        from stats_alerts.kvk_diagnostics import runner
        from utils import utcnow

        def check_destination():
            if ctx.user.id != int(ADMIN_USER_ID) or (
                ctx.channel.id != int(NOTIFY_CHANNEL_ID)
                and getattr(ctx.channel, "parent_id", None) != int(NOTIFY_CHANNEL_ID)
            ):
                raise ValueError("Preview permission changed")
            requester = destination.permissions_for(ctx.user)
            publisher = destination.permissions_for(ctx.guild.me)
            validate_destination(
                guild_id=ctx.guild.id,
                expected_guild_id=int(GUILD_ID),
                channel_guild_id=destination.guild.id,
                channel_id=destination.id,
                forbidden_channels={STATS_ALERT_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID},
                is_text=isinstance(destination, discord.TextChannel)
                and destination.type == discord.ChannelType.text,
                requester_can_send=requester.view_channel and requester.send_messages,
                bot_can_publish=publisher.view_channel
                and publisher.send_messages
                and publisher.embed_links
                and publisher.read_message_history,
            )

        async def build():
            check_destination()
            return await build_kvk_preview(utcnow().strftime("%Y-%m-%d %H:%M UTC"))

        async def publish(preview, message_id, before_send):
            return await publish_kvk_preview(
                ctx.bot, destination, preview, message_id, before_send, check_destination
            )

        try:
            check_destination()
            if not await safe_defer(ctx, ephemeral=True):
                return
            result = await runner.execute(
                guild_id=ctx.guild.id,
                channel_id=destination.id,
                owner_id=ctx.user.id,
                token=session,
                action=action,
                build=build,
                publish=publish,
            )
            snapshot = result.snapshot or {}
            operations = snapshot.get("operations") or []
            operation = operations[-1] if operations else {}
            message_id = result.receipt or snapshot.get("message_id")
            lines = [
                "**Fighting-KVK preview — outside production dispatch**",
                f"Outcome: **{result.outcome}** — {result.detail}",
                f"Session: `{result.session}`",
                f"Destination: `{destination.id}`",
                f"UTC: `{utcnow().isoformat()}`",
                f"Saved phase: `{operation.get('phase', 'none')}`",
                f"Operation: `{operation.get('token', 'none')}`",
            ]
            if message_id:
                lines.append(
                    f"Message: https://discord.com/channels/{ctx.guild.id}/{destination.id}/{message_id}"
                )
            await send_ephemeral(
                ctx.interaction, "\n".join(lines), allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception:
            logger.exception("[KVK PREVIEW] Command rejected or failed")
            await send_ephemeral(
                ctx.interaction,
                "Preview unavailable. Check destination, session ownership and logs. No automatic retry.",
                allowed_mentions=discord.AllowedMentions.none(),
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

        require_valid_embed_payload(embed)
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
