# event_cache.py
import asyncio
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

# Optional: allow partial success (default False keeps current behavior)
ALLOW_PARTIAL_EVENT_CACHE = False

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


def _as_list(x: Any) -> tuple[list[Any], bool]:
    """Return (list_value, ok_flag). ok_flag=False if loader looks failed (None/non-list)."""
    if isinstance(x, list):
        return x, True
    if x is None:
        return [], False
    try:
        return list(x), True
    except Exception:
        return [], False


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


# === Load from disk ===
def load_event_cache() -> list[dict[str, Any]]:
    global event_cache, last_refreshed
    try:
        with open(CACHE_FILE_PATH, encoding="utf-8") as f:
            data = json.load(f)

        raw_events = data.get("events", []) or []
        last_refreshed_str = data.get("last_refreshed")

        parsed: list[dict[str, Any]] = []
        for e in raw_events:
            try:
                # normalize/validate
                st = _parse_dt(e.get("start_time"))
                et = _parse_dt(e.get("end_time"))
                if et <= st:
                    logger.warning(
                        "[EVENT_CACHE] Skipping cached event with non-positive duration: %r", e
                    )
                    continue
                normalized = {
                    **e,
                    "start_time": st,
                    "end_time": et,
                }
                # normalize event type for consistent filtering
                if "type" in normalized and isinstance(normalized["type"], str):
                    normalized["type"] = normalized["type"].lower()
                parsed.append(normalized)
            except Exception as ex:
                logger.warning("[EVENT_CACHE] Skipping malformed cached event: %r (%s)", e, ex)

        with _CACHE_LOCK:
            # Replace in place to preserve external references
            event_cache[:] = sorted(parsed, key=lambda ev: ev["start_time"])
            last_refreshed = _parse_dt(last_refreshed_str) if last_refreshed_str else None

        logger.info(
            "[EVENT_CACHE] Loaded %d events from disk (last refreshed %s).",
            len(event_cache),
            last_refreshed,
        )
        return event_cache

    except FileNotFoundError:
        logger.warning("[EVENT_CACHE] Cache file not found.")
        with _CACHE_LOCK:
            event_cache.clear()
            last_refreshed = None
        return event_cache
    except Exception as e:
        logger.error("[EVENT_CACHE] Failed to load cache: %s", e)
        # Do not clear an existing in-memory cache if we had one already.
        return event_cache


