from __future__ import annotations

import logging

import discord

from core.interaction_safety import private_operation, send_ephemeral
from core.mge_permissions import is_admin_interaction
from core.owned_work import drain_thread
from mge import mge_finalisation, mge_report_service

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
    @private_operation
    async def complete_event_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if await self._deny_if_not_admin(interaction):
            return

        try:
            result = await mge_finalisation.finalise_event(
                interaction.client,
                self.event_id,
                actor_id=int(interaction.user.id),
                complete=True,
            )
        except Exception:
            logger.exception("mge_complete_event_failed event_id=%s", self.event_id)
            await send_ephemeral(
                interaction,
                f"Completion of event {self.event_id} could not be confirmed. Check its current state before repeating.",
            )
            return

        if result.get("domain_completed"):
            await send_ephemeral(
                interaction,
                f"Event {self.event_id} is completed and frozen. Board delivery: {result['states'] or 'historical / no recorded targets'}. Results and summaries remain available.",
            )
            return
        await send_ephemeral(
            interaction,
            f"Completion of event {self.event_id} could not be confirmed. Check its current state before repeating.",
        )

    @discord.ui.button(
        label="Check Final Delivery",
        style=discord.ButtonStyle.primary,
        custom_id="mge_admin_check_final_delivery",
    )
    @private_operation
    async def check_final_delivery_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if await self._deny_if_not_admin(interaction):
            return

        try:
            result = await mge_finalisation.finalise_event(interaction.client, self.event_id)
        except Exception:
            logger.exception("mge_final_delivery_check_failed event_id=%s", self.event_id)
            await send_ephemeral(
                interaction,
                "Final delivery could not be checked. No business action should be repeated.",
            )
            return

        await send_ephemeral(
            interaction,
            f"Final delivery for event {self.event_id}: {result}. Confirmed and held boards are left unchanged.",
        )

    @discord.ui.button(
        label="Review Retirement",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_admin_retire_review",
    )
    @private_operation
    async def retire_review_button(self, button, interaction):
        if await self._deny_if_not_admin(interaction):
            return
        targets = await mge_finalisation.retirement_preview(self.event_id)
        if not targets:
            await send_ephemeral(
                interaction,
                "No pending, failed or held final boards to retire. Unknown edits require reconciliation first.",
            )
            return
        description = "\n".join(
            f"{t['BoardKind']}: channel {t['ChannelId']}, message {t['MessageId']} ({t['DeliveryState']})"
            for t in targets
        )
        await send_ephemeral(
            interaction,
            "Retirement stops final-delivery work and retains these messages and all result/audit data. It does not confirm final delivery or delete messages.\n"
            + description,
            view=_RetireFinalBoards(self.event_id, targets, interaction.user.id),
        )

    @discord.ui.button(
        label="Post Internal Summary",
        style=discord.ButtonStyle.secondary,
        custom_id="mge_admin_post_summary",
    )
    @private_operation
    async def post_summary_button(  # type: ignore[override]
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if await self._deny_if_not_admin(interaction):
            return

        try:
            summary = await drain_thread(
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


class _RetireFinalBoards(discord.ui.View):
    def __init__(self, event_id, targets, actor_id):
        super().__init__(timeout=120)
        self.event_id, self.targets, self.actor_id = event_id, targets, actor_id

    @discord.ui.button(label="Confirm Retirement", style=discord.ButtonStyle.danger)
    @private_operation
    async def confirm(self, button, interaction):
        if interaction.user.id != self.actor_id or not is_admin_interaction(interaction):
            await send_ephemeral(
                interaction, "You do not have permission to confirm this retirement."
            )
            return
        outcomes = await mge_finalisation.retire_targets(
            interaction.client, self.event_id, self.targets, self.actor_id
        )
        await send_ephemeral(
            interaction,
            f"Retirement outcomes: {outcomes}. False means changed or unconfirmed; review current state before repeating.",
        )
        self.stop()
