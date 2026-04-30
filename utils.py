# utils.py (modified to prefer run_step when available)
import asyncio
import csv
from datetime import UTC, datetime, time as _dt_time
import io
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

from decimal import Decimal
import os
import uuid

import aiofiles
import aiohttp
import discord

from constants import CSV_LOG, INPUT_CACHE_FILE, PLAYER_STATS_CACHE, QUEUE_CACHE_FILE
from event_cache import get_all_upcoming_events

# Use timezone.utc for broader compatibility across Python versions
UTC = UTC

# === Live Queue Setup ===
# Stats cache (hot reload with mtime guard)
_STAT_CACHE: dict = {}
_STAT_CACHE_MTIME: float | None = None

live_queue = {
    "message": None,
    "message_meta": None,  # persisted metadata for message recovery: {"channel_id": int, "message_id": int, "message_created": iso8601}
    "jobs": [],  # Each job: {"filename": str, "user": str, "status": str}
}

# NEW: lock to protect live_queue mutations across async tasks
live_queue_lock: asyncio.Lock = asyncio.Lock()


def utcnow():
    """Returns timezone-aware UTC now timestamp."""
    return datetime.now(UTC)


def format_time_utc(dt: datetime | None = None, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    """
    Return an ISO-like UTC timestamp string for the given datetime.
    - If dt is None, uses utcnow().
    - Ensures the result is in UTC and ends with 'Z' by default.
    - fmt can be overridden if callers expect a different layout.
    """
    if dt is None:
        dt = utcnow()
    dt = ensure_aware_utc(dt).astimezone(UTC)
    # Use strftime so we avoid adding Python-specific offsets; default format ends with Z.
    return dt.strftime(fmt)


def ensure_aware_utc(dt: datetime) -> datetime:
    """
    Ensure the given datetime is timezone-aware in UTC.
    - If dt is naive, attaches UTC tzinfo (assumes naive values are UTC).
    - If dt is aware, converts it to UTC.
    """
    if dt is None:
        raise ValueError("dt must be a datetime instance, not None")
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_isoformat_utc(s: str) -> datetime:
    """
    Parse an ISO timestamp string into an aware UTC datetime.
    Accepts:
      - "2025-10-18T15:31:21+00:00"
      - "2025-10-18T15:31:21Z"
      - "2025-10-18 15:31:21" (assumed UTC)
    """
    if not s:
        raise ValueError("empty timestamp string")
    try:
        # Convert trailing Z to +00:00 for fromisoformat compatibility
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
    except Exception:
        # Fallback: try common space-separated formats without offset
        fmts = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f")
        dt = None
        for fmt in fmts:
            try:
                from datetime import datetime as _dt

                dt = _dt.strptime(s, fmt)
                break
            except Exception:
                dt = None
        if dt is None:
            raise
    return ensure_aware_utc(dt)


def date_to_utc_start(date_obj: Any) -> datetime | None:
    """
    Convert a date-like or datetime object to an aware UTC datetime at 00:00:00 for that date.

    - Accepts a datetime or date (or any object with year/month/day attributes).
    - Returns an aware UTC datetime representing midnight (00:00:00) of that date.
    - Returns None if input is falsy or cannot be converted.

    Note: this uses ensure_aware_utc (existing helper in utils) to guarantee the result
    is timezone-aware UTC. If ensure_aware_utc is not available for any reason, adapt accordingly.
    """
    if not date_obj:
        return None
    try:
        # If a full datetime, normalize to the date's midnight
        if isinstance(date_obj, datetime):
            dt = datetime(date_obj.year, date_obj.month, date_obj.day)
        else:
            # Assume date-like object (has year, month, day) or datetime.date
            dt = datetime.combine(date_obj, _dt_time.min)
        # ensure_aware_utc should be defined elsewhere in utils.py; reuse it.
        return ensure_aware_utc(dt)
    except Exception:
        return None


def make_cid(scope: str, uid: int) -> str:
    """Generate a unique, scoped custom_id for a single view instance."""
    return f"{scope}:{uid}:{uuid.uuid4().hex[:6]}"


# NEW: GovernorID normalizer
def normalize_governor_id(value) -> str:
    """
    Canonical string ID without decimals/whitespace.
    Accepts int/str/float-like inputs: '856126.0' -> '856126'
    """
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    try:
        return str(int(float(s)))
    except Exception:
        return s


def _parse_last_refresh_utc(value) -> datetime | None:
    """
    Best-effort parse of LAST_REFRESH into an aware UTC datetime.

    Rules:
    - datetime -> ensure_aware_utc(dt)
    - ISO string ending in 'Z' -> treat as UTC (+00:00)
    - ISO string without tz -> assume UTC (repo standard)
    - otherwise -> None
    """
    if value is None:
        return None
    try:
        if isinstance(value, datetime):
            return ensure_aware_utc(value)
        s = str(value).strip()
        if not s or s.lower() == "nan":
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return ensure_aware_utc(dt)
    except Exception:
        return None


def score_player_stats_rec(rec: dict | None) -> tuple[int, float, str]:
    """
    Canonical scoring function for deduplicating player stats rows.

    Higher is better:
      - INCLUDED beats non-INCLUDED
      - later LAST_REFRESH beats earlier (parsed as datetime when possible)
      - final tie-breaker: lexical LAST_REFRESH string (backward compatible)

    Returns a tuple suitable for tuple comparison.
    """
    rec = rec or {}
    inc = 1 if rec.get("STATUS") == "INCLUDED" else 0

    raw = rec.get("LAST_REFRESH") or ""
    dt = _parse_last_refresh_utc(raw)
    # Use timestamp as numeric sort key; None -> 0.0 (old/unknown)
    ts = float(dt.timestamp()) if dt is not None else 0.0

    # Preserve old lexical behavior as tie-breaker (and for unparseable formats)
    raw_s = str(raw or "")
    return (inc, ts, raw_s)


def load_live_queue():
    """
    Load persisted live queue from QUEUE_CACHE_FILE.
    Expected persisted shape:
    {
      "jobs": [...],
      "message_meta": {"channel_id": 1234567890, "message_id": 9876543210, "message_created": "ISO8601" } | None
    }

    This function will populate live_queue["jobs"] and live_queue["message_meta"].
    It will NOT attempt to fetch the real discord.Message object (that is done in update_live_queue_embed).
    """
    if not os.path.exists(QUEUE_CACHE_FILE):
        return
    try:
        with open(QUEUE_CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f) or {}
        jobs = data.get("jobs", [])
        message_meta = data.get("message_meta")
        # Defensive checks
        if not isinstance(jobs, list):
            logger.warning("[QUEUE] queue file contained non-list jobs; resetting to empty list.")
            jobs = []
        if message_meta is not None and not isinstance(message_meta, dict):
            logger.warning("[QUEUE] queue file contained invalid message_meta; ignoring.")
            message_meta = None

        # Update global live_queue under lock to avoid races with background tasks
        async def _apply():
            async with live_queue_lock:
                live_queue["jobs"] = jobs
                live_queue["message_meta"] = message_meta
                # We intentionally do NOT set live_queue["message"] here (can't rehydrate without bot)

        try:
            loop = asyncio.get_running_loop()
            # running in event loop -> schedule
            asyncio.run_coroutine_threadsafe(_apply(), loop)
        except RuntimeError:
            # No running loop (likely in sync test or separate thread) -> create a temporary loop and run
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(_apply())
            finally:
                new_loop.close()
        except Exception:
            # Catch-all fallback (older code used get_event_loop); try a safe run
            try:
                asyncio.get_event_loop().run_until_complete(_apply())
            except Exception:
                # Last resort: set state without lock (best-effort)
                live_queue["jobs"] = jobs
                live_queue["message_meta"] = message_meta
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to load live queue: {e}")
        return


def load_stat_cache() -> dict:
    """
    Fast, safe loader for player_stats_cache.json.
    - Caches in memory and auto-reloads when file mtime changes.
    - Removes the _meta block.
    - Normalises keys (GovernorID as canonical string) and inner GovernorID.
    - Dedupes by preferring STATUS=='INCLUDED' and later LAST_REFRESH.
    """
    global _STAT_CACHE, _STAT_CACHE_MTIME
    try:
        mtime = os.path.getmtime(PLAYER_STATS_CACHE)
        if _STAT_CACHE and _STAT_CACHE_MTIME == mtime:
            return _STAT_CACHE

        with open(PLAYER_STATS_CACHE, encoding="utf-8") as f:
            data = json.load(f) or {}
        data.pop("_meta", None)

        normalised = {}
        for k, v in data.items():
            nk = normalize_governor_id(k)
            if isinstance(v, dict):
                v["GovernorID"] = normalize_governor_id(v.get("GovernorID"))
            # Prefer INCLUDED / later LAST_REFRESH if duplicate keys occur
            if nk in normalised:

                if score_player_stats_rec(v) > score_player_stats_rec(normalised[nk]):
                    normalised[nk] = v

            else:
                normalised[nk] = v

        _STAT_CACHE = normalised
        _STAT_CACHE_MTIME = mtime
        return _STAT_CACHE
    except FileNotFoundError:
        logger.warning("[CACHE] stats file missing: %s", PLAYER_STATS_CACHE)
        _STAT_CACHE = {}
        _STAT_CACHE_MTIME = None
        return {}
    except Exception as e:
        logger.exception("[CACHE] failed to load stats cache: %s", e)
        _STAT_CACHE = {}
        _STAT_CACHE_MTIME = None
        return {}


def load_stat_row(governor_id: int | str) -> dict | None:
    """
    Convenience getter for a single governor row (string key).
    Accepts raw int/str/float-like IDs and normalises before lookup.
    """
    cache = load_stat_cache()
    gid = normalize_governor_id(governor_id)
    return cache.get(gid)


async def update_live_queue_embed(bot, notify_channel_id):
    """
    Update or create the live queue embed.

    Enhancements:
    - If a message_meta is present and live_queue['message'] is None, attempt to rehydrate it.
    - If rehydration fails (NotFound/Forbidden), clear message reference so a new message will be created.
    - When persisting, prefer run_step when available for consistent telemetry naming.
    - Prefer process offloads (start_callable_offload/run_maintenance_with_isolation) for
      the save operation when available, with thread fallback.
    """
    channel = bot.get_channel(notify_channel_id)
    if channel is None:
        logger.error("❌ Failed to get NOTIFY_CHANNEL. Check the ID and bot permissions.")
        return

    embed = discord.Embed(title="📊 Live Processing Queue", color=0x3498DB)

    # Snapshot jobs & message under lock to avoid races, then release lock for network ops
    async with live_queue_lock:
        jobs_to_show = list((live_queue.get("jobs", []) or [])[-5:])  # copy
        current_message = live_queue.get("message")
        message_meta = live_queue.get("message_meta")

    # If we don't have an in-memory message but have persisted metadata, attempt to rehydrate it.
    if current_message is None and message_meta:
        try:
            chan_obj = bot.get_channel(int(message_meta.get("channel_id")))
            if chan_obj is None:
                # try fetch
                try:
                    chan_obj = await bot.fetch_channel(int(message_meta.get("channel_id")))
                except Exception:
                    chan_obj = None
            if chan_obj is not None:
                try:
                    msg_obj = await chan_obj.fetch_message(int(message_meta.get("message_id")))
                    # successfully rehydrated — set into live_queue under lock
                    async with live_queue_lock:
                        live_queue["message"] = msg_obj
                        current_message = msg_obj
                        # keep message_meta as-is
                        logger.info(
                            "[QUEUE] Rehydrated live_queue message from persisted metadata (channel=%s message=%s).",
                            message_meta.get("channel_id"),
                            message_meta.get("message_id"),
                        )
                except discord.NotFound:
                    # Message was deleted — clear persisted meta so next update creates a new message
                    logger.info(
                        "[QUEUE] Persisted live_queue message not found (deleted). Will create a new one."
                    )
                    async with live_queue_lock:
                        live_queue["message"] = None
                        live_queue["message_meta"] = None
                except discord.Forbidden:
                    logger.warning(
                        "[QUEUE] Forbidden when rehydrating live_queue message; clearing persisted metadata."
                    )
                    async with live_queue_lock:
                        live_queue["message"] = None
                        live_queue["message_meta"] = None
                except Exception as e:
                    logger.warning(
                        "[QUEUE] Unexpected error while rehydrating live_queue message: %s", e
                    )
                    # leave message_meta in place for future attempts
        except Exception:
            logger.debug("[QUEUE] Rehydration attempt raised unexpected exception", exc_info=True)

    if not jobs_to_show:
        embed.description = "✅ No files currently in queue."
    else:

        def sort_key(job):
            status = job.get("status", "")
            return (
                0 if str(status).startswith("🕐") else 1 if str(status).startswith("⚙️") else 2,
                job.get("filename", ""),
            )

        sorted_jobs = sorted(jobs_to_show, key=sort_key)

        for job in sorted_jobs:
            upload_time = str(job.get("uploaded", ""))[:16].replace("T", " ")
            job_channel = job.get("channel", "unknown")
            filename = job.get("filename", "unknown")
            user = job.get("user", "unknown")
            status = job.get("status", "")
            embed.add_field(
                name=f"📄 {filename}",
                value=f"👤 {user}\n📅 {upload_time} UTC\n📣 #{job_channel}\n{status}",
                inline=False,
            )

    embed.set_footer(text="Tracking latest 5 jobs")
    embed.timestamp = utcnow()  # aware UTC

    try:
        # Now perform network ops; update live_queue['message'] if we create a new message.
        async with live_queue_lock:
            current_message = live_queue.get("message")

        if current_message is None:
            new_msg = await channel.send(embed=embed)
            # persist both in-memory message object and light metadata for recovery after restart
            meta = {}
            try:
                meta["channel_id"] = int(getattr(channel, "id", None) or notify_channel_id)
            except Exception:
                meta["channel_id"] = notify_channel_id
            try:
                meta["message_id"] = int(getattr(new_msg, "id", None))
            except Exception:
                meta["message_id"] = None
            try:
                created_at = getattr(new_msg, "created_at", None)
                if created_at:
                    meta["message_created"] = created_at.isoformat()
            except Exception:
                meta["message_created"] = None

            async with live_queue_lock:
                live_queue["message"] = new_msg
                live_queue["message_meta"] = meta
        else:
            try:
                await current_message.edit(embed=embed)
            except discord.NotFound:
                # Message was deleted; send a fresh one and update meta
                new_msg = await channel.send(embed=embed)
                meta = {}
                try:
                    meta["channel_id"] = int(getattr(channel, "id", None) or notify_channel_id)
                except Exception:
                    meta["channel_id"] = notify_channel_id
                try:
                    meta["message_id"] = int(getattr(new_msg, "id", None))
                except Exception:
                    meta["message_id"] = None
                try:
                    created_at = getattr(new_msg, "created_at", None)
                    if created_at:
                        meta["message_created"] = created_at.isoformat()
                except Exception:
                    meta["message_created"] = None

                async with live_queue_lock:
                    live_queue["message"] = new_msg
                    live_queue["message_meta"] = meta
            except Exception as e:
                logger.error(f"[QUEUE] Failed to edit live queue embed: {e}")
    except discord.NotFound:
        # Channel or webhook issues - try to send fresh
        try:
            new_msg = await channel.send(embed=embed)
            meta = {}
            try:
                meta["channel_id"] = int(getattr(channel, "id", None) or notify_channel_id)
            except Exception:
                meta["channel_id"] = notify_channel_id
            try:
                meta["message_id"] = int(getattr(new_msg, "id", None))
            except Exception:
                meta["message_id"] = None
            try:
                created_at = getattr(new_msg, "created_at", None)
                if created_at:
                    meta["message_created"] = created_at.isoformat()
            except Exception:
                meta["message_created"] = None

            async with live_queue_lock:
                live_queue["message"] = new_msg
                live_queue["message_meta"] = meta
        except Exception as e:
            logger.error(f"[QUEUE] Failed to send live queue embed after NotFound: {e}")
    except Exception as e:
        logger.error(f"[EMBED] Failed to send or update live queue embed: {e}")

    # Persist current jobs + light message metadata to disk using sync save_live_queue via run_step when available
    try:
        # Local import to avoid circular-import at module import time
        try:
            from file_utils import run_step  # prefer standardized wrapper
        except Exception:
            run_step = None

        if run_step is not None:
            await run_step(save_live_queue, name="save_live_queue", meta={"path": QUEUE_CACHE_FILE})
            return

        # Prefer process-level offload for saving if available, then thread fallback
        try:
            from file_utils import (  # type: ignore
                run_maintenance_with_isolation,
                start_callable_offload,
            )
        except Exception:
            start_callable_offload = None
            run_maintenance_with_isolation = None

        # Try start_callable_offload first (lighter weight for short callables), else maintenance isolation
        if start_callable_offload is not None:
            try:
                await start_callable_offload(
                    save_live_queue,
                    name="save_live_queue",
                    prefer_process=True,
                    meta={"path": QUEUE_CACHE_FILE},
                )
                return
            except Exception:
                # fall through to other options
                pass

        if run_maintenance_with_isolation is not None:
            try:
                await run_maintenance_with_isolation(
                    save_live_queue,
                    name="save_live_queue",
                    prefer_process=True,
                    meta={"path": QUEUE_CACHE_FILE},
                )
                return
            except Exception:
                pass

        # Thread fallback
        try:
            from file_utils import (
                run_blocking_in_thread as run_blocking_in_thread_fallback,  # type: ignore
            )
        except Exception:
            run_blocking_in_thread_fallback = None

        if run_blocking_in_thread_fallback is not None:
            await run_blocking_in_thread_fallback(
                save_live_queue, name="save_live_queue", meta={"path": QUEUE_CACHE_FILE}
            )
            return

        # Last resort: run in thread via asyncio.to_thread
        await asyncio.to_thread(save_live_queue)
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to persist live queue: {e}")


async def download_attachment(
    attachment,
    save_path,
    max_attempts: int = 3,
    delay_seconds: float = 2,
    channel_name: str | None = None,
    user: object | None = None,
):
    """
    Robust downloader:
    - Reuses one aiohttp session with a reasonable timeout.
    - Streams to disk with aiofiles (low memory).
    - Logs success/failure to CSV.
    """
    timeout = aiohttp.ClientTimeout(total=120)
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    filename = getattr(attachment, "filename", "unknown")
    for attempt in range(1, max_attempts + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(save_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(64 * 1024):
                                await f.write(chunk)

                        # Local import to avoid circular import at module import time
                        try:
                            from file_utils import append_csv_line as _append_csv_line
                        except Exception:
                            _append_csv_line = None

                        if _append_csv_line:
                            try:
                                # Use centralized CSV_LOG constant instead of hard-coded filename
                                await _append_csv_line(
                                    CSV_LOG,
                                    [
                                        utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                        channel_name or "unknown",
                                        filename,
                                        str(user) if user else "unknown",
                                        save_path,
                                    ],
                                )
                            except Exception:
                                logger.warning(
                                    "[DOWNLOAD] Failed to append to CSV log for %s", filename
                                )
                        return True
                    else:
                        logger.warning(
                            "[DOWNLOAD] HTTP %s on attempt %s for %s",
                            resp.status,
                            attempt,
                            filename,
                        )
        except Exception:
            logger.exception(f"[DOWNLOAD] Attempt {attempt} failed for {filename}")
        await asyncio.sleep(delay_seconds)

    # try to log failure
    try:
        from file_utils import append_csv_line as _append_csv_line
    except Exception:
        _append_csv_line = None

    if _append_csv_line:
        try:
            await _append_csv_line(
                CSV_LOG,
                [
                    utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    channel_name or "unknown",
                    filename,
                    str(user) if user else "unknown",
                    "DOWNLOAD FAILED",
                ],
            )
        except Exception:
            logger.warning("[DOWNLOAD] Failed to append failure to CSV log for %s", filename)
    return False


async def async_log_csv(filename, row_dict, headers=None):
    file_exists = os.path.isfile(filename)
    buffer = io.StringIO()
    fieldnames = list(headers) if headers else list(row_dict.keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)

    if not file_exists and headers:
        writer.writeheader()
    writer.writerow(row_dict)

    async with aiofiles.open(filename, mode="a", encoding="utf-8", newline="") as f:
        await f.write(buffer.getvalue())


def load_cached_input():
    if not os.path.exists(INPUT_CACHE_FILE):
        return None
    try:
        with open(INPUT_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[INPUT_CACHE] Failed to load: {e}")
        return None


def save_cached_input(date_str, rank, seed):
    try:
        with open(INPUT_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"date": date_str, "rank": rank, "seed": seed}, f)
    except Exception as e:
        logger.warning(f"[INPUT_CACHE] Failed to save: {e}")


def get_next_fights(limit=3):
    all_events = get_all_upcoming_events()
    fights = []

    for e in all_events:
        event_type = e.get("type", "").lower()
        desc = (e.get("description") or e.get("name") or "").strip().upper()

        if "altar" in event_type:
            fights.append(e)
        elif event_type == "major" and "FIGHT" in desc:
            fights.append(e)

    fights.sort(key=lambda e: e["start_time"])
    return fights[:limit]


def format_countdown(dt, short=False):
    # Normalise naive datetimes to UTC
    dt = ensure_aware_utc(dt)
    now = utcnow()  # aware
    delta = dt - now

    if delta.total_seconds() <= 0:
        return "Now"

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60

    if short:
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if not parts:
            return "Now"
        return " ".join(parts)
    else:
        return f"in {days} day(s), {hours} hour(s), {minutes} minute(s)"


def get_next_events(limit=5, event_type=None):
    all_events = get_all_upcoming_events()
    filtered = []

    # Canonical type mapping to keep utils in sync with embeds
    TYPE_MAP = {
        "ruins": "ruins",
        "next ruins": "ruins",
        "altar": "altar",  # canonical singular here
        "altars": "altar",
        "next altar fight": "altar",
        "chronicle": "chronicle",
        "major": "major",
    }
    for e in all_events:
        raw = (e.get("type") or "").lower()
        etype = TYPE_MAP.get(raw, raw)

        # Only include relevant types
        if etype not in ("altar", "ruins", "chronicle", "major"):
            continue

        # Optional type filter (accept either canonical or raw input)
        if event_type:
            wanted = TYPE_MAP.get(event_type.lower(), event_type.lower())
            if etype != wanted:
                continue

        filtered.append(e)

    filtered.sort(key=lambda e: e["start_time"])
    return filtered[:limit]


# Atomic save for live queue (overwrite temp then replace)
def save_live_queue():
    """
    Persist live_queue jobs and a small message metadata blob so the process can
    attempt to rehydrate the embed after restart.

    Persisted JSON shape:
    {
      "jobs": [...],
      "message_meta": {"channel_id": int, "message_id": int, "message_created": iso8601|null} | null
    }
    """
    try:
        tmp = f"{QUEUE_CACHE_FILE}.tmp"
        # Snapshot current live_queue state in a best-effort, race-tolerant manner.
        try:
            # If running inside an event loop, try to snapshot under lock to avoid races.
            loop = asyncio.get_running_loop()

            # We're in async context -> schedule a quick snapshot coroutine
            async def _snapshot():
                async with live_queue_lock:
                    return {
                        "jobs": live_queue.get("jobs", []),
                        "message_meta": live_queue.get("message_meta"),
                    }

            fut = asyncio.run_coroutine_threadsafe(_snapshot(), loop)
            data = fut.result(timeout=2)
        except Exception:
            # Not in running loop or snapshot failed — shallow copy as best-effort
            data = {
                "jobs": list(live_queue.get("jobs", [])),
                "message_meta": live_queue.get("message_meta"),
            }

        meta = data.get("message_meta") if isinstance(data, dict) else None

        # If live_queue already has a message_meta (from load), prefer that if meta is None
        if meta is None:
            existing_meta = live_queue.get("message_meta")
            if existing_meta:
                meta = existing_meta

        # final persisted payload
        payload = {
            "jobs": data.get("jobs", []) if isinstance(data, dict) else [],
            "message_meta": meta,
        }

        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, QUEUE_CACHE_FILE)
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to save: {e}")


# -----------------------
# New: csv_from_ids & to_ints (moved here)
# -----------------------
def csv_from_ids(ids: list[int]) -> str:
    """Join a list of ints into a CSV string (no spaces)."""
    return ",".join(str(i) for i in ids)


def to_ints(maybe_ids: list[str | int]) -> list[int]:
    """
    Normalize a list of values that may be strings/ints into unique sorted ints.

    - Accepts strings like '123', ' 456 ', '789.0' and numeric types.
    - Silently ignores values that cannot be coerced to int.
    """
    out: set[int] = set()
    for v in maybe_ids or []:
        try:
            # accept float-like strings ("123.0") by converting via float first
            out.add(int(float(str(v).strip())))
        except Exception:
            continue
    return sorted(out)


def fmt_short(n: int | float | None) -> str:
    """
    Small human-friendly integer formatter (e.g., 1200 -> '1.2k', 1_200_000 -> '1.2M').
    This function is intentionally tiny and avoids importing heavy deps.
    """
    try:
        if n is None:
            return "0"
        n = float(n)
        abs_n = abs(n)
        if abs_n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B"
        if abs_n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if abs_n >= 1_000:
            return f"{n/1_000:.1f}k"
        return f"{int(n)}"
    except Exception:
        return str(n)


# New: central JSON default serializer (used across the project)
try:
    import numpy as _np  # optional
except Exception:
    _np = None


def json_default(o):
    """
    JSON serializer fallback for types commonly encountered across the bot:
    - datetime/date -> ISO 8601 string
    - Decimal -> int or float
    - sets/tuples -> list
    - numpy scalars -> Python scalars
    - fallback: str(o)
    """
    try:
        if isinstance(o, (datetime,)):
            return o.isoformat()
    except Exception:
        pass

    try:
        if isinstance(o, Decimal):
            try:
                i = int(o)
                if Decimal(i) == o:
                    return i
            except Exception:
                pass
            return float(o)
    except Exception:
        pass

    try:
        if isinstance(o, (set, tuple)):
            return list(o)
    except Exception:
        pass

    try:
        if _np is not None and isinstance(o, (_np.integer, _np.floating, _np.bool_)):  # type: ignore[attr-defined]
            return o.item()
    except Exception:
        pass

    try:
        return str(o)
    except Exception:
        return None
