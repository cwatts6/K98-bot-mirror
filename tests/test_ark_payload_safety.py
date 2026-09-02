from __future__ import annotations

from datetime import date, datetime, time
from unittest.mock import AsyncMock, patch

import pytest

from ark.ark_scheduler import _build_channel_reminder_embed, _build_dm_reminder_embed
from ark.embeds import (
    build_ark_confirmation_embed_from_match,
    build_ark_registration_embed_from_match,
)
from ark.registration_flow import _build_fuzzy_embed
from ark.team_publish import _header_embed, _team_embed
from ark.team_state import ArkTeamAssignment
from commands.ark_cmds import build_ark_player_report_pages
from core.discord_embed_limits import (
    MAX_DESCRIPTION_CHARACTERS,
    MAX_FIELD_VALUE_CHARACTERS,
    MAX_FIELDS_PER_EMBED,
    MAX_TITLE_CHARACTERS,
    MAX_TOTAL_CHARACTERS,
    measure_embed_payload,
    require_valid_embed_payload,
)
from ui.views.team_builder_views import _Assignment, _build_embed


def _match(*, alliance: str = "K98", notes: str | None = None) -> dict:
    return {
        "MatchId": 42,
        "Alliance": alliance,
        "ArkWeekendDate": date(2026, 3, 7),
        "MatchDay": "Sat",
        "MatchTimeUtc": time(11, 0),
        "SignupCloseUtc": datetime(2026, 3, 6, 23, 0),
        "Notes": notes,
        "Result": "Win",
        "ResultNotes": "R" * 2000,
        "CompletedAtUtc": datetime(2026, 3, 7, 12, 0),
    }


def _name(index: int, length: int = 128) -> str:
    prefix = f"{index:03}-"
    return prefix + ("N" * (length - len(prefix)))


def _roster(players: int = 30, subs: int = 15, *, checked_in: bool = False) -> list[dict]:
    rows = []
    for index in range(players):
        rows.append(
            {
                "GovernorId": index + 1,
                "GovernorNameSnapshot": _name(index),
                "SlotType": "Player",
                "CheckedIn": int(checked_in),
            }
        )
    for index in range(subs):
        rows.append(
            {
                "GovernorId": players + index + 1,
                "GovernorNameSnapshot": _name(players + index),
                "SlotType": "Sub",
                "CheckedIn": int(checked_in),
            }
        )
    return rows


def _assert_valid(embed) -> None:
    usage = require_valid_embed_payload(embed)
    assert usage.embed_count == 1
    assert usage.field_counts[0] <= MAX_FIELDS_PER_EMBED
    assert usage.total_characters <= MAX_TOTAL_CHARACTERS
    assert len(embed.title or "") <= MAX_TITLE_CHARACTERS
    assert len(embed.description or "") <= MAX_DESCRIPTION_CHARACTERS
    assert all(len(field.value) <= MAX_FIELD_VALUE_CHARACTERS for field in embed.fields)


def test_registration_schema_maximum_is_valid_and_marks_omissions() -> None:
    embed = build_ark_registration_embed_from_match(
        _match(alliance="A" * 255, notes="Z" * 2000),
        players_cap=30,
        subs_cap=15,
        roster=_roster(),
    )

    _assert_valid(embed)
    assert embed.title.endswith("…")
    assert any(field.name == "Alliance" and len(field.value) == 255 for field in embed.fields)
    assert any(field.name == "More details" for field in embed.fields)


def test_registration_title_exact_boundary_and_one_over() -> None:
    prefix_length = len("Ark of Osiris — ")
    exact_alliance = "A" * (MAX_TITLE_CHARACTERS - prefix_length)
    exact = build_ark_registration_embed_from_match(
        _match(alliance=exact_alliance),
        players_cap=30,
        subs_cap=15,
        roster=[],
    )
    one_over = build_ark_registration_embed_from_match(
        _match(alliance=exact_alliance + "A"),
        players_cap=30,
        subs_cap=15,
        roster=[],
    )

    _assert_valid(exact)
    _assert_valid(one_over)
    assert len(exact.title) == MAX_TITLE_CHARACTERS
    assert not any(field.name == "Alliance" for field in exact.fields)
    assert one_over.title.endswith("…")
    assert any(field.name == "Alliance" for field in one_over.fields)


