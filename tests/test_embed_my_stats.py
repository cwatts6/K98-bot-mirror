"""
tests/test_embed_my_stats.py

Unit tests for embed_my_stats.py focusing on:
- Async chart generation
- Embed construction
- View interaction safety
"""

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_build_embeds_basic():
    """
    Verify basic embed construction with minimal data.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "wtd",
                "Grouping": "ALL",
                "Alliance": "K98",
                "PowerEnd": 100000000,
                "PowerDelta": 1000000,
                "TroopPowerEnd": 80000000,
                "TroopPowerDelta": 500000,
                "RSSGatheredEnd": 5000000,
                "RSSGatheredDelta": 1000000,
                "RSSAssistEnd": 200000,
                "RSSAssistDelta": 50000,
                "HelpsEnd": 500,
                "HelpsDelta": 100,
                "FortsTotal": 10,
                "FortsLaunched": 5,
                "FortsJoined": 5,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    embeds, files = await build_embeds("wtd", "ALL", data)

    assert len(embeds) >= 1, "Should have at least one embed"
    assert embeds[0].title.startswith("This Week"), "Title should match slice"
    assert any("Power" in f.name for f in embeds[0].fields), "Should have Power field"


@pytest.mark.asyncio
async def test_build_embeds_with_charts():
    """
    Verify chart generation is called asynchronously.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "last_week",
                "Grouping": "PER",
                "GovernorID": "123",
                "Alliance": "K98",
                "PowerEnd": 50000000,
                "PowerDelta": 0,
                "TroopPowerEnd": 40000000,
                "TroopPowerDelta": 0,
                "RSSGatheredEnd": 2000000,
                "RSSGatheredDelta": 500000,
                "RSSAssistEnd": 100000,
                "RSSAssistDelta": 20000,
                "HelpsEnd": 200,
                "HelpsDelta": 50,
                "FortsTotal": 5,
                "FortsLaunched": 3,
                "FortsJoined": 2,
            }
        ],
        "trends": {
            "RSS": [("2025-02-01", 100000), ("2025-02-02", 150000)],
            "FORTS": [("2025-02-01", 2), ("2025-02-02", 3)],
        },
        "trend_avgs": {
            "RSS": 125000.0,
            "FORTS": 2.5,
        },
        "freshness": {},
    }

    # Mock _make_sparkline to track calls
    with patch("embed_my_stats._make_sparkline", new_callable=AsyncMock) as mock_sparkline:
        mock_sparkline.return_value = io.BytesIO(b"fake_png_data")

        embeds, files = await build_embeds("last_week", "TestGov", data, governor_id_for_choice=123)

        # Verify async sparkline was called
        assert mock_sparkline.await_count == 2, "Should generate 2 charts (RSS + Forts)"

        # Verify files were created
        assert len(files) == 2, "Should have 2 chart files"


@pytest.mark.asyncio
async def test_build_embeds_no_data():
    """
    Verify graceful handling when no data rows exist.
    """
    from embed_my_stats import build_embeds

    data = {"rows": [], "trends": {}, "trend_avgs": {}, "freshness": {}}

    embeds, files = await build_embeds("wtd", "ALL", data)

    assert len(embeds) == 1, "Should return empty state embed"
    assert embeds[0].description == "No data.", "Should show no data message"
    assert len(files) == 0, "Should have no chart files"


