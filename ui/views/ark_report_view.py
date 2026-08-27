from __future__ import annotations

from collections.abc import Sequence

import discord


class ArkReportPlayersView(discord.ui.View):
    def __init__(self, *, author_id: int, pages: Sequence[discord.Embed], timeout: float = 600.0):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.pages = list(pages)
        self.page_index = 0

        self.prev_btn = discord.ui.Button(
            label="Previous", style=discord.ButtonStyle.secondary, disabled=True
        )
        self.next_btn = discord.ui.Button(
            label="Next", style=discord.ButtonStyle.secondary, disabled=len(self.pages) <= 1
        )

        self.prev_btn.callback = self._on_prev
        self.next_btn.callback = self._on_next

        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the report requester can change pages.", ephemeral=True
            )
            return False
        return True

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.page_index <= 0
        self.next_btn.disabled = self.page_index >= (len(self.pages) - 1)

    async def _on_prev(self, interaction: discord.Interaction):
        self.page_index = max(0, self.page_index - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page_index], view=self)

    async def _on_next(self, interaction: discord.Interaction):
        self.page_index = min(len(self.pages) - 1, self.page_index + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page_index], view=self)
