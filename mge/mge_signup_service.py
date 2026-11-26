"""Service layer for MGE signup/create/edit/withdraw logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import Any

from core.operation_outcome import MutationOutcome
from mge.dal import mge_signup_dal, mge_signup_mutation_dal
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
from registry.registry_service import get_discord_user_for_governor
from services import governor_account_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ServiceResult:
    success: bool
    message: str
    signup_id: int | None = None
    outcome: MutationOutcome = MutationOutcome.NOT_ENTERED
    operation_id: str | None = None

    def __post_init__(self):
        if self.success and self.outcome == MutationOutcome.NOT_ENTERED:
            self.outcome = MutationOutcome.COMMITTED


def _persist(
    action,
    *,
    event_id,
    governor_id,
    actor_discord_id,
    is_admin,
    event,
    values=None,
    signup_id=None,
    expected_signup=None,
    operation_id=None,
    now_utc=None,
):
    def validate_current(current, now):
        for check in (
            validate_event_not_open_mode(current),
            validate_event_is_mutable_for_anyone(current),
        ):
            if not check.valid:
                return check.message
        if current.get("VariantName") != event.get("VariantName"):
            return "Event variant changed. Refresh before trying again."
        if not is_admin:
            check = validate_self_service_window(current, _now_utc(now))
            if not check.valid:
                return check.message
        return None

    result = mge_signup_mutation_dal.mutate_signup(
        action=action,
        event_id=event_id,
        governor_id=governor_id,
        actor_discord_id=actor_discord_id,
        is_admin=is_admin,
        values=values,
        signup_id=signup_id,
        expected_signup=expected_signup,
        operation_id=operation_id,
        now_utc=now_utc,
        validate_event=validate_current,
    )
    if result.outcome == MutationOutcome.COMMITTED:
        message = {
            "create": "Signup created.",
            "edit": "Signup updated.",
            "withdraw": "Signup withdrawn.",
        }[action]
        return ServiceResult(True, message, result.signup_id, result.outcome, result.operation_id)
    if result.outcome == MutationOutcome.UNKNOWN:
        message = (
            "The signup outcome is not yet confirmed. Do not submit again; ask an administrator to check this reference: "
            + result.operation_id
        )
    else:
        message = result.reason or "No signup change was saved. Please refresh before trying again."
    return ServiceResult(False, message, result.signup_id, result.outcome, result.operation_id)


def _now_utc(now_utc: datetime | None) -> datetime:
    if now_utc is None:
        return datetime.now(UTC)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=UTC)
    return now_utc.astimezone(UTC)


def _is_admin_or_leadership(actor_roles: set[int], admin_role_ids: set[int]) -> bool:
    return bool(actor_roles.intersection(admin_role_ids))


def get_linked_governors_for_user(discord_user_id: int) -> list[dict[str, str]]:
    summary = governor_account_service.get_account_summary_for_user_sync(discord_user_id)
    if not summary.ok:
        return []

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for account in summary.resolved_accounts:
        if account.governor_id_str in seen:
            continue
        seen.add(account.governor_id_str)
        rows.append({"GovernorID": account.governor_id_str, "GovernorName": account.governor_name})
    return rows


def _is_governor_linked_to_user(discord_user_id: int, governor_id: int) -> bool:
    summary = governor_account_service.get_account_summary_for_user_sync(discord_user_id)
    if not summary.ok:
        return False
    return summary.contains_governor_id(governor_id)


def _resolve_signup_discord_user_id(
    *,
    is_admin: bool,
    actor_discord_id: int,
    governor_id: int,
) -> int | None:
    """
    Resolve Discord identity for signup persistence.

    - Self-service: preserve existing behavior (actor is the signup owner).
    - Admin add: resolve target governor owner from registry when present.
    """
    if not is_admin:
        return int(actor_discord_id)

    owner = get_discord_user_for_governor(governor_id)
    if not owner:
        logger.info(
            "mge_admin_add_discord_identity_not_found event_governor_id=%s actor_discord_id=%s",
            governor_id,
            actor_discord_id,
        )
        return None

    resolved_discord_id = int(owner["DiscordUserID"])
    logger.info(
        "mge_admin_add_discord_identity_resolved event_governor_id=%s resolved_discord_id=%s actor_discord_id=%s",
        governor_id,
        resolved_discord_id,
        actor_discord_id,
    )
    return resolved_discord_id


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


def get_active_signup(event_id: int, governor_id: int) -> dict[str, Any] | None:
    return mge_signup_dal.fetch_active_signup_by_event_governor(event_id, governor_id)


def get_signup_for_edit(signup_id: int) -> dict[str, Any] | None:
    return mge_signup_dal.fetch_signup_by_id(signup_id)


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
    operation_id: str | None = None,
    expected_signup: dict | None = None,
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

    return _persist(
        "create",
        event_id=event_id,
        governor_id=governor_id,
        actor_discord_id=actor_discord_id,
        is_admin=is_admin,
        event=event,
        operation_id=operation_id,
        now_utc=now_utc,
        values=dict(
            governor_name_snapshot=governor_name_snapshot,
            discord_user_id=_resolve_signup_discord_user_id(
                is_admin=is_admin, actor_discord_id=actor_discord_id, governor_id=governor_id
            ),
            request_priority=normalize_priority(request_priority).title(),
            preferred_rank_band=normalize_rank_band(preferred_rank_band),
            requested_commander_id=requested_commander_id,
            requested_commander_name=commander_name,
            current_heads=int(current_heads),
            kingdom_role=kingdom_role,
            gear_text=gear_text,
            armament_text=armament_text,
        ),
    )


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
    operation_id: str | None = None,
    expected_signup: dict | None = None,
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

    return _persist(
        "edit",
        signup_id=signup_id,
        event_id=event_id,
        governor_id=existing_governor_id,
        actor_discord_id=actor_discord_id,
        is_admin=is_admin,
        event=event,
        operation_id=operation_id,
        now_utc=now_utc,
        expected_signup=expected_signup,
        values=dict(
            request_priority=normalize_priority(request_priority).title(),
            preferred_rank_band=normalize_rank_band(preferred_rank_band),
            requested_commander_id=requested_commander_id,
            requested_commander_name=commander_name,
            current_heads=int(current_heads),
            kingdom_role=kingdom_role,
            gear_text=gear_text,
            armament_text=armament_text,
        ),
    )


def withdraw_signup(
    *,
    signup_id: int,
    event_id: int,
    governor_id: int,
    actor_discord_id: int,
    actor_role_ids: set[int],
    admin_role_ids: set[int],
    now_utc: datetime | None = None,
    operation_id: str | None = None,
    expected_signup: dict | None = None,
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

    return _persist(
        "withdraw",
        signup_id=signup_id,
        event_id=event_id,
        governor_id=governor_id,
        actor_discord_id=actor_discord_id,
        is_admin=is_admin,
        event=event,
        operation_id=operation_id,
        now_utc=now_utc,
    )
