"""Authorization, aggregation, coverage, cache, and payload assembly for ``/me stats``."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import logging
import time
from typing import Any

from file_utils import emit_telemetry_event
from player_self_service.stats_models import (
    PersonalStatsAccessChanged,
    PersonalStatsDailyRow,
    PersonalStatsDataSet,
    PersonalStatsMetrics,
    PersonalStatsNoAccounts,
    PersonalStatsPayload,
    PersonalStatsUnavailable,
    StatsCoverage,
    StatsDailyPoint,
    StatsGovernorOption,
    StatsMetricSummary,
    StatsPeriod,
    StatsResultState,
    StatsScopeType,
    StatsWindow,
)
from services.governor_account_service import (
    AccountResolutionSummary,
    get_account_summary_for_user,
)
from stats.dal import personal_stats_dal

logger = logging.getLogger(__name__)

AccountLoader = Callable[[int], Awaitable[AccountResolutionSummary]]
DataLoader = Callable[..., PersonalStatsDataSet]

_CACHE_TTL_SECONDS = 30.0
_CACHE_MAX_ENTRIES = 32
_DATA_TIMEOUT_SECONDS = 9.0
_DATA_SEMAPHORE = asyncio.Semaphore(8)
_CACHE_LOCK = asyncio.Lock()


@dataclass(slots=True)
class _CacheEntry:
    expires_at: float
    dataset: PersonalStatsDataSet


_CACHE: OrderedDict[tuple[int, tuple[int, ...]], _CacheEntry] = OrderedDict()
_INFLIGHT: dict[tuple[int, tuple[int, ...]], asyncio.Task[PersonalStatsDataSet]] = {}


async def _remove_finished_inflight(
    key: tuple[int, tuple[int, ...]],
    task: asyncio.Task[PersonalStatsDataSet],
) -> None:
    async with _CACHE_LOCK:
        if _INFLIGHT.get(key) is task:
            _INFLIGHT.pop(key, None)


def _schedule_inflight_cleanup(
    key: tuple[int, tuple[int, ...]],
    task: asyncio.Task[PersonalStatsDataSet],
) -> None:
    try:
        task.exception()
    except asyncio.CancelledError:
        pass
    asyncio.create_task(_remove_finished_inflight(key, task))


def stats_window(period: StatsPeriod, anchor: date) -> StatsWindow:
    if period is StatsPeriod.YESTERDAY:
        selected = anchor - timedelta(days=1)
        return StatsWindow(selected, selected)
    if period is StatsPeriod.THIS_WEEK:
        return StatsWindow(anchor - timedelta(days=anchor.weekday()), anchor)
    if period is StatsPeriod.LAST_WEEK:
        this_monday = anchor - timedelta(days=anchor.weekday())
        return StatsWindow(this_monday - timedelta(days=7), this_monday - timedelta(days=1))
    if period is StatsPeriod.THIS_MONTH:
        return StatsWindow(anchor.replace(day=1), anchor)
    if period is StatsPeriod.LAST_MONTH:
        this_month = anchor.replace(day=1)
        previous_end = this_month - timedelta(days=1)
        return StatsWindow(previous_end.replace(day=1), previous_end)
    if period is StatsPeriod.LAST_90_DAYS:
        return StatsWindow(anchor - timedelta(days=89), anchor)
    if period is StatsPeriod.LAST_180_DAYS:
        return StatsWindow(anchor - timedelta(days=179), anchor)
    raise ValueError(f"Unsupported stats period: {period!r}")


def _options(summary: AccountResolutionSummary) -> tuple[tuple[StatsGovernorOption, ...], bool]:
    options: list[StatsGovernorOption] = []
    seen: set[int] = set()
    duplicate_id = False
    for account in summary.resolved_accounts:
        governor_id = int(account.governor_id)
        if governor_id in seen:
            duplicate_id = True
            continue
        seen.add(governor_id)
        options.append(
            StatsGovernorOption(
                governor_id=governor_id,
                governor_name=(account.governor_name or account.governor_id_str).strip(),
                slot=str(account.slot),
                is_main=str(account.slot).casefold() == "main",
            )
        )
    return tuple(options), duplicate_id


def _fingerprint(summary: AccountResolutionSummary) -> tuple[tuple[str, int], ...]:
    return tuple(
        (str(account.slot), int(account.governor_id)) for account in summary.resolved_accounts
    )


async def _load_registry(
    discord_user_id: int,
    account_loader: AccountLoader,
) -> AccountResolutionSummary:
    try:
        summary = await account_loader(int(discord_user_id))
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("personal_stats_registry_read_failed user_id=%s", discord_user_id)
        raise PersonalStatsUnavailable("The account registry is temporarily unavailable") from exc
    if not summary.ok:
        logger.warning("personal_stats_registry_unavailable user_id=%s", discord_user_id)
        raise PersonalStatsUnavailable("The account registry is temporarily unavailable")
    return summary


async def _fetch_dataset(
    governor_ids: tuple[int, ...],
    data_loader: DataLoader,
) -> PersonalStatsDataSet:
    async with _DATA_SEMAPHORE:
        return await asyncio.wait_for(
            asyncio.to_thread(data_loader, governor_ids, history_days=180),
            timeout=_DATA_TIMEOUT_SECONDS,
        )


async def _authorized_dataset(
    discord_user_id: int,
    governor_ids: tuple[int, ...],
    data_loader: DataLoader,
) -> tuple[PersonalStatsDataSet, bool]:
    key = (int(discord_user_id), tuple(sorted(governor_ids)))
    now = time.monotonic()
    async with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is not None and entry.expires_at > now:
            _CACHE.move_to_end(key)
            return entry.dataset, True
        if entry is not None:
            _CACHE.pop(key, None)
        task = _INFLIGHT.get(key)
        if task is None:
            task = asyncio.create_task(_fetch_dataset(governor_ids, data_loader))
            _INFLIGHT[key] = task
            task.add_done_callback(
                lambda completed, cache_key=key: _schedule_inflight_cleanup(cache_key, completed)
            )

    try:
        dataset = await asyncio.shield(task)
    finally:
        if task.done():
            async with _CACHE_LOCK:
                if _INFLIGHT.get(key) is task:
                    _INFLIGHT.pop(key, None)

    async with _CACHE_LOCK:
        _CACHE[key] = _CacheEntry(
            expires_at=time.monotonic() + _CACHE_TTL_SECONDS,
            dataset=dataset,
        )
        _CACHE.move_to_end(key)
        while len(_CACHE) > _CACHE_MAX_ENTRIES:
            _CACHE.popitem(last=False)
    return dataset, False


def _valid_interval(previous: date | None, current: date, window: StatsWindow) -> bool:
    return bool(
        previous is not None
        and previous < current
        and previous >= window.start_date - timedelta(days=1)
        and window.start_date <= current <= window.end_date
    )


def _metric(
    rows: tuple[PersonalStatsDailyRow, ...],
    window: StatsWindow,
    extractor: Callable[[PersonalStatsDailyRow], int | None],
    *,
    previous: Callable[[PersonalStatsDailyRow], date | None] | None,
) -> StatsMetricSummary:
    totals_by_date: dict[date, int] = {}
    exact_daily: dict[date, int] = {}
    for row in rows:
        if not window.start_date <= row.as_of_date <= window.end_date:
            continue
        value = extractor(row)
        if value is None:
            continue
        previous_date = previous(row) if previous is not None else None
        if previous is not None and not _valid_interval(previous_date, row.as_of_date, window):
            continue
        totals_by_date[row.as_of_date] = totals_by_date.get(row.as_of_date, 0) + value
        if previous is None or previous_date == row.as_of_date - timedelta(days=1):
            exact_daily[row.as_of_date] = exact_daily.get(row.as_of_date, 0) + value

    if not totals_by_date:
        return StatsMetricSummary(None, 0, window.expected_days)
    daily = tuple(
        StatsDailyPoint(reporting_date=reporting_date, value=value)
        for reporting_date, value in sorted(exact_daily.items())
    )
    peak = max(daily, key=lambda point: point.value) if daily else None
    return StatsMetricSummary(
        total=sum(totals_by_date.values()),
        reporting_days=len(totals_by_date),
        expected_days=window.expected_days,
        daily=daily,
        peak_date=peak.reporting_date if peak else None,
        peak_value=peak.value if peak else None,
    )


def _period_end_context(
    rows: tuple[PersonalStatsDailyRow, ...],
    window: StatsWindow,
    governor_ids: tuple[int, ...],
) -> tuple[int | None, int | None, date | None]:
    end_rows = [row for row in rows if row.has_stats and row.as_of_date == window.end_date]
    power_values = {
        row.governor_id: row.power_value for row in end_rows if row.power_value is not None
    }
    troop_values = {
        row.governor_id: row.troop_power_value
        for row in end_rows
        if row.troop_power_value is not None
    }
    complete_power = len(power_values) == len(governor_ids)
    complete_troops = len(troop_values) == len(governor_ids)
    return (
        sum(power_values.values()) if complete_power else None,
        sum(troop_values.values()) if complete_troops else None,
        window.end_date if complete_power or complete_troops else None,
    )


def _build_metrics(
    rows: tuple[PersonalStatsDailyRow, ...],
    window: StatsWindow,
    governor_ids: tuple[int, ...],
) -> PersonalStatsMetrics:
    stats_previous = lambda row: row.previous_stats_date
    activity_previous = lambda row: row.previous_activity_date
    power = _metric(rows, window, lambda row: row.power_delta, previous=stats_previous)
    troop_power = _metric(rows, window, lambda row: row.troop_power_delta, previous=stats_previous)
    rss = _metric(rows, window, lambda row: row.rss_gathered_delta, previous=stats_previous)
    assisted = _metric(rows, window, lambda row: row.rss_assist_delta, previous=stats_previous)
    helps = _metric(rows, window, lambda row: row.helps_delta, previous=stats_previous)
    build = _metric(rows, window, lambda row: row.build_activity_delta, previous=activity_previous)
    tech = _metric(rows, window, lambda row: row.tech_donations_delta, previous=activity_previous)
    forts_total = _metric(rows, window, lambda row: row.forts_total, previous=None)
    forts_launched = _metric(rows, window, lambda row: row.forts_launched, previous=None)
    forts_joined = _metric(rows, window, lambda row: row.forts_joined, previous=None)
    kill_points = _metric(rows, window, lambda row: row.kill_points_delta, previous=stats_previous)
    t4 = _metric(rows, window, lambda row: row.t4_kills_delta, previous=stats_previous)
    t5 = _metric(rows, window, lambda row: row.t5_kills_delta, previous=stats_previous)
    t4_t5 = _metric(
        rows,
        window,
        lambda row: (
            row.t4_kills_delta + row.t5_kills_delta
            if row.t4_kills_delta is not None and row.t5_kills_delta is not None
            else None
        ),
        previous=stats_previous,
    )
    deads = _metric(rows, window, lambda row: row.deads_delta, previous=stats_previous)
    healed = _metric(rows, window, lambda row: row.healed_troops_delta, previous=stats_previous)
    end_power, end_troops, end_date = _period_end_context(rows, window, governor_ids)
    return PersonalStatsMetrics(
        power_change=power,
        troop_power_change=troop_power,
        rss_gathered=rss,
        rss_assisted=assisted,
        helps=helps,
        build_activity=build,
        tech_donations=tech,
        forts_total=forts_total,
        forts_launched=forts_launched,
        forts_joined=forts_joined,
        kill_points=kill_points,
        t4_kills=t4,
        t5_kills=t5,
        t4_t5_kills=t4_t5,
        deads=deads,
        healed_troops=healed,
        period_end_power=end_power,
        period_end_troop_power=end_troops,
        period_end_date=end_date,
    )


def _coverage(
    rows: tuple[PersonalStatsDailyRow, ...],
    window: StatsWindow,
    governor_ids: tuple[int, ...],
) -> StatsCoverage:
    in_window = tuple(row for row in rows if window.start_date <= row.as_of_date <= window.end_date)
    stats_days = {(row.governor_id, row.as_of_date) for row in in_window if row.has_stats}
    activity_days = {
        (row.governor_id, row.as_of_date) for row in in_window if row.has_alliance_activity
    }
    fort_days = {(row.governor_id, row.as_of_date) for row in in_window if row.has_forts}
    return StatsCoverage(
        expected_dates=window.expected_days,
        stats_reporting_dates=len({day for _, day in stats_days}),
        requested_governors=len(governor_ids),
        stats_reporting_governors=len({governor_id for governor_id, _ in stats_days}),
        expected_account_days=window.expected_days * len(governor_ids),
        stats_account_days=len(stats_days),
        activity_account_days=len(activity_days),
        fort_account_days=len(fort_days),
    )


def _result_state(
    coverage: StatsCoverage,
    metrics: PersonalStatsMetrics,
    rows: tuple[PersonalStatsDailyRow, ...],
    window: StatsWindow,
    governor_ids: tuple[int, ...],
) -> StatsResultState:
    usable = any(metric.total is not None for metric in metrics.summaries()) or any(
        value is not None for value in (metrics.period_end_power, metrics.period_end_troop_power)
    )
    if not usable:
        return StatsResultState.NO_DATA
    by_identity = {
        (row.governor_id, row.as_of_date): row
        for row in rows
        if window.start_date <= row.as_of_date <= window.end_date
    }
    required_values_complete = True
    for governor_id in governor_ids:
        for offset in range(window.expected_days):
            reporting_date = window.start_date + timedelta(days=offset)
            row = by_identity.get((governor_id, reporting_date))
            if row is None:
                required_values_complete = False
                break
            stats_values = (
                row.power_delta,
                row.troop_power_delta,
                row.kill_points_delta,
                row.rss_gathered_delta,
                row.rss_assist_delta,
                row.helps_delta,
                row.t4_kills_delta,
                row.t5_kills_delta,
                row.deads_delta,
                row.healed_troops_delta,
            )
            activity_values = (row.build_activity_delta, row.tech_donations_delta)
            fort_values = (row.forts_total, row.forts_launched, row.forts_joined)
            if not (
                row.has_stats
                and _valid_interval(row.previous_stats_date, reporting_date, window)
                and all(value is not None for value in stats_values)
                and row.has_alliance_activity
                and _valid_interval(row.previous_activity_date, reporting_date, window)
                and all(value is not None for value in activity_values)
                and row.has_forts
                and all(value is not None for value in fort_values)
            ):
                required_values_complete = False
                break
        if not required_values_complete:
            break
    complete = required_values_complete and (
        coverage.stats_account_days == coverage.expected_account_days
        and coverage.activity_account_days == coverage.expected_account_days
        and coverage.fort_account_days == coverage.expected_account_days
    )
    return StatsResultState.READY if complete else StatsResultState.PARTIAL


def _scope_label(
    scope_type: StatsScopeType,
    governor_ids: tuple[int, ...],
    options: tuple[StatsGovernorOption, ...],
) -> str:
    if scope_type is StatsScopeType.ALL_LINKED:
        return "All Linked"
    option = next(option for option in options if option.governor_id == governor_ids[0])
    duplicates = sum(
        1
        for candidate in options
        if candidate.governor_name.casefold() == option.governor_name.casefold()
    )
    suffix = f" ({str(option.governor_id)[-4:]})" if duplicates > 1 else ""
    return f"{option.governor_name}{suffix}"


def _emit(event: dict[str, Any]) -> None:
    try:
        emit_telemetry_event(event)
    except Exception:
        logger.debug("personal_stats_telemetry_failed", exc_info=True)


async def build_personal_stats_payload(
    discord_user_id: int,
    *,
    period: StatsPeriod = StatsPeriod.THIS_WEEK,
    governor_id: int | None = None,
    all_linked: bool = False,
    expected_registry_fingerprint: tuple[tuple[str, int], ...] | None = None,
    account_loader: AccountLoader = get_account_summary_for_user,
    data_loader: DataLoader = personal_stats_dal.fetch_personal_stats_daily,
) -> PersonalStatsPayload:
    """Build one authorized immutable payload for a selected or All Linked scope."""
    started = time.perf_counter()
    summary = await _load_registry(discord_user_id, account_loader)
    options, duplicate_id = _options(summary)
    if not options:
        raise PersonalStatsNoAccounts("No linked governors are available")
    fingerprint = _fingerprint(summary)
    if expected_registry_fingerprint is not None and fingerprint != expected_registry_fingerprint:
        raise PersonalStatsAccessChanged("Linked governor access changed")

    authorized_ids = tuple(option.governor_id for option in options)
    if all_linked:
        scope_type = StatsScopeType.ALL_LINKED
        selected_ids = authorized_ids
    else:
        scope_type = StatsScopeType.SELECTED
        selected_id = (
            int(governor_id)
            if governor_id is not None
            else next(
                (option.governor_id for option in options if option.is_main), options[0].governor_id
            )
        )
        if selected_id not in authorized_ids:
            raise PersonalStatsAccessChanged("The selected governor is no longer linked")
        selected_ids = (selected_id,)

    try:
        dataset, cache_hit = await _authorized_dataset(
            int(discord_user_id), selected_ids, data_loader
        )
    except asyncio.CancelledError:
        raise
    except (TimeoutError, ValueError) as exc:
        logger.warning(
            "personal_stats_data_unavailable user_id=%s governor_count=%s",
            discord_user_id,
            len(selected_ids),
            exc_info=True,
        )
        _emit(
            {
                "event": "me_stats_data",
                "period": period.value,
                "scope_type": scope_type.value,
                "governor_count": len(selected_ids),
                "result_state": StatsResultState.UNAVAILABLE.value,
                "fallback_reason": "data_timeout_or_contract",
                "data_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
        raise PersonalStatsUnavailable("Period performance is temporarily unavailable") from exc
    except Exception as exc:
        logger.exception(
            "personal_stats_data_failed user_id=%s governor_count=%s",
            discord_user_id,
            len(selected_ids),
        )
        _emit(
            {
                "event": "me_stats_data",
                "period": period.value,
                "scope_type": scope_type.value,
                "governor_count": len(selected_ids),
                "result_state": StatsResultState.UNAVAILABLE.value,
                "fallback_reason": "data_dependency_failure",
                "data_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
        raise PersonalStatsUnavailable("Period performance is temporarily unavailable") from exc

    final_summary = await _load_registry(discord_user_id, account_loader)
    if _fingerprint(final_summary) != fingerprint:
        raise PersonalStatsAccessChanged("Linked governor access changed during the request")
    final_ids = {int(account.governor_id) for account in final_summary.resolved_accounts}
    if not set(selected_ids).issubset(final_ids):
        raise PersonalStatsAccessChanged("Linked governor access changed during the request")

    anchor = dataset.header.stats_anchor_date
    if anchor is None:
        raise PersonalStatsUnavailable("The Stats reporting anchor is unavailable")
    window = stats_window(period, anchor)
    rows = tuple(row for row in dataset.rows if row.governor_id in set(selected_ids))
    coverage = _coverage(rows, window, selected_ids)
    metrics = _build_metrics(rows, window, selected_ids)
    state = _result_state(coverage, metrics, rows, window, selected_ids)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    _emit(
        {
            "event": "me_stats_data",
            "period": period.value,
            "scope_type": scope_type.value,
            "governor_count": len(selected_ids),
            "stats_reporting_dates": coverage.stats_reporting_dates,
            "stats_account_days": coverage.stats_account_days,
            "result_state": state.value,
            "cache_hit": cache_hit,
            "data_ms": elapsed_ms,
        }
    )
    return PersonalStatsPayload(
        discord_user_id=int(discord_user_id),
        period=period,
        window=window,
        stats_anchor_date=anchor,
        scope_type=scope_type,
        scope_governor_ids=selected_ids,
        scope_label=_scope_label(scope_type, selected_ids, options),
        governor_options=options,
        duplicate_id_warning=duplicate_id,
        registry_fingerprint=fingerprint,
        coverage=coverage,
        state=state,
        metrics=metrics,
        generated_at_utc=datetime.now(UTC),
    )


async def clear_personal_stats_cache() -> None:
    """Test/operational helper for clearing the bounded in-memory cache."""
    async with _CACHE_LOCK:
        _CACHE.clear()