@pytest.mark.asyncio
async def test_slice_buttons_refresh_is_async():
    """
    Verify SliceButtons.refresh_message properly awaits async operations.
    """
    from embed_my_stats import SliceButtons

    # Create mock interaction
    mock_interaction = MagicMock()
    mock_interaction.user.id = 999
    mock_interaction.response.is_done.return_value = False

    view = SliceButtons(
        requester_id=999,
        initial_slice="wtd",
        account_options=["Main"],
        current_choice="Main",
        governor_ids=[123],
        name_to_id={"Main": 123},
        timeout=70,
    )
    view.mark_live()

    # Mock get_stats_payload and build_embeds
    with patch("embed_my_stats.get_stats_payload", new_callable=AsyncMock) as mock_payload:
        with patch("embed_my_stats.build_embeds", new_callable=AsyncMock) as mock_embeds:
            mock_payload.return_value = {
                "rows": [{"WindowKey": "wtd", "Grouping": "ALL", "PowerEnd": 100000000}],
                "trends": {},
                "trend_avgs": {},
                "freshness": {},
            }
            mock_embeds.return_value = ([MagicMock()], [])

            # Mock message/followup
            view.message = MagicMock()
            view.message.id = 12345
            view.followup = MagicMock()
            view.followup.edit_message = AsyncMock()

            await view.refresh_message(mock_interaction)

            # Verify both async calls were awaited
            assert mock_payload.await_count == 1, "get_stats_payload should be awaited"
            assert mock_embeds.await_count == 1, "build_embeds should be awaited"


@pytest.mark.asyncio
async def test_slice_buttons_timeout_constant():
    """
    Verify timeout uses centralized STATS_VIEW_TIMEOUT constant.
    """
    from constants import STATS_VIEW_TIMEOUT
    from embed_my_stats import SliceButtons

    view = SliceButtons(
        requester_id=123,
        initial_slice="wtd",
        account_options=[],
        current_choice="ALL",
        governor_ids=[],
        name_to_id={},
    )

    # Should use constant from constants.py
    assert (
        view.timeout == STATS_VIEW_TIMEOUT
    ), f"Default timeout should be {STATS_VIEW_TIMEOUT} (STATS_VIEW_TIMEOUT constant)"
    assert view.timeout == 840, "STATS_VIEW_TIMEOUT should be 840 seconds (14 minutes)"


@pytest.mark.asyncio
async def test_aoo_fields_render_when_present():
    """
    Verify AOO (Ark of Osiris) fields render when player has participated.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "wtd",
                "Grouping": "PER",
                "GovernorID": "123",
                "Alliance": "K98",
                "PowerEnd": 100000000,
                "PowerDelta": 0,
                "TroopPowerEnd": 80000000,
                "TroopPowerDelta": 0,
                "RSSGatheredEnd": 5000000,
                "RSSGatheredDelta": 1000000,
                "RSSAssistEnd": 200000,
                "RSSAssistDelta": 50000,
                "HelpsEnd": 500,
                "HelpsDelta": 100,
                "FortsTotal": 10,
                "FortsLaunched": 5,
                "FortsJoined": 5,
                # AOO fields (match actual SQL column names)
                "AOOJoinedEnd": 12,
                "AOOWonEnd": 8,
                "AOOAvgKillEnd": 450000,  # Larger values (kills in thousands)
                "AOOAvgDeadEnd": 120000,
                "AOOAvgHealEnd": 350000,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    embeds, _ = await build_embeds("wtd", "TestGov", data, governor_id_for_choice=123)

    # Verify AOO fields are present (check actual field names from your embed code)
    field_names = [f.name for f in embeds[0].fields]

    # Based on your embed_my_stats.py code, the fields are:
    # "Ark Played • Won" and "Ark Avg K/D/H"
    assert any(
        "Ark" in name and "Played" in name for name in field_names
    ), "Ark Played/Won field should be present"
    assert any(
        "Ark" in name and "K/D/H" in name for name in field_names
    ), "Ark Avg K/D/H field should be present"

    # Verify values in the compact format used by your code
    ark_played_field = next((f for f in embeds[0].fields if "Played" in f.name), None)
    assert ark_played_field is not None
    assert "12" in ark_played_field.value, "Should show joined count"
    assert "8" in ark_played_field.value, "Should show won count"

    ark_kdh_field = next((f for f in embeds[0].fields if "K/D/H" in f.name), None)
    assert ark_kdh_field is not None
    # Your code uses fmt_short for these values
    assert "K:" in ark_kdh_field.value, "Should show kills"
    assert "D:" in ark_kdh_field.value, "Should show deads"
    assert "H:" in ark_kdh_field.value, "Should show heals"


@pytest.mark.asyncio
async def test_aoo_fields_hidden_when_not_participated():
    """
    Verify AOO fields are hidden when player has not participated (AOOJoined = 0).
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "wtd",
                "Grouping": "PER",
                "GovernorID": "456",
                "Alliance": "K98",
                "PowerEnd": 50000000,
                "PowerDelta": 0,
                "TroopPowerEnd": 40000000,
                "TroopPowerDelta": 0,
                "RSSGatheredEnd": 2000000,
                "RSSGatheredDelta": 500000,
                "RSSAssistEnd": 100000,
                "RSSAssistDelta": 20000,
                "HelpsEnd": 200,
                "HelpsDelta": 50,
                "FortsTotal": 5,
                "FortsLaunched": 3,
                "FortsJoined": 2,
                # AOO fields - not participated
                "AOOJoinedEnd": 0,
                "AOOWonEnd": 0,
                "AOOAvgKillEnd": 0,
                "AOOAvgDeadEnd": 0,
                "AOOAvgHealEnd": 0,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    embeds, _ = await build_embeds("wtd", "NoArkPlayer", data, governor_id_for_choice=456)

    # Verify AOO fields are NOT present
    field_names = [f.name for f in embeds[0].fields]
    assert "Ark Joined" not in field_names, "Ark fields should be hidden when not participated"
    assert "Ark Won" not in field_names, "Ark fields should be hidden when not participated"
    assert "Ark Avg K/D/H" not in field_names, "Ark fields should be hidden when not participated"


