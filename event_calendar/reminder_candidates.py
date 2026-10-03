"""Pure Calendar reminder eligibility shared by dispatch and projection."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from event_calendar.reminder_prefs import is_dm_allowed, normalize_prefs
from event_calendar.reminder_state import make_key
from event_calendar.reminder_types import REMINDER_OFFSET_TO_DELTA
from event_calendar.runtime_cache import filter_events
from reminder_domain.projection import (
    ReminderAlertCandidate,
    ReminderProjectionSystem,
    ReminderSourceProjection,
    as_utc,
)


class CalendarWindowPhase(StrEnum):
    FUTURE = "FUTURE"
    DUE = "DUE"
    EXPIRED = "EXPIRED"


class CalendarEligibility(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    ALREADY_SENT = "ALREADY_SENT"
    PREFS_EXCLUDED = "PREFS_EXCLUDED"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"
    MISSING_INSTANCE = "MISSING_INSTANCE"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class CalendarOffsetWindow:
    event: Mapping[str, Any]
    reminder_type: str
    scheduled_for_utc: datetime
    event_start_at_utc: datetime
    phase: CalendarWindowPhase


@dataclass(frozen=True, slots=True)
class CalendarAlertEvaluation:
    window: CalendarOffsetWindow
    eligibility: CalendarEligibility
    key: str | None = None
    candidate: ReminderAlertCandidate | None = None


def parse_event_start_utc(event: Mapping[str, Any]) -> datetime | None:
    raw = str(event.get("start_utc") or "").strip()
    if not raw:
        return None
    try:
        return as_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
    except Exception:
        return None


def event_display_name(event: Mapping[str, Any]) -> str:
    title = str(event.get("title") or event.get("Title") or "(untitled)").strip()
    variant = str(event.get("variant") or event.get("Variant") or "").strip()
    return f"{title} ({variant})" if variant else title


def filter_calendar_dispatch_events(
    events: list[dict[str, Any]],
    *,
    now_utc: datetime,
    filterer: Callable[..., list[dict[str, Any]]] = filter_events,
) -> list[dict[str, Any]]:
    """Apply the exact occurrence horizon used by live Calendar dispatch."""

    now = as_utc(now_utc)
    return filterer(
        events,
        now=now - timedelta(days=7),
        days=365,
        event_type="all",
        importance="all",
    )


def collect_calendar_offset_windows(
    *,
    events: Sequence[Mapping[str, Any]],
    now_utc: datetime,
    grace: timedelta,
) -> tuple[CalendarOffsetWindow, ...]:
    now = as_utc(now_utc)
    windows: list[CalendarOffsetWindow] = []
    for event in events:
        start = parse_event_start_utc(event)
        if start is None:
            continue
        for reminder_type, delta in REMINDER_OFFSET_TO_DELTA.items():
            scheduled_for = start - delta
            if now < scheduled_for:
                phase = CalendarWindowPhase.FUTURE
            elif now - scheduled_for <= grace:
                phase = CalendarWindowPhase.DUE
            else:
                phase = CalendarWindowPhase.EXPIRED
            windows.append(
                CalendarOffsetWindow(
                    event=event,
                    reminder_type=reminder_type,
                    scheduled_for_utc=scheduled_for,
                    event_start_at_utc=start,
                    phase=phase,
                )
            )
    return tuple(windows)


def evaluate_calendar_alert_windows(
    *,
    windows: Sequence[CalendarOffsetWindow],
    user_id: int,
    prefs: Mapping[str, Any] | None,
    known_event_types: set[str],
    sent_keys: Mapping[str, str] | set[str],
    now_utc: datetime,
) -> tuple[CalendarAlertEvaluation, ...]:
    """Evaluate preferences and duplicate keys without reads or writes."""

    now = as_utc(now_utc)
    normalized = normalize_prefs(dict(prefs) if isinstance(prefs, Mapping) else None)
    sent = set(sent_keys)
    evaluations: list[CalendarAlertEvaluation] = []

    for window in windows:
        event = window.event
        event_type = str(event.get("type") or "").strip().lower()
        if event_type not in known_event_types:
            evaluations.append(CalendarAlertEvaluation(window, CalendarEligibility.UNKNOWN_TYPE))
            continue
        instance_id = str(event.get("instance_id") or "").strip()
        if not instance_id:
            evaluations.append(
                CalendarAlertEvaluation(window, CalendarEligibility.MISSING_INSTANCE)
            )
            continue
        key = make_key(instance_id, int(user_id), window.reminder_type)
        if key in sent:
            evaluations.append(
                CalendarAlertEvaluation(
                    window,
                    CalendarEligibility.ALREADY_SENT,
                    key=key,
                )
            )
            continue
        try:
            allowed = is_dm_allowed(
                reminder_type=window.reminder_type,
                event_type=event_type,
                prefs=normalized,
                known_event_types=known_event_types,
            )
        except ValueError:
            evaluations.append(
                CalendarAlertEvaluation(window, CalendarEligibility.UNKNOWN_TYPE, key=key)
            )
            continue
        if not allowed:
            evaluations.append(
                CalendarAlertEvaluation(window, CalendarEligibility.PREFS_EXCLUDED, key=key)
            )
            continue
        if window.phase is CalendarWindowPhase.EXPIRED:
            evaluations.append(
                CalendarAlertEvaluation(window, CalendarEligibility.EXPIRED, key=key)
            )
            continue

        candidate = ReminderAlertCandidate(
            system=ReminderProjectionSystem.CALENDAR,
            event_identity=instance_id,
            event_key=event_type,
            event_label=event_display_name(event),
            lead_time_key=window.reminder_type,
            alert_at_utc=max(now, window.scheduled_for_utc),
            scheduled_for_utc=window.scheduled_for_utc,
            event_start_at_utc=window.event_start_at_utc,
        )
        evaluations.append(
            CalendarAlertEvaluation(
                window,
                CalendarEligibility.ELIGIBLE,
                key=key,
                candidate=candidate,
            )
        )
    return tuple(evaluations)


def build_calendar_alert_projection(
    *,
    events: list[dict[str, Any]],
    user_id: int,
    prefs: Mapping[str, Any] | None,
    known_event_types: set[str],
    sent_keys: Mapping[str, str] | set[str],
    now_utc: datetime,
    grace: timedelta,
    source_available: bool = True,
) -> ReminderSourceProjection:
    if not source_available:
        return ReminderSourceProjection.unavailable("Calendar runtime cache unavailable")

    filtered = filter_calendar_dispatch_events(events, now_utc=now_utc)
    windows = collect_calendar_offset_windows(events=filtered, now_utc=now_utc, grace=grace)
    evaluations = evaluate_calendar_alert_windows(
        windows=windows,
        user_id=user_id,
        prefs=prefs,
        known_event_types=known_event_types,
        sent_keys=sent_keys,
        now_utc=now_utc,
    )
    candidates = tuple(
        evaluation.candidate
        for evaluation in evaluations
        if evaluation.eligibility is CalendarEligibility.ELIGIBLE
        and evaluation.candidate is not None
    )
    selected = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.eligibility
        in {
            CalendarEligibility.ELIGIBLE,
            CalendarEligibility.ALREADY_SENT,
            CalendarEligibility.EXPIRED,
        }
    )
    warning_windows_passed = (
        bool(selected)
        and not candidates
        and all(evaluation.window.phase is CalendarWindowPhase.EXPIRED for evaluation in selected)
    )
    return ReminderSourceProjection.healthy(
        candidates,
        warning_windows_passed=warning_windows_passed,
    )
