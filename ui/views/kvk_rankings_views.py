from __future__ import annotations

import asyncio
from collections.abc import Sequence
import logging

import discord

from bot_config import KVK_PLAYER_STATS_CHANNEL_ID
from core.interaction_safety import send_ephemeral
from decoraters import _is_admin
from kvk.models.kvk_rankings import (
    HALL_OF_FAME_METRIC_LABELS,
    PRIMARY_RANKING_LIMITS,
    HallOfFameMetric,
    MyRankLookupResult,
    RankingAccountChoice,
    RankingPayload,
)
from kvk.rendering.kvk_rankings_card_renderer import (
    can_render_current_rankings_top10_card,
    can_render_hall_of_fame_top10_card,
    render_current_rankings_top10_card,
    render_hall_of_fame_top10_card,
)
from kvk.rendering.kvk_rankings_embed import (
    build_current_rankings_embed,
    build_hall_of_fame_embed,
    build_my_rank_embed,
)
from kvk.services import kvk_rankings_service

logger = logging.getLogger(__name__)

_CURRENT_RANKING_ADMIN_OVERRIDE_MODES = {"kvk", "prekvk"}


async def _top10_card_file(payload: RankingPayload) -> discord.File | None:
    if not can_render_current_rankings_top10_card(payload):
        return None
    try:
        rendered = await asyncio.to_thread(render_current_rankings_top10_card, payload)
    except Exception:
        logger.exception(
            "kvk_current_rankings_card_render_failed mode=%s metric=%s limit=%s",
            payload.mode,
            payload.metric,
            payload.limit,
        )
        return None
    if rendered is None:
        return None
    rendered.image_bytes.seek(0)
    return discord.File(rendered.image_bytes, filename=rendered.filename)


async def _records_top10_card_file(payload: RankingPayload) -> discord.File | None:
    if not can_render_hall_of_fame_top10_card(payload):
        return None
    try:
        rendered = await asyncio.to_thread(render_hall_of_fame_top10_card, payload)
    except Exception:
        logger.exception(
            "kvk_records_card_render_failed metric=%s limit=%s",
            payload.metric,
            payload.limit,
        )
        return None
    if rendered is None:
        return None
    rendered.image_bytes.seek(0)
    return discord.File(rendered.image_bytes, filename=rendered.filename)


def _is_kvk_stats_channel_interaction(interaction: discord.Interaction) -> bool:
    channel = getattr(interaction, "channel", None)
    channel_id = getattr(channel, "id", None)
    parent_id = getattr(
        channel,
        "parent_id",
        getattr(getattr(channel, "parent", None), "id", None),
    )
    return channel_id == KVK_PLAYER_STATS_CHANNEL_ID or parent_id == KVK_PLAYER_STATS_CHANNEL_ID


def _truncate_option_text(value: str, *, limit: int = 100) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "."


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        await interaction.response.defer(ephemeral=True)
    except TypeError:
        try:
            await interaction.response.defer()
        except Exception:
            pass
    except Exception:
        pass


async def _send_private_my_rank_result(
    interaction: discord.Interaction,
    result: MyRankLookupResult,
    *,
    requester_id: int,
    mode: str,
    metric: str,
    limit: int,
) -> None:
    if result.status == "multi_account" and result.account_choices:
        await interaction.followup.send(
            result.message,
            view=CurrentRankingsMyRankAccountView(
                requester_id=requester_id,
                mode=mode,
                metric=metric,
                limit=limit,
                choices=result.account_choices,
            ),
            ephemeral=True,
        )
        return
    if result.status == "found":
        await interaction.followup.send(
            embed=build_my_rank_embed(result),
            ephemeral=True,
        )
        return
    await interaction.followup.send(result.message, ephemeral=True)


