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


def _parse_iso(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        return None


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
    age = int((now - mtime).total_seconds() // 60)

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
