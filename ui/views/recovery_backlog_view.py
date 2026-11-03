"""Admin review of a whole evidence group; verification runs through services."""

import io

import discord

from core.interaction_safety import safe_defer
from ui.views.recovery_view import actor_for, call, incident_embed, report_error


class EvidenceGroupConfirmView(discord.ui.View):
    def __init__(self, preview):
        super().__init__(timeout=300)
        self.preview = preview

    @discord.ui.button(label="Confirm grouped repair", style=discord.ButtonStyle.primary)
    async def confirm(self, button, interaction):
        from ui.views.recovery_view import RecoveryIncidentView

        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            row = await call("approve_evidence_group", actor, self.preview)
            await interaction.followup.send(
                embed=incident_embed(row),
                view=RecoveryIncidentView(row),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            button.disabled = True
            self.stop()
        except Exception as exc:
            await report_error(interaction, exc)


async def show_group(interaction):
    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        preview = await call("review_evidence_group", actor)
        if not preview["count"]:
            await interaction.followup.send(
                "No unclaimed evidence-copy repairs are currently eligible. Accepted groups continue in the background; inspect their progress in the recovery centre.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(title=f"Review {preview['count']} evidence repairs", color=0xF1C40F)
        embed.description = "Confirm restoration of the missing or damaged copy for this group. Each item has a surviving copy that matched its original saved hash at its last check."
        embed.add_field(
            name="What the bot will verify",
            value="Recheck every original hash and repair choice. Restore only exact saved bytes, preserve damaged copies, then independently decrypt and verify both copies. Changed or unavailable evidence stays open.",
            inline=False,
        )
        embed.add_field(
            name="After confirmation",
            value="Progress and individual approvals are saved before repairs begin. The bot works through the group in the background and resumes after restart. One failed item does not stop the others. No import, provider write or queue release is included.",
            inline=False,
        )
        await interaction.followup.send(
            embed=embed,
            view=EvidenceGroupConfirmView(preview),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


async def show_complete_report(interaction):
    from core.operator_diagnostic_payloads import resolve_attachment_size_limit

    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        report = await call(
            "download_complete_report",
            actor,
            min(resolve_attachment_size_limit(interaction), 8388608),
        )
        await interaction.followup.send(
            f"Complete report: {report['count']} recorded incidents. The ZIP contains summary.json and all incident details in incidents.jsonl. Resolved incidents are included. No repairs were applied.",
            file=discord.File(io.BytesIO(report["content"]), filename=report["filename"]),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)
