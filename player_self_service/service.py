"""Read-only summary service for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from dataclasses import replace
import logging
from typing import Any

from inventory import profile_service
from inventory import reporting_service
from inventory.models import InventoryReportVisibility
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
class ReminderStatus:
    state: str
    event_summary: str
    time_summary: str
    next_action: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PreferenceStatus:
    inventory_visibility: str
    exports_summary: str
    next_action: str
    vip_summary: str = "use Update VIP to set account VIP levels"
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ExportStatus:
    stats_export: str
    inventory_export: str
    privacy_note: str


@dataclass(frozen=True, slots=True)
class PlayerSelfServiceSummary:
    discord_user_id: int
    accounts: AccountStatus
    reminders: ReminderStatus
    preferences: PreferenceStatus
    exports: ExportStatus


AccountLoader = Callable[[int], Awaitable[AccountResolutionSummary]]
ReminderLoader = Callable[[int], dict[str, Any] | None]
PreferenceLoader = Callable[[int], Awaitable[Any]]
VipProfileLoader = Callable[[int], Awaitable[Any]]


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


async def summarize_preference_status(
    discord_user_id: int,
    *,
    preference_loader: PreferenceLoader = reporting_service.read_visibility_preference,
) -> PreferenceStatus:
    try:
        result = await preference_loader(discord_user_id)
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

    ok = bool(getattr(result, "ok", True))
    if not ok:
        return PreferenceStatus(
            inventory_visibility="unknown",
            exports_summary="available through private export tools",
            next_action="Try again",
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


def summarize_export_status() -> ExportStatus:
    return ExportStatus(
        stats_export="stats export available",
        inventory_export="inventory export available for approved records",
        privacy_note="file exports are delivered privately",
    )


async def build_player_self_service_summary(
    discord_user_id: int,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    reminder_loader: ReminderLoader = get_user_config,
    preference_loader: PreferenceLoader = reporting_service.read_visibility_preference,
    vip_profile_loader: VipProfileLoader = profile_service.fetch_inventory_profile,
) -> PlayerSelfServiceSummary:
    account_summary_task = account_loader(int(discord_user_id))
    preference_task = summarize_preference_status(
        int(discord_user_id),
        preference_loader=preference_loader,
    )
    account_summary, preferences = await asyncio.gather(account_summary_task, preference_task)
    vip_summary = await summarize_vip_status(
        account_summary,
        profile_loader=vip_profile_loader,
    )
    preferences = replace(preferences, vip_summary=vip_summary)

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

    return PlayerSelfServiceSummary(
        discord_user_id=int(discord_user_id),
        accounts=summarize_account_status(account_summary),
        reminders=reminders,
        preferences=preferences,
        exports=summarize_export_status(),
    )
