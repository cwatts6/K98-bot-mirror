from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from ark.dal.ark_dal import (
    clear_team_preference,
    get_team_preference,
    list_active_team_preferences,
    upsert_team_preference,
)
from target_utils import _name_cache, refresh_name_cache_from_sql

logger = logging.getLogger(__name__)
_ALLOWED_TEAMS = {1, 2}
_UTC = dt.UTC if hasattr(dt, "UTC") else dt.UTC


class ArkPreferenceError(ValueError):
    """Raised when Ark team preference validation fails."""


async def _ensure_governor_cache_ready() -> None:
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else None
    if rows:
        return
    await refresh_name_cache_from_sql()


async def _validate_governor_id(governor_id: int) -> dict[str, str]:
    await _ensure_governor_cache_ready()
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
    governor_id_str = str(int(governor_id))
    for row in rows or []:
        if str(row.get("GovernorID") or "").strip() == governor_id_str:
            return {
                "GovernorID": governor_id_str,
                "GovernorName": (
                    str(row.get("GovernorName") or governor_id_str).strip() or governor_id_str
                ),
            }

    logger.warning("[ARK_PREF] Invalid governor id for preference: governor_id=%s", governor_id)
    raise ArkPreferenceError("GovernorID not found in governor cache. Please verify the ID.")


def _normalize_team(team: int) -> int:
    try:
        normalized = int(team)
    except (TypeError, ValueError) as exc:
        raise ArkPreferenceError("Preferred team must be 1 or 2.") from exc
    if normalized not in _ALLOWED_TEAMS:
        raise ArkPreferenceError("Preferred team must be 1 or 2.")
    return normalized


def _normalize_updated_by(updated_by: str) -> str:
    value = str(updated_by or "").strip()
    if not value:
        raise ArkPreferenceError("updated_by is required.")
    return value[:100]


def _serialize_preference(
    row: dict[str, Any] | None, governor_name: str | None = None
) -> dict[str, Any] | None:
    if not row:
        return None
    created_at = row.get("CreatedAtUTC")
    updated_at = row.get("UpdatedAtUTC")
    return {
        "GovernorID": int(row["GovernorID"]),
        "GovernorName": governor_name,
        "PreferredTeam": int(row["PreferredTeam"]),
        "IsActive": bool(row.get("IsActive", 0)),
        "CreatedAtUTC": created_at,
        "UpdatedAtUTC": updated_at,
        "UpdatedBy": str(row.get("UpdatedBy") or ""),
    }


async def set_preference(governor_id: int, team: int, updated_by: str) -> dict[str, Any]:
    validated_governor = await _validate_governor_id(governor_id)
    normalized_team = _normalize_team(team)
    normalized_updated_by = _normalize_updated_by(updated_by)

    existing = await get_team_preference(int(validated_governor["GovernorID"]), active_only=False)
    row = await upsert_team_preference(
        governor_id=int(validated_governor["GovernorID"]),
        preferred_team=normalized_team,
        updated_by=normalized_updated_by,
    )
    if not row:
        raise RuntimeError("Failed to persist Ark team preference.")

    action = (
        "created"
        if not existing
        else ("reactivated" if not existing.get("IsActive") else "updated")
    )
    logger.info(
        "[ARK_PREF] Preference %s: governor_id=%s governor_name=%s preferred_team=%s updated_by=%s at=%s",
        action,
        validated_governor["GovernorID"],
        validated_governor["GovernorName"],
        normalized_team,
        normalized_updated_by,
        dt.datetime.now(_UTC).isoformat(),
    )
    return _serialize_preference(row, governor_name=validated_governor["GovernorName"]) or {}


async def clear_preference(governor_id: int, updated_by: str) -> bool:
    validated_governor = await _validate_governor_id(governor_id)
    normalized_updated_by = _normalize_updated_by(updated_by)
    row = await clear_team_preference(
        governor_id=int(validated_governor["GovernorID"]),
        updated_by=normalized_updated_by,
    )
    if not row:
        logger.info(
            "[ARK_PREF] No active preference to clear: governor_id=%s updated_by=%s at=%s",
            validated_governor["GovernorID"],
            normalized_updated_by,
            dt.datetime.now(_UTC).isoformat(),
        )
        return False

    logger.info(
        "[ARK_PREF] Preference cleared: governor_id=%s governor_name=%s updated_by=%s at=%s",
        validated_governor["GovernorID"],
        validated_governor["GovernorName"],
        normalized_updated_by,
        dt.datetime.now(_UTC).isoformat(),
    )
    return True


async def get_preference(governor_id: int) -> dict[str, Any] | None:
    row = await get_team_preference(int(governor_id), active_only=True)
    if not row:
        return None
    governor_name = None
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
    target_id = str(int(governor_id))
    for item in rows or []:
        if str(item.get("GovernorID") or "").strip() == target_id:
            governor_name = str(item.get("GovernorName") or "").strip() or None
            break
    return _serialize_preference(row, governor_name=governor_name)


async def get_all_active_preferences() -> dict[int, int]:
    rows = await list_active_team_preferences()
    return {int(row["GovernorID"]): int(row["PreferredTeam"]) for row in rows or []}
