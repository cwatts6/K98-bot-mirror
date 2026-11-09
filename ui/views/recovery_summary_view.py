"""Short decision review with optional complete technical evidence."""

import discord

from core.interaction_safety import safe_defer
from ui.views.recovery_view import RecoveryConfirmView, actor_for, call, report_error


async def current_summary(interaction, row, action):
    return await call(
        "review_decision_summary",
        actor_for(interaction),
        row["IncidentID"],
        action,
        row["Revision"],
        row["EvidenceHash"],
    )


async def show_summary(interaction, row, action, *, deferred=False):
    try:
        actor_for(interaction)
        if not deferred and not await safe_defer(interaction, ephemeral=True):
            return
        result = await current_summary(interaction, row, action)
        detail = result["row"]["evidence"]["actions"][action]
        embed = discord.Embed(
            title=detail.get("review_summary_title", "Retire this old export?"), color=0xF1C40F
        )
        for field in result["fields"]:
            embed.add_field(
                name=field["label"],
                value=discord.utils.escape_markdown(field["text"]),
                inline=False,
            )
        embed.set_footer(text="Decision summary · Technical details are optional")
        await interaction.followup.send(
            embed=embed,
            view=RecoverySummaryView(result),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class RecoverySummaryView(discord.ui.View):
    def __init__(self, result):
        super().__init__(timeout=300)
        self.result = result

    @discord.ui.button(label="Continue to confirmation", style=discord.ButtonStyle.primary)
    async def confirm(self, button, interaction):
        try:
            actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            p = self.result
            current = await current_summary(interaction, p["row"], p["action"])
            detail = current["row"]["evidence"]["actions"][p["action"]]
            await interaction.followup.send(
                detail["check"] + "\n\n" + detail["effect"],
                view=RecoveryConfirmView(current["row"], p["action"]),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception as exc:
            await report_error(interaction, exc)

    @discord.ui.button(label="View technical details", style=discord.ButtonStyle.secondary)
    async def technical(self, button, interaction):
        from ui.views.recovery_review_view import show_review_page

        await show_review_page(interaction, self.result["row"], self.result["action"], 0)
