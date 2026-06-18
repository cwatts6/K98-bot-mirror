from __future__ import annotations

import logging

import discord

from bot_config import KVK_PLAYER_STATS_CHANNEL_ID
from core.interaction_safety import send_ephemeral
from decoraters import _is_admin
from kvk.models.kvk_rankings import (
    HALL_OF_FAME_METRIC_LABELS,
    PRIMARY_RANKING_LIMITS,
    HallOfFameMetric,
    RankingPayload,
)
from kvk.rendering.kvk_rankings_embed import build_current_rankings_embed, build_hall_of_fame_embed
from kvk.services import kvk_rankings_service

logger = logging.getLogger(__name__)

_CURRENT_RANKING_ADMIN_OVERRIDE_MODES = {"kvk", "prekvk"}


def _is_kvk_stats_channel_interaction(interaction: discord.Interaction) -> bool:
    channel = getattr(interaction, "channel", None)
    channel_id = getattr(channel, "id", None)
    parent_id = getattr(
        channel,
        "parent_id",
        getattr(getattr(channel, "parent", None), "id", None),
    )
    return channel_id == KVK_PLAYER_STATS_CHANNEL_ID or parent_id == KVK_PLAYER_STATS_CHANNEL_ID


class CurrentRankingsBrowserView(discord.ui.View):
    def __init__(
        self,
        *,
        mode: str = "kvk",
        metric: str | None = None,
        limit: int = 10,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.mode = kvk_rankings_service.parse_current_ranking_mode(mode)
        self.metric = kvk_rankings_service.normalize_current_ranking_metric(self.mode, metric)
        self.limit = kvk_rankings_service.normalize_ranking_limit(limit)
        self.message: discord.Message | None = None
        self.mode_select: discord.ui.Select | None = None
        self.metric_select: discord.ui.Select | None = None
        self._rebuild_controls()

    def _rebuild_controls(self) -> None:
        self.clear_items()
        self.mode_select = discord.ui.Select(
            placeholder="Ranking mode",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=kvk_rankings_service.CURRENT_RANKING_MODE_LABELS[mode],
                    value=mode,
                    default=mode == self.mode,
                )
                for mode in kvk_rankings_service.CURRENT_RANKING_MODE_LABELS
            ],
            row=0,
        )
        self.mode_select.callback = self.on_mode_change
        self.add_item(self.mode_select)

        metric_labels = kvk_rankings_service.CURRENT_RANKING_METRIC_LABELS[self.mode]
        self.metric_select = discord.ui.Select(
            placeholder="Ranking metric",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=label,
                    value=value,
                    default=value == self.metric,
                )
                for value, label in metric_labels.items()
            ],
            row=1,
            disabled=len(metric_labels) == 1,
        )
        self.metric_select.callback = self.on_metric_change
        self.add_item(self.metric_select)

        for option_limit in PRIMARY_RANKING_LIMITS:
            button = discord.ui.Button(
                label=f"Top {option_limit}",
                style=(
                    discord.ButtonStyle.primary
                    if option_limit == self.limit
                    else discord.ButtonStyle.secondary
                ),
                custom_id=f"kvk_rankings_current_top_{option_limit}",
                row=2,
            )
            button.callback = self._make_limit_handler(option_limit)
            self.add_item(button)

    def _sync_from_payload(self, payload: RankingPayload) -> None:
        self.mode = kvk_rankings_service.parse_current_ranking_mode(payload.mode)
        self.metric = kvk_rankings_service.normalize_current_ranking_metric(
            self.mode,
            payload.metric,
        )
        self.limit = kvk_rankings_service.normalize_ranking_limit(payload.limit)
        self._rebuild_controls()

    def _interaction_allowed_for_mode(
        self,
        interaction: discord.Interaction,
        mode: str,
    ) -> bool:
        if _is_kvk_stats_channel_interaction(interaction):
            return True
        return mode in _CURRENT_RANKING_ADMIN_OVERRIDE_MODES and _is_admin(
            getattr(interaction, "user", None)
        )

    async def _ensure_interaction_allowed_for_mode(
        self,
        interaction: discord.Interaction,
        mode: str,
    ) -> bool:
        if self._interaction_allowed_for_mode(interaction, mode):
            return True
        await send_ephemeral(
            interaction,
            f"This ranking mode may only be used in <#{KVK_PLAYER_STATS_CHANNEL_ID}>.",
        )
        return False

    async def _refresh(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_interaction_allowed_for_mode(interaction, self.mode):
            return

        try:
            await interaction.response.defer()
        except Exception:
            pass

        try:
            payload = await kvk_rankings_service.build_current_rankings_payload(
                mode=self.mode,
                metric=self.metric,
                limit=self.limit,
            )
            self._sync_from_payload(payload)
            embed = build_current_rankings_embed(payload)
            message = getattr(interaction, "message", None)
            if message is not None:
                self.message = message
                try:
                    await message.edit(embed=embed, view=self)
                    return
                except Exception:
                    logger.debug("kvk_current_rankings_host_message_edit_failed", exc_info=True)
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception:
            logger.exception(
                "kvk_current_rankings_refresh_failed mode=%s metric=%s limit=%s",
                self.mode,
                self.metric,
                self.limit,
            )
            try:
                await interaction.followup.send(
                    "Rankings failed to refresh. Please try again.",
                    ephemeral=True,
                )
            except Exception:
                logger.debug("kvk_current_rankings_refresh_error_response_failed", exc_info=True)

    async def on_mode_change(self, interaction: discord.Interaction) -> None:
        if self.mode_select is not None:
            requested_mode = kvk_rankings_service.parse_current_ranking_mode(
                self.mode_select.values[0]
            )
            if not await self._ensure_interaction_allowed_for_mode(interaction, requested_mode):
                return
            self.mode = requested_mode
        self.metric = kvk_rankings_service.normalize_current_ranking_metric(self.mode, None)
        await self._refresh(interaction)

    async def on_metric_change(self, interaction: discord.Interaction) -> None:
        if self.metric_select is not None:
            self.metric = kvk_rankings_service.normalize_current_ranking_metric(
                self.mode,
                self.metric_select.values[0],
            )
        await self._refresh(interaction)

    def _make_limit_handler(self, limit: int):
        async def _handler(interaction: discord.Interaction) -> None:
            self.limit = kvk_rankings_service.normalize_ranking_limit(limit)
            await self._refresh(interaction)

        return _handler

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("kvk_current_rankings_view_timeout_edit_failed", exc_info=True)


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
