"""A fresh interaction opens a modal after its data has been prepared off-loop."""

import discord

from core.interaction_safety import send_ephemeral


class PreparedModalView(discord.ui.View):
    def __init__(self, *, owner_id, modal):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.modal = modal

    @discord.ui.button(label="Open form", style=discord.ButtonStyle.primary)
    async def open_form(self, button, interaction):
        if interaction.user.id != self.owner_id:
            await send_ephemeral(interaction, "This form belongs to another user.")
            return
        await interaction.response.send_modal(self.modal)
        self.stop()


async def offer_prepared_modal(interaction, modal):
    await send_ephemeral(
        interaction,
        "Your form is ready.",
        view=PreparedModalView(owner_id=interaction.user.id, modal=modal),
    )
