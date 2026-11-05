from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from ark.ark_scheduler import (
    _build_channel_reminder_embed,
    _build_dm_reminder_embed,
    _build_team_name_fields,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MATCH: dict = {
    "MatchId": 1,
    "Alliance": "k98A",
    "ArkWeekendDate": date(2026, 3, 28),
    "MatchDay": "Sat",
    "MatchTimeUtc": datetime(2026, 3, 28, 11, 0, tzinfo=UTC).time(),
    "SignupCloseUtc": datetime(2026, 3, 28, 9, 0, tzinfo=UTC),
    "RegistrationStartsAtUtc": datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    "RegistrationChannelId": 111,
    "RegistrationMessageId": 222,
    "ConfirmationChannelId": 333,
    "Status": "scheduled",
    "AnnouncementSent": True,
}

ROSTER = [
    {
        "GovernorId": 101,
        "GovernorNameSnapshot": "Chrislos",
        "DiscordUserId": 9001,
        "Status": "Active",
        "SlotType": "Player",
    },
    {
        "GovernorId": 102,
        "GovernorNameSnapshot": "BlazieP",
        "DiscordUserId": 9002,
        "Status": "Active",
        "SlotType": "Player",
    },
    {
        "GovernorId": 103,
        "GovernorNameSnapshot": "PlayerA",
        "DiscordUserId": 9003,
        "Status": "Active",
        "SlotType": "Player",
    },
    {
        "GovernorId": 104,
        "GovernorNameSnapshot": "PlayerB",
        "DiscordUserId": 9004,
        "Status": "Active",
        "SlotType": "Player",
    },
]

FINAL_TEAM_ROWS = [
    {"GovernorId": 101, "TeamNumber": 1, "IsDraft": 0, "IsFinal": 1},
    {"GovernorId": 102, "TeamNumber": 1, "IsDraft": 0, "IsFinal": 1},
    {"GovernorId": 103, "TeamNumber": 2, "IsDraft": 0, "IsFinal": 1},
    {"GovernorId": 104, "TeamNumber": 2, "IsDraft": 0, "IsFinal": 1},
]

DRAFT_ONLY_ROWS = [
    {"GovernorId": 101, "TeamNumber": 1, "IsDraft": 1, "IsFinal": 0},
    {"GovernorId": 102, "TeamNumber": 2, "IsDraft": 1, "IsFinal": 0},
]


# ---------------------------------------------------------------------------
# Test 1 — _build_team_name_fields returns names when IsFinal rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_team_name_fields_returns_names_for_final_rows() -> None:
    with (
        patch(
            "ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=FINAL_TEAM_ROWS)
        ),
    ):
        result = await _build_team_name_fields(match_id=1, roster=ROSTER)

    assert result is not None
    t1, t2 = result
    assert "Chrislos" in t1
    assert "BlazieP" in t1
    assert "PlayerA" in t2
    assert "PlayerB" in t2


# ---------------------------------------------------------------------------
# Test 2 — _build_team_name_fields returns None when only draft rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_team_name_fields_returns_none_for_draft_only() -> None:
    with patch(
        "ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=DRAFT_ONLY_ROWS)
    ):
        result = await _build_team_name_fields(match_id=1, roster=ROSTER)

    assert result is None


# ---------------------------------------------------------------------------
# Test 3 — _build_team_name_fields returns None when no team rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_team_name_fields_returns_none_when_no_rows() -> None:
    with patch("ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=[])):
        result = await _build_team_name_fields(match_id=1, roster=ROSTER)

    assert result is None


# ---------------------------------------------------------------------------
# Test 4 — _build_team_name_fields fetches roster from SQL when not supplied
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_team_name_fields_fetches_roster_when_none() -> None:
    with (
        patch(
            "ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=FINAL_TEAM_ROWS)
        ),
        patch(
            "ark.ark_scheduler.get_roster", new=AsyncMock(return_value=ROSTER)
        ) as mock_get_roster,
    ):
        result = await _build_team_name_fields(match_id=1, roster=None)

    mock_get_roster.assert_awaited_once_with(1)
    assert result is not None


# ---------------------------------------------------------------------------
# Test 5 — channel embed includes Team 1 / Team 2 fields when final rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channel_embed_includes_team_fields() -> None:
    with patch(
        "ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=FINAL_TEAM_ROWS)
    ):
        embed = await _build_channel_reminder_embed(
            match=MATCH,
            reminder_type="4h",
            text="⏰ Ark reminder (4h)",
            roster=ROSTER,
        )

    field_names = [f.name for f in embed.fields]
    assert "Team 1" in field_names
    assert "Team 2" in field_names
    # Must NOT have the old count-based field
    assert "Team Summary" not in field_names


# ---------------------------------------------------------------------------
# Test 6 — channel embed omits team fields when no final rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channel_embed_omits_team_fields_when_no_final_teams() -> None:
    with patch(
        "ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=DRAFT_ONLY_ROWS)
    ):
        embed = await _build_channel_reminder_embed(
            match=MATCH,
            reminder_type="4h",
            text="⏰ Ark reminder (4h)",
            roster=ROSTER,
        )

    field_names = [f.name for f in embed.fields]
    assert "Team 1" not in field_names
    assert "Team 2" not in field_names
    assert "Team Summary" not in field_names


# ---------------------------------------------------------------------------
# Test 7 — DM embed includes team fields when final rows exist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dm_embed_includes_team_fields() -> None:
    with patch(
        "ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=FINAL_TEAM_ROWS)
    ):
        embed = await _build_dm_reminder_embed(
            match=MATCH,
            reminder_type="4h",
            roster=ROSTER,
        )

    field_names = [f.name for f in embed.fields]
    assert "Team 1" in field_names
    assert "Team 2" in field_names
    assert "Team Summary" not in field_names

    # Verify name content — no governor IDs, no @mentions
    team1_field = next(f for f in embed.fields if f.name == "Team 1")
    assert "Chrislos" in team1_field.value
    assert "<@" not in team1_field.value
