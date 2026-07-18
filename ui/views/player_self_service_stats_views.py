"""Private author-gated interaction journey for ``/me stats``."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC
from functools import partial
from io import BytesIO
import logging
from math import ceil
import secrets
import time
from typing import Any

import discord

from file_utils import emit_telemetry_event
from player_self_service.stats_models import (
    PersonalStatsAccessChanged,
    PersonalStatsNoAccounts,
    PersonalStatsPayload,
    PersonalStatsUnavailable,
    StatsMetricSummary,
    StatsMode,
    StatsPeriod,
    StatsScopeType,
)
from player_self_service.stats_renderer import RenderedStatsCard, render_personal_stats_card
from player_self_service.stats_service import build_personal_stats_payload

logger = logging.getLogger(__name__)

PayloadLoader = Callable[..., Awaitable[PersonalStatsPayload]]
Renderer = Callable[..., RenderedStatsCard]

_VIEW_TIMEOUT_SECONDS = 180.0
_RENDER_TIMEOUT_SECONDS = 3.5
_RENDER_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="me-stats-render")
_AVATAR_TIMEOUT_SECONDS = 3.0
_AVATAR_MAX_BYTES = 2 * 1024 * 1024
_GOVERNOR_PAGE_SIZE = 24


def _emit(event: dict[str, Any]) -> None:
    try:
        emit_telemetry_event(event)
    except Exception:
        logger.debug("personal_stats_view_telemetry_failed", exc_info=True)


async def _read_avatar_bytes(user: Any, *, author_id: int) -> bytes | None:
    try:
        if user is None or int(getattr(user, "id", -1)) != int(author_id):
            return None
    except (TypeError, ValueError):
        return None
    avatar = getattr(user, "display_avatar", None) or getattr(user, "avatar", None)
    if avatar is None:
        return None
    try:
        if hasattr(avatar, "with_size"):
            avatar = avatar.with_size(256)
        data = await asyncio.wait_for(avatar.read(), timeout=_AVATAR_TIMEOUT_SECONDS)
        return data if len(data) <= _AVATAR_MAX_BYTES else None
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("personal_stats_avatar_read_failed", exc_info=True)
        return None


async def _cancel_task(task: asyncio.Task[Any]) -> None:
    if not task.done():
        task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def _run_renderer(
    renderer: Renderer,
    payload: PersonalStatsPayload,
    *,
    mode: StatsMode,
    display_name: str,
    avatar_bytes: bytes | None,
) -> RenderedStatsCard:
    loop = asyncio.get_running_loop()
    render_future = loop.run_in_executor(
        _RENDER_EXECUTOR,
        partial(
            renderer,
            payload,
            mode=mode,
            display_name=display_name,
            avatar_bytes=avatar_bytes,
        ),
    )
    return await asyncio.wait_for(render_future, timeout=_RENDER_TIMEOUT_SECONDS)


def _close_files(files: list[discord.File] | None) -> None:
    for file in files or []:
        try:
            file.close()
        except Exception:
            logger.debug("personal_stats_file_close_failed", exc_info=True)
        stream = getattr(file, "fp", None)
        try:
            if stream is not None and not getattr(stream, "closed", False):
                stream.close()
        except Exception:
            logger.debug("personal_stats_stream_close_failed", exc_info=True)


async def _private_message(interaction: discord.Interaction, content: str) -> None:
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("personal_stats_private_message_failed", exc_info=True)


async def _defer(interaction: discord.Interaction, *, ephemeral: bool = False) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=ephemeral)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("personal_stats_defer_failed", exc_info=True)


def _number(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{value:+,}" if value else "0"


def _compact_alt_number(value: int | float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    magnitude = abs(value)
    for divisor, suffix in (
        (1_000_000_000_000_000_000, "E"),
        (1_000_000_000_000_000, "Q"),
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ):
        if magnitude >= divisor:
            rendered = f"{value / divisor:.2f}".rstrip("0").rstrip(".")
            return f"{sign}{rendered}{suffix}"
    rendered = f"{value:,.1f}".rstrip("0").rstrip(".") if isinstance(value, float) else f"{value:,}"
    return f"{sign}{rendered}"


def _metric_text(label: str, metric: StatsMetricSummary) -> str:
    average = metric.average_per_reporting_day
    peak = (
        "no exact daily peak"
        if metric.peak_date is None
        else f"peak {metric.peak_date:%d %b %Y} {_number(metric.peak_value)}"
    )
    average_text = "—" if average is None else f"{average:+,.1f}"
    return (
        f"**{label}:** {_number(metric.total)} • Avg {average_text}/reporting day • "
        f"{peak} • Coverage {metric.reporting_days}/{metric.expected_days} reporting days"
    )


def _metric_alt_text(label: str, metric: StatsMetricSummary) -> str:
    average = metric.average_per_reporting_day
    average_text = _compact_alt_number(average)
    peak = (
        "no exact peak"
        if metric.peak_date is None
        else f"peak {metric.peak_date:%d %b} {_compact_alt_number(metric.peak_value)}"
    )
    return (
        f"{label}: total {_compact_alt_number(metric.total)}, average {average_text}/day, "
        f"{peak}, coverage {metric.reporting_days}/{metric.expected_days} days"
    )


def _attachment_description(payload: PersonalStatsPayload, mode: StatsMode) -> str:
    metrics = payload.metrics
    if mode is StatsMode.OVERVIEW:
        selected = (
            ("Power change", metrics.power_change),
            ("Troop Power change", metrics.troop_power_change),
            ("RSS gathered", metrics.rss_gathered),
            ("Helps", metrics.helps),
            ("Forts total", metrics.forts_total),
            ("Kill Points", metrics.kill_points),
            ("T4+T5 kills", metrics.t4_t5_kills),
            ("Deads", metrics.deads),
        )
    elif mode is StatsMode.ACTIVITY:
        selected = (
            ("RSS gathered", metrics.rss_gathered),
            ("RSS assisted", metrics.rss_assisted),
            ("Helps", metrics.helps),
            ("Build activity", metrics.build_activity),
            ("Tech donations", metrics.tech_donations),
            ("Forts total", metrics.forts_total),
            ("Forts launched", metrics.forts_launched),
            ("Forts joined", metrics.forts_joined),
        )
    else:
        selected = (
            ("Kill Points gained", metrics.kill_points),
            ("T4 kills gained", metrics.t4_kills),
            ("T5 kills gained", metrics.t5_kills),
            ("T4+T5 combined", metrics.t4_t5_kills),
            ("Deads gained", metrics.deads),
            ("Healed Troops gained", metrics.healed_troops),
        )
    description = (
        f"Period Performance {mode.label}, {payload.period.label}, "
        f"{payload.window.start_date:%d %b %Y} to {payload.window.end_date:%d %b %Y}. "
        + "; ".join(_metric_alt_text(label, metric) for label, metric in selected)
    )
    if len(description) > 1024:
        raise ValueError("Stats attachment description exceeds Discord's limit")
    return description


def _add_fallback_lines(
    embed: discord.Embed,
    title: str,
    values: tuple[str, ...],
) -> None:
    chunks: list[str] = []
    current = ""
    for value in values:
        candidate = f"{current}\n{value}" if current else value
        if len(candidate) > 1_000 and current:
            chunks.append(current)
            current = value
        else:
            current = candidate
    if current:
        chunks.append(current)
    for index, chunk in enumerate(chunks):
        suffix = "" if index == 0 else " (continued)"
        embed.add_field(name=f"{title}{suffix}", value=chunk, inline=False)


def build_personal_stats_fallback_embed(
    payload: PersonalStatsPayload,
    *,
    mode: StatsMode,
) -> discord.Embed:
    embed = discord.Embed(
        title=f"Period Performance — {payload.scope_label}",
        description=(
            f"**{mode.label} • {payload.period.label}**\n"
            f"{payload.window.start_date:%d %b %Y} — {payload.window.end_date:%d %b %Y}\n"
            f"State: **{payload.state.value}** • Stats anchor: {payload.stats_anchor_date:%d %b %Y}"
        ),
        color=(
            discord.Color.green()
            if payload.state.value == "READY"
            else discord.Color.gold() if payload.state.value == "PARTIAL" else discord.Color.red()
        ),
    )
    metrics = payload.metrics
    if mode is StatsMode.OVERVIEW:
        values = (
            _metric_text("Power change", metrics.power_change),
            f"Period-end Power: {_number(metrics.period_end_power)}",
            _metric_text("Troop Power change", metrics.troop_power_change),
            f"Period-end Troop Power: {_number(metrics.period_end_troop_power)}",
            _metric_text("RSS gathered", metrics.rss_gathered),
            _metric_text("Helps", metrics.helps),
            _metric_text("Forts total", metrics.forts_total),
            _metric_text("Kill Points", metrics.kill_points),
            _metric_text("T4+T5 kills", metrics.t4_t5_kills),
            _metric_text("Deads", metrics.deads),
        )
        _add_fallback_lines(embed, "Overview", values)
    elif mode is StatsMode.ACTIVITY:
        values = (
            _metric_text("RSS gathered", metrics.rss_gathered),
            _metric_text("RSS assisted", metrics.rss_assisted),
            _metric_text("Helps", metrics.helps),
            _metric_text("Build activity", metrics.build_activity),
            _metric_text("Tech donations", metrics.tech_donations),
            _metric_text("Forts total", metrics.forts_total),
            _metric_text("Forts launched", metrics.forts_launched),
            _metric_text("Forts joined", metrics.forts_joined),
        )
        _add_fallback_lines(embed, "Activity and daily-trend equivalents", values)
    else:
        values = (
            _metric_text("Kill Points gained", metrics.kill_points),
            _metric_text("T4 kills gained", metrics.t4_kills),
            _metric_text("T5 kills gained", metrics.t5_kills),
            _metric_text("T4+T5 combined", metrics.t4_t5_kills),
            _metric_text("Deads gained", metrics.deads),
            _metric_text("Healed Troops gained", metrics.healed_troops),
        )
        _add_fallback_lines(embed, "Combat", values)
    coverage = payload.coverage
    embed.add_field(
        name="Coverage",
        value=(
            f"Stats dates: {coverage.stats_reporting_dates}/{coverage.expected_dates}\n"
            f"Reporting governors: {coverage.stats_reporting_governors}/{coverage.requested_governors}\n"
            f"Stats account-days: {coverage.stats_account_days}/{coverage.expected_account_days}\n"
            f"Alliance Activity account-days: {coverage.activity_account_days}/{coverage.expected_account_days}\n"
            f"Fort account-days: {coverage.fort_account_days}/{coverage.expected_account_days}"
        ),
        inline=False,
    )
    if payload.duplicate_id_warning:
        embed.add_field(
            name="Registry review",
            value="Duplicate linked Governor IDs were deduplicated before data access.",
            inline=False,
        )
    generated_utc = payload.generated_at_utc.astimezone(UTC)
    embed.set_footer(text=f"Private report • Generated {generated_utc:%d %b %Y %H:%M:%S UTC}")
    return embed


class _ActionButton(discord.ui.Button):
    def __init__(
        self,
        *,
        label: str,
        custom_id: str,
        row: int,
        style: discord.ButtonStyle,
        action: Callable[[discord.Interaction], Awaitable[None]],
        disabled: bool = False,
    ) -> None:
        super().__init__(
            label=label,
            custom_id=custom_id,
            row=row,
            style=style,
            disabled=disabled,
        )
        self._action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._action(interaction)


class _PeriodSelect(discord.ui.Select):
    def __init__(self, parent: PersonalStatsView) -> None:
        options = [
            discord.SelectOption(
                label=period.label,
                value=period.value,
                default=period is parent.period,
            )
            for period in StatsPeriod
        ]
        super().__init__(
            placeholder="Change period",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:stats:period",
            row=1,
        )
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent_view.change_period(interaction, StatsPeriod(self.values[0]))


class _ScopeSelect(discord.ui.Select):
    def __init__(self, parent: PersonalStatsView) -> None:
        start = parent.scope_page * _GOVERNOR_PAGE_SIZE
        page_options = parent.payload.governor_options[start : start + _GOVERNOR_PAGE_SIZE]
        choices = [
            discord.SelectOption(
                label="All Linked",
                value=parent._token_for(None),
                description=f"Aggregate {len(parent.payload.governor_options)} distinct governors",
                default=parent.payload.scope_type is StatsScopeType.ALL_LINKED,
            )
        ]
        name_counts: dict[str, int] = {}
        for option in parent.payload.governor_options:
            key = option.governor_name.casefold()
            name_counts[key] = name_counts.get(key, 0) + 1
        for option in page_options:
            duplicate_name = name_counts.get(option.governor_name.casefold(), 0) > 1
            suffix = f" • ID …{str(option.governor_id)[-4:]}" if duplicate_name else ""
            choices.append(
                discord.SelectOption(
                    label=f"{option.slot} • {option.governor_name}{suffix}"[:100],
                    value=parent._token_for(option.governor_id),
                    description=f"Governor ID ending {str(option.governor_id)[-4:]}"[:100],
                    default=(
                        parent.payload.scope_type is StatsScopeType.SELECTED
                        and parent.payload.scope_governor_ids == (option.governor_id,)
                    ),
                )
            )
        super().__init__(
            placeholder="Change governor or scope",
            min_values=1,
            max_values=1,
            options=choices,
            custom_id="me:stats:scope",
            row=2,
        )
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent_view.change_scope(interaction, self.values[0])


class PersonalStatsView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        payload: PersonalStatsPayload,
        avatar_bytes: bytes | None,
        mode: StatsMode = StatsMode.OVERVIEW,
        scope_page: int | None = None,
        payload_loader: PayloadLoader = build_personal_stats_payload,
        renderer: Renderer = render_personal_stats_card,
        timeout: float = _VIEW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.payload = payload
        self.avatar_bytes = avatar_bytes
        self.mode = mode
        self.period = payload.period
        if scope_page is None and payload.scope_type is StatsScopeType.SELECTED:
            selected_id = payload.scope_governor_ids[0]
            selected_index = next(
                (
                    index
                    for index, option in enumerate(payload.governor_options)
                    if option.governor_id == selected_id
                ),
                0,
            )
            scope_page = selected_index // _GOVERNOR_PAGE_SIZE
        self.scope_page = max(0, int(scope_page or 0))
        self.payload_loader = payload_loader
        self.renderer = renderer
        self._generation = 0
        self._active_task: asyncio.Task[Any] | None = None
        self._delivery_lock = asyncio.Lock()
        self._token_map: dict[str, int | None] = {}
        self._expired = False
        self._message_ref: discord.Message | None = None
        self._timeout_editor: Callable[..., Awaitable[Any]] | None = None
        self._build_controls()

    def set_timeout_target(self, target: Any) -> None:
        editor = getattr(target, "edit_original_response", None)
        if callable(editor):
            self._timeout_editor = editor

    def set_message_ref(self, message: discord.Message | None) -> None:
        self._message_ref = message

    def _token_for(self, governor_id: int | None) -> str:
        token = secrets.token_urlsafe(8)
        self._token_map[token] = governor_id
        return token

    def _build_controls(self) -> None:
        self.clear_items()
        self._token_map.clear()
        for mode in StatsMode:
            self.add_item(
                _ActionButton(
                    label=mode.label,
                    custom_id=f"me:stats:mode:{mode.value}",
                    row=0,
                    style=(
                        discord.ButtonStyle.primary
                        if mode is self.mode
                        else discord.ButtonStyle.secondary
                    ),
                    action=lambda interaction, selected=mode: self.change_mode(
                        interaction, selected
                    ),
                    disabled=mode is self.mode,
                )
            )
        self.add_item(_PeriodSelect(self))
        option_count = len(self.payload.governor_options)
        if option_count > 1:
            pages = max(1, ceil(option_count / _GOVERNOR_PAGE_SIZE))
            self.scope_page = min(self.scope_page, pages - 1)
            self.add_item(_ScopeSelect(self))
            if pages > 1:
                self.add_item(
                    _ActionButton(
                        label="Previous Governors",
                        custom_id="me:stats:scope:previous",
                        row=3,
                        style=discord.ButtonStyle.secondary,
                        action=lambda interaction: self.change_scope_page(interaction, -1),
                        disabled=self.scope_page <= 0,
                    )
                )
                self.add_item(
                    _ActionButton(
                        label="Next Governors",
                        custom_id="me:stats:scope:next",
                        row=3,
                        style=discord.ButtonStyle.secondary,
                        action=lambda interaction: self.change_scope_page(interaction, 1),
                        disabled=self.scope_page >= pages - 1,
                    )
                )
        self.add_item(
            _ActionButton(
                label="Dashboard",
                custom_id="me:stats:dashboard",
                row=4,
                style=discord.ButtonStyle.success,
                action=self.open_dashboard,
            )
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._expired:
            await _private_message(
                interaction, "Report controls expired. Run /me stats to refresh."
            )
            return False
        if interaction.user is None or int(interaction.user.id) != self.author_id:
            await _private_message(interaction, "This private Stats report is not for you.")
            return False
        return True

    def _begin_transition(self) -> int:
        self._generation += 1
        current = asyncio.current_task()
        previous = self._active_task
        self._active_task = current
        if previous is not None and previous is not current and not previous.done():
            previous.cancel()
        return self._generation

    def _is_current(self, generation: int) -> bool:
        return not self._expired and generation == self._generation

    async def _render(self, payload: PersonalStatsPayload, mode: StatsMode) -> RenderedStatsCard:
        return await _run_renderer(
            self.renderer,
            payload,
            mode=mode,
            display_name=self.display_name,
            avatar_bytes=self.avatar_bytes,
        )

    async def _edit_transition(
        self,
        interaction: discord.Interaction,
        *,
        generation: int,
        payload: PersonalStatsPayload,
        mode: StatsMode,
        rendered: RenderedStatsCard | None,
        files: list[discord.File],
    ) -> tuple[bool, float]:
        async with self._delivery_lock:
            if not self._is_current(generation):
                _emit({"event": "me_stats_transition", "stale_suppressed": True})
                return False, 0.0
            old_payload, old_mode, old_period = self.payload, self.mode, self.period
            self.payload, self.mode, self.period = payload, mode, payload.period
            self._build_controls()
            delivery_started = time.perf_counter()
            try:
                if rendered is not None:
                    files.append(
                        discord.File(
                            BytesIO(rendered.image_bytes),
                            filename=rendered.filename,
                            description=_attachment_description(payload, mode),
                        )
                    )
                    edited = await interaction.edit_original_response(
                        content=None,
                        embed=None,
                        view=self,
                        attachments=[],
                        files=files,
                    )
                else:
                    edited = await interaction.edit_original_response(
                        content=None,
                        embed=build_personal_stats_fallback_embed(payload, mode=mode),
                        view=self,
                        attachments=[],
                    )
            except Exception:
                self.payload, self.mode, self.period = old_payload, old_mode, old_period
                self._build_controls()
                raise
            delivery_ms = round((time.perf_counter() - delivery_started) * 1000, 1)
            if not self._is_current(generation):
                _emit({"event": "me_stats_transition", "stale_suppressed": True})
                return False, delivery_ms
            self.set_message_ref(getattr(interaction, "message", None) or edited)
            self.set_timeout_target(interaction)
            return True, delivery_ms

    async def _deliver_transition(
        self,
        interaction: discord.Interaction,
        *,
        generation: int,
        payload: PersonalStatsPayload,
        mode: StatsMode,
        fallback_reason: str | None = None,
    ) -> bool:
        files: list[discord.File] = []
        render_started = time.perf_counter()
        render_ms = 0.0
        delivery_ms = 0.0
        fallback = fallback_reason
        rendered: RenderedStatsCard | None = None
        try:
            if fallback is None:
                try:
                    rendered = await self._render(payload, mode)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    fallback = "render_failed"
                    logger.exception("personal_stats_transition_render_failed")
            render_ms = round((time.perf_counter() - render_started) * 1000, 1)
            delivered, delivery_ms = await self._edit_transition(
                interaction,
                generation=generation,
                payload=payload,
                mode=mode,
                rendered=rendered,
                files=files,
            )
            if not delivered:
                return False
            _emit(
                {
                    "event": "me_stats_transition",
                    "mode": mode.value,
                    "period": payload.period.value,
                    "scope_type": payload.scope_type.value,
                    "result_state": payload.state.value,
                    "stats_reporting_dates": payload.coverage.stats_reporting_dates,
                    "stats_reporting_governors": payload.coverage.stats_reporting_governors,
                    "stats_account_days": payload.coverage.stats_account_days,
                    "expected_account_days": payload.coverage.expected_account_days,
                    "render_ms": render_ms,
                    "delivery_ms": delivery_ms,
                    "fallback_reason": fallback
                    or ("avatar_fallback" if self.avatar_bytes is None else None),
                    "stale_suppressed": False,
                }
            )
            return True
        finally:
            _close_files(files)

    async def change_mode(self, interaction: discord.Interaction, mode: StatsMode) -> None:
        generation = self._begin_transition()
        await _defer(interaction)
        try:
            await self._deliver_transition(
                interaction,
                generation=generation,
                payload=self.payload,
                mode=mode,
            )
        except asyncio.CancelledError:
            _emit({"event": "me_stats_transition", "stale_suppressed": True})
        except Exception:
            logger.exception("personal_stats_mode_transition_failed")
            if self._is_current(generation):
                await _private_message(
                    interaction,
                    "That Stats mode could not be opened. Your last report is unchanged.",
                )

    async def change_period(self, interaction: discord.Interaction, period: StatsPeriod) -> None:
        generation = self._begin_transition()
        await _defer(interaction)
        try:
            payload = await self.payload_loader(
                self.author_id,
                period=period,
                governor_id=(
                    self.payload.scope_governor_ids[0]
                    if self.payload.scope_type is StatsScopeType.SELECTED
                    else None
                ),
                all_linked=self.payload.scope_type is StatsScopeType.ALL_LINKED,
                expected_registry_fingerprint=self.payload.registry_fingerprint,
            )
            await self._deliver_transition(
                interaction, generation=generation, payload=payload, mode=self.mode
            )
        except asyncio.CancelledError:
            _emit({"event": "me_stats_transition", "stale_suppressed": True})
        except PersonalStatsAccessChanged:
            _emit({"event": "me_stats_transition", "access_changed": True})
            if self._is_current(generation):
                await _private_message(
                    interaction, "Your linked-governor access changed. Run /me stats to refresh."
                )
        except PersonalStatsUnavailable:
            if self._is_current(generation):
                await _private_message(
                    interaction,
                    "Period performance is temporarily unavailable. Your last report is unchanged.",
                )
        except Exception:
            logger.exception("personal_stats_period_transition_failed")
            if self._is_current(generation):
                await _private_message(
                    interaction, "That period could not be loaded. Your last report is unchanged."
                )

    async def change_scope(self, interaction: discord.Interaction, token: str) -> None:
        if token not in self._token_map:
            await _private_message(
                interaction, "That Stats selection is expired or invalid. Run /me stats to refresh."
            )
            return
        governor_id = self._token_map[token]
        generation = self._begin_transition()
        await _defer(interaction)
        try:
            payload = await self.payload_loader(
                self.author_id,
                period=self.period,
                governor_id=governor_id,
                all_linked=governor_id is None,
                expected_registry_fingerprint=self.payload.registry_fingerprint,
            )
            await self._deliver_transition(
                interaction, generation=generation, payload=payload, mode=self.mode
            )
        except asyncio.CancelledError:
            _emit({"event": "me_stats_transition", "stale_suppressed": True})
        except PersonalStatsAccessChanged:
            _emit({"event": "me_stats_transition", "access_changed": True})
            if self._is_current(generation):
                await _private_message(
                    interaction, "Your linked-governor access changed. Run /me stats to refresh."
                )
        except PersonalStatsUnavailable:
            if self._is_current(generation):
                await _private_message(
                    interaction,
                    "That Stats scope is temporarily unavailable. Your last report is unchanged.",
                )
        except Exception:
            logger.exception("personal_stats_scope_transition_failed")
            if self._is_current(generation):
                await _private_message(
                    interaction,
                    "That Stats scope could not be loaded. Your last report is unchanged.",
                )

    async def change_scope_page(self, interaction: discord.Interaction, delta: int) -> None:
        generation = self._begin_transition()
        pages = max(1, ceil(len(self.payload.governor_options) / _GOVERNOR_PAGE_SIZE))
        next_page = min(max(0, self.scope_page + delta), pages - 1)
        try:
            async with self._delivery_lock:
                if not self._is_current(generation):
                    return
                old_page = self.scope_page
                self.scope_page = next_page
                self._build_controls()
                try:
                    await interaction.response.edit_message(view=self)
                except Exception:
                    self.scope_page = old_page
                    self._build_controls()
                    raise
        except Exception:
            logger.debug("personal_stats_scope_page_failed", exc_info=True)
            if self._is_current(generation):
                await _private_message(
                    interaction, "The governor picker page could not be changed."
                )

    async def open_dashboard(self, interaction: discord.Interaction) -> None:
        generation = self._begin_transition()
        await _defer(interaction)
        try:
            from ui.views.player_self_service_governor_dashboard_views import (
                show_governor_dashboard_for_interaction,
            )

            governor_id = (
                self.payload.scope_governor_ids[0]
                if self.payload.scope_type is StatsScopeType.SELECTED
                else None
            )
            if not self._is_current(generation):
                return
            async with self._delivery_lock:
                if not self._is_current(generation):
                    return
                await show_governor_dashboard_for_interaction(
                    interaction,
                    author_id=self.author_id,
                    display_name=self.display_name,
                    governor_id=governor_id,
                )
            if self._is_current(generation):
                self.stop()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("personal_stats_dashboard_navigation_failed")
            if self._is_current(generation):
                await _private_message(
                    interaction,
                    "The private Dashboard could not be opened. Your report is unchanged.",
                )

    async def on_timeout(self) -> None:
        self._expired = True
        self._generation += 1
        if self._active_task is not None and not self._active_task.done():
            self._active_task.cancel()
        async with self._delivery_lock:
            for child in self.children:
                child.disabled = True
            content = "Report controls expired. Run /me stats to refresh."
            try:
                if self._timeout_editor is not None:
                    await self._timeout_editor(content=content, view=self)
                elif self._message_ref is not None:
                    await self._message_ref.edit(content=content, view=self)
            except Exception:
                logger.debug("personal_stats_timeout_edit_failed", exc_info=True)
        _emit({"event": "me_stats_timeout", "timeout": True})
        self.stop()


async def _initial_delivery(
    target: Any,
    *,
    author_id: int,
    display_name: str,
    payload: PersonalStatsPayload,
    avatar_bytes: bytes | None,
    payload_loader: PayloadLoader,
    renderer: Renderer,
    entry_route: str,
) -> PersonalStatsView:
    view = PersonalStatsView(
        author_id=author_id,
        display_name=display_name,
        payload=payload,
        avatar_bytes=avatar_bytes,
        payload_loader=payload_loader,
        renderer=renderer,
    )
    files: list[discord.File] = []
    fallback_reason: str | None = None
    render_started = time.perf_counter()
    render_ms = 0.0
    delivery_started = 0.0
    try:
        try:
            rendered = await _run_renderer(
                renderer,
                payload,
                mode=StatsMode.OVERVIEW,
                display_name=display_name,
                avatar_bytes=avatar_bytes,
            )
            files = [
                discord.File(
                    BytesIO(rendered.image_bytes),
                    filename=rendered.filename,
                    description=_attachment_description(payload, StatsMode.OVERVIEW),
                )
            ]
            render_ms = round((time.perf_counter() - render_started) * 1000, 1)
            delivery_started = time.perf_counter()
            edited = await target.edit_original_response(
                content=None,
                embed=None,
                view=view,
                attachments=[],
                files=files,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            if render_ms == 0.0:
                render_ms = round((time.perf_counter() - render_started) * 1000, 1)
            _close_files(files)
            files = []
            fallback_reason = "render_or_attachment_failed"
            logger.exception("personal_stats_initial_render_failed")
            delivery_started = time.perf_counter()
            edited = await target.edit_original_response(
                content=None,
                embed=build_personal_stats_fallback_embed(payload, mode=StatsMode.OVERVIEW),
                view=view,
                attachments=[],
            )
        view.set_message_ref(edited)
        view.set_timeout_target(target)
        _emit(
            {
                "event": "me_stats_initial",
                "entry_route": entry_route,
                "mode": StatsMode.OVERVIEW.value,
                "period": payload.period.value,
                "scope_type": payload.scope_type.value,
                "result_state": payload.state.value,
                "stats_reporting_dates": payload.coverage.stats_reporting_dates,
                "stats_reporting_governors": payload.coverage.stats_reporting_governors,
                "stats_account_days": payload.coverage.stats_account_days,
                "expected_account_days": payload.coverage.expected_account_days,
                "render_ms": render_ms,
                "delivery_ms": round((time.perf_counter() - delivery_started) * 1000, 1),
                "fallback_reason": fallback_reason
                or ("avatar_fallback" if avatar_bytes is None else None),
            }
        )
        return view
    finally:
        _close_files(files)


async def show_personal_stats_for_interaction(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    governor_id: int | None = None,
    entry_route: str = "dashboard",
    payload_loader: PayloadLoader = build_personal_stats_payload,
    renderer: Renderer = render_personal_stats_card,
) -> PersonalStatsView | None:
    initial_started = time.perf_counter()
    await _defer(interaction, ephemeral=entry_route == "command")
    avatar_task = asyncio.create_task(
        _read_avatar_bytes(getattr(interaction, "user", None), author_id=author_id)
    )
    try:
        payload = await payload_loader(
            int(author_id),
            period=StatsPeriod.THIS_WEEK,
            governor_id=governor_id,
            all_linked=False,
        )
    except asyncio.CancelledError:
        await _cancel_task(avatar_task)
        raise
    except PersonalStatsNoAccounts:
        await _cancel_task(avatar_task)
        _emit(
            {
                "event": "me_stats_initial",
                "entry_route": entry_route,
                "mode": StatsMode.OVERVIEW.value,
                "period": StatsPeriod.THIS_WEEK.value,
                "result_state": "NO_ACCOUNTS",
                "data_ms": round((time.perf_counter() - initial_started) * 1000, 1),
            }
        )
        await interaction.edit_original_response(
            content="No linked governors were found. Open /me accounts to link a governor.",
            embed=None,
            view=None,
            attachments=[],
        )
        return None
    except PersonalStatsAccessChanged:
        await _cancel_task(avatar_task)
        _emit(
            {
                "event": "me_stats_initial",
                "entry_route": entry_route,
                "mode": StatsMode.OVERVIEW.value,
                "period": StatsPeriod.THIS_WEEK.value,
                "result_state": "ACCESS_CHANGED",
                "access_changed": True,
                "data_ms": round((time.perf_counter() - initial_started) * 1000, 1),
            }
        )
        await interaction.edit_original_response(
            content="Your linked-governor access changed. Run /me stats to refresh.",
            embed=None,
            view=None,
            attachments=[],
        )
        return None
    except PersonalStatsUnavailable:
        await _cancel_task(avatar_task)
        _emit(
            {
                "event": "me_stats_initial",
                "entry_route": entry_route,
                "mode": StatsMode.OVERVIEW.value,
                "period": StatsPeriod.THIS_WEEK.value,
                "result_state": "UNAVAILABLE",
                "fallback_reason": "required_dependency_unavailable",
                "data_ms": round((time.perf_counter() - initial_started) * 1000, 1),
            }
        )
        await interaction.edit_original_response(
            content="Period performance is temporarily unavailable. Please try again shortly.",
            embed=None,
            view=None,
            attachments=[],
        )
        return None
    except Exception:
        await _cancel_task(avatar_task)
        logger.exception("personal_stats_initial_load_failed")
        _emit(
            {
                "event": "me_stats_initial",
                "entry_route": entry_route,
                "mode": StatsMode.OVERVIEW.value,
                "period": StatsPeriod.THIS_WEEK.value,
                "result_state": "UNAVAILABLE",
                "fallback_reason": "unexpected_dependency_failure",
                "data_ms": round((time.perf_counter() - initial_started) * 1000, 1),
            }
        )
        await interaction.edit_original_response(
            content="Period performance is temporarily unavailable. Please try again shortly.",
            embed=None,
            view=None,
            attachments=[],
        )
        return None
    avatar_bytes = await avatar_task
    return await _initial_delivery(
        interaction,
        author_id=int(author_id),
        display_name=display_name,
        payload=payload,
        avatar_bytes=avatar_bytes,
        payload_loader=payload_loader,
        renderer=renderer,
        entry_route=entry_route,
    )


async def send_personal_stats(
    ctx: discord.ApplicationContext,
    *,
    payload_loader: PayloadLoader = build_personal_stats_payload,
    renderer: Renderer = render_personal_stats_card,
) -> PersonalStatsView | None:
    user = getattr(ctx, "user", None)
    display_name = (
        str(getattr(user, "display_name", "") or "").strip()
        or str(getattr(user, "name", "") or "").strip()
        or "player"
    )
    return await show_personal_stats_for_interaction(
        ctx.interaction,
        author_id=int(user.id),
        display_name=display_name,
        entry_route="command",
        payload_loader=payload_loader,
        renderer=renderer,
    )
