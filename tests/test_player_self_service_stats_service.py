from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import date
import time

import pytest

from player_self_service import stats_service
from player_self_service.stats_models import (
    PersonalStatsAccessChanged,
    PersonalStatsDailyRow,
    PersonalStatsDataSet,
    PersonalStatsHeader,
    PersonalStatsNoAccounts,
    StatsPeriod,
    StatsResultState,
    StatsScopeType,
)
from services.governor_account_service import AccountResolutionSummary, ResolvedAccount


def _summary(*accounts: tuple[str, int, str], ok: bool = True) -> AccountResolutionSummary:
    resolved = tuple(
        ResolvedAccount(
            slot=slot,
            governor_id=governor_id,
            governor_id_str=str(governor_id),
            governor_name=name,
            raw={"GovernorID": str(governor_id), "GovernorName": name},
        )
        for slot, governor_id, name in accounts
    )
    return AccountResolutionSummary(
        ok=ok,
        accounts={},
        ordered_accounts={},
        resolved_accounts=resolved,
        governor_ids=tuple(account.governor_id for account in resolved),
        governor_id_strings=tuple(account.governor_id_str for account in resolved),
        account_names=tuple(account.governor_name for account in resolved),
        name_to_id={account.governor_name: account.governor_id for account in resolved},
        default_choice=resolved[0].governor_id_str if resolved else "",
        error=None if ok else "registry unavailable",
    )


def _dataset(anchor: date, *rows: PersonalStatsDailyRow, count: int = 1) -> PersonalStatsDataSet:
    return PersonalStatsDataSet(
        header=PersonalStatsHeader(anchor, anchor.replace(day=1), anchor, count),
        rows=tuple(rows),
    )


def _complete_row(governor_id: int, day: date, *, value: int = 10) -> PersonalStatsDailyRow:
    previous = date.fromordinal(day.toordinal() - 1)
    return PersonalStatsDailyRow(
        governor_id=governor_id,
        as_of_date=day,
        has_stats=True,
        previous_stats_date=previous,
        power_value=1_000 + value,
        troop_power_value=500 + value,
        power_delta=value,
        troop_power_delta=-value,
        kill_points_delta=value * 2,
        rss_gathered_delta=-value * 3,
        rss_assist_delta=value * 4,
        helps_delta=value * 5,
        t4_kills_delta=value * 6,
        t5_kills_delta=-value * 7,
        deads_delta=value * 8,
        healed_troops_delta=value * 9,
        has_alliance_activity=True,
        previous_activity_date=previous,
        build_activity_delta=-value,
        tech_donations_delta=value,
        has_forts=True,
        forts_total=value,
        forts_launched=-value,
        forts_joined=value * 2,
    )


@pytest.mark.parametrize(
    ("period", "anchor", "start", "end", "days"),
    (
        (StatsPeriod.YESTERDAY, date(2026, 1, 1), date(2025, 12, 31), date(2025, 12, 31), 1),
        (StatsPeriod.THIS_WEEK, date(2026, 7, 15), date(2026, 7, 13), date(2026, 7, 15), 3),
        (StatsPeriod.LAST_WEEK, date(2026, 7, 13), date(2026, 7, 6), date(2026, 7, 12), 7),
        (StatsPeriod.THIS_MONTH, date(2024, 2, 29), date(2024, 2, 1), date(2024, 2, 29), 29),
        (StatsPeriod.LAST_MONTH, date(2024, 3, 1), date(2024, 2, 1), date(2024, 2, 29), 29),
        (StatsPeriod.LAST_90_DAYS, date(2026, 1, 1), date(2025, 10, 4), date(2026, 1, 1), 90),
        (StatsPeriod.LAST_180_DAYS, date(2024, 3, 1), date(2023, 9, 4), date(2024, 3, 1), 180),
    ),
)
def test_exact_source_anchored_periods(period, anchor, start, end, days) -> None:
    window = stats_service.stats_window(period, anchor)

    assert (window.start_date, window.end_date, window.expected_days) == (start, end, days)


