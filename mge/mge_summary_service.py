"""Summary helpers for leadership MGE review dataset."""

from __future__ import annotations

from typing import Any


def _to_text(value: Any, default: str = "Unknown") -> str:
    text = str(value or "").strip()
    return text if text else default


def _is_truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    try:
        return int(value) == 1
    except Exception:
        return bool(value)


def summarize_by_priority(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count review rows by signup priority."""
    out: dict[str, int] = {}
    for row in rows:
        key = _to_text(row.get("RequestPriority"), default="Unknown").title()
        out[key] = out.get(key, 0) + 1
    return out


def summarize_by_commander(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count review rows by requested commander name."""
    out: dict[str, int] = {}
    for row in rows:
        key = _to_text(row.get("RequestedCommanderName"))
        out[key] = out.get(key, 0) + 1
    return out


def summarize_by_role(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count review rows by kingdom role."""
    out: dict[str, int] = {}
    for row in rows:
        key = _to_text(row.get("KingdomRole"))
        out[key] = out.get(key, 0) + 1
    return out


def summarize_warnings(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count warning flags across the review dataset."""
    totals = {
        "missing_kvk_data": 0,
        "heads_out_of_range": 0,
        "no_attachments": 0,
        "no_gear_or_armament_text": 0,
    }
    for row in rows:
        if _is_truthy_flag(row.get("WarningMissingKVKData")):
            totals["missing_kvk_data"] += 1
        if _is_truthy_flag(row.get("WarningHeadsOutOfRange")):
            totals["heads_out_of_range"] += 1
        if _is_truthy_flag(row.get("WarningNoAttachments")):
            totals["no_attachments"] += 1
        if _is_truthy_flag(row.get("WarningNoGearOrArmamentText")):
            totals["no_gear_or_armament_text"] += 1
    return totals


def build_review_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build consolidated leadership summary payload."""
    return {
        "total_rows": len(rows),
        "by_priority": summarize_by_priority(rows),
        "by_commander": summarize_by_commander(rows),
        "by_role": summarize_by_role(rows),
        "warnings": summarize_warnings(rows),
    }