def test_registration_1024_and_1025_note_boundaries_are_valid() -> None:
    exact = build_ark_registration_embed_from_match(
        _match(notes="X" * 1024),
        players_cap=30,
        subs_cap=15,
        roster=[],
    )
    one_over = build_ark_registration_embed_from_match(
        _match(notes="X" * 1025),
        players_cap=30,
        subs_cap=15,
        roster=[],
    )

    _assert_valid(exact)
    _assert_valid(one_over)
    assert len([field for field in exact.fields if field.name.startswith("Notes")]) == 1
    assert len([field for field in one_over.fields if field.name.startswith("Notes")]) == 2


def test_confirmation_pathological_payload_retains_result_and_is_valid() -> None:
    updates = [f"Update {index}: " + ("U" * 1500) for index in range(45)]
    embed = build_ark_confirmation_embed_from_match(
        _match(alliance="A" * 255),
        players_cap=30,
        subs_cap=15,
        roster=_roster(checked_in=True),
        updates=updates,
        team_assignment="Click **Reconfirm Teams** to review or edit assignments.",
    )

    _assert_valid(embed)
    assert any(field.name == "Result" for field in embed.fields)
    marker = next(field.value for field in embed.fields if field.name == "More details")
    assert "omitted" in marker
    assert "update" in marker


def test_fuzzy_maximum_display_names_are_compacted_and_valid() -> None:
    matches = [
        {"GovernorName": "G" * 255, "GovernorID": str(10_000_000 + index)} for index in range(15)
    ]
    embed = _build_fuzzy_embed("Q" * 256, matches)

    _assert_valid(embed)
    assert "…" in (embed.description or "")


@pytest.mark.asyncio
async def test_public_and_dm_reminders_pack_maximum_credible_teams() -> None:
    roster = _roster()
    team_rows = [
        {
            "GovernorId": row["GovernorId"],
            "TeamNumber": 1 if index < 30 else 2,
            "IsFinal": 1,
        }
        for index, row in enumerate(roster)
    ]
    with patch(
        "ark.ark_scheduler.list_match_team_rows",
        new=AsyncMock(return_value=team_rows),
    ):
        public = await _build_channel_reminder_embed(
            match=_match(alliance="A" * 255),
            reminder_type="4h",
            text="T" * 400,
            roster=roster,
        )
        dm = await _build_dm_reminder_embed(
            match=_match(alliance="A" * 255),
            reminder_type="4h",
            roster=roster,
        )

    _assert_valid(public)
    _assert_valid(dm)
    assert any(field.name.startswith("Team 1") for field in public.fields)
    assert any(field.name.startswith("Team 2") for field in dm.fields)


def test_team_publication_embeds_are_valid_at_schema_maximum() -> None:
    assignment = ArkTeamAssignment(match_id=42)
    assignment.status = "published"
    assignment.team1_player_ids = list(range(1, 31))
    rows_by_gid = {index: {"GovernorNameSnapshot": _name(index)} for index in range(1, 31)}

    header = _header_embed(_match(alliance="A" * 255), assignment)
    team = _team_embed("Ark Team 1", assignment.team1_player_ids, rows_by_gid)

    _assert_valid(header)
    _assert_valid(team)
    assert header.title.endswith("…")


def test_team_builder_compacts_names_and_keeps_complete_credible_roster() -> None:
    rows = _roster()
    assignment = _Assignment(
        roster_player_ids=[row["GovernorId"] for row in rows],
        team1_player_ids=[row["GovernorId"] for row in rows[:30]],
        team2_player_ids=[row["GovernorId"] for row in rows[30:]],
    )
    embed = _build_embed(_match(alliance="A" * 255), assignment, rows)

    _assert_valid(embed)
    rendered = "\n".join(field.value for field in embed.fields)
    assert rendered.count("…") == 45
    assert not any(field.name == "More details" for field in embed.fields)


def test_report_uses_character_budgeted_pages_without_losing_rows() -> None:
    rows = [
        {
            "GovernorName": _name(index),
            "GovernorId": index,
            "MatchesPlayed": 2_147_483_647,
            "WinPct": 1,
            "EmergencyWithdraws": 2_147_483_647,
            "NoShows": 2_147_483_647,
        }
        for index in range(1, 51)
    ]
    pages = build_ark_player_report_pages(rows)

    assert len(pages) > 2
    for page in pages:
        _assert_valid(page)
    rendered_rows = sum((page.description or "").count("\n") + 1 for page in pages)
    assert rendered_rows == len(rows)
    assert measure_embed_payload(pages[0]).total_characters <= MAX_TOTAL_CHARACTERS
