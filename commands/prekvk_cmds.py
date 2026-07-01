from __future__ import annotations

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, KVK_PLAYER_STATS_CHANNEL_ID
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from core.interaction_safety import safe_command, safe_defer
from decoraters import track_usage
from versioning import versioned

from .prekvk_admin_cmds import attach_prekvk_import_history


def register_prekvk(bot: ext_commands.Bot) -> None:
    group = discord.SlashCommandGroup(
        "prekvk",
        "PreKvK reports and diagnostics",
        guild_ids=[GUILD_ID],
    )

    @group.command(
        name="report",
        description="View the current PreKvK rankings report",
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def prekvk_report(
        ctx: discord.ApplicationContext,
        kvk_no: int | None = discord.Option(
            int,
            "Optional KVK number; defaults to the current KVK",
            required=False,
            default=None,
            min_value=1,
        ),
        sort_by: str = discord.Option(
            str,
            "Initial report ordering",
            choices=["Overall", "Stage 1", "Stage 2", "Stage 3"],
            required=False,
            default="Overall",
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/prekvk report",
                new_path="/kvk rankings type:prekvk",
                detail=(
                    "PreKvK rankings now live in the unified KVK rankings browser. "
                    f"Run it in <#{KVK_PLAYER_STATS_CHANNEL_ID}>."
                ),
            ),
            ephemeral=True,
        )
        return

    attach_prekvk_import_history(group)
    bot.add_application_command(group)
