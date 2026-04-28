from __future__ import annotations

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_or_leadership_only, track_usage
from server_activity.activity_service import get_top_users, resolve_window
from versioning import versioned


def _render_activity_top(result) -> str:
    if not result.rows:
        return f"No tracked activity found for the last {result.window}."

    lines = [f"Top active users - last {result.window}"]
    for idx, row in enumerate(result.rows, start=1):
        lines.append(
            f"{idx}. <@{row.user_id}> - {row.score} "
            f"(messages {row.messages}, reactions {row.reactions}, voice {row.voice_events})"
        )
    return "\n".join(lines)


def register_activity(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="activity_top",
        description="Show the top active users for a recent window.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def activity_top(
        ctx: discord.ApplicationContext,
        window: str = discord.Option(
            str,
            choices=["24h", "3d", "7d"],
            default="24h",
            required=True,
            description="Activity window",
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        try:
            resolved_window = resolve_window(window)
        except ValueError:
            await ctx.interaction.edit_original_response(content="Invalid activity window.")
            return

        guild_id = getattr(getattr(ctx, "guild", None), "id", None)
        if not guild_id:
            await ctx.interaction.edit_original_response(
                content="This command must be used in a server."
            )
            return

        result = await get_top_users(guild_id=int(guild_id), window=resolved_window, limit=10)
        await ctx.interaction.edit_original_response(content=_render_activity_top(result))
