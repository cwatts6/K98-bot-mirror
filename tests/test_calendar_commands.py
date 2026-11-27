from __future__ import annotations

from datetime import UTC, datetime, timedelta

from event_calendar import runtime_cache as rc
from event_calendar.reminder_prefs import (
    default_prefs,
    is_dm_allowed,
    remove_offsets_for_event_type,
    set_enabled,
    set_offsets_for_event_type,
)
from event_calendar.reminder_prefs_store import (
    get_user_prefs,
    load_all_user_prefs,
    save_all_user_prefs,
    set_user_prefs,
)
from event_calendar.reminder_types import expand_offsets
from ui.views.calendar import allowed_days, paginate


def _ev(i: int, days: int, et: str = "raid", imp: str = "high", title: str | None = None):
    start = datetime.now(UTC) + timedelta(days=days)
    end = start + timedelta(hours=1)
    return {
        "instance_id": str(i),
        "title": title or f"Event {i}",
        "type": et,
        "importance": imp,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "tags": ["kvk", "test"],
        "description": f"desc {i}",
    }


def test_paginate_basics():
    items = [
        {
            "instance_id": str(i),
            "title": f"e{i}",
            "type": "raid",
            "importance": "high",
            "start_utc": "2099-01-01T00:00:00+00:00",
            "end_utc": "2099-01-01T01:00:00+00:00",
        }
        for i in range(20)
    ]
    page_items, p, total = paginate(items, 1)
    assert p == 1
    assert total == 3
    assert len(page_items) == 8


def test_paginate_range_math():
    items = [{"instance_id": str(i)} for i in range(9)]
    page_items, p, total = paginate(items, 2)
    assert p == 2
    assert total == 2
    assert len(page_items) == 1


def test_filter_events_days_type_importance():
    now = datetime.now(UTC)
    events = [
        _ev(1, 1, et="raid", imp="high"),
        _ev(2, 5, et="raid", imp="low"),
        _ev(3, 1, et="war", imp="high"),
    ]

    out = rc.filter_events(events, now=now, days=3, event_type="raid", importance="high")
    assert len(out) == 1
    assert out[0]["instance_id"] == "1"


def test_next_event_by_type():
    now = datetime.now(UTC)
    events = [
        _ev(1, 2, et="raid"),
        _ev(2, 1, et="raid"),
        _ev(3, 1, et="war"),
    ]
    nxt = rc.next_event(events, now=now, event_type="raid")
    assert nxt is not None
    assert nxt["instance_id"] == "2"


def test_search_events_contains_starts_exact():
    now = datetime.now(UTC)
    events = [
        _ev(1, 1, title="Dragon Hunt"),
        _ev(2, 1, title="Dragon Siege"),
        _ev(3, 1, title="Farm Run"),
    ]

    c = rc.search_events(events, now=now, field="title", match="contains", query="dragon")
    s = rc.search_events(events, now=now, field="title", match="starts_with", query="dragon")
    e = rc.search_events(events, now=now, field="title", match="exact", query="dragon hunt")

    assert [x["instance_id"] for x in c] == ["1", "2"]
    assert [x["instance_id"] for x in s] == ["1", "2"]
    assert [x["instance_id"] for x in e] == ["1"]


def test_sort_events_deterministic_tiebreak():
    base = datetime.now(UTC) + timedelta(days=1)
    iso = base.isoformat()
    events = [
        {"instance_id": "2", "title": "B", "type": "raid", "start_utc": iso},
        {"instance_id": "1", "title": "A", "type": "raid", "start_utc": iso},
    ]
    out = rc.sort_events_deterministic(events)
    assert [x["instance_id"] for x in out] == ["1", "2"]


def test_list_types_and_importance():
    cache_state = {
        "events": [
            {"type": "Raid", "importance": "High"},
            {"type": "war", "importance": "low"},
            {"type": "", "importance": ""},
        ]
    }
    assert rc.list_event_types(cache_state) == ["raid", "war"]
    assert rc.list_importance_values(cache_state) == ["high", "low"]


def test_days_choices_alignment():
    assert 365 in allowed_days()
    assert 356 not in allowed_days()


def test_reminder_offsets_expand_all_token():
    out = expand_offsets(["all"])
    assert out == {"7d", "3d", "24h", "1h", "start"}


def test_reminder_offsets_expand_csv_tokens():
    out = expand_offsets(["24h", "start"])
    assert out == {"24h", "start"}


def test_reminder_enable_disable_known_type_logic():
    known = {"raid", "war"}

    prefs = default_prefs()
    prefs = set_enabled(prefs, True)
    prefs = set_offsets_for_event_type(
        prefs,
        event_type="raid",
        offsets=["24h", "start"],
        known_event_types=known,
    )

    assert (
        is_dm_allowed(
            reminder_type="24h",
            event_type="raid",
            prefs=prefs,
            known_event_types=known,
        )
        is True
    )

    prefs = remove_offsets_for_event_type(
        prefs,
        event_type="raid",
        offsets=["24h"],
        known_event_types=known,
    )

    assert (
        is_dm_allowed(
            reminder_type="24h",
            event_type="raid",
            prefs=prefs,
            known_event_types=known,
        )
        is False
    )


def test_reminder_unknown_type_rejected():
    known = {"raid", "war"}
    prefs = set_enabled(default_prefs(), True)

    import pytest

    with pytest.raises(ValueError):
        set_offsets_for_event_type(
            prefs,
            event_type="nonsense",
            offsets=["24h"],
            known_event_types=known,
        )


def test_reminder_prefs_store_round_trip(tmp_path, monkeypatch):
    from event_calendar import reminder_prefs_store as store_mod

    test_file = tmp_path / "event_calendar_reminder_prefs.json"
    monkeypatch.setattr(store_mod, "_REMINDER_PREFS_PATH", test_file)

    save_all_user_prefs({})
    all_rows = load_all_user_prefs()
    assert all_rows == {}

    uid = 123456
    prefs = set_enabled(default_prefs(), True)
    prefs = set_offsets_for_event_type(
        prefs,
        event_type="all",
        offsets=["all"],
        known_event_types={"raid", "war"},
    )
    set_user_prefs(uid, prefs)

    loaded = get_user_prefs(uid)
    assert loaded["enabled"] is True
    assert "all" in loaded["by_event_type"]
    assert set(loaded["by_event_type"]["all"]) == {"7d", "3d", "24h", "1h", "start"}
