"""Typed read-only summary contract for the premium ``/me reminders`` card."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum

from constants import DEFAULT_REMINDER_TIMES, REMINDER_MAP, VALID_TYPES
from event_calendar.reminder_types import REMINDER_OFFSET_TO_DELTA, REMINDER_OFFSETS_ORDERED
from event_calendar.runtime_cache import list_event_types, load_runtime_cache

KINGDOM_ID = 1198
MAX_VISIBLE_EVENTS = 3


class ReminderConfigurationState(StrEnum):
    ACTIVE = "ACTIVE"
    REVIEW = "REVIEW"
    OFF = "OFF"


class ReminderCompleteness(StrEnum):
    COMPLETE = "COMPLETE"
    MISSING_EVENTS = "MISSING_EVENTS"
    MISSING_TIMES = "MISSING_TIMES"
    MISSING_BOTH = "MISSING_BOTH"
    UNAVAILABLE_SELECTION = "UNAVAILABLE_SELECTION"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class ReminderHeroKind(StrEnum):
    NEXT_ALERT = "NEXT_ALERT"
    NO_UPCOMING = "NO_UPCOMING"
    COVERAGE = "COVERAGE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class CalendarEventCatalog:
    available: bool
    event_types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NextScheduledReminderAlert:
    system_label: str
    event_label: str
    lead_time_label: str
    alert_at_utc: datetime
    event_start_at_utc: datetime
    occurrence_identity: str


@dataclass(frozen=True, slots=True)
class ReminderHero:
    kind: ReminderHeroKind
    headline: str
    primary_line: str
    secondary_line: str = ""
    next_alert: NextScheduledReminderAlert | None = None


@dataclass(frozen=True, slots=True)
class ReminderSystemSummary:
    system_label: str
    enabled: bool
    completeness: ReminderCompleteness
    state_count_line: str
    selected_event_keys: tuple[str, ...]
    event_labels: tuple[str, ...]
    event_summary: str
    selected_event_count: int
    hidden_event_count: int
    unavailable_event_count: int
    selected_time_keys: tuple[str, ...]
    time_labels: tuple[str, ...]
    time_summary: str
    selected_time_count: int
    unavailable_time_count: int
    includes_start: bool
    longest_lead_label: str | None
    latest_alert_label: str | None
    coverage_label: str
    source_error: str | None = None


@dataclass(frozen=True, slots=True)
class RemindersSummaryPayload:
    viewer_discord_id: int
    display_name: str
    kingdom_id: int
    generated_at_utc: datetime
    configuration_state: ReminderConfigurationState
    state_supporting_text: str
    kvk: ReminderSystemSummary
    calendar: ReminderSystemSummary
    hero: ReminderHero
    insight: str
    warnings: tuple[str, ...] = ()


_KVK_EVENT_LABELS = {
    "ruins": "Ruins",
    "altars": "Altars",
    "major": "Major",
    "fights": "Fights",
    "all": "All KVK events",
}

_CALENDAR_EVENT_LABELS = {
    "20gh": "20 GH",
    "20_gh": "20 GH",
    "ark": "Ark of Osiris",
    "ark_of_osiris": "Ark of Osiris",
}

_TIME_LABELS = {
    "7d": "7d",
    "3d": "3d",
    "24h": "24h",
    "12h": "12h",
    "4h": "4h",
    "1h": "1h",
    "now": "At start",
    "start": "At start",
    "at_start": "At start",
}


def _clean_token(value: object) -> str:
    return str(value or "").strip().lower()


def _dedupe(values: Iterable[object]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = _clean_token(value)
        if token and token not in seen:
            seen.add(token)
            ordered.append(token)
    return tuple(ordered)


def _as_utc(value: datetime) -> datetime:
    """Normalize contract timestamps without treating naive UTC as host-local time."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def kvk_event_label(key: str) -> str:
    return _KVK_EVENT_LABELS.get(_clean_token(key), "Unavailable event")


