"""Private, evidence-bound admin pages followed by an explicit repair confirmation."""

import discord

from core.interaction_safety import safe_defer
from ui.views.recovery_view import RecoveryConfirmView, actor_for, call, report_error


async def reviewed_page(interaction, row, action, page):
    return await call(
        "review_details_page",
        actor_for(interaction),
        row["IncidentID"],
        action,
        row["Revision"],
        row["EvidenceHash"],
        page,
    )


async def show_review_page(interaction, row, action, page, *, deferred=False):
    try:
        actor_for(interaction)
        if not deferred and not await safe_defer(interaction, ephemeral=True):
            return
        result = await reviewed_page(interaction, row, action, page)
        details = result["row"]["evidence"]["actions"][action]
        embed = discord.Embed(
            title=details.get("review_title", "Review retained scan and destinations"),
            description=details.get(
                "review_description",
                "Check the retained scan inputs, original outputs and current output settings. Follow the pages, then confirm only if this scan should use the current destinations.",
            ),
            color=0xF1C40F,
        )
        for field in result["fields"]:
            value = (
                f"[Open workbook](https://docs.google.com/spreadsheets/d/{field['file_id']}/edit)"
                if "file_id" in field
                else discord.utils.escape_markdown(field["text"])
            )
            embed.add_field(name=field["label"], value=value, inline=False)
        embed.set_footer(
            text=f"Page {page + 1}/{result['pages']} · Recovery revision {row['Revision']}"
        )
        await interaction.followup.send(
            embed=embed,
            view=RecoveryReviewView(result),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception as exc:
        await report_error(interaction, exc)


class RecoveryReviewView(discord.ui.View):
    def __init__(self, result):
        super().__init__(timeout=300)
        self.result = result
        self.previous.disabled = result["page"] == 0
        self.next.disabled = result["page"] + 1 == result["pages"]
        self.confirm.disabled = not self.next.disabled

    @discord.ui.button(label="Previous checks", style=discord.ButtonStyle.secondary)
    async def previous(self, button, interaction):
        p = self.result
        await show_review_page(interaction, p["row"], p["action"], p["page"] - 1)

    @discord.ui.button(label="Next checks", style=discord.ButtonStyle.secondary)
    async def next(self, button, interaction):
        p = self.result
        await show_review_page(interaction, p["row"], p["action"], p["page"] + 1)

    @discord.ui.button(label="Continue to confirmation", style=discord.ButtonStyle.primary)
    async def confirm(self, button, interaction):
        try:
            actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            p = self.result
            current = await reviewed_page(interaction, p["row"], p["action"], p["page"])
            if current["page"] + 1 != current["pages"]:
                return
            details = current["row"]["evidence"]["actions"][p["action"]]
            embed = discord.Embed(title=details["label"], color=0xF1C40F)
            embed.add_field(name="Check before confirming", value=details["check"], inline=False)
            embed.add_field(name="What the bot will do", value=details["effect"], inline=False)
            await interaction.followup.send(
                embed=embed,
                view=RecoveryConfirmView(current["row"], p["action"]),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception as exc:
            await report_error(interaction, exc)
