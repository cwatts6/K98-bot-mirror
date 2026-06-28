from datetime import UTC, datetime

import pandas as pd
import pytest

from services.fallback_import_schema import (
    CANONICAL_COLUMNS,
    FULL_FALLBACK_SNAPSHOT,
    INTERIM_AUTO_PARTIAL_SNAPSHOT,
    normalize_fallback_dataframe,
    prepare_fallback_csv_dataframe,
)


def _full_row(**overrides):
    row = {
        "Governor ID": 123,
        "Name": "Alice",
        "Power": 1000,
        "Alliance": "K98",
        "T1-Kills": 1,
        "T2-Kills": 2,
        "T3-Kills": 3,
        "T4-Kills": 4,
        "T5-Kills": 5,
        "Total Kill Points": 999,
        "Dead Troops": 10,
        "Healed Troops": 20,
        "Rss Assistance": 30,
        "Alliance Helps": 40,
        "Rss Gathered": 50,
        "City Hall": 25,
        "Troops Power": 60,
        "Tech Power": 70,
        "Building Power": 80,
        "Commander Power": 90,
        "Civilization": "Britain",
        "Autarch Times": 2,
        "Ranged Points": 77,
        "KvK Played": 3,
        "Most KvK Kill": 100,
        "Most KvK Dead": 200,
        "Most KvK Heal": 300,
        "Acclaim": 400,
        "Highest Acclaim": 500,
        "AOO Joined": 6,
        "AOO Won": 7,
        "AOO Avg Kill": 8,
        "AOO Avg Dead": 9,
        "AOO Avg Heal": 10,
        "Credit": 88.5,
    }
    row.update(overrides)
    return row


def test_conduct_score_maps_to_canonical_credit():
    row = _full_row(**{"Conduct Score": 91.25})
    row.pop("Credit")

    result = normalize_fallback_dataframe(
        pd.DataFrame([row]),
        generated_at_utc=datetime(2026, 6, 25, 8, 14, tzinfo=UTC),
    )

    assert result.metadata.source_type == FULL_FALLBACK_SNAPSHOT
    assert result.metadata.score_header == "Conduct Score"
    assert list(result.dataframe.columns) == CANONICAL_COLUMNS
    assert result.dataframe.loc[0, "Credit"] == pytest.approx(91.25)


def test_credit_header_remains_supported():
    result = normalize_fallback_dataframe(pd.DataFrame([_full_row()]))

    assert result.metadata.source_type == FULL_FALLBACK_SNAPSHOT
    assert result.metadata.score_header == "Credit"
    assert result.dataframe.loc[0, "Credit"] == pytest.approx(88.5)


def test_conflicting_credit_and_conduct_score_fails():
    row = _full_row(**{"Conduct Score": 12.0})

    with pytest.raises(ValueError, match="conflicting"):
        normalize_fallback_dataframe(pd.DataFrame([row]))


def test_duplicate_credit_headers_after_normalization_fail():
    columns = list(_full_row().keys()) + [" credit "]
    values = list(_full_row().values()) + [88.5]

    with pytest.raises(ValueError, match="Duplicate fallback import column"):
        normalize_fallback_dataframe(pd.DataFrame([values], columns=columns))


def test_full_snapshot_without_score_gets_blank_credit():
    row = _full_row()
    row.pop("Credit")

    result = normalize_fallback_dataframe(pd.DataFrame([row]))

    assert result.metadata.source_type == FULL_FALLBACK_SNAPSHOT
    assert pd.isna(result.dataframe.loc[0, "Credit"])


def test_partial_snapshot_overlays_present_columns_and_preserves_absent_fields():
    latest = pd.DataFrame(
        [
            _full_row(
                **{
                    "Governor ID": 123,
                    "Name": "Old Alice",
                    "Power": 1000,
                    "Rss Assistance": 30,
                    "Troops Power": 60,
                    "Credit": 88.5,
                }
            ),
            _full_row(
                **{
                    "Governor ID": 456,
                    "Name": "Bob",
                    "Power": 2000,
                    "Rss Assistance": 300,
                    "Troops Power": 600,
                    "Credit": 77.0,
                }
            ),
        ]
    )
    partial = pd.DataFrame(
        [
            {
                "Governor ID": 123,
                "Name": "Alice",
                "Power": 1500,
                "Alliance": "K98",
                "T1-Kills": 10,
                "T2-Kills": 20,
                "T3-Kills": 30,
                "T4-Kills": 40,
                "T5-Kills": 50,
                "Total Kill Points": 1001,
                "Dead Troops": 11,
                "Healed Troops": 21,
                "City Hall": 25,
                "Civilization": "Rome",
                "Autarch Times": 3,
                "Ranged Points": 78,
                "KvK Played": 4,
                "Most KvK Kill": 101,
                "Most KvK Dead": 201,
                "Most KvK Heal": 301,
                "Acclaim": 401,
                "Highest Acclaim": 501,
                "AOO Joined": 7,
                "AOO Won": 8,
                "AOO Avg Kill": 9,
                "AOO Avg Dead": 10,
                "AOO Avg Heal": 11,
            }
        ]
    )

    result = normalize_fallback_dataframe(partial, latest_rows=latest)
    rows = result.dataframe.set_index("Governor ID")

    assert result.metadata.source_type == INTERIM_AUTO_PARTIAL_SNAPSHOT
    assert rows.loc[123, "Power"] == 1500
    assert rows.loc[123, "Rss Assistance"] == 30
    assert rows.loc[123, "Troops Power"] == 60
    assert rows.loc[123, "Credit"] == pytest.approx(88.5)
    assert rows.loc[456, "Power"] == 2000


def test_prepare_fallback_csv_dataframe_formats_integral_float_values_for_bulk_insert():
    result = normalize_fallback_dataframe(pd.DataFrame([_full_row()]))
    df = result.dataframe.copy()
    df.loc[0, "Governor ID"] = 123.0
    df.loc[0, "Power"] = 1500.0
    df.loc[0, "Credit"] = 88.50

    csv_df = prepare_fallback_csv_dataframe(df)

    assert csv_df.loc[0, "Governor ID"] == "123"
    assert csv_df.loc[0, "Power"] == "1500"
    assert csv_df.loc[0, "Credit"] == "88.5"


def test_prepare_fallback_csv_dataframe_rejects_fractional_integer_values():
    result = normalize_fallback_dataframe(pd.DataFrame([_full_row()]))
    df = result.dataframe.copy()
    df["Power"] = df["Power"].astype("object")
    df.loc[0, "Power"] = "1500.5"

    with pytest.raises(ValueError, match="Non-integer value for Power"):
        prepare_fallback_csv_dataframe(df)
