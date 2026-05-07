from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, MGE_LEADERSHIP_CHANNEL_ID, MGE_SIMPLIFIED_FLOW_ENABLED
from core.interaction_safety import safe_command, safe_defer
from decoraters import (
    channel_only,
    is_admin_or_leadership_only,
    track_usage,
)
from mge.mge_embed_manager import sync_event_leadership_embed
from mge.mge_results_import import OverwriteConfirmationRequired, import_results_manual
from mge.mge_review_service import get_review_pool_with_summary
from ui.views.mge_leadership_board_view import MgeLeadershipBoardView
from ui.views.mge_results_overwrite_confirm_view import MgeResultsOverwriteConfirmView
from versioning import versioned

logger = logging.getLogger(__name__)


def _format_import_report(report: dict) -> str:
    if not report:
        return "No report generated."

    if report.get("type") == "open_top15":
        rows = report.get("rows", [])
        if not rows:
            return "Open report: no rows."
        lines = ["Open Top 15:"]
        for r in rows[:15]:
            lines.append(
                f"#{int(r.get('Rank') or 0)} • {r.get('PlayerName') or 'Unknown'} • {int(r.get('Score') or 0):,}"
            )
        return "\n".join(lines)

    return (
        "Controlled reconciliation:\n"
        f"- Awarded total: {int(report.get('awarded_total') or 0)}\n"
        f"- Matched actual: {int(report.get('matched_actual_total') or 0)}"
    )


