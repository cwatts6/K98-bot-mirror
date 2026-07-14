from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from event_calendar.reminder_config_service import CalendarReminderConfigState
from inventory import reporting_service
from inventory.models import (
    InventoryMaterialPoint,
    InventoryReportVisibility,
    InventoryResourcePoint,
    InventorySpeedupPoint,
)
from player_self_service import service
from player_self_service.profile_preference_service import (
    UserProfilePreference,
    UserProfilePreferenceRead,
)
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


def test_inventory_snapshot_summary_handles_approved_data() -> None:
    scan = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
    snapshot = reporting_service.LatestInventorySnapshot(
        governors=(
            service.RegisteredGovernor(111, "Main Gov", "Main"),
            service.RegisteredGovernor(222, "Alt Gov", "Alt 1"),
        ),
        resources=(InventoryResourcePoint(scan_utc=scan, food=100, wood=200, stone=300, gold=400),),
        speedups=(
            InventorySpeedupPoint(
                scan_utc=scan,
                building_days=1,
                research_days=2,
                training_days=3,
                healing_days=4,
                universal_days=5,
            ),
        ),
        materials=(
            InventoryMaterialPoint(
                scan_utc=scan,
                animal_bone_legendary=1,
                leather_legendary=2,
                ebony_legendary=3,
                iron_ore_legendary=4,
                choice_chest_legendary=5,
            ),
        ),
    )

    status = service.summarize_inventory_snapshot(snapshot, upload_channel_id=123)

    assert status.state == "partial"
    assert status.account_summary == "Approved inventory data for 1/2 registered governor(s)."
    assert status.resources.value == "1K RSS"
    assert status.resources.detail == "1/2 governors | latest 2026-06-25"
    assert status.speedups.value == "15d total"
    assert status.materials.value == "15 legendary"
    assert "<#123>" in status.upload_guidance


def test_inventory_snapshot_summary_requires_complete_category_coverage() -> None:
    scan = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
    snapshot = reporting_service.LatestInventorySnapshot(
        governors=(
            service.RegisteredGovernor(111, "Main Gov", "Main"),
            service.RegisteredGovernor(222, "Alt Gov", "Alt 1"),
        ),
        resources=(
            InventoryResourcePoint(scan_utc=scan, food=100, wood=200, stone=300, gold=400),
            InventoryResourcePoint(scan_utc=scan, food=200, wood=300, stone=400, gold=500),
        ),
        speedups=(
            InventorySpeedupPoint(
                scan_utc=scan,
                building_days=1,
                research_days=2,
                training_days=3,
                healing_days=4,
                universal_days=5,
            ),
            InventorySpeedupPoint(
                scan_utc=scan,
                building_days=2,
                research_days=3,
                training_days=4,
                healing_days=5,
                universal_days=6,
            ),
        ),
        materials=(
            InventoryMaterialPoint(
                scan_utc=scan,
                animal_bone_legendary=1,
                leather_legendary=2,
                ebony_legendary=3,
                iron_ore_legendary=4,
                choice_chest_legendary=5,
            ),
            InventoryMaterialPoint(
                scan_utc=scan,
                animal_bone_legendary=2,
                leather_legendary=3,
                ebony_legendary=4,
                iron_ore_legendary=5,
                choice_chest_legendary=6,
            ),
        ),
    )

    status = service.summarize_inventory_snapshot(snapshot, upload_channel_id=123)

    assert status.state == "available"
    assert (
        status.account_summary == "2 registered governor(s) with complete approved inventory data."
    )
    assert status.resources.detail == "2/2 governors | latest 2026-06-25"


def test_inventory_snapshot_summary_uses_conservative_partial_coverage() -> None:
    scan = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
    snapshot = reporting_service.LatestInventorySnapshot(
        governors=(
            service.RegisteredGovernor(111, "Main Gov", "Main"),
            service.RegisteredGovernor(222, "Alt Gov", "Alt 1"),
        ),
        resources=(
            InventoryResourcePoint(scan_utc=scan, food=100, wood=200, stone=300, gold=400),
            InventoryResourcePoint(scan_utc=scan, food=200, wood=300, stone=400, gold=500),
        ),
        speedups=(
            InventorySpeedupPoint(
                scan_utc=scan,
                building_days=1,
                research_days=2,
                training_days=3,
                healing_days=4,
                universal_days=5,
            ),
        ),
        materials=(
            InventoryMaterialPoint(
                scan_utc=scan,
                animal_bone_legendary=1,
                leather_legendary=2,
                ebony_legendary=3,
                iron_ore_legendary=4,
                choice_chest_legendary=5,
            ),
            InventoryMaterialPoint(
                scan_utc=scan,
                animal_bone_legendary=2,
                leather_legendary=3,
                ebony_legendary=4,
                iron_ore_legendary=5,
                choice_chest_legendary=6,
            ),
        ),
    )

    status = service.summarize_inventory_snapshot(snapshot, upload_channel_id=123)

    assert status.state == "partial"
    assert status.account_summary == "Approved inventory data for 1/2 registered governor(s)."
    assert status.next_action == "Open Report"