@pytest.mark.asyncio
async def test_selected_default_is_main_and_signed_metrics_are_not_clamped() -> None:
    await stats_service.clear_personal_stats_cache()
    summary = _summary(("Alt1", 222, "Same Name"), ("Main", 111, "Same Name"))
    day = date(2026, 7, 14)

    async def account_loader(_user_id: int):
        return summary

    def data_loader(governor_ids, *, history_days):
        assert governor_ids == (111,)
        assert history_days == 180
        return _dataset(date(2026, 7, 15), _complete_row(111, day), count=1)

    payload = await stats_service.build_personal_stats_payload(
        101,
        period=StatsPeriod.YESTERDAY,
        account_loader=account_loader,
        data_loader=data_loader,
    )

    assert payload.scope_governor_ids == (111,)
    assert payload.scope_label == "Same Name (111)"
    assert payload.metrics.rss_gathered.total == -30
    assert payload.metrics.build_activity.total == -10
    assert payload.metrics.forts_launched.total == -10
    assert payload.metrics.t4_t5_kills.total == -10
    assert payload.state is StatsResultState.READY
    assert payload.coverage.stats_reporting_dates == 1


@pytest.mark.asyncio
async def test_all_linked_deduplicates_ids_and_recomputes_daily_totals_and_coverage() -> None:
    await stats_service.clear_personal_stats_cache()
    summary = _summary(
        ("Main", 111, "Main"),
        ("Alt1", 222, "Alt"),
        ("Farm1", 111, "Duplicate ID"),
    )
    day = date(2026, 7, 14)

    async def account_loader(_user_id: int):
        return summary

    def data_loader(governor_ids, *, history_days):
        assert governor_ids == (111, 222)
        return _dataset(
            date(2026, 7, 15),
            _complete_row(111, day, value=10),
            _complete_row(222, day, value=20),
            count=2,
        )

    payload = await stats_service.build_personal_stats_payload(
        102,
        period=StatsPeriod.YESTERDAY,
        all_linked=True,
        account_loader=account_loader,
        data_loader=data_loader,
    )

    assert payload.scope_type is StatsScopeType.ALL_LINKED
    assert payload.scope_governor_ids == (111, 222)
    assert payload.duplicate_id_warning is True
    assert payload.metrics.kill_points.total == 60
    assert payload.metrics.kill_points.reporting_days == 1
    assert payload.metrics.kill_points.daily[0].value == 60
    assert payload.coverage.expected_account_days == 2
    assert payload.coverage.stats_account_days == 2
    assert payload.coverage.stats_reporting_governors == 2


@pytest.mark.asyncio
async def test_missing_yesterday_is_no_data_not_previous_available_scan() -> None:
    await stats_service.clear_personal_stats_cache()
    summary = _summary(("Main", 111, "Main"))

    async def account_loader(_user_id: int):
        return summary

    def data_loader(_governor_ids, *, history_days):
        old = _complete_row(111, date(2026, 7, 13))
        return _dataset(date(2026, 7, 15), old)

    payload = await stats_service.build_personal_stats_payload(
        103,
        period=StatsPeriod.YESTERDAY,
        account_loader=account_loader,
        data_loader=data_loader,
    )

    assert payload.window.start_date == date(2026, 7, 14)
    assert payload.state is StatsResultState.NO_DATA
    assert payload.metrics.power_change.total is None


@pytest.mark.asyncio
async def test_complete_row_coverage_with_a_null_required_metric_is_partial() -> None:
    await stats_service.clear_personal_stats_cache()
    summary = _summary(("Main", 111, "Main"))
    row = replace(_complete_row(111, date(2026, 7, 14)), healed_troops_delta=None)

    async def account_loader(_user_id: int):
        return summary

    payload = await stats_service.build_personal_stats_payload(
        109,
        period=StatsPeriod.YESTERDAY,
        account_loader=account_loader,
        data_loader=lambda *_args, **_kwargs: _dataset(date(2026, 7, 15), row),
    )

    assert payload.coverage.stats_account_days == payload.coverage.expected_account_days
    assert payload.metrics.healed_troops.total is None
    assert payload.state is StatsResultState.PARTIAL


