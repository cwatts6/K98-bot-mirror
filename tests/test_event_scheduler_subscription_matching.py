from __future__ import annotations

import event_scheduler


def test_is_fight_event_matches_altars_and_major_fight_titles() -> None:
    altar = {"type": "altar", "name": "Altar Fight"}
    major_fight = {"type": "major", "name": "Pass 4 FIGHT (Fixed Time)"}
    major_non_fight = {"type": "major", "name": "Crusader Fortress"}
    ruins = {"type": "ruins", "name": "Ruins"}

    assert event_scheduler.is_fight_event(altar) is True
    assert event_scheduler.is_fight_event(major_fight) is True
    assert event_scheduler.is_fight_event(major_non_fight) is False
    assert event_scheduler.is_fight_event(ruins) is False


def test_fights_subscription_does_not_match_non_fight_major_events() -> None:
    altar = {"type": "altar", "name": "Altar Fight"}
    major_fight = {"type": "major", "name": "Pass 4 FIGHT (Fixed Time)"}
    major_non_fight = {"type": "major", "name": "Crusader Fortress"}

    assert event_scheduler.subscription_matches_event(["fights"], altar) is True
    assert event_scheduler.subscription_matches_event(["fights"], major_fight) is True
    assert event_scheduler.subscription_matches_event(["fights"], major_non_fight) is False


def test_major_and_fights_subscription_covers_all_major_and_altars_once() -> None:
    altar = {"type": "altar", "name": "Altar Fight"}
    major_fight = {"type": "major", "name": "Pass 4 FIGHT (Fixed Time)"}
    major_non_fight = {"type": "major", "name": "Crusader Fortress"}
    ruins = {"type": "ruins", "name": "Ruins"}

    selected = ["major", "fights"]

    assert event_scheduler.subscription_matches_event(selected, altar) is True
    assert event_scheduler.subscription_matches_event(selected, major_fight) is True
    assert event_scheduler.subscription_matches_event(selected, major_non_fight) is True
    assert event_scheduler.subscription_matches_event(selected, ruins) is False


def test_ruins_major_and_fights_cover_the_player_visible_event_categories() -> None:
    selected = ["ruins", "major", "fights"]
    events = [
        {"type": "ruins", "name": "Ruins"},
        {"type": "altar", "name": "Altar Fight"},
        {"type": "major", "name": "Pass 4 FIGHT (Fixed Time)"},
        {"type": "major", "name": "Crusader Fortress"},
    ]

    assert all(event_scheduler.subscription_matches_event(selected, event) for event in events)
