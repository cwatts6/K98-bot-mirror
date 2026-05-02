from __future__ import annotations

import json
import re
from typing import Any

from inventory.models import InventoryImportType, InventoryValidationResult

RESOURCE_TYPES = ("food", "wood", "stone", "gold")
SPEEDUP_TYPES = ("building", "research", "training", "healing", "universal")

_RESOURCE_VALUE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([kmb])?\s*$", re.IGNORECASE)
_SPEEDUP_TOKEN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([dhm])", re.IGNORECASE)
_SPEEDUP_DAY_PREFIX_RE = re.compile(
    r"^\s*(\d+)(?:\s*d\b(?:\s*\d+(?:\.\d+)?\s*[hm]\b)*\s*)?$", re.IGNORECASE
)


def parse_resource_value(value: Any) -> int:
    if value is None:
        raise ValueError("Value is required.")
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid inventory quantities.")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Negative values are not allowed.")
        return value
    if isinstance(value, float):
        if value < 0 or not value.is_integer():
            raise ValueError("Resource values must be whole non-negative numbers.")
        return int(value)

    text = str(value).replace(",", "").strip()
    if text == "":
        raise ValueError("Value is required.")
    match = _RESOURCE_VALUE_RE.match(text)
    if not match:
        raise ValueError(f"Invalid resource value: {value!r}.")

    number = float(match.group(1))
    suffix = (match.group(2) or "").lower()
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[suffix]
    parsed = int(round(number * multiplier))
    if parsed < 0:
        raise ValueError("Negative values are not allowed.")
    return parsed


def parse_speedup_minutes(value: Any) -> int:
    if value is None:
        raise ValueError("Value is required.")
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid speedup durations.")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Negative values are not allowed.")
        return value
    if isinstance(value, float):
        if value < 0:
            raise ValueError("Negative values are not allowed.")
        return int(round(value))

    text = str(value).strip().lower()
    if text in {"", "0"}:
        return 0
    if text.isdigit():
        return int(text)

    total = 0.0
    matched = False
    for amount_raw, unit in _SPEEDUP_TOKEN_RE.findall(text):
        matched = True
        amount = float(amount_raw)
        if amount < 0:
            raise ValueError("Negative values are not allowed.")
        if unit.lower() == "d":
            total += amount * 24 * 60
        elif unit.lower() == "h":
            total += amount * 60
        elif unit.lower() == "m":
            total += amount
    if not matched:
        raise ValueError(f"Invalid speedup duration: {value!r}.")
    return int(round(total))


def parse_speedup_days(value: Any) -> int:
    if value is None:
        raise ValueError("Value is required.")
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid speedup durations.")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Negative values are not allowed.")
        return value
    if isinstance(value, float):
        if value < 0:
            raise ValueError("Negative values are not allowed.")
        return int(value)

    text = str(value).replace(",", "").strip().lower()
    if text in {"", "0"}:
        return 0
    match = _SPEEDUP_DAY_PREFIX_RE.match(text)
    if not match:
        raise ValueError(f"Invalid speedup day value: {value!r}.")
    days = int(match.group(1))
    if days < 0:
        raise ValueError("Negative values are not allowed.")
    return days


def speedup_row_from_minutes(total_minutes: int) -> dict[str, int | float]:
    if total_minutes < 0:
        raise ValueError("Negative values are not allowed.")
    return {
        "total_minutes": int(total_minutes),
        "total_hours": round(total_minutes / 60, 4),
        "total_days_decimal": round(total_minutes / 1440, 4),
    }


def speedup_row_from_days(total_days: int) -> dict[str, int | float]:
    if total_days < 0:
        raise ValueError("Negative values are not allowed.")
    minutes = int(total_days) * 1440
    return {
        "total_minutes": minutes,
        "total_hours": int(total_days) * 24,
        "total_days_decimal": float(int(total_days)),
    }


def format_resource_value(value: Any) -> str:
    try:
        parsed = parse_resource_value(value)
    except ValueError:
        return "unreadable"
    if parsed >= 1_000_000_000:
        return f"{parsed / 1_000_000_000:.1f}".rstrip("0").rstrip(".") + "B"
    if parsed >= 1_000_000:
        return f"{parsed / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if parsed >= 1_000:
        return f"{parsed / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(parsed)


def format_speedup_duration(total_minutes: Any) -> str:
    try:
        minutes = parse_speedup_minutes(total_minutes)
    except ValueError:
        return "unreadable"
    return f"{minutes // 1440}d"


