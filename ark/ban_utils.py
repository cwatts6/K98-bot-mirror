from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any


def utc_today() -> date:
    return datetime.now(UTC).date()


def compute_next_ark_weekend_date(
    *,
    anchor_weekend_date: date,
    frequency_weekends: int,
    now_utc: datetime | None = None,
) -> date:
    """
    Return the next Ark weekend date on/after now UTC using configured anchor/frequency.
    """
    if frequency_weekends <= 0:
        frequency_weekends = 2

    today = (now_utc or datetime.now(UTC)).date()
    step_days = frequency_weekends * 7
    cur = anchor_weekend_date
    while cur < today:
        cur = cur + timedelta(days=step_days)
    return cur


def compute_ark_end_weekend_date(
    *,
    start_weekend_date: date,
    banned_ark_weekends: int,
    frequency_weekends: int,
) -> date:
    """
    Inclusive end weekend date for a ban covering N Ark weekends.
    """
    if banned_ark_weekends <= 0:
        banned_ark_weekends = 1
    if frequency_weekends <= 0:
        frequency_weekends = 2
    step_days = frequency_weekends * 7
    return start_weekend_date + timedelta(days=step_days * (banned_ark_weekends - 1))


def is_weekend_date_in_ban_window(
    *,
    target_weekend_date: date,
    start_weekend_date: date,
    banned_ark_weekends: int,
    frequency_weekends: int,
) -> bool:
    if target_weekend_date < start_weekend_date:
        return False

    end_weekend_date = compute_ark_end_weekend_date(
        start_weekend_date=start_weekend_date,
        banned_ark_weekends=banned_ark_weekends,
        frequency_weekends=frequency_weekends,
    )
    if target_weekend_date > end_weekend_date:
        return False

    step_days = max(1, frequency_weekends) * 7
    delta_days = (target_weekend_date - start_weekend_date).days
    return (delta_days % step_days) == 0


def format_ban_block_message(
    *, admin_context: bool, include_reason: bool = False, reason: str | None = None
) -> str:
    if admin_context:
        base = "❌ Cannot add this governor: an active Ark ban applies for this weekend."
    else:
        base = (
            "❌ You cannot sign up for this Ark weekend because this account is currently banned. "
            "If you believe this is incorrect, contact leadership."
        )
    if include_reason and reason:
        return f"{base}\nReason: {reason}"
    return base


def parse_frequency_from_config(config: dict[str, Any] | None) -> int:
    raw = (config or {}).get("FrequencyWeekends", 2)
    try:
        v = int(raw)
    except Exception:
        v = 2
    return v if v > 0 else 2


def admin_override_ban_rule(config: dict[str, Any] | None) -> bool:
    raw = (config or {}).get("AdminOverrideBanRule", 0)
    try:
        return bool(int(raw))
    except Exception:
        return bool(raw)
