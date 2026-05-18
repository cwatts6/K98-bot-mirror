from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from event_calendar.reminder_prefs import (
    default_prefs,
    is_dm_allowed,
    normalize_prefs,
    remove_offsets_for_event_type,
    set_enabled,
    set_offsets_for_event_type,
)
from event_calendar.reminder_state import CalendarReminderState, make_key
from event_calendar.reminder_types import REMINDER_3D, REMINDER_7D, REMINDER_24H, REMINDER_START

KNOWN = {"raid", "war", "alliance"}


def test_default_prefs_opt_in_disabled():
    p = default_prefs()
    assert p["enabled"] is False
    assert p["by_event_type"] == {}


def test_unknown_event_type_rejected():
    with pytest.raises(ValueError):
        is_dm_allowed(
            reminder_type=REMINDER_24H,
            event_type="nonsense",
            prefs=default_prefs(),
            known_event_types=KNOWN,
        )


def test_enable_all_offsets_global_then_allowed():
    p = default_prefs()
    p = set_enabled(p, True)
    p = set_offsets_for_event_type(
        p,
        event_type="all",
        offsets=["all"],
        known_event_types=KNOWN,
    )

    assert is_dm_allowed(
        reminder_type=REMINDER_7D,
        event_type="raid",
        prefs=p,
        known_event_types=KNOWN,
    )
    assert is_dm_allowed(
        reminder_type=REMINDER_START,
        event_type="war",
        prefs=p,
        known_event_types=KNOWN,
    )


def test_event_specific_overrides_work():
    p = default_prefs()
    p = set_enabled(p, True)
    p = set_offsets_for_event_type(
        p,
        event_type="raid",
        offsets=[REMINDER_24H, REMINDER_3D],
        known_event_types=KNOWN,
    )

    assert is_dm_allowed(
        reminder_type=REMINDER_24H,
        event_type="raid",
        prefs=p,
        known_event_types=KNOWN,
    )
    assert not is_dm_allowed(
        reminder_type=REMINDER_24H,
        event_type="war",
        prefs=p,
        known_event_types=KNOWN,
    )


def test_remove_offsets():
    p = default_prefs()
    p = set_enabled(p, True)
    p = set_offsets_for_event_type(
        p,
        event_type="raid",
        offsets=[REMINDER_24H, REMINDER_3D],
        known_event_types=KNOWN,
    )
    p = remove_offsets_for_event_type(
        p,
        event_type="raid",
        offsets=[REMINDER_3D],
        known_event_types=KNOWN,
    )

    assert is_dm_allowed(
        reminder_type=REMINDER_24H,
        event_type="raid",
        prefs=p,
        known_event_types=KNOWN,
    )
    assert not is_dm_allowed(
        reminder_type=REMINDER_3D,
        event_type="raid",
        prefs=p,
        known_event_types=KNOWN,
    )


def test_state_make_key_and_grace(tmp_path):
    path = tmp_path / "state.json"
    st = CalendarReminderState.load(path=path)
    k = make_key("evt-1", 123, REMINDER_24H)

    scheduled = datetime.now(UTC) - timedelta(minutes=5)
    assert st.should_send_with_grace(key=k, scheduled_for=scheduled) is True

    st.mark_sent(k)
    assert st.was_sent(k) is True
    assert st.should_send_with_grace(key=k, scheduled_for=scheduled) is False


def test_state_round_trip(tmp_path):
    path = tmp_path / "state.json"
    st = CalendarReminderState.load(path=path)
    k = make_key("evt-2", 456, REMINDER_START)
    st.mark_sent(k)
    st.save()

    loaded = CalendarReminderState.load(path=path)
    assert loaded.was_sent(k) is True
    assert loaded.sent_at(k) is not None


def test_normalize_prefs_invalid_shape():
    p = normalize_prefs({"enabled": "yes", "by_event_type": "bad"})
    assert p["enabled"] is True
    assert p["by_event_type"] == {}
