from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from event_cache import UpcomingEventCacheSnapshot
from event_calendar.reminder_state import CalendarReminderState
from event_scheduler import KvkDmTrackerSnapshot
from inventory.models import InventoryReportVisibility
from player_self_service import service
from player_self_service.profile_preference_service import (
    UserProfilePreference,
    UserProfilePreferenceRead,
)
from player_self_service.reminders_summary import (
    ReminderConfigurationState,
    ReminderHeroKind,
)
from reminder_domain.kvk_candidates import make_event_id
from services.governor_account_service import summarize_accounts

NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


async def _account_loader(_user_id: int):
    return summarize_accounts({})


async def _preference_loader(_user_id: int):
    return SimpleNamespace(ok=True, visibility=InventoryReportVisibility.PRIVATE)


async def _profile_preference_loader(_user_id: int):
    return UserProfilePreferenceRead(
        ok=True,
        profile=UserProfilePreference(
            timezone_name="UTC",
            location_country_code="GB",
            preferred_language_tag="en-GB",
        ),
    )


def _kvk_event(*, name: str = "Ancient Ruins", start: datetime) -> dict:
    return {
        "name": name,
        "type": "ruins",
        "start_time": start,
        "end_time": start + timedelta(minutes=30),
    }


def _calendar_event(*, instance_id: str, start: datetime) -> dict:
    return {
        "instance_id": instance_id,
        "title": "Ark of Osiris",
        "variant": "League",
        "type": "ark",
        "start_utc": start.isoformat(),
        "end_utc": (start + timedelta(hours=1)).isoformat(),
    }


@pytest.mark.asyncio
async def test_service_bulk_loads_each_projection_source_once_and_selects_earliest() -> None:
    calls: dict[str, int] = {}
    event_loop_thread_id = threading.get_ident()
    kvk_tracker_thread_ids: list[int] = []

    def counted(name: str):
        calls[name] = calls.get(name, 0) + 1

    kvk = _kvk_event(start=NOW + timedelta(hours=25))
    event_id = make_event_id(kvk)
    calendar_events = [
        _calendar_event(instance_id="ark-1", start=NOW + timedelta(hours=2)),
        _calendar_event(instance_id="ark-2", start=NOW + timedelta(hours=4)),
    ]

    def reminder_loader(_user_id: int):
        counted("kvk_config")
        return {"subscriptions": ["ruins"], "reminder_times": ["24h"]}

    def calendar_prefs_loader(_user_id: int):
        counted("calendar_prefs")
        return {"enabled": True, "by_event_type": {"ark": ["start"]}}

    def kvk_event_loader():
        counted("kvk_events")
        return UpcomingEventCacheSnapshot(True, (kvk,), NOW, False)

    def kvk_tracker_loader():
        counted("kvk_trackers")
        kvk_tracker_thread_ids.append(threading.get_ident())
        return KvkDmTrackerSnapshot(
            sent={},
            scheduled={event_id: {"42": {int(timedelta(hours=24).total_seconds())}}},
        )

    def calendar_runtime_loader():
        counted("calendar_runtime")
        return {"ok": True, "events": calendar_events}

    def calendar_state_loader():
        counted("calendar_state")
        return CalendarReminderState(path=Path("unused.json"), sent={})

    summary = await service.build_player_self_service_summary(
        42,
        account_loader=_account_loader,
        reminder_loader=reminder_loader,
        calendar_prefs_loader=calendar_prefs_loader,
        preference_loader=_preference_loader,
        profile_preference_loader=_profile_preference_loader,
        kvk_event_snapshot_loader=kvk_event_loader,
        kvk_tracker_snapshot_loader=kvk_tracker_loader,
        calendar_runtime_cache_loader=calendar_runtime_loader,
        calendar_reminder_state_loader=calendar_state_loader,
        utc_clock=lambda: NOW,
    )

    payload = summary.reminders_summary
    assert payload is not None
    assert payload.hero.kind is ReminderHeroKind.NEXT_ALERT
    assert payload.hero.primary_line == "Ancient Ruins"
    assert "KVK" in payload.hero.secondary_line
    assert "24h" in payload.hero.secondary_line
    assert event_id not in payload.hero.secondary_line
    assert kvk_tracker_thread_ids
    assert kvk_tracker_thread_ids[0] != event_loop_thread_id
    assert calls == {
        "kvk_config": 1,
        "calendar_prefs": 1,
        "kvk_events": 1,
        "kvk_trackers": 1,
        "calendar_runtime": 1,
        "calendar_state": 1,
    }