def apply_resource_total_corrections(
    values: dict[str, Any], corrections: dict[str, Any]
) -> dict[str, Any]:
    resources = values.get("resources") if isinstance(values, dict) else None
    if not isinstance(resources, dict):
        raise ValueError("Missing resources section.")

    merged_resources: dict[str, dict[str, Any]] = {}
    for resource_type in RESOURCE_TYPES:
        row = resources.get(resource_type)
        if not isinstance(row, dict):
            raise ValueError(f"Missing resource row: {resource_type}.")

        merged_row = dict(row)
        if resource_type in corrections:
            merged_row["total_resources_value"] = parse_resource_value(corrections[resource_type])
        merged_resources[resource_type] = merged_row

    normalized_resources = normalize_resource_values({"resources": merged_resources})
    return {"resources": normalized_resources}


def apply_speedup_duration_corrections(
    values: dict[str, Any], corrections: dict[str, Any]
) -> dict[str, Any]:
    speedup_values = values.get("speedups") if isinstance(values, dict) else None
    if not isinstance(speedup_values, dict):
        raise ValueError("Missing speedups section.")

    normalized_speedups: dict[str, dict[str, int | float]] = {}
    for speedup_type in SPEEDUP_TYPES:
        row = speedup_values.get(speedup_type)
        if not isinstance(row, dict):
            raise ValueError(f"Missing speedup row: {speedup_type}.")

        days = (
            parse_speedup_days(corrections[speedup_type])
            if speedup_type in corrections
            else _speedup_days_from_row(row)
        )
        normalized_speedups[speedup_type] = speedup_row_from_days(days)
    return {"speedups": normalized_speedups}


def _speedup_days_from_row(row: dict[str, Any]) -> int:
    if row.get("total_days_decimal") is not None:
        return parse_speedup_days(row.get("total_days_decimal"))
    if row.get("duration") is not None:
        return parse_speedup_days(row.get("duration"))
    if row.get("value") is not None:
        return parse_speedup_days(row.get("value"))
    minutes = parse_speedup_minutes(row.get("total_minutes"))
    return minutes // 1440


def normalize_resource_values(values: dict[str, Any]) -> dict[str, dict[str, int]]:
    resources = values.get("resources") if isinstance(values, dict) else None
    if not isinstance(resources, dict):
        raise ValueError("Missing resources section.")

    normalized: dict[str, dict[str, int]] = {}
    for resource_type in RESOURCE_TYPES:
        row = resources.get(resource_type)
        if not isinstance(row, dict):
            raise ValueError(f"Missing resource row: {resource_type}.")
        from_items = parse_resource_value(row.get("from_items_value"))
        total = parse_resource_value(row.get("total_resources_value"))
        normalized[resource_type] = {
            "from_items_value": from_items,
            "total_resources_value": total,
        }
    return normalized


def normalize_speedup_values(values: dict[str, Any]) -> dict[str, dict[str, int | float]]:
    speedups = values.get("speedups") if isinstance(values, dict) else None
    if not isinstance(speedups, dict):
        raise ValueError("Missing speedups section.")

    normalized: dict[str, dict[str, int | float]] = {}
    for speedup_type in SPEEDUP_TYPES:
        row = speedups.get(speedup_type)
        if not isinstance(row, dict):
            raise ValueError(f"Missing speedup row: {speedup_type}.")
        days = _speedup_days_from_row(row)
        normalized[speedup_type] = speedup_row_from_days(days)
    return normalized


def normalize_final_values(
    import_type: InventoryImportType, values: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    if import_type == InventoryImportType.RESOURCES:
        return {"resources": normalize_resource_values(values)}
    if import_type == InventoryImportType.SPEEDUPS:
        return {"speedups": normalize_speedup_values(values)}
    raise ValueError(f"Unsupported import type for Phase 1A: {import_type}.")


def parse_corrected_json(
    import_type: InventoryImportType, corrected_json: str
) -> tuple[dict[str, Any], InventoryValidationResult]:
    try:
        payload = json.loads(corrected_json)
    except json.JSONDecodeError as exc:
        return {}, InventoryValidationResult(False, error=f"Invalid JSON: {exc.msg}.")
    if not isinstance(payload, dict):
        return {}, InventoryValidationResult(False, error="Corrected data must be a JSON object.")
    try:
        normalized = normalize_final_values(import_type, payload)
    except ValueError as exc:
        return {}, InventoryValidationResult(False, error=str(exc))
    return normalized, InventoryValidationResult(True)
