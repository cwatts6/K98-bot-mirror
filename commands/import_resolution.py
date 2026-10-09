"""Private admin adapter for evidence-bound import resolution."""

import asyncio

import discord

from core.interaction_safety import safe_command, safe_defer
from core.operator_diagnostic_payloads import safe_diagnostic_content
from decoraters import is_admin_and_notify_channel, track_usage
from services.import_resolution_service import operate_import_resolution
from versioning import versioned


def attach_import_resolution(group):
    @group.command(
        name="import_resolution",
        description="Inspect, preview or resolve an exact held stats import",
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    @is_admin_and_notify_channel()
    async def import_resolution(
        ctx,
        preparation_id: discord.Option(str, "Exact preparation UUID"),
        action: discord.Option(
            str, "Read status, preview, or confirm", choices=["status", "preview", "resolve"]
        ) = "status",
        confirmation: discord.Option(str, "Exact token returned by preview", required=False) = "",
        reason: discord.Option(str, "Audit reason for resolution", required=False) = "",
        accept_partial: discord.Option(
            bool, "Accept replacing unfinished reports from a committed import", required=False
        ) = False,
    ):
        from services.legacy_export_snapshot_service import drain_thread

        if not await safe_defer(ctx, ephemeral=True):
            return
        try:
            text = await drain_thread(
                operate_import_resolution,
                preparation_id,
                action,
                confirmation,
                reason,
                accept_partial,
                f"discord:{ctx.author.id}",
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            from kvk.dal.new_source_import_dal import SourceConflict
            from services.stats_import_outcome_service import event

            event(
                preparation_id,
                "admin_resolution",
                "held",
                action="inspect exact preparation; no blind retry",
                error=exc,
            )
            text = (
                str(exc)
                if isinstance(exc, (SourceConflict, ValueError))
                else "Resolution unavailable. Check the correlated stats_import_outcome log and SQL/runtime readiness. No blind retry or import replay is permitted."
            )
        await ctx.respond(
            safe_diagnostic_content("", text),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