@pytest.mark.asyncio
async def test_default_kvk_snapshot_uses_projection_clock(monkeypatch) -> None:
    event = _kvk_event(start=NOW + timedelta(seconds=1))
    observed_now_values: list[datetime | None] = []

    def default_snapshot_loader(
        *, now_utc: datetime | None = None, max_age_hours: int = 12
    ) -> UpcomingEventCacheSnapshot:
        del max_age_hours
        observed_now_values.append(now_utc)
        effective_now = now_utc or NOW + timedelta(seconds=2)
        events = (event,) if event["start_time"] > effective_now else ()
        return UpcomingEventCacheSnapshot(True, events, NOW, False)

    monkeypatch.setattr(service, "get_upcoming_event_cache_snapshot", default_snapshot_loader)

    summary = await service.build_player_self_service_summary(
        42,
        account_loader=_account_loader,
        reminder_loader=lambda _uid: {
            "subscriptions": ["ruins"],
            "reminder_times": ["now"],
        },
        calendar_prefs_loader=lambda _uid: {
            "enabled": False,
            "by_event_type": {},
        },
        preference_loader=_preference_loader,
        profile_preference_loader=_profile_preference_loader,
        kvk_tracker_snapshot_loader=lambda: KvkDmTrackerSnapshot({}, {}),
        calendar_runtime_cache_loader=lambda: {"ok": True, "events": []},
        calendar_reminder_state_loader=lambda: CalendarReminderState(
            path=Path("unused.json"),
            sent={},
        ),
        utc_clock=lambda: NOW,
    )

    assert observed_now_values == [NOW]
    assert summary.reminders_summary is not None
    assert summary.reminders_summary.hero.kind is ReminderHeroKind.NEXT_ALERT


@pytest.mark.asyncio
async def test_event_source_failure_makes_schedule_unavailable_without_false_review() -> None:
    summary = await service.build_player_self_service_summary(
        42,
        account_loader=_account_loader,
        reminder_loader=lambda _uid: {
            "subscriptions": ["ruins"],
            "reminder_times": ["24h"],
        },
        calendar_prefs_loader=lambda _uid: {
            "enabled": False,
            "by_event_type": {},
        },
        preference_loader=_preference_loader,
        profile_preference_loader=_profile_preference_loader,
        kvk_event_snapshot_loader=lambda: UpcomingEventCacheSnapshot(
            False,
            (),
            None,
            True,
            "cache_unavailable",
        ),
        kvk_tracker_snapshot_loader=lambda: KvkDmTrackerSnapshot({}, {}),
        calendar_runtime_cache_loader=lambda: {"ok": True, "events": []},
        calendar_reminder_state_loader=lambda: CalendarReminderState(
            path=Path("unused.json"),
            sent={},
        ),
        utc_clock=lambda: NOW,
    )

    payload = summary.reminders_summary
    assert payload is not None
    assert payload.configuration_state is ReminderConfigurationState.ACTIVE
    assert payload.kvk.state_count_line.startswith("ON")
    assert payload.hero.kind is ReminderHeroKind.UNAVAILABLE


@pytest.mark.asyncio
async def test_malformed_calendar_runtime_source_degrades_to_schedule_unavailable() -> None:
    summary = await service.build_player_self_service_summary(
        42,
        account_loader=_account_loader,
        reminder_loader=lambda _uid: {
            "subscriptions": ["ruins"],
            "reminder_times": ["24h"],
        },
        calendar_prefs_loader=lambda _uid: {
            "enabled": False,
            "by_event_type": {},
        },
        preference_loader=_preference_loader,
        profile_preference_loader=_profile_preference_loader,
        kvk_event_snapshot_loader=lambda: UpcomingEventCacheSnapshot(
            True,
            (),
            NOW,
            False,
        ),
        kvk_tracker_snapshot_loader=lambda: KvkDmTrackerSnapshot({}, {}),
        calendar_runtime_cache_loader=lambda: None,  # type: ignore[return-value]
        calendar_reminder_state_loader=lambda: CalendarReminderState(
            path=Path("unused.json"),
            sent={},
        ),
        utc_clock=lambda: NOW,
    )

    payload = summary.reminders_summary
    assert payload is not None
    assert payload.configuration_state is ReminderConfigurationState.ACTIVE
    assert payload.hero.kind is ReminderHeroKind.UNAVAILABLE


@pytest.mark.asyncio
async def test_healthy_empty_sources_produce_no_upcoming_alert() -> None:
    summary = await service.build_player_self_service_summary(
        42,
        account_loader=_account_loader,
        reminder_loader=lambda _uid: {
            "subscriptions": ["ruins"],
            "reminder_times": ["24h"],
        },
        calendar_prefs_loader=lambda _uid: {
            "enabled": False,
            "by_event_type": {},
        },
        preference_loader=_preference_loader,
        profile_preference_loader=_profile_preference_loader,
        kvk_event_snapshot_loader=lambda: UpcomingEventCacheSnapshot(
            True,
            (),
            NOW,
            False,
        ),
        kvk_tracker_snapshot_loader=lambda: KvkDmTrackerSnapshot({}, {}),
        calendar_runtime_cache_loader=lambda: {"ok": True, "events": []},
        calendar_reminder_state_loader=lambda: CalendarReminderState(
            path=Path("unused.json"),
            sent={},
        ),
        utc_clock=lambda: NOW,
    )

    payload = summary.reminders_summary
    assert payload is not None
    assert payload.hero.kind is ReminderHeroKind.NO_UPCOMING