def calendar_event_label(key: str) -> str:
    token = _clean_token(key)
    if not token:
        return "Unavailable event"
    special = _CALENDAR_EVENT_LABELS.get(token)
    if special:
        return special
    words = token.replace("-", "_").split("_")
    return " ".join(word.upper() if word.isdigit() else word.capitalize() for word in words if word)


def alert_time_label(key: str) -> str:
    return _TIME_LABELS.get(_clean_token(key), "Unavailable alert time")


def load_calendar_event_catalog() -> CalendarEventCatalog:
    cache = load_runtime_cache()
    if not cache.get("ok"):
        return CalendarEventCatalog(available=False, event_types=())
    return CalendarEventCatalog(
        available=True,
        event_types=tuple(list_event_types(cache)),
    )


def with_display_name(
    payload: RemindersSummaryPayload, display_name: str
) -> RemindersSummaryPayload:
    clean = " ".join(str(display_name or "player").replace("\r", " ").replace("\n", " ").split())
    return replace(payload, display_name=clean or "player")


def format_absolute_utc(value: datetime, *, reference: datetime) -> str:
    utc_value = _as_utc(value)
    utc_reference = _as_utc(reference)
    if utc_value.year == utc_reference.year:
        return utc_value.strftime("%d %b %H:%M UTC")
    return utc_value.strftime("%d %b %Y %H:%M UTC")


def next_alert_hero(
    alert: NextScheduledReminderAlert,
    *,
    generated_at_utc: datetime,
) -> ReminderHero:
    return ReminderHero(
        kind=ReminderHeroKind.NEXT_ALERT,
        headline="NEXT SCHEDULED ALERT",
        primary_line=alert.event_label,
        secondary_line=(
            f"{alert.system_label} • {alert.lead_time_label} • "
            f"{format_absolute_utc(alert.alert_at_utc, reference=generated_at_utc)} | "
            f"Event starts {format_absolute_utc(alert.event_start_at_utc, reference=generated_at_utc)}"
        ),
        next_alert=alert,
    )


def no_upcoming_hero(*, warning_windows_passed: bool = False) -> ReminderHero:
    return ReminderHero(
        kind=ReminderHeroKind.NO_UPCOMING,
        headline="NO UPCOMING ALERT",
        primary_line=(
            "No alert remains before the next selected event."
            if warning_windows_passed
            else "No upcoming selected alerts are currently scheduled."
        ),
    )


def unavailable_hero() -> ReminderHero:
    return ReminderHero(
        kind=ReminderHeroKind.UNAVAILABLE,
        headline="SCHEDULE UNAVAILABLE",
        primary_line="Upcoming alert preview is temporarily unavailable.",
        secondary_line="Your saved choices are shown below.",
    )