class _MyRankAccountSelect(discord.ui.Select):
    def __init__(
        self,
        owner: CurrentRankingsMyRankAccountView,
        choices: Sequence[RankingAccountChoice],
    ) -> None:
        self.owner = owner
        options = [
            discord.SelectOption(
                label=_truncate_option_text(f"{choice.slot}: {choice.governor_name}"),
                value=choice.governor_id_str,
                description=_truncate_option_text(
                    f"Governor ID {choice.governor_id_str}",
                ),
            )
            for choice in choices[:25]
        ]
        super().__init__(
            placeholder="Choose a registered governor",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.owner.on_account_selected(interaction, self.values[0])


class CurrentRankingsMyRankAccountView(discord.ui.View):
    def __init__(
        self,
        *,
        requester_id: int,
        mode: str,
        metric: str,
        limit: int,
        choices: Sequence[RankingAccountChoice],
        timeout: float = 120.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.requester_id = int(requester_id)
        self.mode = mode
        self.metric = metric
        self.limit = limit
        self.add_item(_MyRankAccountSelect(self, choices))

    async def on_account_selected(
        self,
        interaction: discord.Interaction,
        governor_id: str,
    ) -> None:
        if int(getattr(getattr(interaction, "user", None), "id", 0)) != self.requester_id:
            await send_ephemeral(interaction, "Only the requester can use this account selector.")
            return
        await _defer_private(interaction)
        try:
            result = await kvk_rankings_service.build_my_rank_lookup_result(
                discord_user_id=self.requester_id,
                mode=self.mode,
                metric=self.metric,
                limit=self.limit,
                governor_id=governor_id,
            )
            await _send_private_my_rank_result(
                interaction,
                result,
                requester_id=self.requester_id,
                mode=self.mode,
                metric=self.metric,
                limit=self.limit,
            )
        except Exception:
            logger.exception(
                "kvk_current_rankings_my_rank_select_failed mode=%s metric=%s limit=%s",
                self.mode,
                self.metric,
                self.limit,
            )
            try:
                await interaction.followup.send(
                    "My Rank failed to load. Please try again.",
                    ephemeral=True,
                )
            except Exception:
                logger.debug("kvk_current_rankings_my_rank_select_response_failed", exc_info=True)


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
        self.limit = kvk_rankings_service.normalize_ranking_limit(limit)
        self.metric = kvk_rankings_service.normalize_current_ranking_metric(
            self.mode,
            metric,
            limit=self.limit,
        )
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

        metric_labels = kvk_rankings_service.current_ranking_metric_labels(
            self.mode,
            limit=self.limit,
        )
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

        my_rank_button = discord.ui.Button(
            label="My Rank",
            style=discord.ButtonStyle.success,
            custom_id="kvk_rankings_current_my_rank",
            row=2,
        )
        my_rank_button.callback = self.on_my_rank
        self.add_item(my_rank_button)

    def _sync_from_payload(self, payload: RankingPayload) -> None:
        self.mode = kvk_rankings_service.parse_current_ranking_mode(payload.mode)
        self.metric = kvk_rankings_service.normalize_current_ranking_metric(
            self.mode,
            payload.metric,
            limit=self.limit,
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
            file = await _top10_card_file(payload)
            message = getattr(interaction, "message", None)
            if file is not None and message is not None:
                self.message = message
                try:
                    await message.edit(
                        content=None,
                        embeds=[],
                        attachments=[],
                        files=[file],
                        view=self,
                    )
                    return
                except Exception:
                    logger.debug("kvk_current_rankings_host_message_edit_failed", exc_info=True)
            if file is not None and message is None:
                try:
                    await interaction.edit_original_response(
                        content=None,
                        embeds=[],
                        attachments=[],
                        files=[file],
                        view=self,
                    )
                    return
                except Exception:
                    logger.debug(
                        "kvk_current_rankings_original_card_edit_failed",
                        exc_info=True,
                    )

            embed = build_current_rankings_embed(payload)
            if message is not None:
                self.message = message
                try:
                    await message.edit(embed=embed, attachments=[], view=self)
                    return
                except Exception:
                    logger.debug("kvk_current_rankings_host_message_edit_failed", exc_info=True)
            await interaction.edit_original_response(
                attachments=[],
                embed=embed,
                view=self,
            )
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
        self.metric = kvk_rankings_service.normalize_current_ranking_metric(
            self.mode,
            None,
            limit=self.limit,
        )
        await self._refresh(interaction)

    async def on_metric_change(self, interaction: discord.Interaction) -> None:
        if self.metric_select is not None:
            self.metric = kvk_rankings_service.normalize_current_ranking_metric(
                self.mode,
                self.metric_select.values[0],
                limit=self.limit,
            )
        await self._refresh(interaction)

    def _make_limit_handler(self, limit: int):
        async def _handler(interaction: discord.Interaction) -> None:
            self.limit = kvk_rankings_service.normalize_ranking_limit(limit)
            self.metric = kvk_rankings_service.normalize_current_ranking_metric(
                self.mode,
                self.metric,
                limit=self.limit,
            )
            await self._refresh(interaction)

        return _handler

    async def on_my_rank(self, interaction: discord.Interaction) -> None:
        if not await self._ensure_interaction_allowed_for_mode(interaction, self.mode):
            return
        await _defer_private(interaction)
        requester_id = int(getattr(getattr(interaction, "user", None), "id", 0))
        try:
            result = await kvk_rankings_service.build_my_rank_lookup_result(
                discord_user_id=requester_id,
                mode=self.mode,
                metric=self.metric,
                limit=self.limit,
            )
            await _send_private_my_rank_result(
                interaction,
                result,
                requester_id=requester_id,
                mode=self.mode,
                metric=self.metric,
                limit=self.limit,
            )
        except Exception:
            logger.exception(
                "kvk_current_rankings_my_rank_failed mode=%s metric=%s limit=%s",
                self.mode,
                self.metric,
                self.limit,
            )
            try:
                await interaction.followup.send(
                    "My Rank failed to load. Please try again.",
                    ephemeral=True,
                )
            except Exception:
                logger.debug("kvk_current_rankings_my_rank_response_failed", exc_info=True)

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
            file = await _records_top10_card_file(payload)
            message = getattr(interaction, "message", None)
            if file is not None and message is not None:
                self.message = message
                try:
                    await message.edit(
                        content=None,
                        embeds=[],
                        attachments=[],
                        files=[file],
                        view=self,
                    )
                    return
                except Exception:
                    logger.debug("kvk_records_host_message_card_edit_failed", exc_info=True)
            if file is not None and message is None:
                try:
                    await interaction.edit_original_response(
                        content=None,
                        embeds=[],
                        attachments=[],
                        files=[file],
                        view=self,
                    )
                    return
                except Exception:
                    logger.debug("kvk_records_original_card_edit_failed", exc_info=True)

            embed = build_hall_of_fame_embed(payload)
            if message is not None:
                self.message = message
                try:
                    await message.edit(embed=embed, attachments=[], view=self)
                    return
                except Exception:
                    logger.debug("kvk_records_host_message_edit_failed", exc_info=True)
            await interaction.edit_original_response(attachments=[], embed=embed, view=self)
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
