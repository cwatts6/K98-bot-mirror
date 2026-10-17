"""Paged, SQL-backed recovery forms. Permissions and decisions stay in services."""

import discord

from core.interaction_safety import safe_defer
from ui.views.recovery_view import (
    RecoveryIncidentView,
    actor_for,
    call,
    incident_embed,
    report_error,
)


def page_embed(page):
    detail = page["row"]["evidence"]["actions"][page["action"]]
    embed = discord.Embed(title=detail["label"], description=detail["check"], color=0xF1C40F)
    for field in page["fields"]:
        embed.add_field(
            name=field["label"],
            value=(field["help"] + "\nSaved: " + (field["value"] or "Not entered"))[:1024],
            inline=False,
        )
    embed.set_footer(
        text=f"Page {page['page'] + 1}/{page['pages']} · {page['completed']}/{page['total']} saved · You can reopen this form after a restart"
    )
    return embed


async def show_input_page(interaction, page):
    await interaction.followup.send(
        embed=page_embed(page),
        view=RecoveryInputView(page),
        ephemeral=True,
        allowed_mentions=discord.AllowedMentions.none(),
    )


class RecoveryInputModal(discord.ui.Modal):
    def __init__(self, page):
        super().__init__(
            title=f"Replacement details ({page['page'] + 1}/{page['pages']})"[:45], timeout=300
        )
        self.page = page
        self.fields = {}
        for field in page["fields"]:
            item = discord.ui.InputText(
                label=field["label"][:45],
                value=field["value"] or None,
                placeholder=field.get("placeholder", "")[:100],
                required=True,
                max_length=field["max_length"],
            )
            self.fields[field["key"]] = item
            self.add_item(item)

    async def callback(self, interaction):
        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            page, row = self.page, self.page["row"]
            saved = await call(
                "save_input",
                actor,
                row["IncidentID"],
                row["Revision"],
                row["EvidenceHash"],
                page["action"],
                page["page"],
                page["draft_version"],
                {key: item.value for key, item in self.fields.items()},
            )
            await show_input_page(interaction, saved)
        except Exception as exc:
            await report_error(interaction, exc)


class RecoveryInputView(discord.ui.View):
    def __init__(self, page):
        super().__init__(timeout=300)
        self.page = page
        self.previous.disabled = page["page"] == 0
        self.next.disabled = page["page"] + 1 == page["pages"]
        self.review.disabled = page["completed"] != page["total"]

    @discord.ui.button(label="Enter / edit this page", style=discord.ButtonStyle.primary)
    async def edit(self, button, interaction):
        try:
            actor_for(interaction)
            # Modal acknowledgement must be immediate. Service-side revision,
            # draft version and permissions are checked again on submission.
            await interaction.response.send_modal(RecoveryInputModal(self.page))
        except Exception as exc:
            await report_error(interaction, exc)

    async def move(self, interaction, offset):
        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            page = await call(
                "input_page",
                actor,
                self.page["row"]["IncidentID"],
                self.page["action"],
                self.page["page"] + offset,
            )
            await show_input_page(interaction, page)
        except Exception as exc:
            await report_error(interaction, exc)

    @discord.ui.button(label="Previous page", style=discord.ButtonStyle.secondary)
    async def previous(self, button, interaction):
        await self.move(interaction, -1)

    @discord.ui.button(label="Next page", style=discord.ButtonStyle.secondary)
    async def next(self, button, interaction):
        await self.move(interaction, 1)

    @discord.ui.button(label="Review saved choices", style=discord.ButtonStyle.success)
    async def review(self, button, interaction):
        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            proposal = await call(
                "input_confirmation", actor, self.page["row"]["IncidentID"], self.page["action"]
            )
            detail = proposal["row"]["evidence"]["actions"][proposal["action"]]
            embed = discord.Embed(
                title="Confirm replacement choices",
                description=proposal["preview"][:3500],
                color=0xF1C40F,
            )
            embed.add_field(
                name="Check before confirming", value=detail["check"][:1024], inline=False
            )
            embed.add_field(
                name="What the bot will do", value=detail["effect"][:1024], inline=False
            )
            await interaction.followup.send(
                embed=embed,
                view=RecoveryInputConfirmView(proposal),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception as exc:
            await report_error(interaction, exc)


class RecoveryInputConfirmView(discord.ui.View):
    def __init__(self, proposal):
        super().__init__(timeout=300)
        self.proposal = proposal

    @discord.ui.button(label="Confirm saved choices", style=discord.ButtonStyle.danger)
    async def confirm(self, button, interaction):
        try:
            actor = actor_for(interaction)
            if not await safe_defer(interaction, ephemeral=True):
                return
            proposal, row = self.proposal, self.proposal["row"]
            updated = await call(
                "execute_input",
                actor,
                row["IncidentID"],
                row["Revision"],
                row["EvidenceHash"],
                proposal["action"],
                proposal["draft_version"],
            )
            await interaction.followup.send(
                embed=incident_embed(updated),
                view=RecoveryIncidentView(updated),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            button.disabled = True
            self.stop()
        except Exception as exc:
            await report_error(interaction, exc)
