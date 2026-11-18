"""
tests/test_stats_exporter_csv.py

Unit tests for CSV export functionality.
"""

import csv
from datetime import datetime
import os
import tempfile

import pandas as pd
import pytest

from stats.dal.stats_export_dal import EXPORT_COLUMNS
from stats_exporter_csv import build_user_stats_csv


@pytest.fixture
def sample_daily_data():
    """Generate sample daily stats data."""
    dates = pd.date_range(end=datetime.now(), periods=90, freq="D")
    data = []

    for i, date in enumerate(dates):
        data.append(
            {
                "GovernorID": 123456,
                "GovernorName": "TestPlayer",
                "Alliance": "K98",
                "AsOfDate": date,
                "Power": 50000000 + (i * 100000),
                "PowerDelta": 100000,
                "TroopPower": 40000000 + (i * 80000),
                "TroopPowerDelta": 80000,
                "KillPoints": 1000000 + (i * 10000),
                "KillPointsDelta": 10000,
                "Deads": 500000 + (i * 5000),
                "DeadsDelta": 5000,
                "RSS_Gathered": 10000000000 + (i * 100000000),
                "RSS_GatheredDelta": 100000000,
                "RSSAssist": 5000000000 + (i * 50000000),
                "RSSAssistDelta": 50000000,
                "Helps": 10000 + (i * 100),
                "HelpsDelta": 100,
                "BuildingMinutes": 500,
                "TechDonations": 200,
                "FortsTotal": 10 + (i // 7),
                "FortsLaunched": 5 + (i // 7),
                "FortsJoined": 5 + (i // 7),
                "AOOJoined": min(i // 7, 10),
                "AOOJoinedDelta": 1 if i % 7 == 0 else 0,
                "AOOWon": min(i // 14, 5),
                "AOOWonDelta": 1 if i % 14 == 0 else 0,
                "AOOAvgKill": 1000000 + (i * 1000),
                "AOOAvgKillDelta": 1000,
                "AOOAvgDead": 500000 + (i * 500),
                "AOOAvgDeadDelta": 500,
                "AOOAvgHeal": 800000 + (i * 800),
                "AOOAvgHealDelta": 800,
                "T4_Kills": 50000 + (i * 500),
                "T4_KillsDelta": 500,
                "T5_Kills": 30000 + (i * 300),
                "T5_KillsDelta": 300,
                "T4T5_Kills": 80000 + (i * 800),
                "T4T5_KillsDelta": 800,
                "HealedTroops": 100000 + (i * 1000),
                "HealedTroopsDelta": 1000,
                "RangedPoints": 200000 + (i * 2000),
                "RangedPointsDelta": 2000,
                "HighestAcclaim": 50,
                "HighestAcclaimDelta": 0,
                "AutarchTimes": 2,
                "AutarchTimesDelta": 0,
            }
        )

    return pd.DataFrame(data)


def test_build_csv_basic(sample_daily_data):
    """Test basic CSV generation."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Should not raise
        build_user_stats_csv(sample_daily_data, None, out_path=tmp_path, days_for_daily_table=90)

        # Verify file exists and has content
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0

        # Verify can be read back
        with open(tmp_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 90
        assert reader.fieldnames == list(EXPORT_COLUMNS)
        assert "GovernorID" in rows[0]
        assert "Power" in rows[0]
        assert "AOOJoined" in rows[0]
        assert "T4_Kills" in rows[0]

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_csv_date_range_filter(sample_daily_data):
    """Test CSV filters to requested date range."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Request only 30 days
        build_user_stats_csv(sample_daily_data, None, out_path=tmp_path, days_for_daily_table=30)

        with open(tmp_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 30
        assert (
            rows[0]["AsOfDate"]
            == pd.Timestamp(sample_daily_data["AsOfDate"].max()).date().isoformat()
        )

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_csv_deprecated_columns_removed(sample_daily_data):
    """Verify deprecated columns are not in CSV output."""
    # Add deprecated columns to source
    df = sample_daily_data.copy()
    df["TechPower"] = 1000000
    df["TechPowerDelta"] = 1000

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        build_user_stats_csv(df, None, out_path=tmp_path)

        with open(tmp_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames

        # Verify deprecated columns removed
        assert "TechPower" not in header
        assert "TechPowerDelta" not in header

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_csv_handles_missing_columns(sample_daily_data):
    """Verify CSV export handles missing optional columns gracefully."""
    # Remove some AOO columns
    df = sample_daily_data.copy()
    df = df.drop(columns=["AOOAvgHeal", "AOOAvgHealDelta"], errors="ignore")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Should not raise
        build_user_stats_csv(df, None, out_path=tmp_path)

        with open(tmp_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Missing columns should be empty strings
        assert "AOOAvgHeal" in rows[0]
        assert rows[0]["AOOAvgHeal"] == ""

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_csv_formula_safety_order_and_numeric_negatives(sample_daily_data):
    frame = sample_daily_data.iloc[:2].copy()
    frame.loc[frame.index[0], "GovernorName"] = '=HYPERLINK("bad")'
    frame.loc[frame.index[1], "Alliance"] = "+unsafe"
    frame["PowerDelta"] = -5

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        build_user_stats_csv(frame, None, out_path=tmp_path, days_for_daily_table=30)
        with open(tmp_path, encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        assert rows[1]["GovernorName"].startswith("'")
        assert rows[0]["Alliance"] == "'+unsafe"
        assert all(row["PowerDelta"] == "-5" for row in rows)
        assert [row["AsOfDate"] for row in rows] == sorted(
            (row["AsOfDate"] for row in rows), reverse=True
        )
    finally:
        os.unlink(tmp_path)


def test_csv_writes_nan_and_infinity_as_empty(sample_daily_data):
    frame = sample_daily_data.iloc[:1].copy()
    frame.loc[frame.index[0], "Power"] = float("nan")
    frame["PowerDelta"] = frame["PowerDelta"].astype(float)
    frame.loc[frame.index[0], "PowerDelta"] = float("inf")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        build_user_stats_csv(frame, None, out_path=tmp_path)
        with open(tmp_path, encoding="utf-8") as handle:
            row = next(csv.DictReader(handle))
        assert row["Power"] == ""
        assert row["PowerDelta"] == ""
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
