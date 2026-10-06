from __future__ import annotations

import asyncio
import logging

import discord

from core.interaction_safety import send_ephemeral
from mge import mge_results_import

logger = logging.getLogger(__name__)


class ConfirmOverwriteView(discord.ui.View):
    def __init__(self, event_id: int, file_bytes: bytes, filename: str, actor_id: int | None):
        super().__init__(timeout=120)
        self.event_id = int(event_id)
        self.file_bytes = file_bytes
        self.filename = filename
        self.actor_id = int(actor_id) if actor_id is not None else None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.actor_id is None:
            return True
        if not interaction.user or int(interaction.user.id) != self.actor_id:
            await send_ephemeral(
                interaction, "Only the command invoker can confirm this overwrite."
            )
            return False
        return True

    @discord.ui.button(
        label="Confirm Overwrite",
        style=discord.ButtonStyle.danger,
        custom_id="mge_results_import_confirm_overwrite",
    )
    async def confirm_overwrite(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            # offload blocking pandas/DB path
            result = await asyncio.to_thread(
                mge_results_import.import_results_manual,
                self.file_bytes,
                self.filename,
                self.event_id,
                self.actor_id,
                True,
            )
            self.disable_all_items()
            self.stop()

            await interaction.followup.send(
                (
                    "✅ Results import complete.\n"
                    f"- EventId: `{result['event_id']}`\n"
                    f"- Rows: `{result['rows']}`\n"
                    f"- Mode: `{result['event_mode']}`\n"
                    f"- ImportId: `{result['import_id']}`"
                ),
                ephemeral=True,
            )
            try:
                if interaction.message:
                    await interaction.message.edit(view=self)
            except Exception:
                logger.debug("Unable to edit overwrite confirmation message", exc_info=True)
        except Exception as e:
            logger.exception("mge_results_confirm_overwrite_failed")
            await interaction.followup.send(
                f"❌ Overwrite failed: `{type(e).__name__}: {e}`", ephemeral=True
            )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_results_import_cancel_overwrite",
    )
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        self.stop()
        await send_ephemeral(interaction, "Cancelled.")
        try:
            if interaction.message:
                await interaction.message.edit(view=self)
        except Exception:
            logger.debug(
                "Unable to edit overwrite confirmation message after cancel", exc_info=True
            )
