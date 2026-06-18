from __future__ import annotations

import logging

import discord

from kvk.models.kvk_rankings import (
    HALL_OF_FAME_METRIC_LABELS,
    HallOfFameMetric,
)
from kvk.rendering.kvk_rankings_embed import build_hall_of_fame_embed
from kvk.services import kvk_rankings_service

logger = logging.getLogger(__name__)


class HallOfFameRecordsView(discord.ui.View):
    def __init__(
        self,
        *,
        metric: HallOfFameMetric = HallOfFameMetric.KILLS,
        limit: int = 10,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.metric = metric
        self.limit = kvk_rankings_service.normalize_hall_of_fame_limit(limit)
        self.message: discord.Message | None = None

        self.metric_select = discord.ui.Select(
            placeholder="Record metric",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=label, value=metric_value.value)
                for metric_value, label in HALL_OF_FAME_METRIC_LABELS.items()
            ],
            row=0,
        )
        self.metric_select.callback = self.on_metric_change
        self.add_item(self.metric_select)
        self._sync_controls()

    def _sync_controls(self) -> None:
        for option in self.metric_select.options:
            option.default = option.value == self.metric.value

    async def _refresh(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer()
        except Exception:
            pass

        try:
            payload = await kvk_rankings_service.build_hall_of_fame_payload(
                metric=self.metric,
                limit=self.limit,
            )
            self._sync_controls()
            embed = build_hall_of_fame_embed(payload)
            message = getattr(interaction, "message", None)
            if message is not None:
                self.message = message
                try:
                    await message.edit(embed=embed, view=self)
                    return
                except Exception:
                    logger.debug("kvk_records_host_message_edit_failed", exc_info=True)
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception:
            logger.exception(
                "kvk_records_refresh_failed metric=%s limit=%s",
                self.metric.value,
                self.limit,
            )
            try:
                await interaction.followup.send(
                    "Hall of Fame rankings failed to refresh. Please try again.",
                    ephemeral=True,
                )
            except Exception:
                logger.debug("kvk_records_refresh_error_response_failed", exc_info=True)

    async def on_metric_change(self, interaction: discord.Interaction) -> None:
        self.metric = kvk_rankings_service.parse_hall_of_fame_metric(self.metric_select.values[0])
        await self._refresh(interaction)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("kvk_records_view_timeout_edit_failed", exc_info=True)
