"""Shared typed contracts for side-effect-free reminder alert projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class ReminderProjectionSystem(StrEnum):
    KVK = "KVK"
    CALENDAR = "CALENDAR"


class ReminderProjectionHealth(StrEnum):
    HEALTHY = "HEALTHY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ReminderAlertCandidate:
    """One alert that live dispatch still considers pending.

    ``scheduled_for_utc`` preserves the scheduler's original warning instant.
    ``alert_at_utc`` is the next actionable instant and is never before the
    injected projection clock; late/immediate scheduler behavior therefore
    cannot leak a past timestamp into the player card.
    """

    system: ReminderProjectionSystem
    event_identity: str
    event_key: str
    event_label: str
    lead_time_key: str
    alert_at_utc: datetime
    scheduled_for_utc: datetime
    event_start_at_utc: datetime
    pending_scheduled: bool = False


@dataclass(frozen=True, slots=True)
class ReminderSourceProjection:
    health: ReminderProjectionHealth
    candidates: tuple[ReminderAlertCandidate, ...] = ()
    warning_windows_passed: bool = False
    error: str | None = None

    @classmethod
    def healthy(
        cls,
        candidates: tuple[ReminderAlertCandidate, ...] = (),
        *,
        warning_windows_passed: bool = False,
    ) -> ReminderSourceProjection:
        return cls(
            health=ReminderProjectionHealth.HEALTHY,
            candidates=candidates,
            warning_windows_passed=warning_windows_passed,
        )

    @classmethod
    def unavailable(cls, error: str) -> ReminderSourceProjection:
        return cls(health=ReminderProjectionHealth.UNAVAILABLE, error=error)


@dataclass(frozen=True, slots=True)
class ReminderProjectionResult:
    health: ReminderProjectionHealth
    next_alert: ReminderAlertCandidate | None = None
    warning_windows_passed: bool = False
    errors: tuple[str, ...] = ()


_SYSTEM_ORDER = {
    ReminderProjectionSystem.KVK: 0,
    ReminderProjectionSystem.CALENDAR: 1,
}

_LEAD_TIME_ORDER = {
    "7d": 0,
    "3d": 1,
    "24h": 2,
    "12h": 3,
    "4h": 4,
    "1h": 5,
    "now": 6,
    "start": 6,
    "at_start": 6,
}


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _candidate_key(candidate: ReminderAlertCandidate) -> tuple[object, ...]:
    return (
        as_utc(candidate.alert_at_utc),
        _SYSTEM_ORDER[candidate.system],
        as_utc(candidate.event_start_at_utc),
        candidate.event_identity,
        _LEAD_TIME_ORDER.get(candidate.lead_time_key, 999),
        candidate.lead_time_key,
    )


def combine_reminder_projections(
    *,
    kvk: ReminderSourceProjection,
    calendar: ReminderSourceProjection,
    now_utc: datetime,
) -> ReminderProjectionResult:
    """Choose the deterministic earliest candidate across both live domains."""

    now = as_utc(now_utc)
    sources = (kvk, calendar)
    errors = tuple(
        source.error or "projection unavailable"
        for source in sources
        if source.health is ReminderProjectionHealth.UNAVAILABLE
    )
    if errors:
        return ReminderProjectionResult(
            health=ReminderProjectionHealth.UNAVAILABLE,
            errors=errors,
        )

    candidates = tuple(
        candidate
        for source in sources
        for candidate in source.candidates
        if as_utc(candidate.alert_at_utc) >= now
    )
    next_alert = min(candidates, key=_candidate_key) if candidates else None
    return ReminderProjectionResult(
        health=ReminderProjectionHealth.HEALTHY,
        next_alert=next_alert,
        warning_windows_passed=(
            next_alert is None and any(source.warning_windows_passed for source in sources)
        ),
    )
