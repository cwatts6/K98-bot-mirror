from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from event_calendar.reminder_types import expand_offsets

PREFS_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ReminderPrefsModel:
    schema_version: int
    enabled: bool
    # {"all": ["7d", ...], "raid": ["24h", ...]}
    by_event_type: dict[str, list[str]]


def default_prefs() -> dict[str, Any]:
    return {
        "schema_version": PREFS_SCHEMA_VERSION,
        "enabled": False,  # opt-in only
        "by_event_type": {},
    }


def normalize_prefs(raw: dict[str, Any] | None) -> dict[str, Any]:
    base = default_prefs()
    if not isinstance(raw, dict):
        return base

    enabled = bool(raw.get("enabled", False))
    by_event_type = raw.get("by_event_type", {})
    if not isinstance(by_event_type, dict):
        by_event_type = {}

    normalized: dict[str, list[str]] = {}
    for k, v in by_event_type.items():
        key = str(k).strip().lower()
        if not key:
            continue

        if isinstance(v, (list, tuple, set)):
            expanded = sorted(expand_offsets([str(x) for x in v]))
        elif v is None:
            expanded = []
        else:
            expanded = sorted(expand_offsets([str(v)]))

        # IMPORTANT: keep empty buckets to support multi-select type staging UX
        normalized[key] = expanded

    return {
        "schema_version": int(raw.get("schema_version") or PREFS_SCHEMA_VERSION),
        "enabled": enabled,
        "by_event_type": normalized,
    }


def _validate_known_event_type(event_type: str, known_event_types: set[str]) -> str:
    et = (event_type or "").strip().lower()
    if et in known_event_types or et == "all":
        return et
    raise ValueError(f"unknown event_type: {event_type}")


def add_event_type_bucket(
    prefs: dict[str, Any] | None,
    *,
    event_type: str,
    known_event_types: set[str],
) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    et = _validate_known_event_type(event_type, known_event_types)

    if et == "all":
        # "all" is exclusive: keep only all-bucket offsets if they exist
        existing_all = list(p["by_event_type"].get("all", []))
        p["by_event_type"] = {"all": sorted(set(existing_all))} if existing_all else {"all": []}
        return p

    # specific type: remove only all bucket, preserve existing specific buckets
    p["by_event_type"].pop("all", None)
    p["by_event_type"].setdefault(et, [])
    p["by_event_type"][et] = sorted(set(p["by_event_type"][et]))
    return p


def remove_event_type_bucket(
    prefs: dict[str, Any] | None,
    *,
    event_type: str,
    known_event_types: set[str],
) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    et = _validate_known_event_type(event_type, known_event_types)
    p["by_event_type"].pop(et, None)
    return p


def clear_event_types(prefs: dict[str, Any] | None) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    p["by_event_type"] = {}
    return p


def add_offsets_for_event_type(
    prefs: dict[str, Any] | None,
    *,
    event_type: str,
    offsets: list[str],
    known_event_types: set[str],
    enabled: bool | None = None,
) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    et = _validate_known_event_type(event_type, known_event_types)
    expanded = sorted(expand_offsets(offsets))
    if not expanded:
        raise ValueError("offsets cannot be empty")

    if et == "all":
        p["by_event_type"] = {"all": sorted(set(expanded))}
    else:
        p["by_event_type"].pop("all", None)
        existing = set(p["by_event_type"].get(et, []))
        p["by_event_type"][et] = sorted(existing | set(expanded))

    if enabled is not None:
        p["enabled"] = bool(enabled)
    return p


def set_offsets_for_event_type(
    prefs: dict[str, Any] | None,
    *,
    event_type: str,
    offsets: list[str],
    known_event_types: set[str],
    enabled: bool | None = None,
) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    et = _validate_known_event_type(event_type, known_event_types)
    expanded = sorted(expand_offsets(offsets))
    if not expanded:
        raise ValueError("offsets cannot be empty")

    p["by_event_type"][et] = expanded
    if enabled is not None:
        p["enabled"] = bool(enabled)
    return p


def remove_offsets_for_event_type(
    prefs: dict[str, Any] | None,
    *,
    event_type: str,
    offsets: list[str],
    known_event_types: set[str],
) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    et = _validate_known_event_type(event_type, known_event_types)
    existing = set(p["by_event_type"].get(et, []))
    if not existing:
        return p

    remove = expand_offsets(offsets)
    remaining = sorted(existing - remove)

    if remaining:
        p["by_event_type"][et] = remaining
    else:
        p["by_event_type"].pop(et, None)
    return p


def clear_offsets_for_event_type(
    prefs: dict[str, Any] | None,
    *,
    event_type: str,
    known_event_types: set[str],
) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    et = _validate_known_event_type(event_type, known_event_types)
    p["by_event_type"].pop(et, None)
    return p


def set_enabled(prefs: dict[str, Any] | None, enabled: bool) -> dict[str, Any]:
    p = normalize_prefs(prefs)
    p["enabled"] = bool(enabled)
    return p


def is_dm_allowed(
    *,
    reminder_type: str,
    event_type: str,
    prefs: dict[str, Any] | None,
    known_event_types: set[str],
) -> bool:
    p = normalize_prefs(prefs)
    rt = str(reminder_type or "").strip().lower()

    et = _validate_known_event_type(event_type, known_event_types)

    if not p.get("enabled", False):
        return False

    by_type = p.get("by_event_type", {})
    specific = set(by_type.get(et, []))
    global_offsets = set(by_type.get("all", []))

    return rt in specific or rt in global_offsets
