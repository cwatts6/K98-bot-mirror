"""
tests/test_stats_service.py

Unit tests for stats_service.py focusing on:
- Process offload compatibility (module-level function imports)
- Graceful error handling
- Data normalization
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_fetch_proc_sync_is_importable():
    """
    CRITICAL: Verify _fetch_proc_sync is a module-level function that maintenance_worker.py can import.

    This test prevents regression of the nested function bug that caused:
    AttributeError: module 'stats_service' has no attribute '_run'
    """
    import stats_service

    # Verify function exists at module level
    assert hasattr(
        stats_service, "_fetch_proc_sync"
    ), "_fetch_proc_sync must be module-level for process offload"

    # Verify it's callable
    assert callable(stats_service._fetch_proc_sync), "_fetch_proc_sync must be callable"

    # Verify signature (3 params)
    import inspect

    sig = inspect.signature(stats_service._fetch_proc_sync)
    assert (
        len(sig.parameters) == 3
    ), "_fetch_proc_sync should accept (gov_ids, slices_csv, include_aggregate)"


def test_fetch_trendlines_sync_is_importable():
    """
    Verify _fetch_trendlines_sync is module-level and importable by maintenance_worker.py
    """
    import stats_service

    assert hasattr(
        stats_service, "_fetch_trendlines_sync"
    ), "_fetch_trendlines_sync must be module-level for process offload"

    assert callable(stats_service._fetch_trendlines_sync), "_fetch_trendlines_sync must be callable"

    import inspect

    sig = inspect.signature(stats_service._fetch_trendlines_sync)
    assert (
        len(sig.parameters) == 2
    ), "_fetch_trendlines_sync should accept (governor_ids, slice_key)"


@pytest.mark.asyncio
async def test_fetch_proc_handles_db_error_gracefully():
    """
    Verify _fetch_proc returns empty list on DB errors instead of raising.
    """
    from stats_service import _fetch_proc

    with patch("file_utils.get_conn_with_retries", side_effect=Exception("DB offline")):
        # Should NOT raise; should fall back gracefully
        try:
            result = await _fetch_proc([123], "wtd", True)
            # If we get here, function handled error gracefully
            assert isinstance(result, list), "Should return list on error"
        except Exception as e:
            # If it raises, that's a bug (we want graceful degradation)
            pytest.fail(f"_fetch_proc should handle DB errors gracefully, but raised: {e}")


@pytest.mark.asyncio
async def test_fetch_proc_normalizes_tuple_responses():
    """
    Verify _fetch_proc handles various response shapes from run_blocking_in_thread.
    """
    from stats_service import _fetch_proc

    # Mock result from run_blocking_in_thread (can return tuple with worker metadata)
    mock_result = [{"GovernorID": 123, "WindowKey": "wtd", "PowerEnd": 100000}]
    mock_worker_meta = {"elapsed": 0.5, "status": "ok"}

    # Patch at the source module (file_utils) since it's imported conditionally
    with patch("file_utils.run_blocking_in_thread", new_callable=AsyncMock) as mock_thread:
        # Simulate run_blocking_in_thread returning (result, metadata) tuple
        mock_thread.return_value = (mock_result, mock_worker_meta)

        result = await _fetch_proc([123], "wtd", True)

        # Verify the mock was called
        assert mock_thread.called, "run_blocking_in_thread should have been called"

        # Verify we extracted the result correctly
        assert result == mock_result, "Should extract first element of (result, metadata) tuple"


@pytest.mark.asyncio
async def test_fetch_trendlines_normalizes_responses():
    """
    Verify _fetch_trendlines handles various response shapes and always returns dict.
    """
    from stats_service import _fetch_trendlines

    # Mock raw DB result: list of tuples (series, date, value)
    mock_rows = [
        ("RSS", "2025-02-01", 1000000),
        ("RSS", "2025-02-02", 1500000),
        ("FORTS", "2025-02-01", 5),
        ("FORTS", "2025-02-02", 7),
    ]

    with patch("stats_service._fetch_trendlines_sync", return_value=mock_rows):
        result = await _fetch_trendlines([123], "wtd")

        # Verify structure
        assert isinstance(result, dict), "Should return dict of series"
        assert "RSS" in result, "Should have RSS series"
        assert "FORTS" in result, "Should have FORTS series"

        # Verify data
        assert len(result["RSS"]) == 2, "RSS should have 2 data points"
        assert result["RSS"][0] == ("2025-02-01", 1000000), "RSS data should match"


@pytest.mark.asyncio
async def test_fetch_proc_thread_fallback():
    """
    Verify _fetch_proc falls back to thread execution when run_maintenance_with_isolation is unavailable.
    """
    from stats_service import _fetch_proc

    # Mock _fetch_proc_sync to return test data
    mock_data = [{"GovernorID": 456, "WindowKey": "last_week"}]

    with patch("stats_service._fetch_proc_sync", return_value=mock_data):
        # Simulate file_utils not having run_maintenance_with_isolation
        # by making the import fail inside _fetch_proc
        import file_utils

        # Temporarily remove the attribute
        original_func = getattr(file_utils, "run_maintenance_with_isolation", None)
        if hasattr(file_utils, "run_maintenance_with_isolation"):
            delattr(file_utils, "run_maintenance_with_isolation")

        try:
            result = await _fetch_proc([456], "last_week", False)

            # Should fall back to asyncio.to_thread
            assert result == mock_data, "Thread fallback should work"
        finally:
            # Restore the original function if it existed
            if original_func is not None:
                file_utils.run_maintenance_with_isolation = original_func


@pytest.mark.asyncio
async def test_make_sparkline_runs_in_thread():
    """
    Verify matplotlib operations are offloaded to thread pool (not blocking event loop).
    """

    from stats_service import _make_sparkline

    # Mock the sync version
    with patch("stats_service._make_sparkline_sync") as mock_sync:
        mock_sync.return_value = io.BytesIO(b"fake_chart")

        points = [("2025-02-01", 1000), ("2025-02-02", 1500)]
        result = await _make_sparkline(points, "Test Chart", 1250.0)

        # Verify sync version was called
        assert mock_sync.called, "_make_sparkline_sync should be called"

        # Verify result is BytesIO
        assert isinstance(result, io.BytesIO), "Should return BytesIO buffer"


@pytest.mark.asyncio
async def test_make_sparkline_empty_points():
    """
    Verify _make_sparkline handles empty input gracefully.
    """
    from stats_service import _make_sparkline

    result = await _make_sparkline([], "Empty Chart", None)

    assert result is None, "Should return None for empty points"


@pytest.mark.asyncio
async def test_get_stats_payload_basic_flow():
    """
    Integration test: verify get_stats_payload calls _fetch_proc and _fetch_trendlines correctly.
    """
    from stats_service import get_stats_payload

    mock_proc_data = [
        {
            "WindowKey": "wtd",
            "Grouping": "PER",
            "GovernorID": 789,
            "PowerEnd": 50000000,
            "RSSGatheredEnd": 2000000,
        }
    ]

    mock_trend_rows = [
        ("RSS", "2025-02-03", 500000),
        ("FORTS", "2025-02-03", 3),
    ]

    with patch("stats_service._fetch_proc_sync", return_value=mock_proc_data):
        with patch("stats_service._fetch_trendlines_sync", return_value=mock_trend_rows):
            # Mock the freshness query
            with patch("file_utils.get_conn_with_retries") as mock_conn:
                mock_cursor = MagicMock()
                mock_cursor.fetchall.return_value = [("2025-02-03",)]
                mock_cursor.description = [("AsOfDate",)]
                mock_conn.return_value.cursor.return_value = mock_cursor

                payload = await get_stats_payload(
                    discord_id=999, governor_ids=[789], slice_key_or_csv="wtd"
                )

                # Verify payload structure
                assert "rows" in payload, "Payload should have rows"
                assert "trends" in payload, "Payload should have trends"
                assert "trend_avgs" in payload, "Payload should have trend_avgs"
                assert "freshness" in payload, "Payload should have freshness"

                # Verify data
                assert len(payload["rows"]) == 1, "Should have 1 row"
                assert payload["rows"][0]["GovernorID"] == 789


def test_csv_from_ids_utility():
    """
    Verify csv_from_ids helper produces correct format for SQL STRING_SPLIT.
    """
    from utils import csv_from_ids

    result = csv_from_ids([123, 456, 789])
    assert result == "123,456,789", "Should produce comma-separated string without spaces"

    # Edge case: single ID
    result_single = csv_from_ids([999])
    assert result_single == "999", "Should handle single ID"

    # Edge case: empty
    result_empty = csv_from_ids([])
    assert result_empty == "", "Should handle empty list"


# Append these tests to existing test_stats_service.py file


@pytest.mark.asyncio
async def test_fetch_proc_returns_export_fields():
    """
    Verify _fetch_proc returns new export-only fields from updated SQL view.
    """
    from stats_service import _fetch_proc

    mock_data = [
        {
            "GovernorID": 123,
            "WindowKey": "wtd",
            # Core fields
            "PowerEnd": 50000000,
            "PowerDelta": 1000000,
            # AOO fields
            "AOOJoinedEnd": 3,
            "AOOWonEnd": 2,
            # New export fields
            "T4_Kills": 50000,
            "T5_Kills": 30000,
            "T4T5_Kills": 80000,
            "HealedTroops": 100000,
            "RangedPoints": 200000,
            "HighestAcclaim": 50,
            "AutarchTimes": 2,
            # Deltas
            "T4_KillsDelta": 5000,
            "T5_KillsDelta": 3000,
            "AOOJoinedDelta": 1,
        }
    ]

    with patch("stats_service._fetch_proc_sync", return_value=mock_data):
        result = await _fetch_proc([123], "wtd", True)

        assert len(result) > 0, "Should return data"
        row = result[0]

        # Verify new fields present
        assert "T4_Kills" in row, "Should have T4_Kills field"
        assert "T5_Kills" in row, "Should have T5_Kills field"
        assert "HealedTroops" in row, "Should have HealedTroops field"
        assert "RangedPoints" in row, "Should have RangedPoints field"

        # Verify deltas present
        assert "T4_KillsDelta" in row, "Should have T4_KillsDelta field"
        assert "AOOJoinedDelta" in row, "Should have AOOJoinedDelta field"


@pytest.mark.asyncio
async def test_get_stats_payload_includes_export_fields():
    """
    Integration test: verify full payload includes export fields from updated SQL schema.
    """
    from stats_service import _cache, _inflight, get_stats_payload

    # Clear cache to ensure fresh data
    _cache.clear()
    _inflight.clear()

    mock_proc_data = [
        {
            "WindowKey": "wtd",
            "Grouping": "PER",
            "GovernorID": 789,
            "PowerEnd": 50000000,
            "RSSGatheredEnd": 2000000,
            # Core fields (used by /my_stats)
            "TroopPowerEnd": 40000000,
            "KillPointsEnd": 1000000,
            "DeadsEnd": 500000,
            "RSSAssistEnd": 1000000,
            "HelpsEnd": 5000,
            "FortsTotal": 10,
            "FortsLaunched": 5,
            "FortsJoined": 5,
            # AOO fields (used by /my_stats)
            "AOOJoinedEnd": 3,
            "AOOWonEnd": 2,
            "AOOAvgKillEnd": 1500000,
            "AOOAvgDeadEnd": 800000,
            "AOOAvgHealEnd": 1200000,
            # Export-only fields (new in updated schema)
            "T4_KillsEnd": 50000,
            "T5_KillsEnd": 30000,
            "T4T5_KillsEnd": 80000,
            "HealedTroopsEnd": 100000,
            "RangedPointsEnd": 200000,
            "HighestAcclaimEnd": 50,
            "AutarchTimesEnd": 2,
            # Deltas
            "T4_KillsDelta": 5000,
            "AOOJoinedDelta": 1,
        }
    ]

    # Mock _fetch_proc directly
    with patch("stats_service._fetch_proc", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_proc_data

        with patch("stats_service._fetch_trendlines", new_callable=AsyncMock) as mock_trends:
            mock_trends.return_value = {
                "RSS": [("2025-02-03", 500000)],
                "FORTS": [("2025-02-03", 3)],
                "AA_BUILD": [],
                "AA_TECH": [],
                "HELPS": [],
                "AA": [],
            }

            # Mock freshness with asyncio.to_thread
            async def mock_freshness_fn():
                return {"daily": "2025-02-03"}

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = {"daily": "2025-02-03"}

                payload = await get_stats_payload(
                    discord_id=999, governor_ids=[789], slice_key_or_csv="wtd"
                )

                # Verify mock was actually called
                assert mock_fetch.called, "_fetch_proc should have been called"

                # Verify payload structure
                assert "rows" in payload
                assert "trends" in payload
                assert "trend_avgs" in payload
                assert "freshness" in payload

                assert len(payload["rows"]) > 0, f"Expected rows but got: {payload}"

                row = payload["rows"][0]

                # Debug: print what we actually got
                print(f"\nActual row keys: {sorted(row.keys())}")
                print("Looking for: T4_KillsEnd")

                # Verify export fields are present in payload
                assert (
                    "T4_KillsEnd" in row
                ), f"Should have T4_KillsEnd field. Got keys: {sorted(row.keys())}"
                assert "T5_KillsEnd" in row, "Should have T5_KillsEnd field"
                assert "HealedTroopsEnd" in row, "Should have HealedTroopsEnd field"

                # Verify AOO fields (used by /my_stats) are present
                assert "AOOJoinedEnd" in row
                assert "AOOWonEnd" in row

                # Verify core fields still present
                assert row["GovernorID"] == 789
                assert row["PowerEnd"] == 50000000


def test_export_fields_do_not_break_my_stats_logic():
    """
    Unit test: verify _num() helper in embed_my_stats handles export fields gracefully.
    """
    from embed_my_stats import _num

    # Simulate row with export fields
    row = {
        "PowerEnd": 50000000,
        "T4_Kills": None,  # NULL
        "T5_Kills": 30000,
        "HighestAcclaim": 50,
        # Missing field: RangedPoints
    }

    # Should handle all gracefully
    assert _num(row.get("PowerEnd")) == 50000000
    assert _num(row.get("T4_Kills")) == 0  # NULL → 0
    assert _num(row.get("T5_Kills")) == 30000
    assert _num(row.get("RangedPoints")) == 0  # Missing → 0


@pytest.mark.asyncio
async def test_my_stats_unchanged_after_schema_update():
    """
    End-to-end simulation: verify /my_stats command flow is unchanged.

    This test simulates the full command flow to ensure schema changes don't break it.
    """
    from unittest.mock import patch

    from embed_my_stats import build_embeds
    from stats_service import get_stats_payload

    # Mock DB to return data with export fields
    mock_proc_data = [
        {
            "WindowKey": "wtd",
            "Grouping": "PER",
            "GovernorID": 123456,
            "GovernorName": "TestPlayer",
            "Alliance": "K98",
            # Core fields used by /my_stats
            "PowerEnd": 50000000,
            "PowerDelta": 1000000,
            "TroopPowerEnd": 40000000,
            "TroopPowerDelta": 800000,
            "RSSGatheredEnd": 10000000000,
            "RSSGatheredDelta": 500000000,
            "RSSAssistEnd": 5000000000,
            "RSSAssistDelta": 250000000,
            "HelpsEnd": 10000,
            "HelpsDelta": 500,
            "FortsTotal": 15,
            "FortsLaunched": 8,
            "FortsJoined": 7,
            "AOOJoinedEnd": 3,
            "AOOWonEnd": 2,
            "AOOAvgKillEnd": 1500000,
            "AOOAvgDeadEnd": 800000,
            "AOOAvgHealEnd": 1200000,
            # New export fields
            "T4_Kills": 50000,
            "T5_Kills": 30000,
            "T4T5_Kills": 80000,
            "HealedTroops": 100000,
            "RangedPoints": 200000,
            "HighestAcclaim": 50,
            "AutarchTimes": 2,
            "T4_KillsDelta": 5000,
            "T5_KillsDelta": 3000,
            "AOOJoinedDelta": 1,
        }
    ]

    with patch("stats_service._fetch_proc_sync", return_value=mock_proc_data):
        with patch("stats_service._fetch_trendlines_sync", return_value=[]):
            with patch("file_utils.get_conn_with_retries") as mock_conn:
                mock_cursor = MagicMock()
                mock_cursor.fetchall.return_value = [("2026-02-05",)]
                mock_cursor.description = [("AsOfDate",)]
                mock_conn.return_value.cursor.return_value = mock_cursor

                # Simulate full command flow
                payload = await get_stats_payload(
                    discord_id=999, governor_ids=[123456], slice_key_or_csv="wtd"
                )

                embeds, files = await build_embeds(
                    "wtd", "TestPlayer", payload, governor_id_for_choice=123456
                )

                # Verify success
                assert len(embeds) >= 1, "/my_stats should work after schema update"

                # Verify core fields displayed
                field_names = [f.name for f in embeds[0].fields]
                assert "Power" in field_names
                assert "Troop Power" in field_names
                assert "RSS Gathered" in field_names
                assert "Forts" in field_names
                assert any("Ark" in name for name in field_names)

                # Verify export fields NOT displayed
                field_names_lower = [n.lower() for n in field_names]
                assert not any("t4" in n and "kill" in n for n in field_names_lower)
                assert not any("ranged" in n for n in field_names_lower)
                assert not any("acclaim" in n for n in field_names_lower)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
