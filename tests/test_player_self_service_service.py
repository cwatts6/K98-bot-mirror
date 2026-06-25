from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from event_calendar.reminder_config_service import CalendarReminderConfigState
from inventory.models import InventoryReportVisibility
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


def test_export_status_is_unavailable_until_account_is_registered() -> None:
    account_status = service.summarize_account_status(summarize_accounts({}))

    export_status = service.summarize_export_status(account_status)

    assert export_status.action_state == "unavailable"
    assert export_status.stats_export == "Unavailable"
    assert export_status.action_summary == "Register an account first."


def test_export_status_is_actionable_for_registered_accounts() -> None:
    account_status = service.summarize_account_status(
        summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})
    )

    export_status = service.summarize_export_status(account_status)

    assert export_status.action_state == "actionable"
    assert export_status.stats_export == "Excel / CSV / Google Sheets"
    assert export_status.action_summary == "Ready"


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
async def test_preference_status_reads_private_public_unset_and_failure() -> None:
    async def private_loader(_uid):
        return SimpleNamespace(ok=True, visibility=InventoryReportVisibility.ONLY_ME)

    async def public_loader(_uid):
        return SimpleNamespace(ok=True, visibility=InventoryReportVisibility.PUBLIC)

    async def unset_loader(_uid):
        return SimpleNamespace(ok=True, visibility=None)

    async def failed_loader(_uid):
        return SimpleNamespace(ok=False, error="db unavailable")

    assert (
        await service.summarize_preference_status(1, preference_loader=private_loader)
    ).inventory_visibility == "private"
    assert (
        await service.summarize_preference_status(1, preference_loader=public_loader)
    ).inventory_visibility == "public"
    assert (
        await service.summarize_preference_status(1, preference_loader=unset_loader)
    ).inventory_visibility == "not set"

    failed = await service.summarize_preference_status(1, preference_loader=failed_loader)
    assert failed.inventory_visibility == "unknown"
    assert failed.next_action == "Try again"


@pytest.mark.asyncio
async def test_build_summary_uses_read_only_loaders() -> None:
    calls = []

    async def account_loader(user_id):
        calls.append(("account", user_id))
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})

    def reminder_loader(user_id):
        calls.append(("reminder", user_id))
        return {"subscriptions": ["all"], "reminder_times": ["24h"]}

    async def preference_loader(user_id):
        calls.append(("preference", user_id))
        return SimpleNamespace(ok=True, visibility=InventoryReportVisibility.PUBLIC)

    async def vip_profile_loader(governor_id):
        calls.append(("vip", governor_id))
        return SimpleNamespace(vip_level_label="VIP 19")

    def calendar_reminder_loader(user_id):
        calls.append(("calendar_reminder", user_id))
        return CalendarReminderConfigState(
            enabled=True,
            selected_types=("raid",),
            selected_offsets=("24h",),
        )

    summary = await service.build_player_self_service_summary(
        42,
        account_loader=account_loader,
        reminder_loader=reminder_loader,
        calendar_reminder_loader=calendar_reminder_loader,
        preference_loader=preference_loader,
        vip_profile_loader=vip_profile_loader,
    )

    assert summary.discord_user_id == 42
    assert summary.accounts.main_state == "set"
    assert summary.reminders.state == "on"
    assert summary.preferences.inventory_visibility == "public"
    assert ("account", 42) in calls
    assert ("reminder", 42) in calls
    assert ("calendar_reminder", 42) in calls
    assert ("preference", 42) in calls
    assert ("vip", 111) in calls
    assert summary.preferences.vip_summary == "Main Gov - 19"
    assert summary.reminders.calendar.state == "on"
    assert summary.exports.action_state == "actionable"


@pytest.mark.asyncio
async def test_vip_summary_lists_registered_account_levels() -> None:
    account_summary = summarize_accounts(
        {
            "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
            "Alt 1": {"GovernorID": "222", "GovernorName": "Alt Gov"},
        }
    )

    async def vip_profile_loader(governor_id):
        labels = {111: "VIP 19", 222: "Unknown / not set"}
        return SimpleNamespace(vip_level_label=labels[governor_id])

    summary = await service.summarize_vip_status(
        account_summary,
        profile_loader=vip_profile_loader,
    )

    assert summary == "Main Gov - 19, Alt Gov - not set"


def test_player_self_service_service_has_no_ui_framework_dependency() -> None:
    source = Path("player_self_service/service.py").read_text(encoding="utf-8")
    framework_name = "dis" + "cord"

    assert f"import {framework_name}" not in source
    assert f"{framework_name}." not in source
