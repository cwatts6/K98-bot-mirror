from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _to_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.isoformat()


def _parse_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    text = str(raw).strip()
    if not text:
        return []
    return [p.strip() for p in text.split(",") if p.strip()]


def build_event_calendar_cache_payload(
    *,
    events: list[dict[str, Any]],
    horizon_days: int = 365,
    generated_utc: datetime | None = None,
) -> dict[str, Any]:
    ts = generated_utc or datetime.now(UTC)
    out_events: list[dict[str, Any]] = []

    for e in events or []:
        start = e.get("start_utc")
        end = e.get("end_utc")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            continue

        out_events.append(
            {
                "instance_id": str(e.get("instance_id", "")),
                "title": str(e.get("title", "")),
                "emoji": str(e.get("emoji", "") or ""),
                "type": str(e.get("type", "") or ""),
                "variant": str(e.get("variant", "") or ""),
                "start_utc": _to_utc_iso(start),
                "end_utc": _to_utc_iso(end),
                "all_day": bool(e.get("all_day", False)),
                "importance": str(e.get("importance", "") or ""),
                "description": str(e.get("description", "") or ""),
                "link_url": str(e.get("link_url", "") or ""),
                "channel_id": str(e.get("channel_id", "") or ""),
                "tags": _parse_tags(e.get("tags")),
            }
        )

    return {
        "generated_utc": _to_utc_iso(ts),
        "horizon_days": int(horizon_days),
        "events": out_events,
    }