@pytest.mark.asyncio
async def test_forged_governor_and_mid_request_registry_change_are_rejected() -> None:
    await stats_service.clear_personal_stats_cache()
    initial = _summary(("Main", 111, "Main"))
    changed = _summary(("Main", 222, "Transferred"))

    async def stable_loader(_user_id: int):
        return initial

    with pytest.raises(PersonalStatsAccessChanged):
        await stats_service.build_personal_stats_payload(
            104,
            governor_id=999,
            account_loader=stable_loader,
            data_loader=lambda *_args, **_kwargs: pytest.fail("SQL must not be called"),
        )

    calls = 0

    async def changing_loader(_user_id: int):
        nonlocal calls
        calls += 1
        return initial if calls == 1 else changed

    with pytest.raises(PersonalStatsAccessChanged):
        await stats_service.build_personal_stats_payload(
            105,
            account_loader=changing_loader,
            data_loader=lambda *_args, **_kwargs: _dataset(date(2026, 7, 15)),
        )


@pytest.mark.asyncio
async def test_no_valid_accounts_is_explicit() -> None:
    async def account_loader(_user_id: int):
        return _summary()

    with pytest.raises(PersonalStatsNoAccounts):
        await stats_service.build_personal_stats_payload(106, account_loader=account_loader)


@pytest.mark.asyncio
async def test_identical_inflight_loads_are_deduplicated_and_cache_reuse_is_authorized() -> None:
    await stats_service.clear_personal_stats_cache()
    summary = _summary(("Main", 111, "Main"))
    data_calls = 0
    registry_calls = 0
    day = date(2026, 7, 14)

    async def account_loader(_user_id: int):
        nonlocal registry_calls
        registry_calls += 1
        return summary

    def data_loader(_governor_ids, *, history_days):
        nonlocal data_calls
        data_calls += 1
        time.sleep(0.05)
        return _dataset(date(2026, 7, 15), _complete_row(111, day))

    first, second = await asyncio.gather(
        stats_service.build_personal_stats_payload(
            107,
            period=StatsPeriod.YESTERDAY,
            account_loader=account_loader,
            data_loader=data_loader,
        ),
        stats_service.build_personal_stats_payload(
            107,
            period=StatsPeriod.YESTERDAY,
            account_loader=account_loader,
            data_loader=data_loader,
        ),
    )
    third = await stats_service.build_personal_stats_payload(
        107,
        period=StatsPeriod.YESTERDAY,
        expected_registry_fingerprint=first.registry_fingerprint,
        account_loader=account_loader,
        data_loader=data_loader,
    )

    assert data_calls == 1
    assert registry_calls == 6  # Before and after every load, including cache reuse.
    assert first.metrics.power_change.total == second.metrics.power_change.total
    assert third.scope_governor_ids == (111,)


@pytest.mark.asyncio
async def test_26_account_180_day_payload_assembly_stays_bounded() -> None:
    await stats_service.clear_personal_stats_cache()
    accounts = tuple(
        ("Main" if index == 1 else f"Farm{index}", index, f"Governor {index}")
        for index in range(1, 27)
    )
    summary = _summary(*accounts)
    anchor = date(2026, 7, 15)
    rows = tuple(
        _complete_row(
            governor_id,
            date.fromordinal(anchor.toordinal() - offset),
            value=governor_id + offset,
        )
        for governor_id in range(1, 27)
        for offset in range(179, -1, -1)
    )

    async def account_loader(_user_id: int):
        return summary

    def data_loader(_governor_ids, *, history_days):
        return _dataset(anchor, *rows, count=26)

    started = time.perf_counter()
    payload = await stats_service.build_personal_stats_payload(
        108,
        period=StatsPeriod.LAST_180_DAYS,
        all_linked=True,
        account_loader=account_loader,
        data_loader=data_loader,
    )
    elapsed = time.perf_counter() - started

    assert payload.state is StatsResultState.READY
    assert payload.coverage.expected_account_days == 4_680
    assert payload.coverage.stats_account_days == 4_680
    assert len(payload.metrics.rss_gathered.daily) == 180
    assert elapsed < 2.0
