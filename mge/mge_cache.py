"""MGE cache build and read pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from file_utils import atomic_write_json, read_json_safe
from mge.dal.mge_dal import fetch_active_commanders, fetch_active_variant_commanders
from mge.mge_constants import MGE_COMMANDERS_CACHE_PATH, MGE_VARIANT_COMMANDERS_CACHE_PATH

logger = logging.getLogger(__name__)


def _to_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return None


def is_commander_available(commander: dict[str, Any], as_of: datetime | None = None) -> bool:
    if not commander.get("IsActive", False):
        return False
    now = as_of or datetime.now(UTC)
    start = _to_utc(commander.get("ReleaseStartUtc"))
    end = _to_utc(commander.get("ReleaseEndUtc"))
    if start and now < start:
        return False
    if end and now > end:
        return False
    return True


def _validate_commanders_payload(payload: list[dict[str, Any]]) -> bool:
    required = {"CommanderId", "CommanderName", "IsActive"}
    return bool(payload) and all(required.issubset(item.keys()) for item in payload)


def _validate_variant_payload(payload: list[dict[str, Any]]) -> bool:
    required = {"VariantCommanderId", "VariantId", "CommanderId", "VariantName", "CommanderName"}
    return bool(payload) and all(required.issubset(item.keys()) for item in payload)


def build_commanders_cache(as_of: datetime | None = None) -> bool:
    raw = fetch_active_commanders()
    filtered = [row for row in raw if is_commander_available(row, as_of=as_of)]
    if not _validate_commanders_payload(filtered):
        logger.warning("mge_commanders_cache_refresh_skipped reason=invalid_or_empty_payload")
        return False
    atomic_write_json(str(MGE_COMMANDERS_CACHE_PATH), filtered)
    logger.info("mge_commanders_cache_refresh_success count=%s", len(filtered))
    return True


def build_variant_commanders_cache() -> bool:
    rows = fetch_active_variant_commanders()
    if not _validate_variant_payload(rows):
        logger.warning("mge_variant_cache_refresh_skipped reason=invalid_or_empty_payload")
        return False
    atomic_write_json(str(MGE_VARIANT_COMMANDERS_CACHE_PATH), rows)
    logger.info("mge_variant_cache_refresh_success count=%s", len(rows))
    return True


def refresh_mge_caches() -> dict[str, bool]:
    return {
        "commanders": build_commanders_cache(),
        "variant_commanders": build_variant_commanders_cache(),
    }


def read_commanders_cache() -> list[dict[str, Any]]:
    data = read_json_safe(str(MGE_COMMANDERS_CACHE_PATH), default=[])
    return data if isinstance(data, list) else []


def read_variant_commanders_cache() -> list[dict[str, Any]]:
    data = read_json_safe(str(MGE_VARIANT_COMMANDERS_CACHE_PATH), default=[])
    return data if isinstance(data, list) else []


def get_commanders_for_variant(variant_name: str) -> list[dict[str, Any]]:
    return [r for r in read_variant_commanders_cache() if r.get("VariantName") == variant_name]
