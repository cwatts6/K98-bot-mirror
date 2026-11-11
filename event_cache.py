# event_cache.py
import asyncio
import copy
from datetime import UTC, datetime, timedelta
import json
import logging
import os
from threading import RLock
from typing import Any

from discord.utils import utcnow

from constants import CACHE_FILE_PATH, GSHEETS_CALL_TIMEOUT

# Keep typed Event import for type hints but call loader functions dynamically via module
from event_data_loader import Event as LoaderEvent
from services.event_cache_service import EventCacheService, UpcomingEventCacheSnapshot

logger = logging.getLogger(__name__)

# Global in-memory cache + metadata
event_cache: list[LoaderEvent] = []
last_refreshed: datetime | None = None
_CACHE_LOCK = RLock()  # cheap guard for concurrent reads/writes

# Use timezone-aware UTC constant
UTC = UTC

# New: preserve existing cache if a refresh produces 0 events but we have a recent cache
# Configurable via environment variable
PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS = int(
    os.getenv("PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS", "3600")
)
EVENT_CACHE_MIN_REFRESH_TIMEOUT = float(os.getenv("EVENT_CACHE_MIN_REFRESH_TIMEOUT", "5.0"))


_generation = 0
_source = "unknown"
_persistence = "unknown"


# ---- Helpers -----------------------------------------------------------------
def _aware(dt: datetime) -> datetime:
    """Force a datetime to UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _parse_dt(s: Any) -> datetime:
    """Parse ISO8601 datetime (string or datetime) to UTC-aware."""
    if isinstance(s, datetime):
        return _aware(s)
    if not isinstance(s, str) or not s:
        raise TypeError(f"Unsupported datetime payload: {type(s)}={s!r}")
    # Support both '+00:00' and legacy 'Z'
    s2 = s.replace("Z", "+00:00")
    return _aware(datetime.fromisoformat(s2))


def get_last_refreshed() -> datetime | None:
    with _CACHE_LOCK:
        return last_refreshed


def get_counts_by_type() -> dict[str, int]:
    counts: dict[str, int] = {}
    with _CACHE_LOCK:
        for e in event_cache:
            t = (e.get("type") or "").lower()
            counts[t] = counts.get(t, 0) + 1
    return counts


def get_next_events(n: int = 5) -> list[dict[str, Any]]:
    with _CACHE_LOCK:
        return list(event_cache[: max(0, n)])


def get_next_events_by_type(event_type: str, n: int = 3) -> list[dict[str, Any]]:
    et = (event_type or "").lower()
    with _CACHE_LOCK:
        items = [e for e in event_cache if (e.get("type") or "").lower() == et]
        return items[: max(0, n)]


def _normalize(rows):
    if not isinstance(rows, list):
        raise ValueError("Incomplete event source")
    result, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid event row")
        start, end = _parse_dt(row.get("start_time")), _parse_dt(row.get("end_time"))
        if end <= start:
            raise ValueError("Invalid event duration")
        kind = str(row.get("type") or "").lower()
        key = kind, str(row.get("name") or ""), start
        if key not in seen:
            seen.add(key)
            result.append(
                {**copy.deepcopy(row), "type": kind, "start_time": start, "end_time": end}
            )
    return sorted(result, key=lambda row: row["start_time"])


def _publish(rows, stamp, persistence, *, source="provider"):
    global last_refreshed, _generation, _source, _persistence
    with _CACHE_LOCK:
        event_cache[:] = copy.deepcopy(rows)
        last_refreshed = stamp
        _generation += 1
        _source, _persistence = source, persistence


def load_event_cache():
    """Validate the entire disk candidate before publishing any of it."""
    try:
        with open(CACHE_FILE_PATH, encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            raise ValueError("Invalid cache envelope")
        stamp = _parse_dt(data.get("last_refreshed"))
        if stamp > _aware(utcnow()) + timedelta(minutes=5):
            raise ValueError("Cache timestamp is in the future")
        rows = _normalize(data["events"])
        _publish(rows, stamp, "saved", source="disk")
        logger.info("[EVENT_CACHE] Loaded validated disk snapshot count=%d", len(rows))
    except FileNotFoundError:
        logger.info("[EVENT_CACHE] Disk cache missing; retaining current availability")
    except Exception as exc:
        logger.warning("[EVENT_CACHE] Disk cache unavailable error_type=%s", type(exc).__name__)
    with _CACHE_LOCK:
        return copy.deepcopy(event_cache)


def save_event_cache(rows=None, stamp=None):
    """Persist an exact snapshot; failures propagate and never change its time."""
    if rows is None:
        with _CACHE_LOCK:
            rows, stamp = copy.deepcopy(event_cache), last_refreshed
    if stamp is None:
        raise ValueError("Cannot persist unvalidated cache")
    payload = {
        "last_refreshed": _aware(stamp).isoformat(),
        "events": [
            {
                **row,
                "start_time": _aware(row["start_time"]).isoformat(),
                "end_time": _aware(row["end_time"]).isoformat(),
            }
            for row in rows
        ],
    }
    try:
        if os.path.exists(CACHE_FILE_PATH):
            with (
                open(CACHE_FILE_PATH, "rb") as source,
                open(f"{CACHE_FILE_PATH}.bak", "wb") as dest,
            ):
                dest.write(source.read())
    except Exception as exc:
        logger.warning("[EVENT_CACHE] Backup failed error_type=%s", type(exc).__name__)
    from file_utils import atomic_write_json

    atomic_write_json(CACHE_FILE_PATH, payload, ensure_parent_dir=True)


async def _persist(rows, stamp):
    from services.legacy_export_snapshot_service import drain_thread

    await drain_thread(save_event_cache, rows, stamp)


async def _fetch():
    import event_data_loader as loaders

    timeout = float(GSHEETS_CALL_TIMEOUT or 30.0)
    tasks = [
        asyncio.create_task(loader(timeout=timeout))
        for loader in (
            loaders.load_upcoming_ruins_events,
            loaders.load_upcoming_altar_events,
            loaders.load_upcoming_major_events,
            loaders.load_upcoming_chronicle_events,
        )
    ]
    try:
        _done, pending = await asyncio.wait(
            tasks, timeout=max(EVENT_CACHE_MIN_REFRESH_TIMEOUT, timeout * 1.5)
        )
        if pending:
            logger.warning("[EVENT_CACHE] Refresh timed out; draining original loaders")
            raise TimeoutError("Event loaders exceeded observation budget")
        results = [task.result() for task in tasks]
        if any(not isinstance(result, list) for result in results):
            raise ValueError("One or more event loaders unavailable")
        return [row for result in results for row in result]
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        drained = asyncio.gather(*tasks, return_exceptions=True)
        while not drained.done():
            try:
                await asyncio.shield(drained)
            except asyncio.CancelledError:
                continue


def _preserve(rows):
    with _CACHE_LOCK:
        return bool(
            not rows
            and event_cache
            and (
                last_refreshed is None
                or (_aware(utcnow()) - _aware(last_refreshed)).total_seconds()
                < PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS
            )
        )


def is_cache_stale(max_age_hours=12):
    stamp = get_last_refreshed()
    return stamp is None or _aware(utcnow()) - _aware(stamp) > timedelta(hours=max_age_hours)


async def refresh_event_cache_result(*, observation_seconds=None):
    return await refresh_service.refresh(observation_seconds=observation_seconds)


async def refresh_event_cache():
    """Legacy count API; all callers participate in the same refresh owner."""
    return (await refresh_event_cache_result()).count


# === Accessors ===
def get_events_by_type(event_type: str) -> list[dict[str, Any]]:
    et = (event_type or "").lower()
    with _CACHE_LOCK:
        return [e for e in event_cache if (e.get("type") or "").lower() == et]


def get_all_upcoming_events() -> list[dict[str, Any]]:
    now = _aware(utcnow())
    with _CACHE_LOCK:
        out: list[dict[str, Any]] = []
        for e in event_cache:
            try:
                if _aware(e["start_time"]) > now:
                    out.append(e)
            except Exception:
                continue
        return out


def get_upcoming_event_cache_snapshot(
    *, now_utc: datetime | None = None, max_age_hours: int = 12
) -> UpcomingEventCacheSnapshot:
    """Bulk-load upcoming events and existing health metadata exactly once.

    A successful empty refresh has ``last_refreshed`` and is healthy. An empty
    cache that has never loaded/refreshed has no such evidence and is reported
    unavailable. Staleness remains diagnostic only, matching live KVK dispatch,
    which continues to consume the current in-memory cache.
    """

    now = _aware(now_utc or utcnow())
    with _CACHE_LOCK:
        refreshed = last_refreshed
        generation, source, persistence = _generation, _source, _persistence
        upcoming: list[dict[str, Any]] = []
        for event in event_cache:
            try:
                if _aware(event["start_time"]) > now:
                    upcoming.append(copy.deepcopy(event))
            except Exception:
                continue

    ok = refreshed is not None or bool(upcoming)
    stale = True
    if refreshed is not None:
        try:
            stale = now - _aware(refreshed) > timedelta(hours=max_age_hours)
        except Exception:
            stale = True
    return UpcomingEventCacheSnapshot(
        ok=ok,
        events=tuple(upcoming),
        last_refreshed=refreshed,
        stale=stale,
        error=None if ok else "cache_unavailable",
        generation=generation,
        source=source,
        persistence=persistence,
    )


# Optional convenience: include ongoing items too (not used elsewhere, but handy)
def get_upcoming_or_ongoing_events() -> list[dict[str, Any]]:
    now = _aware(utcnow())
    with _CACHE_LOCK:
        out: list[dict[str, Any]] = []
        for e in event_cache:
            try:
                if _aware(e["end_time"]) > now:
                    out.append(e)
            except Exception:
                continue
        return out


refresh_service = EventCacheService(
    snapshot=lambda: get_upcoming_event_cache_snapshot(),
    fetch=_fetch,
    normalize=_normalize,
    preserve=_preserve,
    persist=_persist,
    publish=_publish,
    clock=lambda: _aware(utcnow()),
)
