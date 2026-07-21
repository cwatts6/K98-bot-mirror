from __future__ import annotations

from datetime import UTC, datetime, timedelta

from reminder_domain.projection import (
    ReminderAlertCandidate,
    ReminderProjectionHealth,
    ReminderProjectionSystem,
    ReminderSourceProjection,
    combine_reminder_projections,
)

NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


def _candidate(system: ReminderProjectionSystem, *, identity: str, hours: int):
    at = NOW + timedelta(hours=hours)
    return ReminderAlertCandidate(
        system=system,
        event_identity=identity,
        event_key="event",
        event_label="Friendly event",
        lead_time_key="24h",
        alert_at_utc=at,
        scheduled_for_utc=at,
        event_start_at_utc=at + timedelta(hours=24),
    )


def test_selects_earliest_across_systems() -> None:
    result = combine_reminder_projections(
        kvk=ReminderSourceProjection.healthy(
            (_candidate(ReminderProjectionSystem.KVK, identity="kvk", hours=3),)
        ),
        calendar=ReminderSourceProjection.healthy(
            (_candidate(ReminderProjectionSystem.CALENDAR, identity="cal", hours=2),)
        ),
        now_utc=NOW,
    )

    assert result.next_alert is not None
    assert result.next_alert.event_identity == "cal"


def test_deterministic_tie_break_prefers_kvk_then_identity() -> None:
    result = combine_reminder_projections(
        kvk=ReminderSourceProjection.healthy(
            (_candidate(ReminderProjectionSystem.KVK, identity="z", hours=2),)
        ),
        calendar=ReminderSourceProjection.healthy(
            (_candidate(ReminderProjectionSystem.CALENDAR, identity="a", hours=2),)
        ),
        now_utc=NOW,
    )

    assert result.next_alert is not None
    assert result.next_alert.system is ReminderProjectionSystem.KVK


def test_required_source_failure_wins_over_other_source_candidate() -> None:
    result = combine_reminder_projections(
        kvk=ReminderSourceProjection.unavailable("KVK unavailable"),
        calendar=ReminderSourceProjection.healthy(
            (_candidate(ReminderProjectionSystem.CALENDAR, identity="cal", hours=2),)
        ),
        now_utc=NOW,
    )

    assert result.health is ReminderProjectionHealth.UNAVAILABLE
    assert result.next_alert is None


def test_past_candidates_are_never_selected() -> None:
    past = _candidate(ReminderProjectionSystem.KVK, identity="past", hours=-1)
    result = combine_reminder_projections(
        kvk=ReminderSourceProjection.healthy((past,)),
        calendar=ReminderSourceProjection.healthy(),
        now_utc=NOW,
    )

    assert result.next_alert is None
