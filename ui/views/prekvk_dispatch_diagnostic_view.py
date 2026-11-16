"""Owner-bound diagnostic local-time button; no shared tracker or DM fallback."""

import logging

import discord

from bot_config import ADMIN_USER_ID, GUILD_ID
from core.interaction_safety import send_ephemeral
from embed_utils import LocalTimeToggleView
from stats_alerts.dispatch_reservations import _io

logger = logging.getLogger(__name__)


class PreKvkDispatchDiagnosticView(LocalTimeToggleView):
    def __init__(self, events, session):
        super().__init__(events, prefix=f"prekvk_diag_{session.token}", timeout=None)
        self.session = session
        self.clear_items()
        button = discord.ui.Button(
            label="Show in My Local Time",
            style=discord.ButtonStyle.success,
            custom_id=f"prekvk_diag_{session.token}_local_time",
        )
        button.callback = self.show_local_time
        self.add_item(button)

    async def show_local_time(self, interaction):
        async def respond(content):
            await send_ephemeral(
                interaction, content, allowed_mentions=discord.AllowedMentions.none()
            )

        manifest = self.session.manifest
        if (
            interaction.user.id != manifest["owner_id"]
            or interaction.user.id != int(ADMIN_USER_ID)
            or interaction.guild_id != manifest["guild_id"]
            or interaction.guild_id != int(GUILD_ID)
            or interaction.channel_id != manifest["channel_id"]
        ):
            await respond("This diagnostic belongs to its initiating operator and destination.")
            return
        try:
            permissions = interaction.channel.permissions_for(interaction.user)
            if not permissions.view_channel or not permissions.send_messages:
                await respond("You no longer have access to this diagnostic destination.")
                return
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            snapshot = await _io(self.session.snapshot)
            if interaction.message.id != snapshot["message_id"]:
                await respond(
                    "This diagnostic message is stale. Reopen the session using the command."
                )
                return
            embed = await self.build_local_time_embed()
            await send_ephemeral(
                interaction, "", embed=embed, allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception:
            logger.exception(
                "[PREKVK DIAGNOSTIC] Local-time callback failed session=%s", self.session.token
            )
            await respond("Diagnostic view unavailable. Reopen the session using the command.")
