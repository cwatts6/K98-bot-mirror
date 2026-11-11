"""Bounded pages of the complete reviewed old/new output mapping."""

import discord

from core.interaction_safety import safe_defer
from ui.views.recovery_view import actor_for, call, report_error


async def show_target_page(interaction, incident_id, page):
    try:
        actor = actor_for(interaction)
        if not await safe_defer(interaction, ephemeral=True):
            return
        row = await call("review", actor, incident_id)
        targets = row["evidence"].get("targets", [])
        mapping = row["evidence"].get("replacements", {})
        pages = max(1, (len(targets) + 4) // 5)
        page = max(0, min(page, pages - 1))
        embed = discord.Embed(
            title="Recovery output locations",
            description=row["evidence"].get("output_location_note")
            or "Old files may still receive the delayed write. Use the verified replacements after their publication completes.",
            color=0xF1C40F,
        )
        for ordinal, old in enumerate(targets[page * 5 : (page + 1) * 5], page * 5 + 1):
            publication = row["evidence"].get("target_purpose") == "publication"
            text = f"[{'Registered output' if publication else 'Old output'}](https://docs.google.com/spreadsheets/d/{old}/edit)"
            if old in mapping:
                text += (
                    f" → [Replacement](https://docs.google.com/spreadsheets/d/{mapping[old]}/edit)"
                )
                summary = row["evidence"].get("configuration_checks", {}).get(mapping[old], [])
                if summary:
                    text += "\nConfiguration checked: " + ", ".join(
                        f"{item['tab']}: {item['rows']} rows" for item in summary
                    )
                    text += "\nOpen the replacement and verify these settings before activation."
                    text += " Empty optional tabs keep existing SQL settings; blank ProcConfig cells also retain stored values."
                    checked = row["evidence"].get("configuration_preflight", {}).get(mapping[old])
                    if checked:
                        text += (
                            f"\nSQL preflight: season {checked['season']}, "
                            f"selected scan {checked['selected_scan']}, "
                            f"{checked['source_periods_checked']} source periods checked."
                        )
            elif not publication:
                text += " · Replacement not yet chosen"
            embed.add_field(name=f"Output {ordinal}", value=text, inline=False)
        embed.set_footer(
            text=f"Page {page + 1}/{pages} · {len(targets)} outputs · Current recovery revision {row['Revision']}"
        )
        await interaction.followup.send(
            embed=embed,
            view=RecoveryTargetsView(incident_id, page, pages),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class RecoveryTargetsView(discord.ui.View):
    def __init__(self, incident_id, page, pages):
        super().__init__(timeout=300)
        self.incident_id, self.page = incident_id, page
        self.previous.disabled = page == 0
        self.next.disabled = page + 1 == pages

    @discord.ui.button(label="Previous outputs", style=discord.ButtonStyle.secondary)
    async def previous(self, button, interaction):
        await show_target_page(interaction, self.incident_id, self.page - 1)

    @discord.ui.button(label="Next outputs", style=discord.ButtonStyle.secondary)
    async def next(self, button, interaction):
        await show_target_page(interaction, self.incident_id, self.page + 1)
