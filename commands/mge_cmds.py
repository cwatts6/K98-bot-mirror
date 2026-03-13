from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, MGE_LEADERSHIP_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import channel_only, is_admin_or_leadership_only, track_usage
from mge.mge_review_service import get_review_pool_with_summary
from ui.views.mge_leadership_board_view import MgeLeadershipBoardView
from versioning import versioned

logger = logging.getLogger(__name__)


def register_mge(bot: ext_commands.Bot) -> None:
    """Register MGE leadership scaffold command(s)."""

    @bot.slash_command(
        name="mge_leadership_board",
        description="Open leadership review board scaffold for an MGE event",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
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

        payload = await asyncio.to_thread(get_review_pool_with_summary, int(event_id))
        summary = payload.get("summary", {})

        view = MgeLeadershipBoardView(event_id=int(event_id))

        await ctx.followup.send(
            (
                f"📋 Leadership board opened for event `{event_id}`.\n"
                f"- Applicants: **{summary.get('total_rows', 0)}**\n"
                f"- By priority: `{summary.get('by_priority', {})}`\n"
                f"- Warnings: `{summary.get('warnings', {})}`"
            ),
            view=view,
            ephemeral=True,
        )