def register_mge(bot: ext_commands.Bot) -> None:
    """Register MGE leadership command(s)."""

    @bot.slash_command(
        name="mge_leadership_board",
        description="Open leadership board and roster builder for an MGE event",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(MGE_LEADERSHIP_CHANNEL_ID, admin_override=True, allow_threads=True)
    @track_usage()
    async def mge_leadership_board(
        ctx: discord.ApplicationContext,
        event_id: int = discord.Option(int, "MGE event id", min_value=1),
    ):
        logger.info(
            "mge_leadership_board_command_used actor_discord_id=%s event_id=%s",
            ctx.user.id,
            event_id,
        )
        await safe_defer(ctx, ephemeral=True)

        if MGE_SIMPLIFIED_FLOW_ENABLED:
            refreshed = await sync_event_leadership_embed(
                bot=ctx.bot,
                event_id=int(event_id),
                channel_id=MGE_LEADERSHIP_CHANNEL_ID,
            )
            if refreshed:
                await ctx.followup.send(
                    (
                        f"✅ Leadership control center refreshed in <#{int(MGE_LEADERSHIP_CHANNEL_ID)}> "
                        f"for event `{event_id}`."
                    ),
                    ephemeral=True,
                )
            else:
                await ctx.followup.send(
                    "❌ Failed to refresh leadership control center.",
                    ephemeral=True,
                )
            return

        try:
            payload = await asyncio.to_thread(get_review_pool_with_summary, int(event_id))
        except Exception:
            logger.exception(
                "mge_leadership_board_failed actor_discord_id=%s event_id=%s",
                ctx.user.id,
                event_id,
            )
            await ctx.followup.send(
                "❌ Failed to load leadership board data. Please try again in a moment.",
                ephemeral=True,
            )
            return

        summary = payload.get("summary", {})

        view = MgeLeadershipBoardView(event_id=int(event_id))
        await ctx.followup.send(
            (
                f"📋 Leadership board opened for event `{event_id}`.\n"
                f"- Applicants: **{summary.get('total_rows', 0)}**\n"
                f"- By priority: `{summary.get('by_priority', {})}`\n"
                f"- Warnings: `{summary.get('warnings', {})}`\n\n"
                "Use **Open Roster Builder** below."
            ),
            view=view,
            ephemeral=True,
        )

    @bot.slash_command(
        name="mge_import_results",
        description="Manually import MGE results (.xlsx) for a completed event",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(MGE_LEADERSHIP_CHANNEL_ID, admin_override=True, allow_threads=True)
    @track_usage()
    async def mge_import_results(
        ctx: discord.ApplicationContext,
        event_id: int = discord.Option(int, "Completed event id", min_value=1),
        attachment: discord.Attachment = discord.Option(
            discord.Attachment,
            "xlsx file (mge_rankings_kd####_YYYYMMDD.xlsx)",
            required=True,
        ),
    ) -> None:
        logger.info(
            "mge_import_results_command_used actor_discord_id=%s event_id=%s filename=%s",
            ctx.user.id,
            event_id,
            attachment.filename if attachment else None,
        )
        await safe_defer(ctx, ephemeral=True)

        try:
            file_bytes = await attachment.read()
        except Exception:
            logger.exception(
                "mge_import_results_attachment_read_failed actor_discord_id=%s event_id=%s filename=%s",
                ctx.user.id,
                event_id,
                attachment.filename if attachment else None,
            )
            await ctx.followup.send("❌ Failed to read the uploaded file.", ephemeral=True)
            return

        try:
            result = await asyncio.to_thread(
                import_results_manual,
                file_bytes,
                attachment.filename,
                int(event_id),
                int(ctx.user.id),
                False,
            )
            report_text = _format_import_report(result.get("report", {}))
            await ctx.followup.send(
                (
                    "✅ MGE results imported.\n"
                    f"- EventId: `{result['event_id']}`\n"
                    f"- Mode: `{result['event_mode']}`\n"
                    f"- Rows: `{result['rows']}`\n"
                    f"- ImportId: `{result['import_id']}`\n\n"
                    f"{report_text}"
                ),
                ephemeral=True,
            )
            logger.info(
                "mge_import_results_success actor_discord_id=%s event_id=%s rows=%s import_id=%s mode=%s",
                ctx.user.id,
                result.get("event_id"),
                result.get("rows"),
                result.get("import_id"),
                result.get("event_mode"),
            )
            return
        except OverwriteConfirmationRequired:
            logger.info(
                "mge_import_results_overwrite_confirmation_required actor_discord_id=%s event_id=%s",
                ctx.user.id,
                event_id,
            )
        except ValueError as e:
            logger.warning(
                "mge_import_results_validation_failed actor_discord_id=%s event_id=%s error=%s",
                ctx.user.id,
                event_id,
                str(e),
            )
            await ctx.followup.send(f"❌ Import failed: `{e}`", ephemeral=True)
            return
        except Exception:
            logger.exception(
                "mge_import_results_unhandled_failure actor_discord_id=%s event_id=%s",
                ctx.user.id,
                event_id,
            )
            await ctx.followup.send(
                "❌ Import failed due to an unexpected error. Please retry and check logs.",
                ephemeral=True,
            )
            return

        view = MgeResultsOverwriteConfirmView(
            actor_discord_id=int(ctx.user.id),
            event_id=int(event_id),
            filename=attachment.filename,
            file_bytes=file_bytes,
        )
        await ctx.followup.send(
            (
                "⚠️ This event already has imported results.\n"
                "Overwrite will replace existing rows for this event.\n\n"
                "Click **Confirm Overwrite** to proceed."
            ),
            view=view,
            ephemeral=True,
        )

    @bot.slash_command(
        name="mge_refresh_cache",
        description="Refresh MGE commander caches from database",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(MGE_LEADERSHIP_CHANNEL_ID, admin_override=True, allow_threads=True)
    @track_usage()
    async def mge_refresh_cache(ctx: discord.ApplicationContext) -> None:
        logger.info(
            "mge_refresh_cache_command_used actor_discord_id=%s",
            ctx.user.id,
        )
        await safe_defer(ctx, ephemeral=True)

        try:
            from mge.mge_cache import refresh_mge_caches

            results = await asyncio.to_thread(refresh_mge_caches)
            commanders_ok = results.get("commanders", False)
            variant_ok = results.get("variant_commanders", False)

            if commanders_ok and variant_ok:
                # Read back counts for confirmation
                from mge.mge_cache import read_commanders_cache, read_variant_commanders_cache

                cmd_count = len(read_commanders_cache())
                var_count = len(read_variant_commanders_cache())
                await ctx.followup.send(
                    (
                        "✅ MGE caches refreshed successfully.\n"
                        f"- Commanders: **{cmd_count}** entries\n"
                        f"- Variant commanders: **{var_count}** entries"
                    ),
                    ephemeral=True,
                )
            else:
                await ctx.followup.send(
                    (
                        "⚠️ MGE cache refresh completed with issues.\n"
                        f"- Commanders: {'✅' if commanders_ok else '❌ failed/empty'}\n"
                        f"- Variant commanders: {'✅' if variant_ok else '❌ failed/empty'}"
                    ),
                    ephemeral=True,
                )
            logger.info(
                "mge_refresh_cache_complete commanders=%s variant_commanders=%s",
                commanders_ok,
                variant_ok,
            )
        except Exception:
            logger.exception(
                "mge_refresh_cache_failed actor_discord_id=%s",
                ctx.user.id,
            )
            await ctx.followup.send(
                "❌ Cache refresh failed. Check logs for details.",
                ephemeral=True,
            )
