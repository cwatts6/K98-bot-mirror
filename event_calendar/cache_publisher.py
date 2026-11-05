from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import logging
from pathlib import Path
from typing import Any

from constants import EVENT_CALENDAR_CACHE_FILE_PATH, EVENT_TYPE_INDEX_FILE_PATH
from event_calendar.cache_contract import build_event_calendar_cache_payload
from event_calendar.sql_lifecycle import SqlOutcome, SqlSession, error_facts
from file_utils import atomic_json_write, get_conn_with_retries

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(EVENT_CALENDAR_CACHE_FILE_PATH)
_TYPE_INDEX_PATH = Path(EVENT_TYPE_INDEX_FILE_PATH)


@dataclass
class PublishResult:
    ok: bool
    status: str
    events_written: int | None = None
    cache_path: str = field(default_factory=lambda: str(_CACHE_PATH))
    type_index_path: str = field(default_factory=lambda: str(_TYPE_INDEX_PATH))
    error_message: str | None = None
    primary: str = "not_attempted"
    index: str = "not_attempted"
    generation: str | None = None
    sql: SqlOutcome = field(default_factory=SqlOutcome)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_json_write(
        str(path), payload, ensure_ascii=True, sort_keys=False, default=None, replace_retries=1
    )


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
    result = PublishResult(ok=False, status="failed_publish")
    session = SqlSession(
        lambda: get_conn_with_retries(meta={"operation": "calendar_publish_cache"}),
        read_only=True,
    )
    result.sql = session.outcome
    try:
        with session as conn:
            instances = load_runtime_instances(conn, horizon_days=horizon_days)
        if result.sql.cleanup == "unconfirmed":
            result.status = "cleanup_unconfirmed"
            return result
        payload = build_cache_payload(instances, horizon_days=horizon_days)
        events = payload.get("events", [])
        if not events and _CACHE_PATH.exists() and not force_empty:
            result.ok = True
            result.status = "skipped_empty_preserve_existing"
            result.primary = "preserved"
            result.events_written = 0
            return result
        result.primary = "unknown"
        result.events_written = None
        _atomic_write_json(_CACHE_PATH, payload)
        result.ok = True
        result.status = "success"
        result.events_written = len(events)
        result.primary = "new"
        result.generation = str(payload.get("generated_utc", ""))
    except Exception as error:
        result.error_message = str(error_facts(error))
        return result
    # Index construction and replacement cannot erase the primary acknowledgement.
    try:
        index = build_event_type_index_payload(
            payload=payload, horizon_days=horizon_days, generated_utc=result.generation
        )
        _atomic_write_json(_TYPE_INDEX_PATH, index)
        result.index = "same_payload"
    except Exception as error:
        result.status = "success_index_warning"
        result.index = "old_or_unknown"
        result.error_message = str(error_facts(error))
    return result