@pytest.mark.asyncio
async def test_aoo_fields_with_null_values():
    """
    Verify AOO fields handle NULL/missing values gracefully.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "last_week",
                "Grouping": "ALL",
                "Alliance": "K98",
                "PowerEnd": 100000000,
                "PowerDelta": 0,
                "TroopPowerEnd": 80000000,
                "TroopPowerDelta": 0,
                "RSSGatheredEnd": 5000000,
                "RSSGatheredDelta": 1000000,
                "RSSAssistEnd": 200000,
                "RSSAssistDelta": 50000,
                "HelpsEnd": 500,
                "HelpsDelta": 100,
                "FortsTotal": 10,
                "FortsLaunched": 5,
                "FortsJoined": 5,
                # AOO fields intentionally missing/None
                "AOOJoinedEnd": None,
                "AOOWonEnd": None,
                "AOOAvgKillEnd": None,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    # Should not raise exception
    embeds, _ = await build_embeds("last_week", "ALL", data)

    # Verify AOO fields are hidden (treated as 0)
    field_names = [f.name for f in embeds[0].fields]
    assert "Ark Joined" not in field_names, "Ark fields should be hidden when NULL"


@pytest.mark.asyncio
async def test_aoo_aggregate_view():
    """
    Verify AOO fields display correctly for ALL (aggregate) view.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "mtd",
                "Grouping": "ALL",  # Aggregate across all governors
                "Alliance": "K98",
                "PowerEnd": 500000000,
                "PowerDelta": 10000000,
                "TroopPowerEnd": 400000000,
                "TroopPowerDelta": 5000000,
                "RSSGatheredEnd": 50000000,
                "RSSGatheredDelta": 10000000,
                "RSSAssistEnd": 2000000,
                "RSSAssistDelta": 500000,
                "HelpsEnd": 5000,
                "HelpsDelta": 1000,
                "FortsTotal": 100,
                "FortsLaunched": 50,
                "FortsJoined": 50,
                # AOO aggregate (sum across all governors)
                "AOOJoinedEnd": 45,
                "AOOWonEnd": 30,
                "AOOAvgKillEnd": 12500000,  # aggregate average (larger number)
                "AOOAvgDeadEnd": 3500000,
                "AOOAvgHealEnd": 9800000,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    embeds, _ = await build_embeds("mtd", "ALL", data)

    # Check for Ark fields (using actual field names from your code)
    ark_played_field = next(
        (f for f in embeds[0].fields if "Ark" in f.name and "Played" in f.name), None
    )
    assert ark_played_field is not None, "ALL view should show AOO aggregate"
    assert "45" in ark_played_field.value, "Should show total arks joined"
    assert "30" in ark_played_field.value, "Should show total arks won"