def test_inventory_snapshot_summary_handles_no_approved_data() -> None:
    snapshot = reporting_service.LatestInventorySnapshot(
        governors=(service.RegisteredGovernor(111, "Main Gov", "Main"),),
    )

    status = service.summarize_inventory_snapshot(snapshot, upload_channel_id=None)

    assert status.state == "empty"
    assert status.next_action == "Open Report"
    assert status.resources.value == "No approved data"
    assert "`/inventory import`" in status.upload_guidance


@pytest.mark.asyncio
async def test_inventory_status_does_not_fetch_without_accounts() -> None:
    async def snapshot_loader(_governors):
        raise AssertionError("should not fetch inventory without registered governors")

    status = await service.summarize_inventory_status(
        summarize_accounts({}),
        snapshot_loader=snapshot_loader,
    )

    assert status.state == "none"
    assert status.next_action == "Register account"


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
    async def profile_loader(_uid):
        return UserProfilePreferenceRead(
            ok=True,
            profile=UserProfilePreference(
                timezone_name="Europe/London",
                location_country_code="GB",
                preferred_language_tag="en-GB",
            ),
        )

    async def private_loader(_uid):
        return SimpleNamespace(ok=True, visibility=InventoryReportVisibility.ONLY_ME)

    async def public_loader(_uid):
        return SimpleNamespace(ok=True, visibility=InventoryReportVisibility.PUBLIC)

    async def unset_loader(_uid):
        return SimpleNamespace(ok=True, visibility=None)

    async def failed_loader(_uid):
        return SimpleNamespace(ok=False, error="db unavailable")

    assert (
        await service.summarize_preference_status(
            1,
            preference_loader=private_loader,
            profile_preference_loader=profile_loader,
        )
    ).inventory_visibility == "private"
    public = await service.summarize_preference_status(
        1,
        preference_loader=public_loader,
        profile_preference_loader=profile_loader,
    )
    assert public.inventory_visibility == "public"
    assert public.timezone == "Europe/London"
    assert public.location_country == "United Kingdom (GB)"
    assert public.preferred_language == "English (en-GB)"
    assert (
        await service.summarize_preference_status(
            1,
            preference_loader=unset_loader,
            profile_preference_loader=profile_loader,
        )
    ).inventory_visibility == "not set"

    failed = await service.summarize_preference_status(
        1,
        preference_loader=failed_loader,
        profile_preference_loader=profile_loader,
    )
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

    async def profile_preference_loader(user_id):
        calls.append(("profile_preference", user_id))
        return UserProfilePreferenceRead(
            ok=True,
            profile=UserProfilePreference(
                timezone_name="Europe/London",
                location_country_code="GB",
                preferred_language_tag="en-GB",
            ),
        )

    async def vip_profile_loader(governor_id):
        calls.append(("vip", governor_id))
        return SimpleNamespace(vip_level_label="VIP 19")

    async def inventory_snapshot_loader(governors):
        calls.append(("inventory", tuple(item.governor_id for item in governors)))
        return reporting_service.LatestInventorySnapshot(governors=tuple(governors))

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
        preference_loader=preference_loader,
        profile_preference_loader=profile_preference_loader,
        vip_profile_loader=vip_profile_loader,
        inventory_snapshot_loader=inventory_snapshot_loader,
    )

    assert summary.discord_user_id == 42
    assert summary.accounts.main_state == "set"
    assert summary.reminders.state == "on"
    assert summary.preferences.inventory_visibility == "public"
    assert ("account", 42) in calls
    assert ("reminder", 42) in calls
    assert ("calendar_reminder", 42) in calls
    assert ("calendar_catalog", None) in calls
    assert ("preference", 42) in calls
    assert ("profile_preference", 42) in calls
    assert ("vip", 111) in calls
    assert ("inventory", (111,)) in calls
    assert summary.preferences.vip_summary == "Main Gov - 19"
    assert summary.preferences.location_country == "United Kingdom (GB)"
    assert summary.reminders.calendar.state == "on"
    assert summary.reminders_summary is not None
    assert summary.reminders_summary.configuration_state.value == "ACTIVE"
    assert summary.reminders_summary.calendar.event_summary == "Raid"
    assert summary.reminders_summary.generated_at_utc == datetime(2026, 7, 14, 15, 30, tzinfo=UTC)
    assert summary.exports.action_state == "actionable"
    assert summary.inventory.state == "empty"


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
