from __future__ import annotations

from datetime import UTC, datetime
import inspect
from pathlib import Path

import pytest

from event_calendar.reminder_config_service import CalendarReminderConfigState
from player_self_service import service
from services.governor_account_service import summarize_accounts


def test_account_status_for_new_player_shows_register_next_action() -> None:
    status = service.summarize_account_status(summarize_accounts({}))

    assert status.state == "none"
    assert status.linked_count == 0
    assert status.main_state == "not set"
    assert status.next_action == "Register"


def test_account_status_for_multiple_accounts_stays_compact() -> None:
    status = service.summarize_account_status(
        summarize_accounts(
            {
                "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
                "Alt 1": {"GovernorID": "222", "GovernorName": "Alt Gov"},
            }
        )
    )

    assert status.state == "multiple"
    assert status.linked_label == "multiple linked"
    assert status.main_label == "Main Gov (111)"
    assert status.next_action == "Manage"


def test_account_status_reports_unknown_when_registry_fails() -> None:
    status = service.summarize_account_status(summarize_accounts({}, ok=False, error="SQL down"))

    assert status.state == "unknown"
    assert status.main_state == "unknown"
    assert status.next_action == "Try again"
    assert status.error == "SQL down"


def test_reminder_status_for_unsubscribed_player_is_off() -> None:
    status = service.summarize_reminder_status(None)

    assert status.state == "off"
    assert status.event_summary == "not subscribed"
    assert status.time_summary == "not set"
    assert status.next_action == "Set up"


def test_reminder_status_summarizes_subscribed_player() -> None:
    status = service.summarize_reminder_status(
        {"subscriptions": ["major", "altars"], "reminder_times": ["1h", "24h", "4h"]}
    )

    assert status.state == "on"
    assert status.event_summary == "major, altars"
    assert status.time_summary == "24h, 4h, 1h"
    assert status.next_action == "Manage"


def test_reminder_status_reports_unknown_for_invalid_shape() -> None:
    status = service.summarize_reminder_status({"subscriptions": "all", "reminder_times": []})

    assert status.state == "unknown"
    assert status.event_summary == "unknown"
    assert status.error == "invalid reminder config shape"


def test_calendar_reminder_status_summarizes_enabled_calendar_prefs() -> None:
    status = service.summarize_calendar_reminder_status(
        CalendarReminderConfigState(
            enabled=True,
            selected_types=("all",),
            selected_offsets=("24h", "1h"),
        )
    )

    assert status.state == "on"
    assert status.event_summary == "all calendar events"
    assert status.time_summary == "24h, 1h"
    assert status.next_action == "Manage"


def test_reminder_status_combined_state_handles_calendar_only() -> None:
    status = service.ReminderStatus(
        state="off",
        event_summary="not subscribed",
        time_summary="not set",
        next_action="Set up",
        calendar=service.CalendarReminderStatus(
            state="on",
            event_summary="all calendar events",
            time_summary="24h",
            next_action="Manage",
        ),
    )

    assert status.combined_state == "on"
    assert status.combined_next_action == "Manage"


def test_reminder_status_combined_next_action_handles_incomplete_calendar() -> None:
    status = service.ReminderStatus(
        state="off",
        event_summary="not subscribed",
        time_summary="not set",
        next_action="Set up",
        calendar=service.CalendarReminderStatus(
            state="incomplete",
            event_summary="raid",
            time_summary="not set",
            next_action="Finish setup",
        ),
    )

    assert status.combined_state == "incomplete"
    assert status.combined_next_action == "Finish setup"


@pytest.mark.asyncio
async def test_build_summary_uses_read_only_loaders() -> None:
    calls = []

    async def account_loader(user_id):
        calls.append(("account", user_id))
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})

    def reminder_loader(user_id):
        calls.append(("reminder", user_id))
        return {"subscriptions": ["all"], "reminder_times": ["24h"]}

    def calendar_reminder_loader(user_id):
        calls.append(("calendar_reminder", user_id))
        return CalendarReminderConfigState(
            enabled=True,
            selected_types=("raid",),
            selected_offsets=("24h",),
        )

    def calendar_event_catalog_loader():
        calls.append(("calendar_catalog", None))
        return service.reminders_summary.CalendarEventCatalog(
            available=True,
            event_types=("raid",),
        )

    summary = await service.build_player_self_service_summary(
        42,
        account_loader=account_loader,
        reminder_loader=reminder_loader,
        calendar_reminder_loader=calendar_reminder_loader,
        calendar_event_catalog_loader=calendar_event_catalog_loader,
        utc_clock=lambda: datetime(2026, 7, 14, 15, 30, tzinfo=UTC),
    )

    assert summary.discord_user_id == 42
    assert summary.accounts.main_state == "set"
    assert summary.reminders.state == "on"
    assert ("account", 42) in calls
    assert ("reminder", 42) in calls
    assert ("calendar_reminder", 42) in calls
    assert ("calendar_catalog", None) in calls
    assert not {"preference", "profile_preference", "vip", "inventory"}.intersection(
        name for name, _value in calls
    )
    assert summary.reminders.calendar.state == "on"
    assert summary.reminders_summary is not None
    assert summary.reminders_summary.configuration_state.value == "ACTIVE"
    assert summary.reminders_summary.calendar.event_summary == "Raid"
    assert summary.reminders_summary.generated_at_utc == datetime(2026, 7, 14, 15, 30, tzinfo=UTC)


def test_player_self_service_service_has_no_ui_framework_dependency() -> None:
    source = Path("player_self_service/service.py").read_text(encoding="utf-8")
    framework_name = "dis" + "cord"

    assert f"import {framework_name}" not in source
    assert f"{framework_name}." not in source


def test_generic_summary_exposes_no_obsolete_inventory_or_visibility_loaders() -> None:
    parameters = inspect.signature(service.build_player_self_service_summary).parameters

    assert "preference_loader" not in parameters
    assert "profile_preference_loader" not in parameters
    assert "vip_profile_loader" not in parameters
    assert "inventory_snapshot_loader" not in parameters
