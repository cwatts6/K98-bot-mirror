from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from event_calendar.reminder_candidates import (
    CalendarEligibility,
    CalendarWindowPhase,
    build_calendar_alert_projection,
    collect_calendar_offset_windows,
    evaluate_calendar_alert_windows,
)
from event_calendar.reminder_state import make_key
from reminder_domain.projection import ReminderProjectionHealth

NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
GRACE = timedelta(minutes=15)


def _event(
    instance_id: str,
    *,
    start: datetime,
    event_type: str = "raid",
    title: str = "Ark of Osiris",
) -> dict:
    return {
        "instance_id": instance_id,
        "title": title,
        "variant": "League",
        "type": event_type,
        "start_utc": start.isoformat(),
        "end_utc": (start + timedelta(hours=1)).isoformat(),
    }


def _project(*, events, prefs, sent=None, available=True):
    return build_calendar_alert_projection(
        events=events,
        user_id=42,
        prefs=prefs,
        known_event_types={"raid", "ceroli"},
        sent_keys=sent or {},
        now_utc=NOW,
        grace=GRACE,
        source_available=available,
    )


def test_global_and_specific_preferences_select_only_their_offsets() -> None:
    raid = _event("raid-1", start=NOW + timedelta(days=2))
    ceroli = _event(
        "ceroli-1",
        start=NOW + timedelta(days=4),
        event_type="ceroli",
        title="Ceroli Crisis",
    )

    global_result = _project(
        events=[raid, ceroli],
        prefs={"enabled": True, "by_event_type": {"all": ["24h"]}},
    )
    specific_result = _project(
        events=[raid, ceroli],
        prefs={"enabled": True, "by_event_type": {"raid": ["24h"]}},
    )

    assert [(c.event_key, c.lead_time_key) for c in global_result.candidates] == [
        ("raid", "24h"),
        ("ceroli", "24h"),
    ]
    assert [(c.event_key, c.lead_time_key) for c in specific_result.candidates] == [("raid", "24h")]


def test_due_window_within_grace_retries_until_sent_key_exists() -> None:
    event = _event("raid-due", start=NOW + timedelta(hours=24) - timedelta(minutes=10))
    windows = collect_calendar_offset_windows(events=[event], now_utc=NOW, grace=GRACE)
    due_24h = tuple(
        window
        for window in windows
        if window.reminder_type == "24h" and window.phase is CalendarWindowPhase.DUE
    )
    prefs = {"enabled": True, "by_event_type": {"raid": ["24h"]}}

    first = evaluate_calendar_alert_windows(
        windows=due_24h,
        user_id=42,
        prefs=prefs,
        known_event_types={"raid"},
        sent_keys={},
        now_utc=NOW,
    )
    sent_key = make_key("raid-due", 42, "24h")
    after_success = evaluate_calendar_alert_windows(
        windows=due_24h,
        user_id=42,
        prefs=prefs,
        known_event_types={"raid"},
        sent_keys={sent_key: NOW.isoformat()},
        now_utc=NOW,
    )

    assert first[0].eligibility is CalendarEligibility.ELIGIBLE
    assert first[0].candidate is not None
    assert first[0].candidate.alert_at_utc == NOW
    assert after_success[0].eligibility is CalendarEligibility.ALREADY_SENT


def test_expired_grace_window_is_not_a_candidate_and_reports_passed_windows() -> None:
    event = _event("raid-expired", start=NOW + timedelta(hours=24) - timedelta(minutes=16))

    result = _project(
        events=[event],
        prefs={"enabled": True, "by_event_type": {"raid": ["24h"]}},
    )

    assert result.candidates == ()
    assert result.warning_windows_passed is True


def test_calendar_start_offset_is_a_future_at_start_candidate() -> None:
    event = _event("raid-start", start=NOW + timedelta(hours=2))

    result = _project(
        events=[event],
        prefs={"enabled": True, "by_event_type": {"raid": ["start"]}},
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].lead_time_key == "start"
    assert result.candidates[0].alert_at_utc == NOW + timedelta(hours=2)


def test_unknown_event_type_and_disabled_preferences_are_not_candidates() -> None:
    unknown = _event("unknown", start=NOW + timedelta(days=2), event_type="retired")
    known = _event("known", start=NOW + timedelta(days=2))

    unknown_result = _project(
        events=[unknown],
        prefs={"enabled": True, "by_event_type": {"all": ["24h"]}},
    )
    disabled_result = _project(
        events=[known],
        prefs={"enabled": False, "by_event_type": {"all": ["24h"]}},
    )

    assert unknown_result.candidates == ()
    assert disabled_result.candidates == ()


def test_projection_is_side_effect_free_and_source_health_is_explicit() -> None:
    event = _event("raid-safe", start=NOW + timedelta(days=2))
    prefs = {"enabled": True, "by_event_type": {"raid": ["24h"]}}
    sent: dict[str, str] = {}
    before = deepcopy((event, prefs, sent))

    healthy = _project(events=[event], prefs=prefs, sent=sent)
    unavailable = _project(events=[], prefs=prefs, available=False)

    assert healthy.health is ReminderProjectionHealth.HEALTHY
    assert unavailable.health is ReminderProjectionHealth.UNAVAILABLE
    assert (event, prefs, sent) == before