# === Save to disk ===
def save_event_cache() -> None:
    global last_refreshed
    try:
        with _CACHE_LOCK:
            snapshot = [
                {
                    **e,
                    "start_time": _aware(e["start_time"]).isoformat(),
                    "end_time": _aware(e["end_time"]).isoformat(),
                }
                for e in event_cache
            ]

        now_ts = _aware(utcnow())
        payload = {"last_refreshed": now_ts.isoformat(), "events": snapshot}

        # Backup previous cache if present (best-effort)
        try:
            if os.path.exists(CACHE_FILE_PATH):
                bak = f"{CACHE_FILE_PATH}.bak"
                with open(CACHE_FILE_PATH, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
        except Exception:
            pass

        # Lazy import to avoid circular dependency during startup
        from file_utils import atomic_write_json  # type: ignore

        atomic_write_json(CACHE_FILE_PATH, payload, ensure_parent_dir=True)

        with _CACHE_LOCK:
            last_refreshed = now_ts

        logger.info("[EVENT_CACHE] Saved %d events to disk.", len(snapshot))
    except Exception as e:
        logger.error("[EVENT_CACHE] Failed to save cache: %s", e)


# === Check if stale ===
def is_cache_stale(max_age_hours: int = 12) -> bool:
    with _CACHE_LOCK:
        lr = last_refreshed
    if not lr:
        return True
    try:
        return _aware(utcnow()) - _aware(lr) > timedelta(hours=max_age_hours)
    except Exception:
        # Defensive: if anything off with timestamps, treat as stale.
        return True


# === Refresh from GSheet ===
async def refresh_event_cache() -> int:
    """
    Refresh from Google Sheet loaders.

    RETURNS:
        int: number of events now in-memory.

    BEHAVIOR:
    - If all loaders succeed (or partial allowed and at least one succeeded), replace cache and save.
    - If required loaders failed (and partial not allowed), preserve previous cache and do not save.
    - If merge yields zero events but previous cache had items and was refreshed recently,
      PRESERVE previous in-memory cache (do not overwrite with empty).
    """
    global event_cache
    try:
        # Import loaders at runtime so tests can monkeypatch event_data_loader.* easily
        import event_data_loader as edl

        # Build loader coroutines with per-loader timeout param
        per_loader_timeout = float(GSHEETS_CALL_TIMEOUT or 30.0)
        tasks = [
            edl.load_upcoming_ruins_events(timeout=per_loader_timeout),
            edl.load_upcoming_altar_events(timeout=per_loader_timeout),
            edl.load_upcoming_major_events(timeout=per_loader_timeout),
            edl.load_upcoming_chronicle_events(timeout=per_loader_timeout),
        ]

        # Bound the entire refresh so a misbehaving loader can't hang forever.
        overall_timeout = max(5.0, per_loader_timeout * 1.5)
        try:
            ruins_raw, altars_raw, majors_raw, chronicles_raw = await asyncio.wait_for(
                asyncio.gather(*tasks), timeout=overall_timeout
            )
        except TimeoutError:
            logger.warning(
                "[EVENT_CACHE] Refresh timed out after %.1fs; preserving previous cache.",
                overall_timeout,
            )
            return len(event_cache)

        ruins, ok_r = _as_list(ruins_raw)
        altars, ok_a = _as_list(altars_raw)
        majors, ok_m = _as_list(majors_raw)
        chronicles, ok_c = _as_list(chronicles_raw)

        logger.info(
            "[EVENT_CACHE] Loader counts — ruins=%d altars=%d majors=%d chronicles=%d",
            len(ruins),
            len(altars),
            len(majors),
            len(chronicles),
        )

        loaders_ok = ok_r and ok_a and ok_m and ok_c
        if not loaders_ok:
            bad = [
                name
                for name, ok in [
                    ("ruins", ok_r),
                    ("altars", ok_a),
                    ("majors", ok_m),
                    ("chronicles", ok_c),
                ]
                if not ok
            ]
            if not ALLOW_PARTIAL_EVENT_CACHE:
                logger.warning(
                    "[EVENT_CACHE] One or more loaders failed: %s — preserving previous cache.",
                    ", ".join(bad),
                )
                return len(event_cache)
            else:
                logger.warning(
                    "[EVENT_CACHE] Partial refresh; failed: %s — proceeding with available data.",
                    ", ".join(bad),
                )

        # Merge available (even if some are empty)
        new_events_raw: list[dict[str, Any]] = []
        if ok_r:
            new_events_raw += ruins
        if ok_a:
            new_events_raw += altars
        if ok_m:
            new_events_raw += majors
        if ok_c:
            new_events_raw += chronicles

        # Normalize, validate, and de-duplicate
        seen: set[tuple] = set()
        normalized: list[dict[str, Any]] = []
        for e in new_events_raw:
            try:
                st = _parse_dt(e.get("start_time"))
                et = _parse_dt(e.get("end_time"))
                if et <= st:
                    logger.warning("[EVENT_CACHE] Dropping event with non-positive duration: %r", e)
                    continue

                typ = (e.get("type") or "").lower()
                name = str(e.get("name") or "")
                key = (typ, name, st.isoformat())

                if key in seen:
                    continue
                seen.add(key)

                row = {**e, "type": typ, "start_time": st, "end_time": et}
                normalized.append(row)
            except Exception as ex:
                logger.warning(
                    "[EVENT_CACHE] Dropping malformed event from loaders: %r (%s)", e, ex
                )

        normalized.sort(key=lambda ev: ev["start_time"])

        # PROTECT: do not overwrite non-empty cache with an empty refresh if the previous cache
        # was refreshed recently (configurable).
        with _CACHE_LOCK:
            prev_count = len(event_cache)
            prev_lr = last_refreshed

        if len(normalized) == 0 and prev_count > 0:
            # If we have a previous cache and it was refreshed recently, preserve it.
            preserve = False
            try:
                if prev_lr is not None:
                    age_seconds = (_aware(utcnow()) - _aware(prev_lr)).total_seconds()
                    if age_seconds < PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS:
                        preserve = True
                else:
                    # No last_refreshed recorded; be conservative and preserve
                    preserve = True
            except Exception:
                preserve = True

            if preserve:
                logger.warning(
                    "[EVENT_CACHE] Refusing to replace non-empty cache with empty refresh (age=%s sec) — preserving previous cache.",
                    (
                        (_aware(utcnow()) - _aware(prev_lr)).total_seconds()
                        if prev_lr
                        else "unknown"
                    ),
                )
                # Emit telemetry for operators (best-effort)
                try:
                    from file_utils import emit_telemetry_event

                    emit_telemetry_event(
                        {
                            "event": "event_cache_preserve_on_empty",
                            "prev_count": prev_count,
                            "preserve_seconds": PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS,
                            "last_refreshed": prev_lr.isoformat() if prev_lr else None,
                        }
                    )
                except Exception:
                    try:
                        telemetry_logger = logging.getLogger("telemetry")
                        telemetry_logger.info(
                            {
                                "event": "event_cache_preserve_on_empty",
                                "prev_count": prev_count,
                                "preserve_seconds": PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS,
                                "last_refreshed": prev_lr.isoformat() if prev_lr else None,
                            }
                        )
                    except Exception:
                        pass
                return len(event_cache)

        with _CACHE_LOCK:
            event_cache[:] = normalized

        try:
            from file_utils import run_blocking_in_thread  # type: ignore
        except Exception:
            run_blocking_in_thread = None

        if run_blocking_in_thread:
            await run_blocking_in_thread(save_event_cache, name="save_event_cache")
        else:
            await asyncio.to_thread(save_event_cache)

        logger.info("[EVENT_CACHE] Refreshed event data. (%d events)", len(normalized))
        return len(normalized)

    except Exception as e:
        logger.error("[EVENT_CACHE] Failed to refresh event cache: %s", e)
        return len(event_cache)


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
