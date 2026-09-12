"""Pure KVK reminder eligibility shared by live dispatch and read-only projection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any

from constants import DEFAULT_REMINDER_TIMES, REMINDER_MAP
from event_utils import serialize_event
from reminder_domain.projection import (
    ReminderAlertCandidate,
    ReminderProjectionSystem,
    ReminderSourceProjection,
    as_utc,
)

KVK_SCHEDULING_HORIZON = timedelta(hours=48)
_SUPPORTED_EVENT_TYPES = {"ruins", "altars", "major", "chronicle"}


def normalized_event_type(event: Mapping[str, Any]) -> str:
    raw = str(event.get("type") or "").lower().strip()
    return {
        "next ruins": "ruins",
        "ruins": "ruins",
        "next altar fight": "altars",
        "altar": "altars",
        "altars": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }.get(raw, raw)


def is_fight_event(event: Mapping[str, Any]) -> bool:
    event_type = normalized_event_type(event)
    event_text = " ".join(
        str(event.get(key) or "").upper() for key in ("name", "title", "description")
    )
    return event_type == "altars" or (event_type == "major" and "FIGHT" in event_text)


def subscription_matches_event(subscribed_types: Sequence[str], event: Mapping[str, Any]) -> bool:
    selected = {str(event_type).lower().strip() for event_type in subscribed_types}
    event_type = normalized_event_type(event)
    if "all" in selected:
        return event_type in {"ruins", "altars", "major"}
    if event_type in selected:
        return True
    return "fights" in selected and is_fight_event(event)


def make_event_id(event: Mapping[str, Any]) -> str:
    event_type = normalized_event_type(event)
    name_token = (
        str(event.get("name") or event.get("title") or "").strip().lower().replace(" ", "_")[:64]
    )
    try:
        timestamp = serialize_event(dict(event)).get("start_time")
    except Exception:
        raw = event.get("start_time")
        timestamp = as_utc(raw).isoformat() if isinstance(raw, datetime) else str(raw)
    return f"{event_type}:{name_token}:{timestamp}"


def _event_label(event: Mapping[str, Any], event_type: str) -> str:
    label = str(event.get("name") or event.get("title") or "").strip()
    if label:
        return label
    return {
        "ruins": "Ruins",
        "altars": "Altars",
        "major": "Major",
        "chronicle": "Chronicle",
    }.get(event_type, "KVK event")


def _tracker_values(
    tracker: Mapping[str, Mapping[str, Sequence[int]]],
    *,
    event_id: str,
    user_id: str,
) -> set[int]:
    values = tracker.get(event_id, {}).get(user_id, ())
    normalized: set[int] = set()
    for value in values:
        try:
            normalized.add(int(value))
        except (TypeError, ValueError):
            continue
    return normalized


def build_kvk_alert_projection(
    *,
    events: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any] | None,
    user_id: int | str,
    sent_tracker: Mapping[str, Mapping[str, Sequence[int]]],
    scheduled_tracker: Mapping[str, Mapping[str, set[int] | Sequence[int]]],
    now_utc: datetime,
    source_available: bool = True,
) -> ReminderSourceProjection:
    """Return all pending KVK candidates without mutating scheduler state."""

    if not source_available:
        return ReminderSourceProjection.unavailable("KVK event cache unavailable")

    raw_config = config if isinstance(config, Mapping) else {}
    subscribed_types = raw_config.get("subscriptions", [])
    reminder_times = raw_config.get("reminder_times", DEFAULT_REMINDER_TIMES)
    if not isinstance(subscribed_types, (list, tuple, set)) or not isinstance(
        reminder_times, (list, tuple, set)
    ):
        return ReminderSourceProjection.healthy()

    now = as_utc(now_utc)
    uid = str(user_id)
    candidates: list[ReminderAlertCandidate] = []

    for event in events:
        event_type = normalized_event_type(event)
        if event_type not in _SUPPORTED_EVENT_TYPES:
            continue
        raw_start = event.get("start_time")
        if not isinstance(raw_start, datetime):
            continue
        start = as_utc(raw_start)
        if start <= now or start - now > KVK_SCHEDULING_HORIZON:
            continue
        if not subscription_matches_event(tuple(str(value) for value in subscribed_types), event):
            continue

        event_id = make_event_id(event)
        sent_values = _tracker_values(
            sent_tracker,
            event_id=event_id,
            user_id=uid,
        )
        scheduled_values = _tracker_values(
            scheduled_tracker,
            event_id=event_id,
            user_id=uid,
        )
        for raw_reminder_time in reminder_times:
            reminder_time = str(raw_reminder_time).strip().lower()
            delta = REMINDER_MAP.get(reminder_time)
            # ``timedelta(0)`` is the authorized KVK at-start option, not a
            # missing mapping. Live dispatch and projection both use this rule.
            if delta is None:
                continue
            delta_seconds = int(delta.total_seconds())
            if delta_seconds in sent_values:
                continue
            scheduled_for = start - delta
            candidates.append(
                ReminderAlertCandidate(
                    system=ReminderProjectionSystem.KVK,
                    event_identity=event_id,
                    event_key=event_type,
                    event_label=_event_label(event, event_type),
                    lead_time_key=reminder_time,
                    alert_at_utc=max(now, scheduled_for),
                    scheduled_for_utc=scheduled_for,
                    event_start_at_utc=start,
                    pending_scheduled=delta_seconds in scheduled_values,
                )
            )

    return ReminderSourceProjection.healthy(tuple(candidates))
