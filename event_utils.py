"""
event_utils.py

Centralized helpers for serializing/parsing event dicts shared across modules.

Functions:
 - events_from_persisted(raw_events) -> list[dict]  (validated; start_time -> aware datetime)
 - events_to_persisted(events) -> list[dict]     (ISO strings)
 - validate_event_shape(entry) -> bool
 - serialize_event(event) -> dict
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from utils import ensure_aware_utc, parse_isoformat_utc


def validate_event_shape(entry: Any) -> bool:
    """
    Return True if entry looks like a valid event dict (has start_time).
    This is intentionally permissive about optional keys (name/type/description).
    """
    if not isinstance(entry, dict):
        return False
    return "start_time" in entry


def events_from_persisted(raw_events: Iterable[Any]) -> list[dict[str, Any]]:
    """
    Parse persisted event representations into canonical in-memory events.

    Each persisted item should be a dict with:
      - 'start_time': ISO string or datetime
      - optional 'name', 'type', 'description'

    Returns list of events where 'start_time' is a timezone-aware UTC datetime.

    Raises ValueError for malformed individual events (caller can catch/decide to prune).
    """
    out: list[dict[str, Any]] = []
    for e in raw_events or []:
        if not isinstance(e, dict):
            raise ValueError("event must be a dict")
        st = e.get("start_time")
        if isinstance(st, str):
            dt = parse_isoformat_utc(st)
        elif isinstance(st, datetime):
            dt = ensure_aware_utc(st)
        else:
            raise ValueError("event.start_time must be ISO string or datetime")
        out.append(
            {
                "name": e.get("name"),
                "type": e.get("type"),
                "start_time": dt,
                "description": e.get("description", "") or "",
            }
        )
    return out


def events_to_persisted(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert canonical in-memory events into JSON-serializable dicts where 'start_time'
    is an ISO-formatted UTC string. Malformed events are skipped.
    """
    out: list[dict[str, Any]] = []
    for e in events or []:
        try:
            st = e.get("start_time")
            if isinstance(st, str):
                dt = parse_isoformat_utc(st)
            elif isinstance(st, datetime):
                dt = ensure_aware_utc(st)
            else:
                raise ValueError("event.start_time must be datetime or ISO string")
            out.append(
                {
                    "name": e.get("name"),
                    "type": e.get("type"),
                    "start_time": dt.isoformat(),
                    "description": e.get("description", "") or "",
                }
            )
        except Exception:
            # Skip problematic events to avoid corrupting persisted file
            continue
    return out


def serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Serialize a single event dict into JSON-safe form (ISO string for start_time).
    """
    st = event.get("start_time")
    if isinstance(st, datetime):
        st_iso = ensure_aware_utc(st).isoformat()
    else:
        st_iso = str(st)
    return {
        "name": event.get("name"),
        "type": event.get("type"),
        "start_time": st_iso,
        "description": event.get("description", "") or "",
    }
