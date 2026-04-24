from __future__ import annotations

import asyncio
import logging

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_interaction
from mge import mge_completion_service, mge_report_service

logger = logging.getLogger(__name__)


class MgeAdminCompletionView(discord.ui.View):
    def __init__(self, event_id: int, leadership_channel_id: int, timeout: float | None = 300):
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)
        self.leadership_channel_id = int(leadership_channel_id)

    async def _deny_if_not_admin(self, interaction: discord.Interaction) -> bool:
        if is_admin_interaction(interaction):
            return False
        await send_ephemeral(interaction, "You do not have permission to perform this action.")
        return True

    @discord.ui.button(
        label="Complete Event",
        style=discord.ButtonStyle.danger,
        custom_id="mge_admin_complete_event",
    )
    async def complete_event_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if await self._deny_if_not_admin(interaction):
            return

        try:
            result = await asyncio.to_thread(
                mge_completion_service.complete_event,
                event_id=self.event_id,
                actor_discord_id=int(interaction.user.id),
                source="admin_view",
            )
        except Exception:
            logger.exception("mge_complete_event_failed event_id=%s", self.event_id)
            await send_ephemeral(interaction, f"Failed to complete event {self.event_id}.")
            return

        if result.get("ok"):
            await send_ephemeral(interaction, f"Event {self.event_id} marked completed.")
            return
        await send_ephemeral(interaction, f"Failed to complete event {self.event_id}.")

    @discord.ui.button(
        label="Reopen Event",
        style=discord.ButtonStyle.primary,
        custom_id="mge_admin_reopen_event",
    )
    async def reopen_event_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if await self._deny_if_not_admin(interaction):
            return

        try:
            result = await asyncio.to_thread(
                mge_completion_service.reopen_event,
                event_id=self.event_id,
                actor_discord_id=int(interaction.user.id),
            )
        except Exception:
            logger.exception("mge_reopen_event_failed event_id=%s", self.event_id)
            await send_ephemeral(interaction, f"Failed to reopen event {self.event_id}.")
            return

        if result.get("ok"):
            await send_ephemeral(interaction, f"Event {self.event_id} reopened.")
            return
        await send_ephemeral(interaction, f"Event {self.event_id} is not in completed state.")

    @discord.ui.button(
        label="Post Internal Summary",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_admin_post_summary",
    )
    async def post_summary_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if await self._deny_if_not_admin(interaction):
            return

        try:
            summary = await asyncio.to_thread(
                mge_report_service.build_post_event_summary,
                self.event_id,
            )
        except Exception:
            logger.exception("mge_build_summary_failed event_id=%s", self.event_id)
            await send_ephemeral(
                interaction, f"Failed to generate summary for event {self.event_id}."
            )
            return

        if interaction.client is None:
            await send_ephemeral(
                interaction,
                "Leadership channel post skipped: bot client unavailable.",
            )
            return

        channel = interaction.client.get_channel(self.leadership_channel_id)
        if channel is None:
            try:
                channel = await interaction.client.fetch_channel(self.leadership_channel_id)
            except Exception:
                logger.exception(
                    "mge_summary_fetch_channel_failed channel_id=%s",
                    self.leadership_channel_id,
                )
                channel = None

        if channel is None or not hasattr(channel, "send"):
            await send_ephemeral(
                interaction,
                f"Leadership channel unavailable or not sendable (id={self.leadership_channel_id}).",
            )
            return

        try:
            await channel.send(
                f"[MGE Summary] Event {self.event_id}\n"
                f"Total signups: {summary['Totals']['TotalSignups']}\n"
                f"Awarded: {summary['Awards']['AwardedCount']} | "
                f"Waitlist: {summary['Awards']['WaitlistCount']}\n"
                f"PublishVersion: {summary['RepublishMetrics']['PublishVersion']} | "
                f"Changes: {summary['RepublishMetrics']['ChangeCount']}"
            )
        except Exception:
            logger.exception(
                "mge_summary_channel_send_failed event_id=%s channel_id=%s",
                self.event_id,
                self.leadership_channel_id,
            )
            await send_ephemeral(
                interaction,
                f"Summary generated but failed to post to leadership channel (id={self.leadership_channel_id}).",
            )
            return

        await send_ephemeral(
            interaction, f"Summary generated and posted for event {self.event_id}."
        )
