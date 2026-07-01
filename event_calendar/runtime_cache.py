from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from constants import (
    EVENT_CALENDAR_CACHE_FILE_PATH,
    EVENT_CALENDAR_STALE_DEGRADED_MINUTES,
    EVENT_CALENDAR_STALE_WARN_MINUTES,
)
from event_calendar.datetime_utils import parse_iso_utc_nullable


def load_runtime_cache() -> dict[str, Any]:
    p = Path(EVENT_CALENDAR_CACHE_FILE_PATH)
    if not p.exists():
        return {"ok": False, "error": "cache_missing", "events": []}

    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "cache_invalid", "events": []}

    now = datetime.now(UTC)
    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=UTC)
    age = max(0, int((now - mtime).total_seconds() // 60))

    degraded = age >= EVENT_CALENDAR_STALE_DEGRADED_MINUTES
    warning = age >= EVENT_CALENDAR_STALE_WARN_MINUTES

    return {
        "ok": True,
        "payload": payload,
        "events": payload.get("events", []),
        "cache_age_minutes": age,
        "stale_warning": warning,
        "degraded": degraded,
    }


def stale_banner(cache_state: dict[str, Any]) -> str | None:
    if not cache_state.get("ok"):
        return "⚠️ Calendar cache unavailable; showing limited data."
    if cache_state.get("degraded"):
        return "⚠️ Calendar cache is stale (degraded mode). Data may be outdated."
    if cache_state.get("stale_warning"):
        return "⚠️ Calendar cache is aging; data may be slightly stale."
    return None


def list_event_types(cache_state: dict[str, Any]) -> list[str]:
    events = cache_state.get("events", [])
    out = {str((e or {}).get("type", "")).strip().lower() for e in events if isinstance(e, dict)}
    out.discard("")
    return sorted(out)


def list_importance_values(cache_state: dict[str, Any]) -> list[str]:
    events = cache_state.get("events", [])
    out = {
        str((e or {}).get("importance", "")).strip().lower() for e in events if isinstance(e, dict)
    }
    out.discard("")
    return sorted(out)


def sort_events_deterministic(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _key(e: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            str(e.get("start_utc") or ""),
            str(e.get("type") or "").lower(),
            str(e.get("title") or "").lower(),
            str(e.get("instance_id") or ""),
        )

    return sorted(events, key=_key)


def filter_events(
    events: list[dict[str, Any]],
    *,
    now: datetime,
    days: int,
    event_type: str = "all",
    importance: str = "all",
) -> list[dict[str, Any]]:
    horizon_end = now.timestamp() + (days * 86400)
    type_norm = (event_type or "all").strip().lower()
    imp_norm = (importance or "all").strip().lower()

    out: list[dict[str, Any]] = []
    for e in events:
        if not isinstance(e, dict):
            continue

        start = parse_iso_utc_nullable(str(e.get("start_utc") or ""))
        if not start:
            continue

        if start.timestamp() < now.timestamp():
            continue
        if start.timestamp() > horizon_end:
            continue

        if type_norm != "all" and str(e.get("type") or "").strip().lower() != type_norm:
            continue
        if imp_norm != "all" and str(e.get("importance") or "").strip().lower() != imp_norm:
            continue

        out.append(e)

    return sort_events_deterministic(out)


def next_event(
    events: list[dict[str, Any]], *, now: datetime, event_type: str = "all"
) -> dict[str, Any] | None:
    filtered = filter_events(events, now=now, days=3650, event_type=event_type, importance="all")
    return filtered[0] if filtered else None


def search_events(
    events: list[dict[str, Any]],
    *,
    now: datetime,
    field: str,
    match: str,
    query: str,
) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return []

    field = (field or "all").strip().lower()
    match = (match or "contains").strip().lower()

    def _matches(text: str) -> bool:
        t = (text or "").lower()
        if match == "exact":
            return t == q
        if match == "starts_with":
            return t.startswith(q)
        return q in t

    searchable = {
        "title": lambda e: str(e.get("title") or ""),
        "tags": lambda e: (
            ",".join(e.get("tags") or [])
            if isinstance(e.get("tags"), list)
            else str(e.get("tags") or "")
        ),
        "type": lambda e: str(e.get("type") or ""),
        "description": lambda e: str(e.get("description") or ""),
    }

    def _event_matches(e: dict[str, Any]) -> bool:
        if field == "all":
            return any(_matches(fn(e)) for fn in searchable.values())
        fn = searchable.get(field)
        if not fn:
            return False
        return _matches(fn(e))

    future_events = filter_events(events, now=now, days=3650, event_type="all", importance="all")
    return [e for e in future_events if _event_matches(e)]
