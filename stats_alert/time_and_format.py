# time_and_format.py
"""
Helper module for consistent date/time formatting across embeds.

Provides two main helpers:
- format_date_utc: Format dates/datetimes to UTC date strings
- format_time_utc: Format datetimes to UTC time strings
"""

from datetime import UTC, date, datetime, time as _dt_time
from typing import Any


def _ensure_aware_utc(dt: datetime) -> datetime:
    """
    Ensure the given datetime is timezone-aware in UTC.
    - If dt is naive, attaches UTC tzinfo (assumes naive values are UTC).
    - If dt is aware, converts it to UTC.

    Internal helper copied from utils.ensure_aware_utc to avoid circular imports.
    """
    if dt is None:
        raise ValueError("dt must be a datetime instance, not None")
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _date_to_utc_start(date_obj: Any) -> datetime | None:
    """
    Convert a date-like or datetime object to an aware UTC datetime at 00:00:00 for that date.

    Internal helper copied from utils.date_to_utc_start to avoid circular imports.
    """
    if not date_obj:
        return None
    try:
        # If a full datetime, normalize to the date's midnight
        if isinstance(date_obj, datetime):
            dt = datetime(date_obj.year, date_obj.month, date_obj.day)
        else:
            # Assume date-like object (has year, month, day) or datetime.date
            dt = datetime.combine(date_obj, _dt_time.min)
        return _ensure_aware_utc(dt)
    except Exception:
        return None


def format_date_utc(dt: datetime | date | None, fmt: str = "%d %b %Y") -> str:
    """
    Format a date or datetime object to a UTC date string.

    Args:
        dt: A datetime, date object, or None
        fmt: strftime format string (default: "%d %b %Y" -> "02 Jan 2025")

    Returns:
        Formatted date string in UTC, or "TBD" if dt is None or invalid

    Examples:
        >>> from datetime import datetime, date
        >>> format_date_utc(date(2025, 1, 2))
        '02 Jan 2025'
        >>> format_date_utc(datetime(2025, 1, 2, 10, 30))
        '02 Jan 2025'
        >>> format_date_utc(None)
        'TBD'
    """
    if dt is None:
        return "TBD"

    try:
        # Handle datetime.date objects
        if isinstance(dt, date) and not isinstance(dt, datetime):
            # Convert date to datetime at midnight UTC
            normalized = _date_to_utc_start(dt)
            if normalized is None:
                return "TBD"
            return normalized.strftime(fmt)

        # Handle datetime objects (naive or aware)
        if isinstance(dt, datetime):
            # Ensure aware UTC datetime
            aware_dt = _ensure_aware_utc(dt)
            return aware_dt.strftime(fmt)

        # Fallback: try to use date_to_utc_start for other date-like objects
        normalized = _date_to_utc_start(dt)
        if normalized is None:
            return "TBD"
        return normalized.strftime(fmt)
    except Exception:
        return "TBD"


def format_time_utc(dt: datetime | None, fmt: str = "%H:%M:%S") -> str:
    """
    Format a datetime object to a UTC time string.

    Args:
        dt: A datetime object (aware or naive), or None
        fmt: strftime format string (default: "%H:%M:%S" -> "14:30:00")

    Returns:
        Formatted time string in UTC, or "—" if dt is None or invalid

    Examples:
        >>> from datetime import datetime
        >>> format_time_utc(datetime(2025, 1, 2, 14, 30, 0))
        '14:30:00'
        >>> format_time_utc(None)
        '—'
    """
    if dt is None:
        return "—"

    try:
        # Ensure aware UTC datetime
        if isinstance(dt, datetime):
            aware_dt = _ensure_aware_utc(dt)
            return aware_dt.strftime(fmt)
        return "—"
    except Exception:
        return "—"


# Re-export convenience: Can import fmt_short from embed_utils when needed
__all__ = ["format_date_utc", "format_time_utc"]
