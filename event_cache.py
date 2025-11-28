# event_cache.py
import asyncio
from datetime import UTC, datetime, timedelta
import json
import logging
import os
import tempfile
from threading import RLock
from typing import Any

from discord.utils import utcnow

from constants import CACHE_FILE_PATH
from event_data_loader import (
    Event as LoaderEvent,  # <- typed view, optional
    load_upcoming_altar_events,
    load_upcoming_chronicle_events,
    load_upcoming_major_events,
    load_upcoming_ruins_events,
)

# Optional: allow partial success (default False keeps current behavior)
ALLOW_PARTIAL_EVENT_CACHE = False

logger = logging.getLogger(__name__)

# Global in-memory cache + metadata
event_cache: list[LoaderEvent] = []
last_refreshed: datetime | None = None
_CACHE_LOCK = RLock()  # cheap guard for concurrent reads/writes

# Use timezone-aware UTC constant
UTC = UTC


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


def _atomic_json_write(path: str, payload: dict) -> None:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".eventcache.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        # Best effort cleanup
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        raise


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

        # --- NEW: take a backup of the CURRENT file first (previous snapshot) ---
        try:
            if os.path.exists(CACHE_FILE_PATH):
                bak = f"{CACHE_FILE_PATH}.bak"
                # Copy the existing cache to .bak so we can restore it if the new write goes bad
                # Use binary copy; metadata not essential
                with open(CACHE_FILE_PATH, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
        except Exception:
            # Best-effort: if backup fails, keep going; the atomic write still protects main file
            pass

        # Atomic write of the NEW payload
        _atomic_json_write(CACHE_FILE_PATH, payload)

        # Only set last_refreshed after successful write
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
    """
    global event_cache
    try:
        ruins_raw, altars_raw, majors_raw, chronicles_raw = await asyncio.gather(
            load_upcoming_ruins_events(),
            load_upcoming_altar_events(),
            load_upcoming_major_events(),
            load_upcoming_chronicle_events(),
        )

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
        with _CACHE_LOCK:
            event_cache[:] = normalized

        save_event_cache()  # updates last_refreshed
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
