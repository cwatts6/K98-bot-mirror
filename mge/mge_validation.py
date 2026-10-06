"""Validation helpers for MGE signup flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import functools
from typing import Any

_ALLOWED_PRIORITIES = {"high", "medium", "low"}
_ALLOWED_RANK_BANDS = {"1-5", "6-10", "11-15", "no_preference"}
_BLOCK_STATUSES = {"published", "completed"}


@functools.lru_cache(maxsize=1)
def _get_priority_rank_values() -> frozenset[str]:
    """Return the set of valid combined priority-rank dropdown values.

    Lazily imported to avoid circular imports at module load time.
    lru_cache provides thread-safe single-initialisation semantics.
    """
    from mge.mge_priority_rank_map import PRIORITY_RANK_OPTIONS

    return frozenset(o.value for o in PRIORITY_RANK_OPTIONS)


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    message: str = ""


def normalize_priority(value: str) -> str:
    return str(value or "").strip().lower()


def normalize_rank_band(value: str | None) -> str | None:
    text = str(value or "").strip().lower()
    return text if text else None


def validate_heads(value: Any) -> ValidationResult:
    try:
        n = int(value)
    except Exception:
        return ValidationResult(False, "Current heads must be an integer.")
    if n < 0 or n > 680:
        return ValidationResult(False, "Current heads must be between 0 and 680.")
    return ValidationResult(True)


def validate_priority(value: str) -> ValidationResult:
    p = normalize_priority(value)
    if p not in _ALLOWED_PRIORITIES:
        return ValidationResult(False, "Priority must be one of: High, Medium, Low.")
    return ValidationResult(True)


def validate_rank_band(value: str | None) -> ValidationResult:
    rb = normalize_rank_band(value)
    if rb is None:
        return ValidationResult(True)
    if rb not in _ALLOWED_RANK_BANDS:
        return ValidationResult(False, "Preferred rank band is invalid.")
    return ValidationResult(True)


def validate_priority_rank_value(value: str) -> ValidationResult:
    """Validate a combined Priority (Rank) dropdown value against known options."""
    if value in _get_priority_rank_values():
        return ValidationResult(True)
    return ValidationResult(
        False,
        f"Priority (Rank) value '{value}' is not a recognised option.",
    )


def validate_event_is_mutable_for_anyone(event_row: dict[str, Any]) -> ValidationResult:
    status = str(event_row.get("Status") or "").strip().lower()
    if status in _BLOCK_STATUSES:
        return ValidationResult(False, "This event is locked (published/completed).")
    return ValidationResult(True)


def validate_event_not_open_mode(event_row: dict[str, Any]) -> ValidationResult:
    mode = str(event_row.get("EventMode") or "").strip().lower()
    if mode == "open":
        return ValidationResult(False, "Signup actions are disabled for open-mode events.")
    return ValidationResult(True)


def validate_self_service_window(event_row: dict[str, Any], now_utc: datetime) -> ValidationResult:
    status_check = validate_event_is_mutable_for_anyone(event_row)
    if not status_check.valid:
        return status_check

    close_dt = event_row.get("SignupCloseUtc")
    if isinstance(close_dt, datetime):
        close_aware = (
            close_dt.replace(tzinfo=UTC) if close_dt.tzinfo is None else close_dt.astimezone(UTC)
        )
        if now_utc > close_aware:
            return ValidationResult(False, "Signup is closed for self-service changes.")
    return ValidationResult(True)
