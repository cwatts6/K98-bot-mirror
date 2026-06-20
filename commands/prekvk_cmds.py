from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from core.interaction_safety import safe_command, safe_defer
from decoraters import track_usage
from prekvk import report_service
from ui.views.prekvk_report_views import send_prekvk_report
from versioning import versioned

from .prekvk_admin_cmds import attach_prekvk_import_history

logger = logging.getLogger(__name__)


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
                detail="PreKvK rankings now live in the unified KVK rankings browser.",
            ),
            ephemeral=True,
        )
        return

        try:
            parsed_sort = report_service.parse_report_sort(sort_by)
            await send_prekvk_report(
                ctx=ctx,
                kvk_no=kvk_no,
                sort_by=parsed_sort,
                limit=10,
            )
        except ValueError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception(
                "prekvk_report_command_failed actor_discord_id=%s kvk_no=%s sort_by=%s",
                getattr(ctx.user, "id", None),
                kvk_no,
                sort_by,
            )
            await ctx.followup.send(
                "PreKvK report generation failed. Please try again or contact an admin.",
                ephemeral=True,
            )

    attach_prekvk_import_history(group)
    bot.add_application_command(group)