@pytest.mark.asyncio
async def test_build_embeds_uses_fmt_short():
    """
    Verify build_embeds uses centralized fmt_short() instead of local _short().
    """
    # Verify local _short doesn't exist
    import embed_my_stats
    from embed_my_stats import build_embeds

    assert not hasattr(
        embed_my_stats, "_short"
    ), "Local _short() should be removed in favor of fmt_short()"

    # Verify fmt_short is used (basic smoke test)
    data = {
        "rows": [
            {
                "WindowKey": "wtd",
                "Grouping": "ALL",
                "Alliance": "K98",
                "PowerEnd": 123456789,  # Large number to trigger short formatting
                "PowerDelta": 1234567,
                "TroopPowerEnd": 80000000,
                "TroopPowerDelta": 500000,
                "RSSGatheredEnd": 5000000,
                "RSSGatheredDelta": 1000000,
                "RSSAssistEnd": 200000,
                "RSSAssistDelta": 50000,
                "HelpsEnd": 500,
                "HelpsDelta": 100,
                "FortsTotal": 10,
                "FortsLaunched": 5,
                "FortsJoined": 5,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    embeds, _ = await build_embeds("wtd", "ALL", data)

    # Verify short notation in embed (e.g., "123M" instead of full number)
    power_field = next(f for f in embeds[0].fields if f.name == "Power")
    assert (
        "M" in power_field.value or "K" in power_field.value
    ), "Should use short notation (M/K) for large numbers"


@pytest.mark.asyncio
async def test_build_embeds_error_handling():
    """
    Verify build_embeds returns error embed instead of crashing on bad data.
    """
    from embed_my_stats import build_embeds

    # Malformed data that would cause errors
    bad_data = {
        "rows": [
            {
                "WindowKey": "wtd",
                "Grouping": "ALL",
                # Missing required fields like PowerEnd, TroopPowerEnd, etc.
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    # Should not raise exception
    embeds, files = await build_embeds("wtd", "ALL", bad_data)

    # Should return error embed (or empty embed at minimum)
    assert len(embeds) >= 1, "Should return at least one embed"
    # Either error embed or graceful handling
    assert files == [], "Should not generate charts on error"


@pytest.mark.asyncio
async def test_refresh_message_error_handling():
    """
    Verify SliceButtons.refresh_message handles errors gracefully.
    """
    from unittest.mock import AsyncMock

    from embed_my_stats import SliceButtons

    mock_interaction = MagicMock()
    mock_interaction.user.id = 999
    mock_interaction.response.is_done.return_value = False
    mock_interaction.response.send_message = AsyncMock()

    view = SliceButtons(
        requester_id=999,
        initial_slice="wtd",
        account_options=["Main"],
        current_choice="Main",
        governor_ids=[123],
        name_to_id={"Main": 123},
        timeout=70,
    )
    view.mark_live()

    # Mock get_stats_payload to raise exception
    with patch("embed_my_stats.get_stats_payload", side_effect=Exception("DB offline")):
        await view.refresh_message(mock_interaction)

        # Verify error was shown to user
        assert mock_interaction.response.send_message.called, "Should show error message to user"

        call_args = mock_interaction.response.send_message.call_args
        assert "Failed to load stats" in str(call_args), "Error message should mention failure"


@pytest.mark.asyncio
async def test_stats_payload_graceful_degradation():
    """
    Verify get_stats_payload returns empty payload instead of raising on DB errors.
    """
    from stats_service import get_stats_payload

    # Mock DB functions to fail
    with patch("stats_service._fetch_proc_sync", side_effect=Exception("DB connection failed")):
        with patch(
            "stats_service._fetch_trendlines_sync", side_effect=Exception("DB connection failed")
        ):
            # Should not raise
            result = await get_stats_payload(
                discord_id=999, governor_ids=[123], slice_key_or_csv="wtd"
            )

            # Give pending futures a chance to complete (prevents "never retrieved" warning)
            await asyncio.sleep(0.01)

            # Should return empty structure
            assert isinstance(result, dict), "Should return dict"
            assert "rows" in result, "Should have rows key"
            assert result["rows"] == [], "Rows should be empty on error"


@pytest.mark.asyncio
async def test_slice_button_emits_telemetry():
    """
    Verify slice button interactions emit telemetry events.
    """
    from unittest.mock import AsyncMock, patch

    from embed_my_stats import SliceButtons

    mock_interaction = MagicMock()
    mock_interaction.user.id = 999
    mock_interaction.response.edit_message = AsyncMock()

    view = SliceButtons(
        requester_id=999,
        initial_slice="wtd",
        account_options=["Main"],
        current_choice="Main",
        governor_ids=[123],
        name_to_id={"Main": 123},
    )
    view.mark_live()
    view.message = MagicMock()
    view.message.id = 12345
    view.followup = MagicMock()
    view.followup.edit_message = AsyncMock()

    # Mock get_stats_payload and build_embeds to prevent actual work
    with patch("embed_my_stats.get_stats_payload", new_callable=AsyncMock) as mock_payload:
        with patch("embed_my_stats.build_embeds", new_callable=AsyncMock) as mock_embeds:
            with patch("file_utils.emit_telemetry_event") as mock_telemetry:
                mock_payload.return_value = {
                    "rows": [],
                    "trends": {},
                    "trend_avgs": {},
                    "freshness": {},
                }
                mock_embeds.return_value = ([MagicMock()], [])

                # Simulate button click (wtd -> last_week)
                slice_btn = next(
                    b for b in view.children if hasattr(b, "key") and b.key == "last_week"
                )
                await slice_btn.callback(mock_interaction)

                # Verify telemetry was emitted (should be called twice: slice_change + refresh)
                assert (
                    mock_telemetry.call_count >= 2
                ), f"Expected at least 2 telemetry calls, got {mock_telemetry.call_count}"

                # Check that slice_change event was emitted
                all_calls = [call[0][0] for call in mock_telemetry.call_args_list]
                slice_change_events = [
                    c for c in all_calls if c.get("event") == "my_stats_slice_change"
                ]

                assert (
                    len(slice_change_events) > 0
                ), f"Should have slice_change event. Got events: {[c.get('event') for c in all_calls]}"

                slice_event = slice_change_events[0]
                assert (
                    slice_event["to_slice"] == "last_week"
                ), "Should track slice change to last_week"


@pytest.mark.asyncio
async def test_account_select_emits_telemetry():
    """
    Verify account selection emits telemetry events.
    """
    from unittest.mock import AsyncMock, PropertyMock, patch

    from embed_my_stats import AccountSelect, SliceButtons

    mock_interaction = MagicMock()
    mock_interaction.user.id = 999
    mock_interaction.response.edit_message = AsyncMock()

    view = SliceButtons(
        requester_id=999,
        initial_slice="wtd",
        account_options=["Main", "Alt 1"],
        current_choice="Main",
        governor_ids=[123, 456],
        name_to_id={"Main": 123, "Alt 1": 456},
    )
    view.mark_live()
    view.message = MagicMock()
    view.message.id = 12345
    view.followup = MagicMock()
    view.followup.edit_message = AsyncMock()

    # Mock get_stats_payload and build_embeds
    with patch("embed_my_stats.get_stats_payload", new_callable=AsyncMock) as mock_payload:
        with patch("embed_my_stats.build_embeds", new_callable=AsyncMock) as mock_embeds:
            with patch("file_utils.emit_telemetry_event") as mock_telemetry:
                mock_payload.return_value = {
                    "rows": [],
                    "trends": {},
                    "trend_avgs": {},
                    "freshness": {},
                }
                mock_embeds.return_value = ([MagicMock()], [])

                # Find the AccountSelect component
                account_select = next(c for c in view.children if isinstance(c, AccountSelect))

                # Mock the values property to return "Alt 1"
                with patch.object(
                    type(account_select), "values", new_callable=PropertyMock
                ) as mock_values:
                    mock_values.return_value = ["Alt 1"]

                    await account_select.callback(mock_interaction)

                # Verify telemetry was emitted (should be called twice: account_change + refresh)
                assert (
                    mock_telemetry.call_count >= 2
                ), f"Expected at least 2 telemetry calls, got {mock_telemetry.call_count}"

                # Check that account_change event was emitted
                all_calls = [call[0][0] for call in mock_telemetry.call_args_list]
                account_change_events = [
                    c for c in all_calls if c.get("event") == "my_stats_account_change"
                ]

                assert (
                    len(account_change_events) > 0
                ), f"Should have account_change event. Got events: {[c.get('event') for c in all_calls]}"

                account_event = account_change_events[0]
                assert account_event["from_account"] == "Main", "Should track change from Main"
                assert account_event["to_account"] == "Alt 1", "Should track change to Alt 1"


def test_constants_imported_correctly():
    """
    Verify stats constants are properly imported from constants.py.
    """
    from constants import DOWN_ARROW_EMOJI, STATS_VIEW_TIMEOUT, UP_ARROW_EMOJI

    # Verify constants exist
    assert STATS_VIEW_TIMEOUT is not None, "STATS_VIEW_TIMEOUT should be defined"
    assert isinstance(STATS_VIEW_TIMEOUT, int), "STATS_VIEW_TIMEOUT should be int"
    assert STATS_VIEW_TIMEOUT == 840, "STATS_VIEW_TIMEOUT should be 840 seconds"

    # Verify emojis exist
    assert UP_ARROW_EMOJI is not None, "UP_ARROW_EMOJI should be defined"
    assert DOWN_ARROW_EMOJI is not None, "DOWN_ARROW_EMOJI should be defined"
    assert isinstance(UP_ARROW_EMOJI, str), "UP_ARROW_EMOJI should be string"
    assert isinstance(DOWN_ARROW_EMOJI, str), "DOWN_ARROW_EMOJI should be string"


# Append these tests to existing test_embed_my_stats.py file


@pytest.mark.asyncio
async def test_build_embeds_ignores_new_export_fields():
    """
    CRITICAL: Verify /my_stats embed ignores new export-only fields added to view.

    This test ensures adding T4_Kills, T5_Kills, etc. to vDaily_PlayerExport
    does NOT break the /my_stats command.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                # Existing fields used by /my_stats
                "WindowKey": "wtd",
                "Grouping": "PER",
                "GovernorID": 123456,
                "GovernorName": "TestPlayer",
                "Alliance": "K98",
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
                # AOO fields (already used)
                "AOOJoinedEnd": 3,
                "AOOWonEnd": 2,
                "AOOAvgKillEnd": 1500000,
                "AOOAvgDeadEnd": 800000,
                "AOOAvgHealEnd": 1200000,
                # NEW export-only fields (should be ignored by /my_stats)
                "T4_Kills": 50000,
                "T4_KillsDelta": 5000,
                "T5_Kills": 30000,
                "T5_KillsDelta": 3000,
                "T4T5_Kills": 80000,
                "T4T5_KillsDelta": 8000,
                "HealedTroops": 100000,
                "HealedTroopsDelta": 10000,
                "RangedPoints": 200000,
                "RangedPointsDelta": 20000,
                "HighestAcclaim": 50,
                "HighestAcclaimDelta": 0,
                "AutarchTimes": 2,
                "AutarchTimesDelta": 0,
                # AOO deltas (export-only)
                "AOOJoinedDelta": 1,
                "AOOWonDelta": 1,
                "AOOAvgKillDelta": 50000,
                "AOOAvgDeadDelta": 20000,
                "AOOAvgHealDelta": 30000,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    # Should not raise exception despite extra fields
    embeds, files = await build_embeds(
        window_key="wtd", choice="TestPlayer", data=data, governor_id_for_choice=123456
    )

    assert len(embeds) >= 1, "Should successfully build embed"

    # Verify export-only fields are NOT displayed
    field_names = [f.name.lower() for f in embeds[0].fields]

    # These should NOT appear in the embed
    assert not any(
        "t4" in name and "kill" in name for name in field_names
    ), "T4 kills should not appear in /my_stats embed"
    assert not any(
        "t5" in name and "kill" in name for name in field_names
    ), "T5 kills should not appear in /my_stats embed"
    assert not any(
        "ranged" in name for name in field_names
    ), "Ranged points should not appear in /my_stats embed"
    assert not any(
        "acclaim" in name for name in field_names
    ), "Acclaim should not appear in /my_stats embed"
    assert not any(
        "autarch" in name for name in field_names
    ), "Autarch should not appear in /my_stats embed"

    # These SHOULD still appear (already in use)
    assert "Power" in [f.name for f in embeds[0].fields], "Power should still be displayed"
    assert "Forts" in [f.name for f in embeds[0].fields], "Forts should still be displayed"

    # AOO should appear (player participated)
    assert any(
        "Ark" in f.name for f in embeds[0].fields
    ), "AOO fields should appear when participated"


@pytest.mark.asyncio
async def test_build_embeds_all_aggregate_with_new_fields():
    """
    Verify ALL (aggregate) view works correctly with new export-only fields.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "mtd",
                "Grouping": "ALL",  # Aggregate
                "Alliance": "K98",
                "PowerEnd": 500000000,
                "PowerDelta": 10000000,
                "TroopPowerEnd": 400000000,
                "TroopPowerDelta": 5000000,
                "RSSGatheredEnd": 50000000000,
                "RSSGatheredDelta": 1000000000,
                "RSSAssistEnd": 20000000000,
                "RSSAssistDelta": 500000000,
                "HelpsEnd": 50000,
                "HelpsDelta": 5000,
                "FortsTotal": 100,
                "FortsLaunched": 50,
                "FortsJoined": 50,
                "AOOJoinedEnd": 45,
                "AOOWonEnd": 30,
                "AOOAvgKillEnd": 12500000,
                "AOOAvgDeadEnd": 3500000,
                "AOOAvgHealEnd": 9800000,
                # New export fields (should be ignored)
                "T4_Kills": 500000,
                "T5_Kills": 300000,
                "T4T5_Kills": 800000,
                "HealedTroops": 1000000,
                "RangedPoints": 2000000,
                "HighestAcclaim": 75,
                "AutarchTimes": 15,
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    embeds, files = await build_embeds("mtd", "ALL", data)

    assert len(embeds) >= 1, "Should build aggregate embed"
    assert "ALL" in embeds[0].title or "ALL" in str(
        embeds[0].description
    ), "Should indicate aggregate view"

    # Verify core fields present
    field_names = [f.name for f in embeds[0].fields]
    assert "Power" in field_names
    assert "Forts" in field_names

    # Verify export-only fields absent
    field_names_lower = [n.lower() for n in field_names]
    assert not any("t4" in n and "kill" in n for n in field_names_lower)
    assert not any("ranged" in n for n in field_names_lower)


@pytest.mark.asyncio
async def test_find_row_with_export_fields():
    """
    Verify _find_row still correctly identifies rows despite additional fields.
    """
    from embed_my_stats import _find_row

    rows = [
        {
            "WindowKey": "wtd",
            "Grouping": "PER",
            "GovernorID": 123456,
            "GovernorName": "Player1",
            "PowerEnd": 50000000,
            # Export-only fields
            "T4_Kills": 50000,
            "T5_Kills": 30000,
            "RangedPoints": 200000,
        },
        {
            "WindowKey": "wtd",
            "Grouping": "PER",
            "GovernorID": 789012,
            "GovernorName": "Player2",
            "PowerEnd": 60000000,
            # Export-only fields
            "T4_Kills": 60000,
            "T5_Kills": 40000,
            "RangedPoints": 250000,
        },
    ]

    # Find by GovernorID
    result = _find_row(rows, "wtd", "Player1", governor_id_for_choice=123456)
    assert len(result) == 1
    assert result[0]["GovernorName"] == "Player1"
    assert result[0]["PowerEnd"] == 50000000

    # Find by name (fallback)
    result2 = _find_row(rows, "wtd", "Player2", governor_id_for_choice=None)
    assert len(result2) == 1
    assert result2[0]["GovernorName"] == "Player2"


@pytest.mark.asyncio
async def test_build_embeds_partial_export_fields():
    """
    Verify embed building works when some export fields are NULL/missing.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "last_week",
                "Grouping": "PER",
                "GovernorID": 456789,
                "GovernorName": "PartialData",
                "Alliance": "K98",
                "PowerEnd": 40000000,
                "PowerDelta": 500000,
                "TroopPowerEnd": 30000000,
                "TroopPowerDelta": 400000,
                "RSSGatheredEnd": 5000000000,
                "RSSGatheredDelta": 200000000,
                "RSSAssistEnd": 2000000000,
                "RSSAssistDelta": 100000000,
                "HelpsEnd": 5000,
                "HelpsDelta": 250,
                "FortsTotal": 8,
                "FortsLaunched": 4,
                "FortsJoined": 4,
                "AOOJoinedEnd": 2,
                "AOOWonEnd": 1,
                "AOOAvgKillEnd": 800000,
                "AOOAvgDeadEnd": 300000,
                "AOOAvgHealEnd": 500000,
                # Some export fields present, others NULL/missing
                "T4_Kills": 25000,
                "T5_Kills": None,  # NULL
                # T4T5_Kills missing entirely
                "HealedTroops": 50000,
                "RangedPoints": None,
                # Remaining fields missing
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    # Should not raise exception
    embeds, files = await build_embeds(
        "last_week", "PartialData", data, governor_id_for_choice=456789
    )

    assert len(embeds) >= 1, "Should handle partial export field data"

    # Verify core functionality intact
    field_names = [f.name for f in embeds[0].fields]
    assert "Power" in field_names
    assert any("Ark" in name for name in field_names)  # AOO present


@pytest.mark.asyncio
async def test_backward_compatibility_no_export_fields():
    """
    Verify /my_stats still works if export fields are missing entirely (old view schema).

    This ensures graceful degradation if SQL update hasn't been applied yet.
    """
    from embed_my_stats import build_embeds

    data = {
        "rows": [
            {
                "WindowKey": "wtd",
                "Grouping": "PER",
                "GovernorID": 111222,
                "GovernorName": "OldSchema",
                "Alliance": "K98",
                "PowerEnd": 45000000,
                "PowerDelta": 750000,
                "TroopPowerEnd": 35000000,
                "TroopPowerDelta": 600000,
                "RSSGatheredEnd": 8000000000,
                "RSSGatheredDelta": 300000000,
                "RSSAssistEnd": 3000000000,
                "RSSAssistDelta": 150000000,
                "HelpsEnd": 7500,
                "HelpsDelta": 350,
                "FortsTotal": 12,
                "FortsLaunched": 6,
                "FortsJoined": 6,
                "AOOJoinedEnd": 5,
                "AOOWonEnd": 3,
                "AOOAvgKillEnd": 1200000,
                "AOOAvgDeadEnd": 600000,
                "AOOAvgHealEnd": 900000,
                # NO export-only fields (simulates old schema)
            }
        ],
        "trends": {},
        "trend_avgs": {},
        "freshness": {},
    }

    # Should work fine without export fields
    embeds, files = await build_embeds("wtd", "OldSchema", data, governor_id_for_choice=111222)

    assert len(embeds) >= 1, "Should work with old schema (no export fields)"

    # Verify all expected fields present
    field_names = [f.name for f in embeds[0].fields]
    assert "Power" in field_names
    assert "Troop Power" in field_names
    assert "RSS Gathered" in field_names
    assert "Forts" in field_names
    assert any("Ark" in name for name in field_names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
