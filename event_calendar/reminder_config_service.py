from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from event_calendar.reminder_prefs import normalize_prefs
from event_calendar.reminder_prefs_store import get_user_prefs, set_user_prefs
from event_calendar.reminder_types import REMINDER_OFFSETS_ORDERED, expand_offsets
from event_calendar.runtime_cache import list_event_types, load_runtime_cache

logger = logging.getLogger(__name__)


PrefsLoader = Callable[[int], dict[str, Any]]
PrefsWriter = Callable[[int, dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class CalendarReminderConfigState:
    enabled: bool
    selected_types: tuple[str, ...]
    selected_offsets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CalendarReminderMutationResult:
    ok: bool
    message: str
    state: CalendarReminderConfigState | None = None
    prefs: dict[str, Any] | None = None


def _normalize_type_selection(selected: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    values = tuple(sorted({str(value).strip().lower() for value in selected if str(value).strip()}))
    if "all" in values:
        return ("all",)
    return values


def _ordered_offsets(selected: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    expanded = expand_offsets({str(value).strip().lower() for value in selected})
    ordered = tuple(offset for offset in REMINDER_OFFSETS_ORDERED if offset in expanded)
    extras = tuple(sorted(expanded - set(ordered)))
    return ordered + extras


def known_calendar_event_types() -> tuple[str, ...]:
    cache_state = load_runtime_cache()
    if not cache_state.get("ok"):
        return ()
    return tuple(sorted({event_type for event_type in list_event_types(cache_state) if event_type}))


def state_from_prefs(prefs: dict[str, Any] | None) -> CalendarReminderConfigState:
    normalized = normalize_prefs(prefs)
    by_type = normalized.get("by_event_type", {}) or {}
    selected_types = _normalize_type_selection(tuple(by_type.keys()))
    selected_offsets: set[str] = set()
    for values in by_type.values():
        if isinstance(values, (list, tuple, set)):
            selected_offsets.update(str(value).strip().lower() for value in values)

    return CalendarReminderConfigState(
        enabled=bool(normalized.get("enabled", False)),
        selected_types=selected_types,
        selected_offsets=_ordered_offsets(tuple(selected_offsets)),
    )


def load_user_calendar_reminder_state(
    user_id: int,
    *,
    prefs_loader: PrefsLoader = get_user_prefs,
) -> CalendarReminderConfigState:
    return state_from_prefs(prefs_loader(int(user_id)))


def compose_prefs_payload(
    *,
    enabled: bool,
    selected_types: list[str] | tuple[str, ...] | set[str],
    selected_offsets: list[str] | tuple[str, ...] | set[str],
    known_event_types: list[str] | tuple[str, ...] | set[str],
) -> dict[str, Any]:
    types = _normalize_type_selection(selected_types)
    offsets = _ordered_offsets(selected_offsets)
    known = {str(value).strip().lower() for value in known_event_types if str(value).strip()}

    if not types:
        raise ValueError("Select at least one event type before saving.")
    if not offsets:
        raise ValueError("Select at least one reminder offset before saving.")

    invalid = [
        event_type
        for event_type in types
        if known and event_type != "all" and event_type not in known
    ]
    if invalid:
        raise ValueError(f"Unknown calendar event type: {', '.join(invalid)}")

    return {
        "enabled": bool(enabled),
        "by_event_type": {event_type: list(offsets) for event_type in types},
    }


def save_user_calendar_reminder_preferences(
    user_id: int,
    *,
    enabled: bool,
    selected_types: list[str] | tuple[str, ...] | set[str],
    selected_offsets: list[str] | tuple[str, ...] | set[str],
    known_event_types: list[str] | tuple[str, ...] | set[str],
    writer: PrefsWriter = set_user_prefs,
) -> CalendarReminderMutationResult:
    try:
        payload = compose_prefs_payload(
            enabled=enabled,
            selected_types=selected_types,
            selected_offsets=selected_offsets,
            known_event_types=known_event_types,
        )
    except ValueError as exc:
        return CalendarReminderMutationResult(ok=False, message=str(exc))

    try:
        writer(int(user_id), payload)
    except Exception:
        logger.exception(
            "calendar_reminder_preferences_save_failed user_id=%s enabled=%s types=%s offsets=%s",
            user_id,
            enabled,
            sorted(str(value) for value in selected_types),
            sorted(str(value) for value in selected_offsets),
        )
        return CalendarReminderMutationResult(
            ok=False,
            message="Failed to save calendar reminders. Please try again in a moment.",
        )

    state = state_from_prefs(payload)
    logger.info(
        "calendar_reminder_preferences_saved user_id=%s enabled=%s types=%s offsets=%s",
        user_id,
        state.enabled,
        list(state.selected_types),
        list(state.selected_offsets),
    )
    status = "enabled" if state.enabled else "saved disabled"
    return CalendarReminderMutationResult(
        ok=True,
        message=f"Calendar reminder preferences {status}.",
        state=state,
        prefs=payload,
    )
