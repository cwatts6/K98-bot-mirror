"""
Formatting helpers for stats_alert embeds — normalize to UTC then format.

Functions:
- format_date_utc(dt, fmt="%d %b %Y") -> str
- format_time_utc(dt, fmt="%H:%M:%S") -> str

These are intentionally small, defensive wrappers so embed code can call a
single, well-tested helper rather than repeating strftime/naive/aware logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from utils import date_to_utc_start, ensure_aware_utc, utcnow


def format_date_utc(date_obj: Any, fmt: str = "%d %b %Y") -> str:
    """
    Format a date or datetime as a UTC-normalized date string.

    - Accepts datetime.date, datetime.datetime (naive or aware) or None.
    - Uses date_to_utc_start to normalize to midnight UTC for the provided date.
    - Returns a formatted string or "TBD" when input is falsy/unparseable.
    """
    if not date_obj:
        return "TBD"
    try:
        # date_to_utc_start returns an aware UTC datetime at midnight for the date
        dt_utc = date_to_utc_start(date_obj)
        if not dt_utc:
            return "TBD"
        return dt_utc.strftime(fmt)
    except Exception:
        return "TBD"


def format_time_utc(dt_obj: Any, fmt: str = "%H:%M:%S") -> str:
    """
    Format a datetime as a UTC-normalized time string.

    - Accepts datetime.datetime (naive or aware) or None.
    - Coerces naive datetimes to aware UTC using ensure_aware_utc.
    - Returns a formatted time string or "—" when input is falsy/unparseable.
    """
    if not dt_obj:
        return "—"
    try:
        if not isinstance(dt_obj, datetime):
            # If a date was passed, convert to midnight of that date in UTC
            dt_utc = date_to_utc_start(dt_obj)
            if not dt_utc:
                return "—"
            return dt_utc.strftime(fmt)
        # Ensure aware in UTC
        dt_aware = ensure_aware_utc(dt_obj)
        return dt_aware.strftime(fmt)
    except Exception:
        # As a last-resort, format current UTC time so function never crashes callers
        try:
            return utcnow().strftime(fmt)
        except Exception:
            return "—"
