"""MGE edit/withdraw helper view for existing signup selection."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

logger = logging.getLogger(__name__)


class MgeEditActionView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        on_edit: Callable[[discord.Interaction], Awaitable[None]],
        on_withdraw: Callable[[discord.Interaction], Awaitable[None]],
    ) -> None:
        super().__init__(timeout=180)
        self.author_id = author_id
        self._on_edit = on_edit
        self._on_withdraw = on_withdraw

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu is not for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(
        label="Edit My Request", style=discord.ButtonStyle.primary, custom_id="mge_edit_my_request"
    )
    async def edit_btn(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await self._on_edit(interaction)

    @discord.ui.button(
        label="Withdraw", style=discord.ButtonStyle.danger, custom_id="mge_withdraw_my_request"
    )
    async def withdraw_btn(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._on_withdraw(interaction)
