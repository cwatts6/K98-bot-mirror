from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, INVENTORY_UPLOAD_CHANNEL_ID
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from core.interaction_safety import safe_command, safe_defer
from decoraters import admin_only, channel_only, track_usage
from inventory import audit_service, reporting_service
from inventory.models import InventoryAuditRecord
from ui.views.inventory_report_views import (
    send_inventory_preference_prompt,
    start_myinventory_command,
)
from ui.views.inventory_views import start_import_command
from versioning import versioned

logger = logging.getLogger(__name__)


def register_inventory(bot: ext_commands.Bot) -> None:
    inventory_group = discord.SlashCommandGroup(
        "inventory",
        "Inventory admin controls",
        guild_ids=[GUILD_ID],
    )

    @inventory_group.command(
        name="import",
        description="Import a resources, speedups, or materials inventory screenshot",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @channel_only(
        INVENTORY_UPLOAD_CHANNEL_ID,
        admin_override=True,
        missing_config_message=(
            "Inventory imports are not configured yet. Missing inventory channel."
        ),
    )
    @track_usage()
    async def import_inventory(ctx: discord.ApplicationContext) -> None:
        await safe_defer(ctx, ephemeral=True)
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
        description="View your latest inventory report",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def myinventory(ctx: discord.ApplicationContext) -> None:
        try:
            final_visibility = await reporting_service.get_visibility_preference_or_none(
                int(ctx.user.id)
            )
        except Exception:
            logger.exception("myinventory_preference_resolution_failed actor=%s", ctx.user.id)
            await safe_defer(ctx, ephemeral=True)
            await ctx.followup.send(
                "Inventory reporting preferences are not available yet. Please contact an admin.",
                ephemeral=True,
            )
            return

        if final_visibility is None:
            await safe_defer(ctx, ephemeral=True)
            await send_inventory_preference_prompt(ctx)
            return

        await safe_defer(ctx, ephemeral=True)
        try:
            await start_myinventory_command(
                ctx=ctx,
                visibility=final_visibility,
            )
        except PermissionError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except ValueError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception(
                "myinventory_command_failed actor=%s",
                ctx.user.id,
            )
            await ctx.followup.send(
                "Inventory report generation failed. Please try again or contact an admin.",
                ephemeral=True,
            )

    @bot.slash_command(
        name="inventory_preferences",
        description="Choose whether inventory reports are private or public",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def inventory_preferences(ctx: discord.ApplicationContext) -> None:
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/inventory_preferences",
                new_path="/me preferences",
                detail="Profile preferences now manage private/public inventory report visibility alongside timezone, location, and language.",
            ),
            ephemeral=True,
        )
        return

    @bot.slash_command(
        name="export_inventory",
        description="Export your approved inventory records",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def export_inventory(
        ctx: discord.ApplicationContext,
        format: str = discord.Option(
            str,
            "Choose export format",
            choices=["Excel", "CSV", "GoogleSheets"],
            required=False,
            default="Excel",
        ),
        view: str = discord.Option(
            str,
            "Inventory records to export",
            choices=["Resources", "Speedups", "Materials", "All"],
            required=False,
            default="All",
        ),
        governor: int | None = discord.Option(
            int,
            "Governor ID to export (optional; defaults to all registered governors)",
            required=False,
            default=None,
        ),
        days: int = discord.Option(
            int,
            "Number of days to include",
            min_value=1,
            max_value=366,
            required=False,
            default=366,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/export_inventory",
                new_path="/me exports",
                detail="The export centre now provides inventory exports from the same private self-service menu.",
            ),
            ephemeral=True,
        )
        return

    @inventory_group.command(
        name="audit",
        description="Admin: review inventory import batches and retained debug references",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @admin_only(denial_message="You do not have permission to use this command.")
    @track_usage()
    async def inventory_import_audit(
        ctx: discord.ApplicationContext,
        status: str = discord.Option(
            str,
            "Import status filter",
            choices=[
                "All",
                "Awaiting Upload",
                "Analysed",
                "Approved",
                "Rejected",
                "Cancelled",
                "Failed",
            ],
            required=False,
            default="All",
        ),
        import_type: str = discord.Option(
            str,
            "Import type filter",
            choices=["All", "Resources", "Speedups", "Materials", "Unknown"],
            required=False,
            default="All",
        ),
        governor: int | None = discord.Option(
            int,
            "Governor ID filter",
            required=False,
            default=None,
        ),
        discord_user_id: int | None = discord.Option(
            int,
            "Discord user ID filter",
            required=False,
            default=None,
        ),
        days: int = discord.Option(
            int,
            "Lookback days",
            min_value=1,
            max_value=366,
            required=False,
            default=30,
        ),
        limit: int = discord.Option(
            int,
            "Rows to show",
            min_value=1,
            max_value=25,
            required=False,
            default=10,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            parsed_status = audit_service.parse_audit_status(
                status.strip().lower().replace(" ", "_")
            )
            parsed_type = audit_service.parse_audit_import_type(import_type)
            records = await audit_service.fetch_inventory_audit(
                status=parsed_status,
                import_type=parsed_type,
                governor_id=governor,
                discord_user_id=discord_user_id,
                lookback_days=int(days),
                limit=int(limit),
            )
            embed = _build_inventory_audit_embed(records, days=int(days))
            await ctx.followup.send(embed=embed, ephemeral=True)
        except ValueError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception("inventory_import_audit_failed actor=%s", ctx.user.id)
            await ctx.followup.send(
                "Inventory import audit failed. Please try again or contact an admin.",
                ephemeral=True,
            )

    bot.add_application_command(inventory_group)


def _build_inventory_audit_embed(
    records: list[InventoryAuditRecord], *, days: int
) -> discord.Embed:
    embed = discord.Embed(
        title="Inventory Import Audit",
        description=f"Recent inventory import batches from the last {days} day(s).",
        color=discord.Color.blurple(),
    )
    if not records:
        embed.add_field(name="Results", value="No matching inventory import batches.", inline=False)
        return embed

    for record in records[:25]:
        confidence = (
            f"{record.confidence_score:.2f}" if record.confidence_score is not None else "n/a"
        )
        json_parts = audit_service.summarize_json_comparison(record)
        value = (
            f"Governor `{record.governor_id}` | User `{record.discord_user_id}`\n"
            f"type `{record.import_type or 'unknown'}` | flow `{record.flow_type}` | "
            f"confidence `{confidence}`\n"
            f"debug {record.debug_reference} | json `{json_parts}`"
        )
        embed.add_field(
            name=f"Batch {record.import_batch_id} - {record.status}",
            value=value[:1024],
            inline=False,
        )
    return embed
