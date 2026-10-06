from __future__ import annotations

import pandas as pd
import pytest

from player_self_service.account_data_export_contract import (
    ALLOWED_HISTORY_DAYS,
    AccountDataOutputKind,
    filter_history_window,
    spreadsheet_safe_text,
    validate_history_days,
    validate_output_kind,
)


@pytest.mark.parametrize("days", ALLOWED_HISTORY_DAYS)
def test_history_window_uses_exact_inclusive_calendar_span(days: int) -> None:
    dates = pd.date_range("2025-01-01", periods=400, freq="D")
    frame = pd.DataFrame(
        {"GovernorID": [1] * len(dates), "AsOfDate": dates, "Power": range(len(dates))}
    )

    result = filter_history_window(frame, days)

    assert result.row_count == days
    assert result.window_end == dates[-1].date()
    assert result.window_start == (dates[-1] - pd.Timedelta(days=days - 1)).date()
    assert result.written_start == result.window_start
    assert result.written_end == result.window_end


def test_history_window_filters_all_governors_before_counts_and_preserves_gaps() -> None:
    frame = pd.DataFrame(
        {
            "GovernorID": [2, 1, 1, 2, 1],
            "AsOfDate": ["2026-07-10", "bad", "2026-07-16", "2026-01-01", "2026-07-01"],
        }
    )

    result = filter_history_window(frame, 30)

    assert result.invalid_date_rows == 1
    assert list(result.frame["GovernorID"]) == [1, 1, 2]
    assert [item.date().isoformat() for item in result.frame["AsOfDate"]] == [
        "2026-07-16",
        "2026-07-01",
        "2026-07-10",
    ]
    assert result.row_count == 3
    assert result.written_start.isoformat() == "2026-07-01"


def test_history_window_rejects_duplicate_source_grain() -> None:
    frame = pd.DataFrame({"GovernorID": [1, 1], "AsOfDate": ["2026-07-16", "2026-07-16"]})

    with pytest.raises(ValueError, match="duplicate GovernorID/source-date"):
        filter_history_window(frame, 90)


def test_output_kind_and_days_are_strict() -> None:
    assert validate_output_kind("full_workbook") is AccountDataOutputKind.FULL_WORKBOOK
    assert validate_history_days(AccountDataOutputKind.FULL_WORKBOOK, None) == 90
    assert validate_history_days(AccountDataOutputKind.CURRENT_SNAPSHOT, 123) is None
    with pytest.raises(ValueError, match="Unsupported Account Data"):
        validate_output_kind("GoogleSheets")
    with pytest.raises(ValueError, match="30, 60, 90, 180, 360"):
        validate_history_days(AccountDataOutputKind.RAW_HISTORY, 31)


def test_spreadsheet_safety_protects_text_without_touching_numeric_negatives() -> None:
    assert spreadsheet_safe_text("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert spreadsheet_safe_text("  -formula") == "'  -formula"
    assert spreadsheet_safe_text("@name\nnext") == "'@name next"
    assert spreadsheet_safe_text(-42) == -42
