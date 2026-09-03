from __future__ import annotations

from datetime import date
from decimal import Decimal
import os
from pathlib import Path

import pytest

from leadership_player_review import dal
from leadership_player_review.last_active import (
    LastActiveObservation,
    classify_last_active,
    derive_last_active,
)


@pytest.mark.parametrize(
    "source_code",
    (
        "POWER",
        "HEALED",
        "RSS_GATHERED",
        "RSS_ASSISTED",
        "HELPS",
        "TECH_DONATIONS",
        "BUILDING_MINUTES",
        "FORT_RALLIES",
    ),
)
def test_each_eligible_source_can_establish_last_active(source_code: str) -> None:
    previous_values = () if source_code == "FORT_RALLIES" else ((source_code, Decimal(10)),)
    current_values = () if source_code == "FORT_RALLIES" else ((source_code, Decimal(11)),)
    current_intervals = (
        frozenset({"FORT_RALLIES"}) if source_code == "FORT_RALLIES" else frozenset()
    )
    result = derive_last_active(
        (
            LastActiveObservation(100, date(2026, 7, 19), previous_values),
            LastActiveObservation(
                101,
                date(2026, 7, 20),
                current_values,
                positive_interval_sources=current_intervals,
            ),
        )
    )

    assert result == (date(2026, 7, 20), source_code, 101)


@pytest.mark.parametrize(
    ("previous", "current"),
    (
        (Decimal(10), Decimal(10)),
        (Decimal(10), Decimal(9)),
        (None, Decimal(10)),
        (Decimal(10), None),
    ),
)
def test_zero_reset_and_missing_source_values_do_not_qualify(previous, current) -> None:
    result = derive_last_active(
        (
            LastActiveObservation(100, date(2026, 7, 19), (("HELPS", previous),)),
            LastActiveObservation(101, date(2026, 7, 20), (("HELPS", current),)),
        )
    )

    assert result is None


def test_missing_governor_scan_is_not_an_implicit_zero_on_return() -> None:
    result = derive_last_active(
        (
            LastActiveObservation(100, date(2026, 7, 18), (("POWER", Decimal(100)),)),
            # Scan 101 is absent because the Governor ID was not observed.
            LastActiveObservation(102, date(2026, 7, 20), (("POWER", Decimal(100)),)),
        )
    )

    assert result is None


def test_latest_qualifying_complete_scan_wins_once_for_multiple_metrics() -> None:
    result = derive_last_active(
        (
            LastActiveObservation(
                100,
                date(2026, 7, 18),
                (("POWER", Decimal(100)), ("HELPS", Decimal(10))),
            ),
            LastActiveObservation(
                101,
                date(2026, 7, 19),
                (("POWER", Decimal(101)), ("HELPS", Decimal(11))),
            ),
            LastActiveObservation(
                102,
                date(2026, 7, 20),
                (("POWER", Decimal(101)), ("HELPS", Decimal(12))),
            ),
        )
    )

    assert result == (date(2026, 7, 20), "HELPS", 102)


def test_authoritative_scan_date_orders_before_scan_order() -> None:
    result = derive_last_active(
        (
            LastActiveObservation(20, date(2026, 7, 19), (("POWER", Decimal(100)),)),
            LastActiveObservation(10, date(2026, 7, 20), (("POWER", Decimal(101)),)),
        )
    )

    assert result == (date(2026, 7, 20), "POWER", 10)


def test_duplicate_selected_scan_orders_are_rejected() -> None:
    observations = (
        LastActiveObservation(100, date(2026, 7, 19), ()),
        LastActiveObservation(100, date(2026, 7, 20), ()),
    )

    with pytest.raises(ValueError, match="unique selected scan orders"):
        derive_last_active(observations)


def test_exactly_30_utc_days_is_active_and_31_is_inactive() -> None:
    today = date(2026, 7, 21)

    assert classify_last_active(date(2026, 6, 21), today) == "ACTIVE"
    assert classify_last_active(date(2026, 6, 20), today) == "INACTIVE"
    assert classify_last_active(None, today) == "NOT_RECORDED"


def test_last_active_dal_maps_and_validates_the_compact_result(monkeypatch) -> None:
    row = {
        "GovernorID": 123,
        "EffectiveUtcDate": date(2026, 7, 21),
        "HistoryStartDate": date(2024, 8, 2),
        "HistoryEndDate": date(2026, 7, 21),
        "LastActiveDate": date(2026, 7, 20),
        "ActivityState": "ACTIVE",
        "QualifyingSourceCode": "RSS_ASSISTED",
        "QualifyingScanOrder": 321,
        "ComparedCompleteScanCount": 190,
        "HistoryDays": 720,
    }

    class _Cursor:
        def __init__(self) -> None:
            self.timeout = None
            self.description = [(key,) for key in row]

        def execute(self, *_args, **_kwargs) -> None:
            return None

        def fetchall(self):
            return [tuple(row.values())]

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def cursor(self):
            return _Cursor()

    monkeypatch.setattr(dal, "get_conn_with_retries", _Connection)
    diagnostics: dict[str, object] = {}

    result = dal.fetch_last_active(123, diagnostics=diagnostics)

    assert result.last_active_date == date(2026, 7, 20)
    assert result.activity_state == "ACTIVE"
    assert result.qualifying_source_code == "RSS_ASSISTED"
    assert diagnostics["result_rows"] == 1
    assert diagnostics["approximate_result_bytes"] > 0

    row["GovernorID"] = 456
    with pytest.raises(ValueError, match="mismatched Governor ID"):
        dal.fetch_last_active(123)


def test_sql_contract_contains_all_sources_and_no_permanent_index() -> None:
    sql_repo_env = os.environ.get("K98_SQL_REPO")
    sql_repo = Path(sql_repo_env) if sql_repo_env else Path(r"C:\K98-bot-SQL-Server")
    sql_path = sql_repo / "sql_schema" / "dbo.usp_GetLeadershipPlayerLastActive.StoredProcedure.sql"
    if not sql_path.exists():
        if not sql_repo_env:
            pytest.skip(
                "SQL contract tests require the external SQL repository; "
                f"set K98_SQL_REPO to enable them. Missing expected file: {sql_path}"
            )
        if any(
            os.environ.get(name) for name in ("CI", "GITHUB_ACTIONS", "BUILD_BUILDID", "TF_BUILD")
        ):
            pytest.fail(f"SQL repo file not available in CI: {sql_path}")
        pytest.skip(f"SQL repo file not available: {sql_path}")
    source = sql_path.read_text(encoding="utf-8-sig")

    for token in (
        "source.Power",
        "source.HealedTroops",
        "source.RSS_Gathered",
        "source.RSSAssistance",
        "source.Helps",
        "activity_row.TechDonationTotal",
        "activity_row.BuildingTotal",
        "dbo.RallyDailySnapshotHeader",
    ):
        assert token in source
    assert "CREATE INDEX" not in source
    assert "ALTER TABLE" not in source
