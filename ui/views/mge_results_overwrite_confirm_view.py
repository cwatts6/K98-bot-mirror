from __future__ import annotations

import asyncio
import logging

import discord

from mge.mge_results_import import import_results_manual

logger = logging.getLogger(__name__)


class MgeResultsOverwriteConfirmView(discord.ui.View):
    """Confirmation view for destructive manual MGE results overwrite."""

    def __init__(
        self,
        *,
        actor_discord_id: int,
        event_id: int,
        filename: str,
        file_bytes: bytes,
    ) -> None:
        super().__init__(timeout=180)
        self.actor_discord_id = int(actor_discord_id)
        self.event_id = int(event_id)
        self.filename = filename
        self.file_bytes = file_bytes
        self.completed = False

    async def _deny_if_not_actor(self, interaction: discord.Interaction) -> bool:
        if not interaction.user or int(interaction.user.id) != self.actor_discord_id:
            await interaction.response.send_message(
                "Only the command invoker can confirm this overwrite.",
                ephemeral=True,
            )
            return True
        return False

    @discord.ui.button(
        label="Confirm Overwrite",
        style=discord.ButtonStyle.danger,
        custom_id="mge_results_confirm_overwrite",
    )
    async def confirm_overwrite(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        if await self._deny_if_not_actor(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        try:
            result = await asyncio.to_thread(
                import_results_manual,
                self.file_bytes,
                self.filename,
                self.event_id,
                self.actor_discord_id,
                True,  # explicit overwrite
            )
            self.completed = True
            self.disable_all_items()
            await interaction.followup.send(
                (
                    "✅ Overwrite import complete.\n"
                    f"- EventId: `{result['event_id']}`\n"
                    f"- Mode: `{result['event_mode']}`\n"
                    f"- Rows: `{result['rows']}`\n"
                    f"- ImportId: `{result['import_id']}`"
                ),
                ephemeral=True,
            )
            try:
                await interaction.message.edit(view=self)
            except Exception:
                logger.debug("Unable to edit overwrite confirmation view message", exc_info=True)
        except Exception as e:
            logger.exception("mge_results_overwrite_confirm_failed")
            await interaction.followup.send(
                f"❌ Overwrite failed: `{type(e).__name__}: {e}`",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_results_cancel_overwrite",
    )
    async def cancel_overwrite(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        if await self._deny_if_not_actor(interaction):
            return

        self.disable_all_items()
        await interaction.response.send_message("Cancelled. No changes were made.", ephemeral=True)
        try:
            await interaction.message.edit(view=self)
        except Exception:
            logger.debug("Unable to edit overwrite confirmation view message", exc_info=True)
