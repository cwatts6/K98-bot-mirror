"""Read-only summary service for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from constants import EVENT_CALENDAR_REMINDER_GRACE_MINUTES
from event_cache import UpcomingEventCacheSnapshot, get_upcoming_event_cache_snapshot
from event_calendar.reminder_candidates import build_calendar_alert_projection
from event_calendar.reminder_config_service import (
    CalendarReminderConfigState,
    state_from_prefs,
)
from event_calendar.reminder_prefs_store import get_user_prefs
from event_calendar.reminder_state import CalendarReminderState
from event_calendar.runtime_cache import list_event_types, load_runtime_cache
from event_scheduler import KvkDmTrackerSnapshot, snapshot_dm_trackers
from player_self_service import reminders_summary
from player_self_service.reminders_summary import RemindersSummaryPayload
from reminder_domain.kvk_candidates import build_kvk_alert_projection
from reminder_domain.projection import ReminderSourceProjection, combine_reminder_projections
from services.governor_account_service import (
    AccountResolutionSummary,
    get_account_summary_for_user,
)
from subscription_tracker import get_user_config

logger = logging.getLogger(__name__)

_REMINDER_TIME_ORDER = ("24h", "12h", "4h", "1h", "now")


@dataclass(frozen=True, slots=True)
class AccountStatus:
    state: str
    linked_count: int
    linked_label: str
    main_state: str
    main_label: str
    next_action: str
    account_names: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CalendarReminderStatus:
    state: str
    event_summary: str
    time_summary: str
    next_action: str
    error: str | None = None


def _default_calendar_reminder_status() -> CalendarReminderStatus:
    return CalendarReminderStatus(
        state="off",
        event_summary="not configured",
        time_summary="not set",
        next_action="Configure",
    )


@dataclass(frozen=True, slots=True)
class ReminderStatus:
    state: str
    event_summary: str
    time_summary: str
    next_action: str
    error: str | None = None
    calendar: CalendarReminderStatus = field(default_factory=_default_calendar_reminder_status)

    @property
    def combined_state(self) -> str:
        states = {self.state.strip().lower(), self.calendar.state.strip().lower()}
        if "unknown" in states:
            return "unknown"
        if "incomplete" in states:
            return "incomplete"
        if "on" in states:
            return "on"
        return "off"

    @property
    def combined_next_action(self) -> str:
        state = self.combined_state
        if state == "unknown":
            return "Try again"
        if state == "incomplete":
            return "Finish setup"
        if state == "off":
            return "Set up"
        return "Manage"


@dataclass(frozen=True, slots=True)
class ExportStatus:
    stats_export: str
    inventory_export: str
    privacy_note: str
    action_state: str = "actionable"
    action_summary: str = "Default private exports are available here."


@dataclass(frozen=True, slots=True)
class PlayerSelfServiceSummary:
    discord_user_id: int
    accounts: AccountStatus
    reminders: ReminderStatus
    exports: ExportStatus
    reminders_summary: RemindersSummaryPayload | None = None


AccountLoader = Callable[[int], Awaitable[AccountResolutionSummary]]
ReminderLoader = Callable[[int], dict[str, Any] | None]
CalendarReminderLoader = Callable[[int], CalendarReminderConfigState]
CalendarPrefsLoader = Callable[[int], dict[str, Any]]
CalendarEventCatalogLoader = Callable[[], reminders_summary.CalendarEventCatalog]
KvkEventSnapshotLoader = Callable[[], UpcomingEventCacheSnapshot]
KvkTrackerSnapshotLoader = Callable[[], KvkDmTrackerSnapshot]
CalendarRuntimeCacheLoader = Callable[[], dict[str, Any]]
CalendarReminderStateLoader = Callable[[], CalendarReminderState]
UtcClock = Callable[[], datetime]


def summarize_account_status(summary: AccountResolutionSummary) -> AccountStatus:
    if not summary.ok:
        logger.warning("player_self_service_accounts_unavailable error=%s", summary.error)
        return AccountStatus(
            state="unknown",
            linked_count=0,
            linked_label="unknown",
            main_state="unknown",
            main_label="unknown",
            next_action="Try again",
            error=summary.error or "account source unavailable",
        )

    linked_count = len(summary.resolved_accounts)
    main = summary.ordered_accounts.get("Main") or {}
    main_gid = str(main.get("GovernorID") or main.get("GovernorId") or "").strip()
    main_name = str(main.get("GovernorName") or main.get("governor_name") or "").strip()
    if main_gid:
        main_state = "set"
        main_label = f"{main_name or 'Main account'} ({main_gid})"
    else:
        main_state = "not set"
        main_label = "not set"

    if linked_count == 0:
        linked_label = "0 linked"
        state = "none"
        next_action = "Register"
    elif linked_count == 1:
        linked_label = "1 linked"
        state = "single"
        next_action = "Review"
    else:
        linked_label = "multiple linked"
        state = "multiple"
        next_action = "Manage"

    return AccountStatus(
        state=state,
        linked_count=linked_count,
        linked_label=linked_label,
        main_state=main_state,
        main_label=main_label,
        next_action=next_action,
        account_names=tuple(summary.account_names),
    )


def _ordered_reminder_times(values: list[Any]) -> tuple[str, ...]:
    seen = {str(value).strip().lower() for value in values if str(value).strip()}
    ordered = [item for item in _REMINDER_TIME_ORDER if item in seen]
    ordered.extend(sorted(seen - set(ordered)))
    return tuple(ordered)


def summarize_reminder_status(config: dict[str, Any] | None) -> ReminderStatus:
    if config is None:
        return ReminderStatus(
            state="off",
            event_summary="not subscribed",
            time_summary="not set",
            next_action="Set up",
        )
    if not isinstance(config, dict):
        return ReminderStatus(
            state="unknown",
            event_summary="unknown",
            time_summary="unknown",
            next_action="Try again",
            error="invalid reminder config",
        )

    raw_types = config.get("subscriptions") or []
    raw_times = config.get("reminder_times") or []
    if not isinstance(raw_types, list) or not isinstance(raw_times, list):
        return ReminderStatus(
            state="unknown",
            event_summary="unknown",
            time_summary="unknown",
            next_action="Try again",
            error="invalid reminder config shape",
        )

    event_types = tuple(str(value).strip().lower() for value in raw_types if str(value).strip())
    times = _ordered_reminder_times(raw_times)
    if not event_types and not times:
        return ReminderStatus(
            state="off",
            event_summary="not subscribed",
            time_summary="not set",
            next_action="Set up",
        )

    if "all" in event_types:
        event_summary = "all KVK events"
    else:
        event_summary = ", ".join(event_types) if event_types else "events not set"

    return ReminderStatus(
        state="on",
        event_summary=event_summary,
        time_summary=", ".join(times) if times else "times not set",
        next_action="Manage",
    )


def summarize_calendar_reminder_status(
    state: CalendarReminderConfigState | None,
) -> CalendarReminderStatus:
    if state is None:
        return _default_calendar_reminder_status()

    selected_types = tuple(state.selected_types)
    selected_offsets = tuple(state.selected_offsets)

    if selected_types == ("all",):
        event_summary = "all calendar events"
    elif selected_types:
        event_summary = ", ".join(selected_types)
    else:
        event_summary = "not configured"

    time_summary = ", ".join(selected_offsets) if selected_offsets else "not set"

    if state.enabled and selected_types and selected_offsets:
        return CalendarReminderStatus(
            state="on",
            event_summary=event_summary,
            time_summary=time_summary,
            next_action="Manage",
        )
    if state.enabled:
        return CalendarReminderStatus(
            state="incomplete",
            event_summary=event_summary,
            time_summary=time_summary,
            next_action="Finish setup",
        )
    return CalendarReminderStatus(
        state="off",
        event_summary=event_summary,
        time_summary=time_summary,
        next_action="Configure",
    )


def summarize_export_status(accounts: AccountStatus) -> ExportStatus:
    if accounts.state == "unknown":
        return ExportStatus(
            stats_export="Unavailable",
            inventory_export="Unavailable",
            privacy_note="Private",
            action_state="unavailable",
            action_summary="Try again later.",
        )
    if accounts.linked_count <= 0:
        return ExportStatus(
            stats_export="Unavailable",
            inventory_export="Unavailable",
            privacy_note="Private",
            action_state="unavailable",
            action_summary="Register an account first.",
        )
    return ExportStatus(
        stats_export="Excel / CSV / Google Sheets",
        inventory_export="Excel / CSV / Google Sheets",
        privacy_note="Private",
        action_state="actionable",
        action_summary="Ready",
    )


async def build_player_self_service_summary(
    discord_user_id: int,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    reminder_loader: ReminderLoader = get_user_config,
    calendar_reminder_loader: CalendarReminderLoader | None = None,
    calendar_prefs_loader: CalendarPrefsLoader = get_user_prefs,
    calendar_event_catalog_loader: CalendarEventCatalogLoader | None = None,
    kvk_event_snapshot_loader: KvkEventSnapshotLoader | None = None,
    kvk_tracker_snapshot_loader: KvkTrackerSnapshotLoader = snapshot_dm_trackers,
    calendar_runtime_cache_loader: CalendarRuntimeCacheLoader = load_runtime_cache,
    calendar_reminder_state_loader: CalendarReminderStateLoader = CalendarReminderState.load,
    utc_clock: UtcClock = lambda: datetime.now(UTC),
) -> PlayerSelfServiceSummary:
    generated_at = utc_clock()
    account_summary = await account_loader(int(discord_user_id))

    reminder_config: object = None
    kvk_source_available = True
    try:
        reminder_config = await asyncio.to_thread(reminder_loader, int(discord_user_id))
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        kvk_source_available = False
        logger.exception(
            "player_self_service_reminders_unavailable user_id=%s",
            discord_user_id,
        )
        reminders = ReminderStatus(
            state="unknown",
            event_summary="unknown",
            time_summary="unknown",
            next_action="Try again",
            error=f"{type(exc).__name__}: {exc}",
        )
    else:
        reminders = summarize_reminder_status(reminder_config)

    calendar_state: CalendarReminderConfigState | None = None
    calendar_prefs: dict[str, Any] = {"enabled": False, "by_event_type": {}}
    calendar_source_available = True
    try:
        if calendar_reminder_loader is None:
            calendar_prefs = await asyncio.to_thread(
                calendar_prefs_loader,
                int(discord_user_id),
            )
            calendar_state = state_from_prefs(calendar_prefs)
        else:
            calendar_state = await asyncio.to_thread(
                calendar_reminder_loader,
                int(discord_user_id),
            )
            calendar_prefs = {
                "enabled": calendar_state.enabled,
                "by_event_type": {
                    event_type: list(calendar_state.selected_offsets)
                    for event_type in calendar_state.selected_types
                },
            }
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        calendar_source_available = False
        logger.exception(
            "player_self_service_calendar_reminders_unavailable user_id=%s",
            discord_user_id,
        )
        calendar = CalendarReminderStatus(
            state="unknown",
            event_summary="unknown",
            time_summary="unknown",
            next_action="Try again",
            error=f"{type(exc).__name__}: {exc}",
        )
    else:
        calendar = summarize_calendar_reminder_status(calendar_state)
    reminders = replace(reminders, calendar=calendar)

    kvk_event_snapshot: UpcomingEventCacheSnapshot | None = None
    kvk_tracker_snapshot: KvkDmTrackerSnapshot | None = None
    calendar_runtime: dict[str, Any] = {}
    calendar_dispatch_state: CalendarReminderState | None = None

    try:
        if kvk_event_snapshot_loader is None:
            kvk_event_snapshot = await asyncio.to_thread(
                get_upcoming_event_cache_snapshot,
                now_utc=generated_at,
            )
        else:
            kvk_event_snapshot = await asyncio.to_thread(kvk_event_snapshot_loader)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_kvk_projection_source_unavailable user_id=%s",
            discord_user_id,
        )
    try:
        kvk_tracker_snapshot = await asyncio.to_thread(kvk_tracker_snapshot_loader)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_kvk_projection_tracker_unavailable user_id=%s",
            discord_user_id,
        )
    try:
        calendar_runtime = await asyncio.to_thread(calendar_runtime_cache_loader)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_calendar_projection_source_unavailable user_id=%s",
            discord_user_id,
        )
    try:
        calendar_dispatch_state = await asyncio.to_thread(calendar_reminder_state_loader)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_calendar_projection_tracker_unavailable user_id=%s",
            discord_user_id,
        )

    if not isinstance(calendar_runtime, dict):
        logger.warning(
            "player_self_service_calendar_projection_source_invalid user_id=%s",
            discord_user_id,
        )
        calendar_runtime = {}
    calendar_projection_source_available = bool(calendar_runtime.get("ok"))
    try:
        known_calendar_types = (
            tuple(list_event_types(calendar_runtime))
            if calendar_projection_source_available
            else ()
        )
    except Exception:
        logger.exception(
            "player_self_service_calendar_projection_catalog_failed user_id=%s",
            discord_user_id,
        )
        calendar_projection_source_available = False
        known_calendar_types = ()
    if calendar_event_catalog_loader is None:
        calendar_catalog = reminders_summary.CalendarEventCatalog(
            available=calendar_projection_source_available,
            event_types=known_calendar_types,
        )
    else:
        try:
            calendar_catalog = await asyncio.to_thread(calendar_event_catalog_loader)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "player_self_service_calendar_event_catalog_unavailable user_id=%s",
                discord_user_id,
            )
            calendar_catalog = reminders_summary.CalendarEventCatalog(
                available=False,
                event_types=(),
            )

    try:
        kvk_projection = build_kvk_alert_projection(
            events=kvk_event_snapshot.events if kvk_event_snapshot is not None else (),
            config=reminder_config if isinstance(reminder_config, dict) else None,
            user_id=discord_user_id,
            sent_tracker=(kvk_tracker_snapshot.sent if kvk_tracker_snapshot is not None else {}),
            scheduled_tracker=(
                kvk_tracker_snapshot.scheduled if kvk_tracker_snapshot is not None else {}
            ),
            now_utc=generated_at,
            source_available=(
                kvk_source_available
                and kvk_event_snapshot is not None
                and kvk_event_snapshot.ok
                and kvk_tracker_snapshot is not None
            ),
        )
    except Exception:
        logger.exception(
            "player_self_service_kvk_projection_failed user_id=%s",
            discord_user_id,
        )
        kvk_projection = ReminderSourceProjection.unavailable("KVK projection unavailable")
    try:
        calendar_projection = build_calendar_alert_projection(
            events=(
                calendar_runtime.get("events", [])
                if isinstance(calendar_runtime.get("events", []), list)
                else []
            ),
            user_id=int(discord_user_id),
            prefs=calendar_prefs,
            known_event_types=set(known_calendar_types),
            sent_keys=(calendar_dispatch_state.sent if calendar_dispatch_state is not None else {}),
            now_utc=generated_at,
            grace=timedelta(minutes=EVENT_CALENDAR_REMINDER_GRACE_MINUTES),
            source_available=(
                calendar_source_available
                and calendar_projection_source_available
                and calendar_dispatch_state is not None
            ),
        )
    except Exception:
        logger.exception(
            "player_self_service_calendar_projection_failed user_id=%s",
            discord_user_id,
        )
        calendar_projection = ReminderSourceProjection.unavailable(
            "Calendar projection unavailable"
        )
    projection = combine_reminder_projections(
        kvk=kvk_projection,
        calendar=calendar_projection,
        now_utc=generated_at,
    )
    reminders_payload = reminders_summary.build_reminders_summary_payload(
        viewer_discord_id=int(discord_user_id),
        display_name="",
        kvk_config=reminder_config,
        calendar_prefs=calendar_prefs,
        calendar_catalog=calendar_catalog,
        generated_at_utc=generated_at,
        kvk_source_available=kvk_source_available,
        calendar_source_available=calendar_source_available,
        hero=reminders_summary.hero_from_projection(
            projection,
            generated_at_utc=generated_at,
        ),
    )

    accounts = summarize_account_status(account_summary)
    return PlayerSelfServiceSummary(
        discord_user_id=int(discord_user_id),
        accounts=accounts,
        reminders=reminders,
        exports=summarize_export_status(accounts),
        reminders_summary=reminders_payload,
    )
