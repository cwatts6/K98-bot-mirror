from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from constants import EVENT_CALENDAR_CACHE_FILE_PATH, EVENT_TYPE_INDEX_FILE_PATH
from event_calendar.cache_contract import build_event_calendar_cache_payload
from file_utils import get_conn_with_retries

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(EVENT_CALENDAR_CACHE_FILE_PATH)
_TYPE_INDEX_PATH = Path(EVENT_TYPE_INDEX_FILE_PATH)


@dataclass
class PublishResult:
    ok: bool
    status: str
    events_written: int = 0
    cache_path: str = str(_CACHE_PATH)
    type_index_path: str = str(_TYPE_INDEX_PATH)
    error_message: str | None = None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)


def load_runtime_instances(conn, *, horizon_days: int = 365) -> list[dict[str, Any]]:
    now = _utcnow()
    end = now + timedelta(days=horizon_days)

    sql = """
    SELECT InstanceID, SourceKind, SourceID, StartUTC, EndUTC, AllDay, Emoji, Title, EventType, Variant,
           Importance, Description, LinkURL, ChannelID, SignupURL, Tags, SortOrder, IsCancelled
    FROM dbo.EventInstances
    WHERE IsCancelled = 0
      AND StartUTC >= ?
      AND StartUTC <= ?
    ORDER BY StartUTC ASC, EventType ASC, SourceKind ASC, SourceID ASC, Title ASC
    """
    cur = conn.cursor()
    cur.execute(sql, now, end)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "instance_id": r.get("InstanceID"),
                "source_kind": r.get("SourceKind"),
                "source_id": r.get("SourceID"),
                "title": r.get("Title"),
                "emoji": r.get("Emoji"),
                "type": r.get("EventType"),
                "variant": r.get("Variant"),
                "start_utc": r.get("StartUTC"),
                "end_utc": r.get("EndUTC"),
                "all_day": bool(r.get("AllDay")),
                "importance": r.get("Importance"),
                "description": r.get("Description"),
                "link_url": r.get("LinkURL"),
                "channel_id": r.get("ChannelID"),
                "signup_url": r.get("SignupURL"),
                "tags": r.get("Tags"),
                "sort_order": r.get("SortOrder"),
            }
        )
    return out


def build_cache_payload(instances: list[dict[str, Any]], *, horizon_days: int) -> dict[str, Any]:
    payload = build_event_calendar_cache_payload(events=instances, horizon_days=horizon_days)
    payload["source"] = "sql_event_instances"
    return payload


def build_event_type_index_payload(
    *, payload: dict[str, Any], horizon_days: int, generated_utc: str
) -> dict[str, Any]:
    idx: dict[str, list[str]] = {}
    for e in payload.get("events", []):
        et = str(e.get("type", "") or "").strip().lower()
        iid = str(e.get("instance_id", "")).strip()
        if not et or not iid:
            continue
        idx.setdefault(et, []).append(iid)

    for k in idx:
        idx[k] = sorted(idx[k])

    return {
        "generated_utc": generated_utc,
        "horizon_days": int(horizon_days),
        "event_type_index": idx,
    }


def publish_event_calendar_cache(
    *, horizon_days: int = 365, force_empty: bool = False
) -> PublishResult:
    try:
        with get_conn_with_retries(meta={"operation": "calendar_publish_cache"}) as conn:
            instances = load_runtime_instances(conn, horizon_days=horizon_days)

        payload = build_cache_payload(instances, horizon_days=horizon_days)
        events = payload.get("events", [])

        if not events and _CACHE_PATH.exists() and not force_empty:
            return PublishResult(
                ok=True,
                status="skipped_empty_preserve_existing",
                events_written=0,
            )

        generated_utc = str(payload.get("generated_utc", ""))
        type_index_payload = build_event_type_index_payload(
            payload=payload, horizon_days=horizon_days, generated_utc=generated_utc
        )

        _atomic_write_json(_CACHE_PATH, payload)
        _atomic_write_json(_TYPE_INDEX_PATH, type_index_payload)

        return PublishResult(
            ok=True,
            status="success",
            events_written=len(events),
        )
    except Exception as e:
        logger.exception("[CALENDAR] publish_event_calendar_cache failed")
        return PublishResult(
            ok=False,
            status="failed_publish",
            error_message=f"{type(e).__name__}: {e}",
        )
