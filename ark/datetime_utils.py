from __future__ import annotations

from datetime import date, datetime, time, timedelta

from utils import ensure_aware_utc


def _coerce_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    raise TypeError(f"close_time_utc must be datetime.time or HH:MM string, got {type(value)!r}")


def compute_signup_close(
    ark_weekend_date: date,
    close_day: str,
    close_time_utc: time | str,
) -> datetime:
    """
    Compute the UTC datetime when Ark signup closes.

    The close date is the configured weekday on or before the Ark weekend date.
    """
    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    close_idx = day_map.get((close_day or "").strip().lower())
    if close_idx is None:
        raise ValueError(f"Invalid close day: {close_day}")

    close_time = _coerce_time(close_time_utc)

    weekend_idx = ark_weekend_date.weekday()
    diff = (weekend_idx - close_idx) % 7
    close_date = ark_weekend_date - timedelta(days=diff)
    return ensure_aware_utc(datetime.combine(close_date, close_time))
