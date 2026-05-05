from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any

from ark.dal.ark_dal import (
    clear_team_preference,
    get_team_preference,
    list_active_team_preferences,
    upsert_team_preference,
)
from profile_cache import get_profile_cached
from target_utils import _name_cache, refresh_name_cache_from_sql, sync_refresh_worker

logger = logging.getLogger(__name__)
_ALLOWED_TEAMS = {1, 2}
_UTC = dt.UTC if hasattr(dt, "UTC") else dt.UTC


class ArkPreferenceError(ValueError):
    """Raised when Ark team preference validation fails."""


async def _ensure_governor_cache_ready() -> None:
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else None
    if rows:
        return

    # First attempt: existing async refresh path (may run in subprocess)
    try:
        await refresh_name_cache_from_sql()
    except Exception:
        logger.exception("[ARK_PREF] refresh_name_cache_from_sql failed")

    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else None
    if rows:
        return

    # Second attempt: force same-process load so this process sees data
    try:
        await asyncio.to_thread(sync_refresh_worker)
    except Exception:
        logger.exception("[ARK_PREF] sync_refresh_worker same-process fallback failed")


async def _get_profile_cached_async(governor_id: int) -> dict[str, Any] | None:
    return await asyncio.to_thread(get_profile_cached, int(governor_id))


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


def _row_get(row: Any, key: str, default=None):
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return getattr(row, key)
    except Exception:
        return default


def _serialize_preference(
    row: dict[str, Any] | Any | None,
    governor_name: str | None = None,
) -> dict[str, Any] | None:
    if not row:
        return None

    governor_id = _row_get(row, "GovernorID")
    preferred_team = _row_get(row, "PreferredTeam")
    is_active = _row_get(row, "IsActive", 0)
    created_at = _row_get(row, "CreatedAtUTC")
    updated_at = _row_get(row, "UpdatedAtUTC")
    updated_by = _row_get(row, "UpdatedBy", "")

    if governor_id is None or preferred_team is None:
        return None

    return {
        "GovernorID": int(governor_id),
        "GovernorName": governor_name,
        "PreferredTeam": int(preferred_team),
        "IsActive": bool(is_active),
        "CreatedAtUTC": created_at,
        "UpdatedAtUTC": updated_at,
        "UpdatedBy": str(updated_by or ""),
    }


async def _validate_governor_id(governor_id: int) -> dict[str, str]:
    governor_id = int(governor_id)
    governor_id_str = str(governor_id)

    # 1) in-memory cache (fast path)
    await _ensure_governor_cache_ready()
    rows = (_name_cache or {}).get("rows") if isinstance(_name_cache, dict) else []
    for row in rows or []:
        if str(row.get("GovernorID") or "").strip() == governor_id_str:
            return {
                "GovernorID": governor_id_str,
                "GovernorName": (
                    str(row.get("GovernorName") or governor_id_str).strip() or governor_id_str
                ),
            }

    # 2) DB-backed fallback (authoritative) without blocking the event loop
    try:
        profile = await _get_profile_cached_async(governor_id)
        if profile:
            gov_name = (
                str(
                    profile.get("GovernorName") or profile.get("governor_name") or governor_id_str
                ).strip()
                or governor_id_str
            )
            return {"GovernorID": governor_id_str, "GovernorName": gov_name}
    except Exception:
        logger.exception(
            "[ARK_PREF] get_profile_cached fallback failed for governor_id=%s", governor_id
        )

    logger.warning("[ARK_PREF] Invalid governor id for preference: governor_id=%s", governor_id)
    raise ArkPreferenceError("GovernorID not found. Please verify the ID.")


async def set_preference(governor_id: int, team: int, updated_by: str) -> dict[str, Any]:
    validated_governor = await _validate_governor_id(governor_id)
    normalized_team = _normalize_team(team)
    normalized_updated_by = _normalize_updated_by(updated_by)
    gid = int(validated_governor["GovernorID"])

    existing = await get_team_preference(gid, active_only=False)

    write_row = await upsert_team_preference(
        governor_id=gid,
        preferred_team=normalized_team,
        updated_by=normalized_updated_by,
    )

    parsed = _serialize_preference(write_row, governor_name=validated_governor["GovernorName"])
    if parsed and int(parsed["PreferredTeam"]) == normalized_team:
        action = (
            "created"
            if not existing
            else ("reactivated" if not _row_get(existing, "IsActive") else "updated")
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
        return parsed

    verified_row = await get_team_preference(gid, active_only=False)
    verified = _serialize_preference(verified_row, governor_name=validated_governor["GovernorName"])
    if not verified:
        raise RuntimeError("Failed to persist Ark team preference.")
    if int(verified["PreferredTeam"]) != normalized_team or not bool(verified["IsActive"]):
        raise RuntimeError("Failed to persist Ark team preference.")

    action = (
        "created"
        if not existing
        else ("reactivated" if not _row_get(existing, "IsActive") else "updated")
    )
    logger.info(
        "[ARK_PREF] Preference %s (verified-readback): governor_id=%s governor_name=%s preferred_team=%s updated_by=%s at=%s",
        action,
        validated_governor["GovernorID"],
        validated_governor["GovernorName"],
        normalized_team,
        normalized_updated_by,
        dt.datetime.now(_UTC).isoformat(),
    )
    return verified


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

    if not governor_name:
        try:
            profile = await _get_profile_cached_async(int(governor_id))
            if profile:
                governor_name = (
                    str(profile.get("GovernorName") or profile.get("governor_name") or "").strip()
                    or None
                )
        except Exception:
            logger.exception("[ARK_PREF] get_profile_cached name fallback failed for %s", target_id)

    return _serialize_preference(row, governor_name=governor_name)


async def get_all_active_preferences() -> dict[int, int]:
    rows = await list_active_team_preferences()
    out: dict[int, int] = {}
    for row in rows or []:
        gid = _row_get(row, "GovernorID")
        team = _row_get(row, "PreferredTeam")
        if gid is None or team is None:
            continue
        out[int(gid)] = int(team)
    return out
