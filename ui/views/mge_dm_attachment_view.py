"""Discord DM view for optional MGE gear/armament attachment uploads."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import discord

from mge import mge_dm_followup
from mge.dal import mge_signup_dal

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _PendingSlot:
    kind: str | None = None


class MgeDmAttachmentView(discord.ui.View):
    """DM-only attachment workflow view for one signup."""

    def __init__(self, *, signup_id: int, event_id: int, actor_discord_id: int) -> None:
        super().__init__(timeout=900)
        self.signup_id = int(signup_id)
        self.event_id = int(event_id)
        self.actor_discord_id = int(actor_discord_id)
        self._pending = _PendingSlot()

    async def _send_ephemeral(self, interaction: discord.Interaction, message: str) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    async def _fetch_governor_for_signup(self) -> int | None:
        row = mge_signup_dal.fetch_signup_by_id(self.signup_id)
        if not row:
            return None
        try:
            return int(row.get("GovernorId"))
        except Exception:
            return None

    @discord.ui.button(
        label="Upload Gear Image",
        style=discord.ButtonStyle.primary,
        custom_id="mge_dm_upload_gear",
    )
    async def upload_gear(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self._pending.kind = "gear"
        await self._send_ephemeral(
            interaction,
            "Please send your **gear** image in this DM now (as an attachment).",
        )

    @discord.ui.button(
        label="Upload Armament Image",
        style=discord.ButtonStyle.primary,
        custom_id="mge_dm_upload_armament",
    )
    async def upload_armament(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self._pending.kind = "armament"
        await self._send_ephemeral(
            interaction,
            "Please send your **armament** image in this DM now (as an attachment).",
        )

    @discord.ui.button(
        label="Skip / Done",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_dm_skip_done",
    )
    async def skip_done(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        mge_dm_followup.clear_dm_session(self.actor_discord_id)
        self.stop()
        await self._send_ephemeral(
            interaction,
            "No problem — your signup is valid without attachments. You can re-open this later.",
        )

    async def on_timeout(self) -> None:
        mge_dm_followup.clear_dm_session(self.actor_discord_id)
        logger.info(
            "mge_dm_attachment_view_timeout event_id=%s signup_id=%s actor_discord_id=%s",
            self.event_id,
            self.signup_id,
            self.actor_discord_id,
        )

    async def handle_dm_message(self, message: discord.Message) -> str:
        """
        Handle DM message attachment for current pending slot.
        Returns user-facing status text.
        """
        if not self._pending.kind:
            return "Please click a button first to choose Gear or Armament."

        attachment = mge_dm_followup.validate_and_get_image(list(message.attachments or []))
        if not attachment:
            return "No valid image attachment found. Please upload an image file."

        governor_id = await self._fetch_governor_for_signup()
        if governor_id is None:
            return "Could not find your signup record. Please contact leadership."

        result = mge_dm_followup.save_attachment_for_signup(
            signup_id=self.signup_id,
            event_id=self.event_id,
            governor_id=governor_id,
            actor_discord_id=self.actor_discord_id,
            kind=self._pending.kind,
            attachment=attachment,
        )
        if result.success:
            return f"{result.message} (latest upload is now active)"
        return result.message
