# tests/test_stats_export.py
"""Unit tests for stats export functionality."""

from datetime import datetime
import os
import tempfile

import pandas as pd
import pytest

from stats_exporter import _calc_period, _clean_text, _safe_sheet_name, build_user_stats_excel


@pytest.fixture
def sample_daily_data():
    """Generate sample daily stats data matching vDaily_PlayerExport schema."""
    dates = pd.date_range(end=datetime.now(), periods=90, freq="D")
    data = []

    for i, date in enumerate(dates):
        data.append(
            {
                "GovernorID": 123456,
                "GovernorName": "TestPlayer",
                "Alliance": "K98",
                "AsOfDate": date,
                # Core metrics
                "Power": 50000000 + (i * 100000),
                "PowerDelta": 100000,
                "TroopPower": 40000000 + (i * 80000),
                "TroopPowerDelta": 80000,
                "KillPoints": 1000000 + (i * 10000),
                "KillPointsDelta": 10000,
                "Deads": 500000 + (i * 5000),
                "DeadsDelta": 5000,
                # Activity
                "RSS_Gathered": 10000000000 + (i * 100000000),
                "RSS_GatheredDelta": 100000000,
                "RSSAssist": 5000000000 + (i * 50000000),
                "RSSAssistDelta": 50000000,
                "Helps": 10000 + (i * 100),
                "HelpsDelta": 100,
                "BuildingMinutes": 500,
                "TechDonations": 200,
                # Forts
                "FortsTotal": 10 + (i // 7),  # Increment weekly
                "FortsLaunched": 5 + (i // 7),
                "FortsJoined": 5 + (i // 7),
                # AOO
                "AOOJoined": min(i // 7, 10),  # Max 10 events
                "AOOJoinedDelta": 1 if i % 7 == 0 else 0,
                "AOOWon": min(i // 14, 5),  # Max 5 wins
                "AOOWonDelta": 1 if i % 14 == 0 else 0,
                "AOOAvgKill": 1000000 + (i * 1000),
                "AOOAvgKillDelta": 1000,
                "AOOAvgDead": 500000 + (i * 500),
                "AOOAvgDeadDelta": 500,
                "AOOAvgHeal": 800000 + (i * 800),
                "AOOAvgHealDelta": 800,
                # Detailed metrics
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


def test_calc_period_basic(sample_daily_data):
    """Test period calculation for standard metrics."""
    df = sample_daily_data
    end_date = pd.Timestamp(df["AsOfDate"].max())
    start_date = end_date - pd.Timedelta(days=30)

    result = _calc_period(df, start_date, end_date)

    # Verify snapshots are from end of period
    assert result["PowerEnd"] > 0
    assert result["TroopPowerEnd"] > 0

    # Verify deltas are sums
    assert result["PowerDelta"] == 100000 * 31  # 31 days
    assert result["KillPointsDelta"] == 10000 * 31


def test_calc_period_aoo_metrics(sample_daily_data):
    """Test AOO metric calculation."""
    df = sample_daily_data
    end_date = pd.Timestamp(df["AsOfDate"].max())
    start_date = end_date - pd.Timedelta(days=30)

    result = _calc_period(df, start_date, end_date)

    # AOO metrics should be snapshots (cumulative)
    assert "AOOJoinedEnd" in result
    assert "AOOWonEnd" in result
    assert result["AOOJoinedEnd"] >= 0
    assert result["AOOWonEnd"] >= 0


def test_calc_period_detailed_kills(sample_daily_data):
    """Test detailed kill metric calculation."""
    df = sample_daily_data
    end_date = pd.Timestamp(df["AsOfDate"].max())
    start_date = end_date - pd.Timedelta(days=7)

    result = _calc_period(df, start_date, end_date)

    # Verify detailed metrics present
    assert "T4_KillsEnd" in result
    assert "T5_KillsEnd" in result
    assert "T4T5_KillsEnd" in result
    assert "HealedTroopsEnd" in result

    # Verify deltas
    assert result["T4_KillsDelta"] == 500 * 8  # 8 days
    assert result["T5_KillsDelta"] == 300 * 8


def test_clean_text():
    """Test text cleaning function."""
    assert _clean_text("  Test  Player  ") == "Test Player"
    assert _clean_text(None) == ""
    assert _clean_text("Test\nPlayer") == "Test Player"


def test_safe_sheet_name():
    """Test Excel sheet name sanitization."""
    # Test forbidden characters
    assert "[" not in _safe_sheet_name("Test[1]", "fallback")
    assert ":" not in _safe_sheet_name("Test:Player", "fallback")

    # Test length limit
    long_name = "A" * 50
    result = _safe_sheet_name(long_name, "fallback", max_len=31)
    assert len(result) <= 31

    # Test fallback
    result = _safe_sheet_name("", "MyFallback")
    assert result == "MyFallback"


def test_build_excel_basic(sample_daily_data):
    """Test basic Excel generation."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Should not raise
        build_user_stats_excel(sample_daily_data, None, out_path=tmp_path)

        # Verify file exists and has content
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0

        # Verify can be read back
        df_test = pd.read_excel(tmp_path, sheet_name="ALL_DAILY")
        assert not df_test.empty
        assert "GovernorID" in df_test.columns
        assert "AOOJoined" in df_test.columns
        assert "T4_Kills" in df_test.columns

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_build_excel_multiple_governors(sample_daily_data):
    """Test Excel with multiple governors."""
    # Add second governor
    df2 = sample_daily_data.copy()
    df2["GovernorID"] = 789012
    df2["GovernorName"] = "Player2"

    combined = pd.concat([sample_daily_data, df2], ignore_index=True)

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        build_user_stats_excel(combined, None, out_path=tmp_path)

        # Verify both governors present
        df_test = pd.read_excel(tmp_path, sheet_name="ALL_DAILY")
        assert 123456 in df_test["GovernorID"].values
        assert 789012 in df_test["GovernorID"].values

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_deprecated_columns_removed(sample_daily_data):
    """Verify deprecated columns are not in output."""
    # Add deprecated columns to source
    df = sample_daily_data.copy()
    df["TechPower"] = 1000000
    df["TechPowerDelta"] = 1000

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        build_user_stats_excel(df, None, out_path=tmp_path)

        df_test = pd.read_excel(tmp_path, sheet_name="ALL_DAILY")

        # Verify deprecated columns removed
        assert "TechPower" not in df_test.columns
        assert "TechPowerDelta" not in df_test.columns

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def test_no_dkp_in_export():
    """Verify DKP/targets removed from export per requirements."""
    # This test verifies the signature and that targets param is ignored
    df = pd.DataFrame(
        {
            "GovernorID": [123],
            "GovernorName": ["Test"],
            "Alliance": ["K98"],
            "AsOfDate": [datetime.now()],
            "Power": [50000000],
            "PowerDelta": [0],
        }
    )

    # Fake targets dataframe (should be ignored)
    df_targets = pd.DataFrame(
        {
            "GovernorID": [123],
            "DKP_TARGET": [100],
            "DKP_SCORE": [80],
        }
    )

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Targets should be ignored (set to None internally)
        build_user_stats_excel(df, df_targets, out_path=tmp_path)

        # Verify no DKP columns in output
        df_test = pd.read_excel(tmp_path, sheet_name="ALL_DAILY")
        assert "DKP_TARGET" not in df_test.columns
        assert "DKP_SCORE" not in df_test.columns

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
