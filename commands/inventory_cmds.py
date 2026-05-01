from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import ADMIN_USER_ID, GUILD_ID, INVENTORY_UPLOAD_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import _is_admin, track_usage
from inventory import audit_service, export_service, reporting_service
from inventory.models import InventoryAuditRecord, InventoryReportVisibility
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

    @bot.slash_command(
        name="export_inventory",
        description="Export your approved resources and speedups inventory records",
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
            choices=["Resources", "Speedups", "All"],
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
        export_file = None
        try:
            export_format = export_service.parse_export_format(format)
            export_view = export_service.parse_export_view(view)
            export_file = await export_service.build_inventory_export_file(
                discord_user_id=int(ctx.user.id),
                username=getattr(ctx.user, "display_name", None)
                or getattr(ctx.user, "name", "user"),
                export_format=export_format,
                view=export_view,
                governor_id=governor,
                lookback_days=int(days),
                is_admin=_is_admin(ctx.user),
                discord_user=ctx.user,
            )
            file_obj = discord.File(str(export_file.path), filename=export_file.filename)
            await ctx.followup.send(
                content=(
                    "Inventory export ready. "
                    f"`{export_file.row_count}` raw approved row(s), "
                    f"`{len(export_file.governor_ids)}` governor(s)."
                ),
                file=file_obj,
                ephemeral=True,
            )
        except PermissionError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except ValueError as exc:
            await ctx.followup.send(str(exc), ephemeral=True)
        except Exception:
            logger.exception("export_inventory_command_failed actor=%s", ctx.user.id)
            await ctx.followup.send(
                "Inventory export failed. Please try again or contact an admin.",
                ephemeral=True,
            )
        finally:
            if export_file is not None:
                export_service.cleanup_export_file(export_file)

    @bot.slash_command(
        name="inventory_import_audit",
        description="Admin: review inventory import batches and retained debug references",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
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
        if not _is_admin(ctx.user):
            await ctx.followup.send("You do not have permission to use this command.", ephemeral=True)
            return
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
