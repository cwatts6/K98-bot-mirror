from __future__ import annotations

from datetime import date, datetime, time

from ark.embeds import build_ark_confirmation_embed_from_match


def test_confirmation_embed_includes_checked_in_and_updates():
    match = {
        "Alliance": "K98",
        "ArkWeekendDate": date(2026, 3, 7),
        "MatchDay": "Sat",
        "MatchTimeUtc": time(11, 0),
        "SignupCloseUtc": datetime(2026, 3, 6, 23, 0),
        "Notes": None,
    }
    roster = [
        {"GovernorNameSnapshot": "Player 1", "SlotType": "Player", "CheckedIn": 1},
        {"GovernorNameSnapshot": "Player 2", "SlotType": "Player"},
        {"GovernorNameSnapshot": "Sub 1", "SlotType": "Sub"},
    ]

    embed = build_ark_confirmation_embed_from_match(
        match,
        players_cap=30,
        subs_cap=15,
        roster=roster,
        updates=["Emergency withdraw: Player 2 (222)"],
    )

    fields = {f.name: f.value for f in embed.fields}
    assert any("Checked in" in f.name for f in embed.fields)
    assert "Updates" in fields


def test_confirmation_embed_updates_field_snapshot():
    match = {
        "Alliance": "K98",
        "ArkWeekendDate": date(2026, 3, 7),
        "MatchDay": "Sat",
        "MatchTimeUtc": time(11, 0),
        "SignupCloseUtc": datetime(2026, 3, 6, 23, 0),
        "Notes": None,
    }
    roster = [
        {"GovernorNameSnapshot": "Player 1", "SlotType": "Player", "CheckedIn": 1},
        {"GovernorNameSnapshot": "Player 2", "SlotType": "Player"},
        {"GovernorNameSnapshot": "Sub 1", "SlotType": "Sub"},
    ]
    updates = ["Emergency withdraw: Player 2 (222)"]

    embed = build_ark_confirmation_embed_from_match(
        match,
        players_cap=30,
        subs_cap=15,
        roster=roster,
        updates=updates,
    )

    fields = {f.name: f.value for f in embed.fields}
    assert "Updates" in fields
    assert "Emergency withdraw" in fields["Updates"]
