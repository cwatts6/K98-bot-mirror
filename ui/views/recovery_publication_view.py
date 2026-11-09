"""Private selection of retained publications; provider checks require confirmation."""

import discord

from core.interaction_safety import safe_defer
from ui.views.recovery_view import (
    RecoveryIncidentView,
    actor_for,
    call,
    incident_embed,
    report_error,
)


async def show_publications(interaction, after=None):
    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        rows = await call("published_outputs", actor, after)
        await interaction.followup.send(
            (
                "Choose a retained publication, then confirm Check published output. Listing does not contact Sheets."
                if rows
                else "No further retained publications on this page. Existing failed or uncertain exports remain in the recovery centre."
            ),
            view=PublicationListView(rows),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class PublicationListView(discord.ui.View):
    def __init__(self, rows):
        super().__init__(timeout=300)
        if not rows:
            return
        select = discord.ui.Select(
            placeholder="Published outputs — oldest first (UTC)",
            options=[
                discord.SelectOption(
                    label=f"KVK {r['KVK_NO']} · {r['CreatedUTC']}"[:100],
                    description=f"Retained input {r['InputHash'][:12]} · Export {r['JobID'][-12:]}"[
                        :100
                    ],
                    value=r["JobID"],
                )
                for r in rows
            ],
        )

        async def selected(interaction):
            try:
                actor = actor_for(interaction)
                if not await safe_defer(interaction, ephemeral=True):
                    return
                current = await call("review_source", actor, "export_job", select.values[0])
                await interaction.followup.send(
                    embed=incident_embed(current),
                    view=RecoveryIncidentView(current),
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except Exception as exc:
                await report_error(interaction, exc)

        select.callback = selected
        self.add_item(select)
        if len(rows) == 20:
            button = discord.ui.Button(
                label="Next published outputs", style=discord.ButtonStyle.secondary
            )

            async def next_page(interaction):
                await show_publications(interaction, rows[-1]["JobID"])

            button.callback = next_page
            self.add_item(button)
