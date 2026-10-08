from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from reminder_domain.kvk_candidates import build_kvk_alert_projection, make_event_id
from reminder_domain.projection import ReminderProjectionHealth

NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


def _event(*, hours: float, event_type: str = "ruins", name: str = "Ancient Ruins") -> dict:
    start = NOW + timedelta(hours=hours)
    return {
        "name": name,
        "type": event_type,
        "start_time": start,
        "end_time": start + timedelta(minutes=30),
    }


def _project(
    *,
    events: list[dict],
    times: list[str],
    subscriptions: list[str] | None = None,
    sent: dict | None = None,
    scheduled: dict | None = None,
    available: bool = True,
):
    return build_kvk_alert_projection(
        events=events,
        config={
            "subscriptions": subscriptions or ["ruins"],
            "reminder_times": times,
        },
        user_id=42,
        sent_tracker=sent or {},
        scheduled_tracker=scheduled or {},
        now_utc=NOW,
        source_available=available,
    )


def test_authorized_now_offset_is_a_genuine_at_start_candidate() -> None:
    event = _event(hours=6)

    result = _project(events=[event], times=["now"])

    assert result.health is ReminderProjectionHealth.HEALTHY
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.lead_time_key == "now"
    assert candidate.alert_at_utc == event["start_time"]
    assert candidate.scheduled_for_utc == event["start_time"]


def test_sent_is_excluded_but_scheduled_future_alert_remains_pending() -> None:
    event = _event(hours=30)
    event_id = make_event_id(event)
    delta_24h = int(timedelta(hours=24).total_seconds())
    delta_4h = int(timedelta(hours=4).total_seconds())

    result = _project(
        events=[event],
        times=["24h", "4h"],
        sent={event_id: {"42": [delta_24h]}},
        scheduled={event_id: {"42": {delta_4h}}},
    )

    assert [candidate.lead_time_key for candidate in result.candidates] == ["4h"]
    assert result.candidates[0].pending_scheduled is True
    assert result.candidates[0].alert_at_utc == NOW + timedelta(hours=26)


def test_passed_warning_is_immediate_and_never_projects_a_past_timestamp() -> None:
    event = _event(hours=2)

    result = _project(events=[event], times=["24h"])

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.scheduled_for_utc == NOW - timedelta(hours=22)
    assert candidate.alert_at_utc == NOW


def test_exact_48_hour_horizon_is_included_and_later_event_is_excluded() -> None:
    result = _project(
        events=[_event(hours=48, name="Boundary"), _event(hours=48.01, name="Outside")],
        times=["24h"],
    )

    assert [candidate.event_label for candidate in result.candidates] == ["Boundary"]


def test_fights_subscription_matches_only_authoritative_fight_occurrences() -> None:
    altar = _event(hours=10, event_type="altar", name="Altar Fight")
    fight = _event(hours=12, event_type="major", name="Pass 4 FIGHT")
    non_fight = _event(hours=14, event_type="major", name="Crusader Fortress")

    result = _project(
        events=[altar, fight, non_fight],
        times=["4h"],
        subscriptions=["fights"],
    )

    assert [candidate.event_label for candidate in result.candidates] == [
        "Altar Fight",
        "Pass 4 FIGHT",
    ]


def test_projection_is_side_effect_free_and_tolerates_malformed_tracker_values() -> None:
    event = _event(hours=30)
    event_id = make_event_id(event)
    sent = {event_id: {"42": ["not-a-number"]}}
    scheduled = {event_id: {"42": []}}
    before = deepcopy((event, sent, scheduled))

    result = _project(
        events=[event],
        times=["24h"],
        sent=sent,
        scheduled=scheduled,
    )

    assert len(result.candidates) == 1
    assert (event, sent, scheduled) == before


def test_unavailable_source_is_explicit_and_healthy_empty_is_distinct() -> None:
    unavailable = _project(events=[], times=["24h"], available=False)
    healthy_empty = _project(events=[], times=["24h"], available=True)

    assert unavailable.health is ReminderProjectionHealth.UNAVAILABLE
    assert healthy_empty.health is ReminderProjectionHealth.HEALTHY
    assert healthy_empty.candidates == ()
