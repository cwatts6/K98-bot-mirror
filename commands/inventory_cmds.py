from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, INVENTORY_UPLOAD_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import channel_only, track_usage
from ui.views.inventory_views import start_import_command
from versioning import versioned

logger = logging.getLogger(__name__)


def register_inventory(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="import_inventory",
        description="Import a resources or speedups inventory screenshot",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @channel_only(INVENTORY_UPLOAD_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def import_inventory(ctx: discord.ApplicationContext) -> None:
        await safe_defer(ctx, ephemeral=True)
        if not INVENTORY_UPLOAD_CHANNEL_ID:
            await ctx.followup.send(
                "Inventory imports are not configured yet. Missing inventory channel.",
                ephemeral=True,
            )
            return
        try:
            await start_import_command(ctx, bot)
        except PermissionError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except ValueError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception("import_inventory_command_failed actor=%s", ctx.user.id)
            await ctx.followup.send(
                "Inventory import setup failed. Please try again or contact an admin.",
                ephemeral=True,
            )
