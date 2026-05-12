"""Service layer for MGE commander administration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import Any

from mge import mge_cache
from mge.dal import mge_commander_dal

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CommanderServiceResult:
    success: bool
    message: str
    commander_id: int | None = None
    variant_id: int | None = None


def _now_utc(now_utc: datetime | None = None) -> datetime:
    if now_utc is None:
        return datetime.now(UTC)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=UTC)
    return now_utc.astimezone(UTC)


def _normalize_name(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def list_variants() -> list[dict[str, Any]]:
    return mge_commander_dal.fetch_active_variants()


def list_commanders_by_variant(
    variant_id: int, *, include_inactive: bool = True
) -> list[dict[str, Any]]:
    return mge_commander_dal.fetch_commanders_for_variant(
        int(variant_id),
        include_inactive=include_inactive,
    )


def save_commander_assignment(
    *,
    commander_id: int | None,
    commander_name: str,
    variant_id: int,
    is_active: bool,
    now_utc: datetime | None = None,
) -> CommanderServiceResult:
    name = _normalize_name(commander_name)
    if not name:
        return CommanderServiceResult(False, "Commander name cannot be empty.")
    if len(name) > 100:
        return CommanderServiceResult(False, "Commander name is too long (max 100 characters).")
    if int(variant_id or 0) <= 0:
        return CommanderServiceResult(False, "A linked variant is required.")

    existing_by_name = mge_commander_dal.fetch_commander_by_name(name)
    if existing_by_name and int(existing_by_name["CommanderId"]) != int(commander_id or 0):
        return CommanderServiceResult(
            False,
            "A commander with that name already exists.",
        )

    row = mge_commander_dal.upsert_commander_assignment(
        commander_id=commander_id,
        commander_name=name,
        variant_id=int(variant_id),
        is_active=bool(is_active),
        now_utc=_now_utc(now_utc),
    )
    if not row:
        return CommanderServiceResult(False, "Failed to save commander.")

    refresh = mge_cache.refresh_mge_caches()
    if not all(refresh.values()):
        logger.warning(
            "mge_commander_save_cache_refresh_partial commander_id=%s results=%s",
            row.get("CommanderId"),
            refresh,
        )

    logger.info(
        "mge_commander_saved commander_id=%s variant_id=%s is_active=%s",
        row.get("CommanderId"),
        row.get("VariantId"),
        row.get("IsActive"),
    )
    return CommanderServiceResult(
        True,
        "Commander saved.",
        commander_id=int(row["CommanderId"]),
        variant_id=int(row["VariantId"]),
    )
