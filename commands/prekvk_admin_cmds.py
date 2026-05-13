from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
from prekvk.diagnostics_service import format_history_rows, get_recent_import_history
from versioning import versioned

logger = logging.getLogger(__name__)


def register_prekvk_admin(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="prekvk_import_history",
        description="Show recent PreKvK import diagnostics",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def prekvk_import_history(
        ctx: discord.ApplicationContext,
        kvk_no: int = discord.Option(
            int,
            "Optional KVK number filter",
            required=False,
            default=None,
            min_value=1,
        ),
        status: str = discord.Option(
            str,
            "Filter: all, accepted, rejected, duplicate, failed",
            required=False,
            default="all",
        ),
        limit: int = discord.Option(
            int,
            "Rows to show",
            required=False,
            default=10,
            min_value=1,
            max_value=25,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)

        status_filter = str(status or "all").strip().lower()
        if status_filter in {"", "all", "*"}:
            status_filter = None
        elif status_filter not in {"accepted", "rejected", "duplicate", "failed"}:
            await ctx.followup.send(
                "Invalid status. Use `all`, `accepted`, `rejected`, `duplicate`, or `failed`.",
                ephemeral=True,
            )
            return

        try:
            rows = await asyncio.to_thread(
                get_recent_import_history,
                kvk_no=kvk_no,
                status=status_filter,
                limit=limit,
            )
        except Exception:
            logger.exception(
                "prekvk_import_history_failed actor_discord_id=%s kvk_no=%s status=%s",
                getattr(ctx.user, "id", None),
                kvk_no,
                status_filter,
            )
            await ctx.followup.send(
                "Failed to load PreKvK import history. Check logs for details.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="PreKvK Import History",
            description=format_history_rows(rows),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="KVK", value=str(kvk_no or "all"), inline=True)
        embed.add_field(name="Status", value=str(status_filter or "all"), inline=True)
        embed.add_field(name="Rows", value=str(len(rows)), inline=True)

        await ctx.followup.send(embed=embed, ephemeral=True)
