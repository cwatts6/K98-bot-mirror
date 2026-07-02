from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging

import discord

logger = logging.getLogger(__name__)


class ArkFuzzySelectView(discord.ui.View):
    def __init__(
        self,
        matches: list[dict],
        author_id: int,
        on_select: Callable[[discord.Interaction, str], object],
        *,
        timeout: float = 120,
    ):
        self._init_error: Exception | None = None
        try:
            super().__init__(timeout=timeout)
        except RuntimeError:
            # No running loop (common in sync unit tests). Spin up a temporary loop.
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._init_view_async(timeout))
            finally:
                asyncio.set_event_loop(None)
                loop.close()

        self._init_state(matches, author_id, on_select)

    async def _init_view_async(self, timeout: float) -> None:
        super().__init__(timeout=timeout)

    def _init_state(
        self,
        matches: list[dict],
        author_id: int,
        on_select: Callable[[discord.Interaction, str], object],
    ) -> None:
        self.matches = matches
        self.author_id = author_id
        self._on_select = on_select
        self.message: discord.Message | None = None

        options = []
        for m in matches[:25]:
            name = str(m.get("GovernorName") or "")[:75]
            gid = str(m.get("GovernorID") or "")
            desc = f"ID: {gid}"
            options.append(discord.SelectOption(label=name, description=desc, value=gid))

        self.select = discord.ui.Select(
            placeholder="Choose a governor…", options=options, min_values=1, max_values=1
        )
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This selector isn’t for you.", ephemeral=True)
            return

        gid = str(self.select.values[0])
        await self._on_select(interaction, gid)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            if interaction.response.is_done():
                await interaction.followup.send("This selector isn’t for you.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    "This selector isn’t for you.", ephemeral=True
                )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        logger.exception("[ARK FUZZY SELECT VIEW ERROR]", exc_info=error)
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send("⚠️ Something went wrong.", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)

    async def send_followup(self, interaction: discord.Interaction, embed: discord.Embed):
        if interaction.response.is_done():
            self.message = await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            self.message = await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
