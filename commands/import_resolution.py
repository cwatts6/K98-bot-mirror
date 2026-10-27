"""Private admin adapter for evidence-bound import resolution."""

import asyncio

import discord

from core.interaction_safety import safe_command, safe_defer
from core.operator_diagnostic_payloads import safe_diagnostic_content
from decoraters import is_admin_and_notify_channel, track_usage
from versioning import versioned


def attach_import_resolution(group):
    @group.command(
        name="import_resolution",
        description="Open guided review for an exact held stats import",
    )
    @versioned("v1.01")
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
            from services.recovery_runtime import call_recovery
            from ui.views.recovery_view import RecoveryIncidentView, actor_for, incident_embed

            # Retain old slash-command arguments for already registered clients,
            # but never treat a legacy token as a new repair intent. Every action
            # now goes through current evidence, release policy and guided confirmation.
            row = await drain_thread(
                call_recovery,
                "review_source",
                actor_for(ctx.interaction),
                "stats_import",
                preparation_id,
            )
            await ctx.respond(
                content=(
                    "Legacy resolution now opens guided review. Review the current checks "
                    "and use its confirmation button; the old token has not applied a repair."
                    if action == "resolve"
                    else None
                ),
                embed=incident_embed(row),
                view=RecoveryIncidentView(row),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
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