def _ordered_tokens(
    values: Iterable[object], order: tuple[str, ...]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    selected = _dedupe(values)
    known = tuple(item for item in order if item in selected)
    unknown = tuple(item for item in selected if item not in set(order))
    return known, unknown


def _event_display(labels: tuple[str, ...]) -> tuple[str, int]:
    if not labels:
        return "No events selected", 0
    shown = labels[:MAX_VISIBLE_EVENTS]
    hidden = max(0, len(labels) - len(shown))
    text = " • ".join(shown)
    if hidden:
        text = f"{text} • + {hidden} more"
    return text, hidden


def _time_display(labels: tuple[str, ...]) -> str:
    return " • ".join(labels) if labels else "No alert times selected"


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def _coverage_label(
    *,
    enabled: bool,
    ordered_times: tuple[str, ...],
    delta_seconds: dict[str, int],
) -> tuple[str, bool, str | None, str | None]:
    if not ordered_times:
        return "No active coverage", False, None, None
    ranked = sorted(ordered_times, key=lambda token: delta_seconds[token], reverse=True)
    longest = ranked[0]
    latest = ranked[-1]
    includes_start = delta_seconds[latest] == 0
    longest_label = alert_time_label(longest)
    latest_label = alert_time_label(latest)
    prefix = "Coverage" if enabled else "Saved coverage"
    if len(ranked) == 1:
        if includes_start:
            text = f"{prefix}: At start"
        else:
            text = f"{prefix}: {longest_label} before start"
    elif includes_start:
        text = f"{prefix}: {longest_label} → start"
    else:
        text = f"{prefix}: {longest_label} → {latest_label} before start"
    return text, includes_start, longest_label, latest_label


def _completeness(
    *,
    source_available: bool,
    valid_events: int,
    valid_times: int,
    unavailable_events: int,
    unavailable_times: int,
) -> ReminderCompleteness:
    if not source_available:
        return ReminderCompleteness.SOURCE_UNAVAILABLE
    if unavailable_events or unavailable_times:
        return ReminderCompleteness.UNAVAILABLE_SELECTION
    if not valid_events and not valid_times:
        return ReminderCompleteness.MISSING_BOTH
    if not valid_events:
        return ReminderCompleteness.MISSING_EVENTS
    if not valid_times:
        return ReminderCompleteness.MISSING_TIMES
    return ReminderCompleteness.COMPLETE


def _state_count_line(
    *,
    enabled: bool,
    completeness: ReminderCompleteness,
    event_count: int,
    time_count: int,
    unavailable_count: int,
) -> str:
    if completeness is ReminderCompleteness.SOURCE_UNAVAILABLE:
        return "REVIEW • Settings unavailable"
    if not enabled:
        if not event_count and not time_count:
            return "OFF • No saved choices"
        return (
            f"OFF • {_plural(event_count, 'saved event')} • "
            f"{_plural(time_count, 'saved alert time')}"
        )
    if completeness is ReminderCompleteness.COMPLETE:
        return f"ON • {_plural(event_count, 'event')} • {_plural(time_count, 'alert time')}"
    if completeness is ReminderCompleteness.MISSING_EVENTS:
        return "REVIEW • No events selected"
    if completeness is ReminderCompleteness.MISSING_TIMES:
        return "REVIEW • No alert times selected"
    if completeness is ReminderCompleteness.MISSING_BOTH:
        return "REVIEW • No events or alert times selected"
    if completeness is ReminderCompleteness.UNAVAILABLE_SELECTION:
        return f"REVIEW • {_plural(unavailable_count, 'saved choice', 'saved choices')} unavailable"
    return "REVIEW • Settings unavailable"


def _kvk_summary(config: object, *, source_available: bool) -> ReminderSystemSummary:
    raw = config if isinstance(config, dict) else {}
    enabled = source_available and isinstance(config, dict)
    raw_events = raw.get("subscriptions", [])
    raw_times = raw.get("reminder_times", [])
    event_values = raw_events if isinstance(raw_events, (list, tuple, set)) else ()
    time_values = raw_times if isinstance(raw_times, (list, tuple, set)) else ()
    valid_events, unknown_events = _ordered_tokens(event_values, tuple(VALID_TYPES))
    valid_times, unknown_times = _ordered_tokens(time_values, tuple(DEFAULT_REMINDER_TIMES))
    labels = tuple(kvk_event_label(key) for key in valid_events)
    if unknown_events:
        labels += tuple("Unavailable event" for _ in unknown_events)
    time_labels = tuple(alert_time_label(key) for key in valid_times)
    if unknown_times:
        time_labels += tuple("Unavailable alert time" for _ in unknown_times)
    event_summary, hidden = _event_display(labels)
    coverage, includes_start, longest, latest = _coverage_label(
        enabled=enabled,
        ordered_times=valid_times,
        delta_seconds={key: int(value.total_seconds()) for key, value in REMINDER_MAP.items()},
    )
    completeness = _completeness(
        source_available=source_available,
        valid_events=len(valid_events),
        valid_times=len(valid_times),
        unavailable_events=len(unknown_events),
        unavailable_times=len(unknown_times),
    )
    event_count = len(valid_events) + len(unknown_events)
    time_count = len(valid_times) + len(unknown_times)
    return ReminderSystemSummary(
        system_label="KVK",
        enabled=enabled,
        completeness=completeness,
        state_count_line=_state_count_line(
            enabled=enabled,
            completeness=completeness,
            event_count=event_count,
            time_count=time_count,
            unavailable_count=len(unknown_events) + len(unknown_times),
        ),
        selected_event_keys=valid_events + unknown_events,
        event_labels=labels,
        event_summary=event_summary,
        selected_event_count=event_count,
        hidden_event_count=hidden,
        unavailable_event_count=len(unknown_events),
        selected_time_keys=valid_times + unknown_times,
        time_labels=time_labels,
        time_summary=_time_display(time_labels),
        selected_time_count=time_count,
        unavailable_time_count=len(unknown_times),
        includes_start=includes_start,
        longest_lead_label=longest,
        latest_alert_label=latest,
        coverage_label=coverage,
        source_error=None if source_available else "KVK settings unavailable",
    )


def _calendar_summary(
    prefs: object,
    *,
    source_available: bool,
    catalog: CalendarEventCatalog,
) -> ReminderSystemSummary:
    raw = prefs if isinstance(prefs, dict) else {}
    enabled = bool(raw.get("enabled", False)) if source_available else False
    by_type = raw.get("by_event_type", {})
    if not isinstance(by_type, dict):
        by_type = {}

    event_offsets: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for raw_event, values in by_type.items():
        event_key = _clean_token(raw_event)
        if not event_key:
            continue
        if isinstance(values, (list, tuple, set)):
            raw_values: tuple[object, ...] = tuple(values)
        elif values is None:
            raw_values = ()
        else:
            raw_values = (values,)
        normalized = tuple(
            "start" if _clean_token(value) == "at_start" else _clean_token(value)
            for value in raw_values
        )
        previous_valid, previous_unknown = event_offsets.get(event_key, ((), ()))
        event_offsets[event_key] = _ordered_tokens(
            (*previous_valid, *previous_unknown, *normalized),
            REMINDER_OFFSETS_ORDERED,
        )

    # Empty buckets are intentionally persisted while the Calendar Settings multi-select
    # is staged. When reminders are enabled they are not dispatch-eligible event choices,
    # so another event's offsets must not make them look covered on the summary card.
    selected_events = tuple(
        event_key
        for event_key, (valid_offsets, unknown_offsets) in event_offsets.items()
        if not enabled or valid_offsets or unknown_offsets
    )
    known_catalog = set(catalog.event_types)
    if "all" in selected_events:
        valid_events = ("all",)
        unknown_events: tuple[str, ...] = ()
    elif catalog.available:
        valid_events = tuple(key for key in catalog.event_types if key in selected_events)
        unknown_events = tuple(key for key in selected_events if key not in known_catalog)
    else:
        valid_events = selected_events
        unknown_events = ()

    normalized_offsets = tuple(
        offset
        for event_key in selected_events
        for offsets in event_offsets[event_key]
        for offset in offsets
    )
    valid_times, unknown_times = _ordered_tokens(normalized_offsets, REMINDER_OFFSETS_ORDERED)
    labels = tuple(
        "All calendar events" if key == "all" else calendar_event_label(key) for key in valid_events
    )
    if unknown_events:
        labels += tuple("Unavailable event" for _ in unknown_events)
    time_labels = tuple(alert_time_label(key) for key in valid_times)
    if unknown_times:
        time_labels += tuple("Unavailable alert time" for _ in unknown_times)
    event_summary, hidden = _event_display(labels)
    coverage, includes_start, longest, latest = _coverage_label(
        enabled=enabled,
        ordered_times=valid_times,
        delta_seconds={
            key: int(value.total_seconds()) for key, value in REMINDER_OFFSET_TO_DELTA.items()
        },
    )
    completeness = _completeness(
        source_available=source_available,
        valid_events=len(valid_events),
        valid_times=len(valid_times),
        unavailable_events=len(unknown_events),
        unavailable_times=len(unknown_times),
    )
    event_count = len(valid_events) + len(unknown_events)
    time_count = len(valid_times) + len(unknown_times)
    return ReminderSystemSummary(
        system_label="CALENDAR",
        enabled=enabled,
        completeness=completeness,
        state_count_line=_state_count_line(
            enabled=enabled,
            completeness=completeness,
            event_count=event_count,
            time_count=time_count,
            unavailable_count=len(unknown_events) + len(unknown_times),
        ),
        selected_event_keys=valid_events + unknown_events,
        event_labels=labels,
        event_summary=event_summary,
        selected_event_count=event_count,
        hidden_event_count=hidden,
        unavailable_event_count=len(unknown_events),
        selected_time_keys=valid_times + unknown_times,
        time_labels=time_labels,
        time_summary=_time_display(time_labels),
        selected_time_count=time_count,
        unavailable_time_count=len(unknown_times),
        includes_start=includes_start,
        longest_lead_label=longest,
        latest_alert_label=latest,
        coverage_label=coverage,
        source_error=None if source_available else "Calendar settings unavailable",
    )


def _configuration_state(
    kvk: ReminderSystemSummary,
    calendar: ReminderSystemSummary,
) -> ReminderConfigurationState:
    systems = (kvk, calendar)
    if not any(system.enabled for system in systems):
        if any(
            system.completeness is ReminderCompleteness.SOURCE_UNAVAILABLE for system in systems
        ):
            return ReminderConfigurationState.REVIEW
        return ReminderConfigurationState.OFF
    if any(
        system.enabled and system.completeness is not ReminderCompleteness.COMPLETE
        for system in systems
    ):
        return ReminderConfigurationState.REVIEW
    return ReminderConfigurationState.ACTIVE


def _system_name(system: ReminderSystemSummary) -> str:
    return "KVK" if system.system_label == "KVK" else system.system_label.title()


def _issue_text(system: ReminderSystemSummary) -> str:
    name = _system_name(system)
    if system.completeness is ReminderCompleteness.MISSING_EVENTS:
        return f"{name} needs an event"
    if system.completeness is ReminderCompleteness.MISSING_TIMES:
        return f"{name} needs an alert time"
    if system.completeness is ReminderCompleteness.MISSING_BOTH:
        return f"{name} needs an event and an alert time"
    if system.completeness is ReminderCompleteness.UNAVAILABLE_SELECTION:
        return f"{name} has unavailable saved selections"
    return f"{name} settings are unavailable"


def _supporting_text(
    state: ReminderConfigurationState,
    kvk: ReminderSystemSummary,
    calendar: ReminderSystemSummary,
) -> str:
    if state is ReminderConfigurationState.OFF:
        return "All reminder systems are off"
    if state is ReminderConfigurationState.ACTIVE:
        enabled = int(kvk.enabled) + int(calendar.enabled)
        return f"{enabled} of 2 systems enabled"
    issues = [
        _issue_text(system)
        for system in (kvk, calendar)
        if system.completeness is ReminderCompleteness.SOURCE_UNAVAILABLE
        or (system.enabled and system.completeness is not ReminderCompleteness.COMPLETE)
    ]
    if len(issues) == 1:
        return issues[0]
    return f"{len(issues)} settings need review"


def _configuration_insight(system: ReminderSystemSummary) -> str:
    name = _system_name(system)
    if system.completeness is ReminderCompleteness.MISSING_EVENTS:
        return f"{name} reminders are enabled, but no event types are selected."
    if system.completeness is ReminderCompleteness.MISSING_TIMES:
        return f"{name} reminders are enabled, but no alert times are selected."
    if system.completeness is ReminderCompleteness.MISSING_BOTH:
        return f"{name} reminders need an event and an alert time."
    if system.completeness is ReminderCompleteness.UNAVAILABLE_SELECTION:
        count = system.unavailable_event_count + system.unavailable_time_count
        if count == 1:
            return f"1 saved choice for {name} is no longer available; review it in Manage."
        return f"{count} saved {name} choices are no longer available; review them in Manage."
    return f"{name} reminder settings are temporarily unavailable."


def _insight(
    state: ReminderConfigurationState,
    kvk: ReminderSystemSummary,
    calendar: ReminderSystemSummary,
) -> str:
    for system in (kvk, calendar):
        if system.completeness is ReminderCompleteness.SOURCE_UNAVAILABLE or (
            system.enabled and system.completeness is not ReminderCompleteness.COMPLETE
        ):
            return _configuration_insight(system)
    if state is ReminderConfigurationState.OFF:
        return "All reminders are off; use Manage to choose what you want to receive."
    if kvk.enabled and not calendar.enabled:
        return "Calendar reminders are off; only KVK alerts will be sent."
    if calendar.enabled and not kvk.enabled:
        return "KVK reminders are off; only Calendar alerts will be sent."
    for system in (kvk, calendar):
        if system.enabled and not system.includes_start and system.latest_alert_label:
            return (
                f"{_system_name(system)} coverage ends {system.latest_alert_label} before "
                "the event; no start-time alert is selected."
            )
    active = tuple(system for system in (kvk, calendar) if system.enabled)
    longest = max(
        (system.longest_lead_label for system in active if system.longest_lead_label),
        key=lambda label: _lead_seconds(label),
        default="At start",
    )
    return f"Both systems are active; coverage begins {longest} before event start."


def _lead_seconds(label: str) -> int:
    reverse = {
        alert_time_label(key): int(delta.total_seconds()) for key, delta in REMINDER_MAP.items()
    }
    reverse.update(
        {
            alert_time_label(key): int(delta.total_seconds())
            for key, delta in REMINDER_OFFSET_TO_DELTA.items()
        }
    )
    return reverse.get(label, 0)


def _coverage_value(system: ReminderSystemSummary) -> str:
    value = system.coverage_label
    for prefix in ("Coverage: ", "Saved coverage: "):
        if value.startswith(prefix):
            return value.removeprefix(prefix)
    return value


def coverage_hero(
    kvk: ReminderSystemSummary,
    calendar: ReminderSystemSummary,
) -> ReminderHero:
    event_count = kvk.selected_event_count + calendar.selected_event_count
    time_count = kvk.selected_time_count + calendar.selected_time_count
    return ReminderHero(
        kind=ReminderHeroKind.COVERAGE,
        headline="REMINDER COVERAGE",
        primary_line=(f"KVK: {_coverage_value(kvk)} • Calendar: {_coverage_value(calendar)}"),
        secondary_line=(
            f"{_plural(event_count, 'event type')} • {_plural(time_count, 'alert time')}"
        ),
    )


def build_reminders_summary_payload(
    *,
    viewer_discord_id: int,
    display_name: str,
    kvk_config: object,
    calendar_prefs: object,
    calendar_catalog: CalendarEventCatalog,
    generated_at_utc: datetime,
    kvk_source_available: bool = True,
    calendar_source_available: bool = True,
    hero: ReminderHero | None = None,
) -> RemindersSummaryPayload:
    generated = _as_utc(generated_at_utc)
    kvk = _kvk_summary(kvk_config, source_available=kvk_source_available)
    calendar = _calendar_summary(
        calendar_prefs,
        source_available=calendar_source_available,
        catalog=calendar_catalog,
    )
    state = _configuration_state(kvk, calendar)
    warnings = tuple(
        value
        for value in (
            kvk.source_error,
            calendar.source_error,
            None if calendar_catalog.available else "Calendar event catalogue unavailable",
        )
        if value
    )
    return RemindersSummaryPayload(
        viewer_discord_id=int(viewer_discord_id),
        display_name=display_name,
        kingdom_id=KINGDOM_ID,
        generated_at_utc=generated,
        configuration_state=state,
        state_supporting_text=_supporting_text(state, kvk, calendar),
        kvk=kvk,
        calendar=calendar,
        hero=hero or coverage_hero(kvk, calendar),
        insight=_insight(state, kvk, calendar),
        warnings=warnings,
    )
