"""Service layer for MGE signup/create/edit/withdraw logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import Any

from governor_registry import load_registry
from mge.dal import mge_signup_dal
from mge.mge_cache import get_commanders_for_variant
from mge.mge_validation import (
    normalize_priority,
    normalize_rank_band,
    validate_event_is_mutable_for_anyone,
    validate_event_not_open_mode,
    validate_heads,
    validate_priority,
    validate_rank_band,
    validate_self_service_window,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ServiceResult:
    success: bool
    message: str
    signup_id: int | None = None


def _now_utc(now_utc: datetime | None) -> datetime:
    if now_utc is None:
        return datetime.now(UTC)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=UTC)
    return now_utc.astimezone(UTC)


def _is_admin_or_leadership(actor_roles: set[int], admin_role_ids: set[int]) -> bool:
    return bool(actor_roles.intersection(admin_role_ids))


def get_linked_governors_for_user(discord_user_id: int) -> list[dict[str, str]]:
    registry = load_registry() or {}
    block = registry.get(str(discord_user_id)) or registry.get(discord_user_id) or {}
    accounts = block.get("accounts") or {}
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    for _slot, info in accounts.items():
        gid = str(info.get("GovernorID") or "").strip()
        gname = str(info.get("GovernorName") or "").strip()
        if not gid or gid in seen:
            continue
        seen.add(gid)
        rows.append({"GovernorID": gid, "GovernorName": gname or "Unknown"})
    return rows


def _is_governor_linked_to_user(discord_user_id: int, governor_id: int) -> bool:
    linked = get_linked_governors_for_user(discord_user_id)
    return any(str(item["GovernorID"]) == str(governor_id) for item in linked)


def _commander_options_for_event_variant(variant_name: str) -> dict[int, str]:
    options = get_commanders_for_variant(variant_name)
    result: dict[int, str] = {}
    for row in options:
        try:
            cid = int(row["CommanderId"])
            cname = str(row.get("CommanderName") or "").strip()
            if cname:
                result[cid] = cname
        except Exception:
            continue
    return result


def get_event_context(event_id: int) -> dict[str, Any] | None:
    return mge_signup_dal.fetch_event_signup_context(event_id)


def create_signup(
    *,
    event_id: int,
    actor_discord_id: int,
    actor_role_ids: set[int],
    admin_role_ids: set[int],
    governor_id: int,
    governor_name_snapshot: str,
    request_priority: str,
    preferred_rank_band: str | None,
    requested_commander_id: int,
    current_heads: int,
    kingdom_role: str | None,
    gear_text: str | None,
    armament_text: str | None,
    now_utc: datetime | None = None,
) -> ServiceResult:
    now = _now_utc(now_utc)
    event = mge_signup_dal.fetch_event_signup_context(event_id)
    if not event:
        return ServiceResult(False, "Event not found.")

    for check in (
        validate_event_not_open_mode(event),
        validate_event_is_mutable_for_anyone(event),
    ):
        if not check.valid:
            return ServiceResult(False, check.message)

    is_admin = _is_admin_or_leadership(actor_role_ids, admin_role_ids)
    if not is_admin:
        window_check = validate_self_service_window(event, now)
        if not window_check.valid:
            return ServiceResult(False, window_check.message)
        if not _is_governor_linked_to_user(actor_discord_id, governor_id):
            return ServiceResult(False, "Governor is not linked to your Discord account.")

    for check in (
        validate_priority(request_priority),
        validate_rank_band(preferred_rank_band),
        validate_heads(current_heads),
    ):
        if not check.valid:
            return ServiceResult(False, check.message)

    active = mge_signup_dal.fetch_active_signup_by_event_governor(event_id, governor_id)
    if active:
        return ServiceResult(False, "An active signup already exists for this governor/event.")

    variant_name = str(event.get("VariantName") or "").strip()
    commanders = _commander_options_for_event_variant(variant_name)
    commander_name = commanders.get(int(requested_commander_id))
    if not commander_name:
        return ServiceResult(False, "Requested commander is not eligible for this event variant.")

    signup_id = mge_signup_dal.insert_signup(
        event_id=event_id,
        governor_id=governor_id,
        governor_name_snapshot=governor_name_snapshot,
        discord_user_id=(
            actor_discord_id
            if (not is_admin or _is_governor_linked_to_user(actor_discord_id, governor_id))
            else None
        ),
        request_priority=normalize_priority(request_priority).title(),
        preferred_rank_band=normalize_rank_band(preferred_rank_band),
        requested_commander_id=requested_commander_id,
        requested_commander_name=commander_name,
        current_heads=int(current_heads),
        kingdom_role=kingdom_role,
        gear_text=gear_text,
        armament_text=armament_text,
        source="admin" if is_admin else "discord",
        now_utc=now,
    )
    if signup_id is None:
        return ServiceResult(False, "Failed to create signup.")

    mge_signup_dal.insert_signup_audit(
        signup_id=signup_id,
        event_id=event_id,
        governor_id=governor_id,
        action_type="create" if not is_admin else "admin_add",
        actor_discord_id=actor_discord_id,
        details={"source": "admin" if is_admin else "discord"},
        now_utc=now,
    )
    return ServiceResult(True, "Signup created.", signup_id=signup_id)


def edit_signup(
    *,
    signup_id: int,
    event_id: int,
    actor_discord_id: int,
    actor_role_ids: set[int],
    admin_role_ids: set[int],
    existing_governor_id: int,
    request_priority: str,
    preferred_rank_band: str | None,
    requested_commander_id: int,
    current_heads: int,
    kingdom_role: str | None,
    gear_text: str | None,
    armament_text: str | None,
    now_utc: datetime | None = None,
) -> ServiceResult:
    now = _now_utc(now_utc)
    event = mge_signup_dal.fetch_event_signup_context(event_id)
    if not event:
        return ServiceResult(False, "Event not found.")

    for check in (
        validate_event_not_open_mode(event),
        validate_event_is_mutable_for_anyone(event),
    ):
        if not check.valid:
            return ServiceResult(False, check.message)

    is_admin = _is_admin_or_leadership(actor_role_ids, admin_role_ids)
    if not is_admin:
        window_check = validate_self_service_window(event, now)
        if not window_check.valid:
            return ServiceResult(False, window_check.message)
        if not _is_governor_linked_to_user(actor_discord_id, existing_governor_id):
            return ServiceResult(False, "You can only edit your own linked governor signup.")

    for check in (
        validate_priority(request_priority),
        validate_rank_band(preferred_rank_band),
        validate_heads(current_heads),
    ):
        if not check.valid:
            return ServiceResult(False, check.message)

    variant_name = str(event.get("VariantName") or "").strip()
    commanders = _commander_options_for_event_variant(variant_name)
    commander_name = commanders.get(int(requested_commander_id))
    if not commander_name:
        return ServiceResult(False, "Requested commander is not eligible for this event variant.")

    ok = mge_signup_dal.update_signup(
        signup_id=signup_id,
        request_priority=normalize_priority(request_priority).title(),
        preferred_rank_band=normalize_rank_band(preferred_rank_band),
        requested_commander_id=requested_commander_id,
        requested_commander_name=commander_name,
        current_heads=int(current_heads),
        kingdom_role=kingdom_role,
        gear_text=gear_text,
        armament_text=armament_text,
        now_utc=now,
    )
    if not ok:
        return ServiceResult(False, "Failed to update signup.")

    mge_signup_dal.insert_signup_audit(
        signup_id=signup_id,
        event_id=event_id,
        governor_id=existing_governor_id,
        action_type="edit" if not is_admin else "admin_edit",
        actor_discord_id=actor_discord_id,
        details={"source": "admin" if is_admin else "discord"},
        now_utc=now,
    )
    return ServiceResult(True, "Signup updated.", signup_id=signup_id)


def withdraw_signup(
    *,
    signup_id: int,
    event_id: int,
    governor_id: int,
    actor_discord_id: int,
    actor_role_ids: set[int],
    admin_role_ids: set[int],
    now_utc: datetime | None = None,
) -> ServiceResult:
    now = _now_utc(now_utc)
    event = mge_signup_dal.fetch_event_signup_context(event_id)
    if not event:
        return ServiceResult(False, "Event not found.")

    for check in (
        validate_event_not_open_mode(event),
        validate_event_is_mutable_for_anyone(event),
    ):
        if not check.valid:
            return ServiceResult(False, check.message)

    is_admin = _is_admin_or_leadership(actor_role_ids, admin_role_ids)
    if not is_admin:
        window_check = validate_self_service_window(event, now)
        if not window_check.valid:
            return ServiceResult(False, window_check.message)
        if not _is_governor_linked_to_user(actor_discord_id, governor_id):
            return ServiceResult(False, "You can only withdraw your own linked governor signup.")

    ok = mge_signup_dal.withdraw_signup(signup_id=signup_id, now_utc=now)
    if not ok:
        return ServiceResult(False, "Failed to withdraw signup.")

    mge_signup_dal.insert_signup_audit(
        signup_id=signup_id,
        event_id=event_id,
        governor_id=governor_id,
        action_type="withdraw" if not is_admin else "admin_remove",
        actor_discord_id=actor_discord_id,
        details={"source": "admin" if is_admin else "discord"},
        now_utc=now,
    )
    return ServiceResult(True, "Signup withdrawn.", signup_id=signup_id)
