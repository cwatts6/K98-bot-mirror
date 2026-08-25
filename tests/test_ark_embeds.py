from __future__ import annotations

from datetime import date, datetime, time

from ark.embeds import build_ark_registration_embed_from_match


def _make_roster(players: int, subs: int) -> list[dict]:
    roster = []
    for i in range(players):
        roster.append(
            {
                "GovernorNameSnapshot": f"Player {i + 1} - ExtraLongName" * 2,
                "SlotType": "Player",
            }
        )
    for i in range(subs):
        roster.append(
            {
                "GovernorNameSnapshot": f"Sub {i + 1} - ExtraLongName" * 2,
                "SlotType": "Sub",
            }
        )
    return roster


def test_registration_embed_splits_roster_fields():
    match = {
        "Alliance": "K98",
        "ArkWeekendDate": date(2026, 3, 7),
        "MatchDay": "Sat",
        "MatchTimeUtc": time(11, 0),
        "SignupCloseUtc": datetime(2026, 3, 6, 23, 0),
        "Notes": None,
    }
    roster = _make_roster(players=30, subs=15)

    embed = build_ark_registration_embed_from_match(
        match,
        players_cap=30,
        subs_cap=15,
        roster=roster,
    )

    assert embed.fields, "Expected roster fields to be present"
    for field in embed.fields:
        assert len(field.value) <= 1024
