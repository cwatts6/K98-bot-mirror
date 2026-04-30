from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import ADMIN_USER_ID, GUILD_ID, INVENTORY_UPLOAD_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import track_usage
from inventory import reporting_service
from inventory.models import InventoryReportVisibility
from ui.views.inventory_report_views import start_myinventory_command
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
    @track_usage()
    async def import_inventory(ctx: discord.ApplicationContext) -> None:
        await safe_defer(ctx, ephemeral=True)
        if not INVENTORY_UPLOAD_CHANNEL_ID:
            await ctx.followup.send(
                "Inventory imports are not configured yet. Missing inventory channel.",
                ephemeral=True,
            )
            return
        chan = getattr(ctx, "channel", None)
        chan_id = getattr(chan, "id", None)
        parent_id = getattr(chan, "parent_id", None)
        try:
            is_admin = int(ctx.user.id) == int(ADMIN_USER_ID)
        except Exception:
            is_admin = False
        if (
            not is_admin
            and chan_id != INVENTORY_UPLOAD_CHANNEL_ID
            and parent_id != INVENTORY_UPLOAD_CHANNEL_ID
        ):
            await ctx.followup.send(
                f"❌ This command may only be used in <#{INVENTORY_UPLOAD_CHANNEL_ID}>. Please try there.",
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

    @bot.slash_command(
        name="myinventory",
        description="View your latest resources or speedups inventory report",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def myinventory(
        ctx: discord.ApplicationContext,
        governor: int | None = discord.Option(
            int,
            "Governor ID to view (optional if you have one registered governor)",
            required=False,
            default=None,
        ),
        view: str = discord.Option(
            str,
            "Inventory view",
            choices=["Resources", "Speedups", "All"],
            required=False,
            default="All",
        ),
        report_range: str = discord.Option(
            str,
            "Report range",
            name="range",
            choices=["1M", "3M", "6M", "12M"],
            required=False,
            default="1M",
        ),
        visibility: str | None = discord.Option(
            str,
            "Output visibility; saved as your default when changed",
            choices=["Only Me", "Public Output Channel"],
            required=False,
            default=None,
        ),
    ) -> None:
        try:
            report_view = reporting_service.parse_report_view(view)
            parsed_range = reporting_service.parse_report_range(report_range)
            selected_visibility = reporting_service.parse_visibility(visibility)
            final_visibility = await reporting_service.resolve_visibility(
                discord_user_id=int(ctx.user.id),
                selected_visibility=selected_visibility,
            )
        except ValueError as exc:
            await safe_defer(ctx, ephemeral=True)
            await ctx.followup.send(str(exc), ephemeral=True)
            return
        except Exception:
            logger.exception("myinventory_preference_resolution_failed actor=%s", ctx.user.id)
            await safe_defer(ctx, ephemeral=True)
            await ctx.followup.send(
                "Inventory reporting preferences are not available yet. Please contact an admin.",
                ephemeral=True,
            )
            return

        await safe_defer(ctx, ephemeral=final_visibility == InventoryReportVisibility.ONLY_ME)
        try:
            await start_myinventory_command(
                ctx=ctx,
                governor_id=governor,
                report_view=report_view,
                range_key=parsed_range,
                visibility=final_visibility,
            )
        except PermissionError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except ValueError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception(
                "myinventory_command_failed actor=%s governor=%s",
                ctx.user.id,
                governor,
            )
            await ctx.followup.send(
                "Inventory report generation failed. Please try again or contact an admin.",
                ephemeral=True,
            )
