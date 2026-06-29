"""Read-only summary service for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
import logging
from typing import Any

from bot_config import INVENTORY_UPLOAD_CHANNEL_ID
from event_calendar.reminder_config_service import (
    CalendarReminderConfigState,
    load_user_calendar_reminder_state,
)
from inventory import profile_service, reporting_service
from inventory.models import InventoryReportVisibility, RegisteredGovernor
from inventory.parsing import format_resource_value
from player_self_service import profile_preference_service
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
class PreferenceStatus:
    inventory_visibility: str
    exports_summary: str
    next_action: str
    vip_summary: str = "use Update VIP to set account VIP levels"
    timezone: str = "not set"
    location_country: str = "not set"
    preferred_language: str = "not set"
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ExportStatus:
    stats_export: str
    inventory_export: str
    privacy_note: str
    action_state: str = "actionable"
    action_summary: str = "Default private exports are available here."


@dataclass(frozen=True, slots=True)
class InventoryCategoryStatus:
    state: str
    value: str
    detail: str
    governor_count: int = 0
    latest_scan_label: str = "not available"


def _default_inventory_category() -> InventoryCategoryStatus:
    return InventoryCategoryStatus(
        state="missing",
        value="No approved data",
        detail="Upload inventory screenshots to begin.",
    )


@dataclass(frozen=True, slots=True)
class InventoryStatus:
    state: str
    account_summary: str
    resources: InventoryCategoryStatus = field(default_factory=_default_inventory_category)
    speedups: InventoryCategoryStatus = field(default_factory=_default_inventory_category)
    materials: InventoryCategoryStatus = field(default_factory=_default_inventory_category)
    next_action: str = "Open Report"
    upload_guidance: str = "Use the inventory upload channel to add screenshots."
    error: str | None = None


def _default_inventory_status() -> InventoryStatus:
    return InventoryStatus(
        state="unknown",
        account_summary="Inventory data not loaded yet.",
        next_action="Try again",
        upload_guidance="Use the inventory upload channel to add screenshots.",
    )


@dataclass(frozen=True, slots=True)
class PlayerSelfServiceSummary:
    discord_user_id: int
    accounts: AccountStatus
    reminders: ReminderStatus
    preferences: PreferenceStatus
    exports: ExportStatus
    inventory: InventoryStatus = field(default_factory=_default_inventory_status)


AccountLoader = Callable[[int], Awaitable[AccountResolutionSummary]]
ReminderLoader = Callable[[int], dict[str, Any] | None]
CalendarReminderLoader = Callable[[int], CalendarReminderConfigState]
PreferenceLoader = Callable[[int], Awaitable[Any]]
ProfilePreferenceLoader = Callable[
    [int], Awaitable[profile_preference_service.UserProfilePreferenceRead]
]
VipProfileLoader = Callable[[int], Awaitable[Any]]
InventorySnapshotLoader = Callable[
    [list[RegisteredGovernor]], Awaitable[reporting_service.LatestInventorySnapshot]
]


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


async def summarize_preference_status(
    discord_user_id: int,
    *,
    preference_loader: PreferenceLoader = reporting_service.read_visibility_preference,
    profile_preference_loader: ProfilePreferenceLoader = (
        profile_preference_service.read_user_profile_preference
    ),
) -> PreferenceStatus:
    try:
        result, profile_result = await asyncio.gather(
            preference_loader(discord_user_id),
            profile_preference_loader(discord_user_id),
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception(
            "player_self_service_preferences_unavailable user_id=%s",
            discord_user_id,
        )
        return PreferenceStatus(
            inventory_visibility="unknown",
            exports_summary="available through private export tools",
            next_action="Try again",
            error=f"{type(exc).__name__}: {exc}",
        )

    profile_error = None
    timezone = "not set"
    location_country = "not set"
    preferred_language = "not set"
    if getattr(profile_result, "ok", False):
        profile = getattr(profile_result, "profile", None)
        if profile is not None:
            timezone = getattr(profile, "timezone_label", "not set")
            location_country = getattr(profile, "country_label", "not set")
            preferred_language = getattr(profile, "language_label", "not set")
    else:
        profile_error = getattr(profile_result, "error", None) or "profile source unavailable"

    ok = bool(getattr(result, "ok", True))
    if not ok:
        return PreferenceStatus(
            inventory_visibility="unknown",
            exports_summary="available through private export tools",
            next_action="Try again",
            timezone=timezone,
            location_country=location_country,
            preferred_language=preferred_language,
            error=getattr(result, "error", None) or "preference source unavailable",
        )

    visibility = getattr(result, "visibility", result)
    if visibility == InventoryReportVisibility.ONLY_ME:
        label = "private"
    elif visibility == InventoryReportVisibility.PUBLIC:
        label = "public"
    elif visibility is None:
        label = "not set"
    else:
        label = "unknown"

    next_action = "Review preferences" if label != "unknown" else "Try again"
    return PreferenceStatus(
        inventory_visibility=label,
        exports_summary="available through private export tools",
        next_action=next_action,
        timezone=timezone,
        location_country=location_country,
        preferred_language=preferred_language,
        error=profile_error,
    )


def _compact_vip_label(value: object) -> str:
    label = str(value or "").strip()
    if not label or label.casefold() == "unknown / not set":
        return "not set"
    if label.startswith("VIP "):
        return label.removeprefix("VIP ").replace(" or less", " or less")
    return label


async def summarize_vip_status(
    account_summary: AccountResolutionSummary,
    *,
    profile_loader: VipProfileLoader = profile_service.fetch_inventory_profile,
) -> str:
    if not account_summary.ok:
        return "unavailable"
    if not account_summary.resolved_accounts:
        return "register an account, then use Update VIP"
    try:
        profiles = await asyncio.gather(
            *(
                profile_loader(int(account.governor_id))
                for account in account_summary.resolved_accounts
            )
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("player_self_service_vip_profiles_unavailable")
        return "temporarily unavailable"

    labels: list[str] = []
    for account, profile in zip(account_summary.resolved_accounts, profiles, strict=True):
        name = account.governor_name or account.governor_id_str
        vip = _compact_vip_label(getattr(profile, "vip_level_label", None))
        labels.append(f"{name} - {vip}")
    return ", ".join(labels)


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


def _upload_guidance(upload_channel_id: int | None = INVENTORY_UPLOAD_CHANNEL_ID) -> str:
    if upload_channel_id:
        return f"Use `/inventory import` or upload inventory screenshots in <#{int(upload_channel_id)}>."
    return "Use `/inventory import` in the inventory upload channel."


def _governors_from_account_summary(
    account_summary: AccountResolutionSummary,
) -> list[RegisteredGovernor]:
    governors: list[RegisteredGovernor] = []
    for account in account_summary.resolved_accounts:
        name = str(
            account.raw.get("GovernorName")
            or account.raw.get("Governor")
            or account.governor_name
            or account.governor_id_str
        )
        governors.append(
            RegisteredGovernor(
                governor_id=int(account.governor_id),
                governor_name=name,
                account_type=str(account.slot),
            )
        )
    return governors


def _scan_label(value: Any) -> str:
    if value is None:
        return "not available"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _category_detail(count: int, total: int, scan: Any) -> str:
    return f"{count}/{total} governors | latest {_scan_label(scan)}"


def _inventory_category_status(
    *,
    count: int,
    total: int,
    value: str,
    latest_scan: Any,
) -> InventoryCategoryStatus:
    return InventoryCategoryStatus(
        state="available",
        value=value,
        detail=_category_detail(count, total, latest_scan),
        governor_count=count,
        latest_scan_label=_scan_label(latest_scan),
    )


def summarize_inventory_snapshot(
    snapshot: reporting_service.LatestInventorySnapshot,
    *,
    upload_channel_id: int | None = INVENTORY_UPLOAD_CHANNEL_ID,
) -> InventoryStatus:
    total_governors = len(snapshot.governors)
    guidance = _upload_guidance(upload_channel_id)
    if total_governors <= 0:
        return InventoryStatus(
            state="none",
            account_summary="No registered governors.",
            next_action="Register account",
            upload_guidance="Register a governor before uploading inventory screenshots.",
        )

    resources = _default_inventory_category()
    if snapshot.resources:
        total = sum(point.total for point in snapshot.resources)
        latest_scan = max((point.scan_utc for point in snapshot.resources), default=None)
        resources = _inventory_category_status(
            count=len(snapshot.resources),
            total=total_governors,
            value=f"{format_resource_value(total)} RSS",
            latest_scan=latest_scan,
        )

    speedups = _default_inventory_category()
    if snapshot.speedups:
        total_days = sum(
            float(point.building_days)
            + float(point.research_days)
            + float(point.training_days)
            + float(point.healing_days)
            + float(point.universal_days)
            for point in snapshot.speedups
        )
        latest_scan = max((point.scan_utc for point in snapshot.speedups), default=None)
        speedups = _inventory_category_status(
            count=len(snapshot.speedups),
            total=total_governors,
            value=f"{int(round(total_days)):,}d total",
            latest_scan=latest_scan,
        )

    materials = _default_inventory_category()
    if snapshot.materials:
        total_legendary = sum(float(point.total_legendary) for point in snapshot.materials)
        latest_scan = max((point.scan_utc for point in snapshot.materials), default=None)
        materials = _inventory_category_status(
            count=len(snapshot.materials),
            total=total_governors,
            value=f"{total_legendary:,.0f} legendary",
            latest_scan=latest_scan,
        )

    categories = (resources, speedups, materials)
    available_count = sum(category.state == "available" for category in categories)
    approved_governor_count = min(
        (category.governor_count for category in categories if category.state == "available"),
        default=0,
    )
    has_complete_category_coverage = all(
        category.state == "available" and category.governor_count >= total_governors
        for category in categories
    )
    if has_complete_category_coverage:
        state = "available"
        account_summary = (
            f"{total_governors} registered governor(s) with complete approved inventory data."
        )
    elif available_count > 0:
        state = "partial"
        account_summary = (
            f"Approved inventory data for {approved_governor_count}/{total_governors} "
            "registered governor(s)."
        )
    else:
        state = "empty"
        account_summary = (
            f"No approved inventory data for {total_governors} registered governor(s)."
        )

    return InventoryStatus(
        state=state,
        account_summary=account_summary,
        resources=resources,
        speedups=speedups,
        materials=materials,
        next_action="Open Report",
        upload_guidance=guidance,
    )


async def summarize_inventory_status(
    account_summary: AccountResolutionSummary,
    *,
    snapshot_loader: InventorySnapshotLoader = reporting_service.build_latest_inventory_snapshot,
    upload_channel_id: int | None = INVENTORY_UPLOAD_CHANNEL_ID,
) -> InventoryStatus:
    if not account_summary.ok:
        return InventoryStatus(
            state="unknown",
            account_summary="Inventory account data is unavailable.",
            next_action="Try again",
            upload_guidance=_upload_guidance(upload_channel_id),
            error=account_summary.error or "account source unavailable",
        )

    governors = _governors_from_account_summary(account_summary)
    if not governors:
        return summarize_inventory_snapshot(
            reporting_service.LatestInventorySnapshot(governors=()),
            upload_channel_id=upload_channel_id,
        )

    try:
        snapshot = await snapshot_loader(governors)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("player_self_service_inventory_unavailable")
        return InventoryStatus(
            state="unknown",
            account_summary="Inventory data is temporarily unavailable.",
            next_action="Try again",
            upload_guidance=_upload_guidance(upload_channel_id),
            error=f"{type(exc).__name__}: {exc}",
        )
    return summarize_inventory_snapshot(snapshot, upload_channel_id=upload_channel_id)


async def build_player_self_service_summary(
    discord_user_id: int,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    reminder_loader: ReminderLoader = get_user_config,
    calendar_reminder_loader: CalendarReminderLoader = load_user_calendar_reminder_state,
    preference_loader: PreferenceLoader = reporting_service.read_visibility_preference,
    profile_preference_loader: ProfilePreferenceLoader = (
        profile_preference_service.read_user_profile_preference
    ),
    vip_profile_loader: VipProfileLoader = profile_service.fetch_inventory_profile,
    inventory_snapshot_loader: InventorySnapshotLoader = (
        reporting_service.build_latest_inventory_snapshot
    ),
) -> PlayerSelfServiceSummary:
    account_summary_task = account_loader(int(discord_user_id))
    preference_task = summarize_preference_status(
        int(discord_user_id),
        preference_loader=preference_loader,
        profile_preference_loader=profile_preference_loader,
    )
    account_summary, preferences = await asyncio.gather(account_summary_task, preference_task)
    vip_summary = await summarize_vip_status(
        account_summary,
        profile_loader=vip_profile_loader,
    )
    preferences = replace(preferences, vip_summary=vip_summary)
    inventory = await summarize_inventory_status(
        account_summary,
        snapshot_loader=inventory_snapshot_loader,
    )

    try:
        reminder_config = await asyncio.to_thread(reminder_loader, int(discord_user_id))
    except asyncio.CancelledError:
        raise
    except Exception as exc:
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

    try:
        calendar_state = await asyncio.to_thread(
            calendar_reminder_loader,
            int(discord_user_id),
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
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

    accounts = summarize_account_status(account_summary)
    return PlayerSelfServiceSummary(
        discord_user_id=int(discord_user_id),
        accounts=accounts,
        reminders=reminders,
        preferences=preferences,
        exports=summarize_export_status(accounts),
        inventory=inventory,
    )
