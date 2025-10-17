# utils.py
import asyncio
import csv
from datetime import UTC, datetime
import io
import json
import logging

logger = logging.getLogger(__name__)

import os
import uuid

import aiofiles
import aiohttp
import discord

from constants import INPUT_CACHE_FILE, PLAYER_STATS_CACHE, QUEUE_CACHE_FILE
from event_cache import get_all_upcoming_events
from file_utils import append_csv_line

# === Live Queue Setup ===
# Stats cache (hot reload with mtime guard)
_STAT_CACHE: dict = {}
_STAT_CACHE_MTIME: float | None = None

live_queue = {
    "message": None,
    "jobs": [],  # Each job: {"filename": str, "user": str, "status": str}
}


def utcnow():
    """Returns timezone-aware UTC now timestamp."""
    return datetime.now(UTC)


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


def load_live_queue():
    if not os.path.exists(QUEUE_CACHE_FILE):
        return
    try:
        with open(QUEUE_CACHE_FILE, encoding="utf-8") as f:
            live_queue["jobs"] = json.load(f)
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to load: {e}")


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

                def score(rec):
                    inc = 1 if (rec or {}).get("STATUS") == "INCLUDED" else 0
                    dt = str((rec or {}).get("LAST_REFRESH") or "")
                    return (inc, dt)

                if score(v) > score(normalised[nk]):
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
    channel = bot.get_channel(notify_channel_id)
    if channel is None:
        logger.error("❌ Failed to get NOTIFY_CHANNEL. Check the ID and bot permissions.")
        return

    embed = discord.Embed(title="📊 Live Processing Queue", color=0x3498DB)

    jobs_to_show = live_queue["jobs"][-5:]  # ✅ Show only last 5 jobs (adjustable)
    if not jobs_to_show:
        embed.description = "✅ No files currently in queue."
    else:

        def sort_key(job):
            status = job["status"]
            return (
                0 if status.startswith("🕐") else 1 if status.startswith("⚙️") else 2,
                job["filename"],
            )

        sorted_jobs = sorted(jobs_to_show, key=sort_key)

        for job in sorted_jobs:
            upload_time = job.get("uploaded", "")[:16].replace("T", " ")
            job_channel = job.get("channel", "unknown")
            embed.add_field(
                name=f"📄 {job['filename']}",
                value=f"👤 {job['user']}\n📅 {upload_time} UTC\n📣 #{job_channel}\n{job['status']}",
                inline=False,
            )

    embed.set_footer(text="Tracking latest 5 jobs")
    embed.timestamp = utcnow()  # aware UTC

    try:
        if live_queue["message"] is None:
            live_queue["message"] = await channel.send(embed=embed)
        else:
            await live_queue["message"].edit(embed=embed)
    except discord.NotFound:
        live_queue["message"] = await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"[EMBED] Failed to send or update live queue embed: {e}")

    save_live_queue()


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
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(1, max_attempts + 1):
            try:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(save_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(64 * 1024):
                                await f.write(chunk)

                        await append_csv_line(
                            "download_log.csv",
                            [
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                channel_name or "unknown",
                                attachment.filename,
                                str(user) if user else "unknown",
                                save_path,
                            ],
                        )
                        return True
                    else:
                        logger.warning(
                            "[DOWNLOAD] HTTP %s on attempt %s for %s",
                            resp.status,
                            attempt,
                            attachment.filename,
                        )
            except Exception:
                logger.exception(f"[DOWNLOAD] Attempt {attempt} failed for {attachment.filename}")
            await asyncio.sleep(delay_seconds)

    await append_csv_line(
        "download_log.csv",
        [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            channel_name or "unknown",
            attachment.filename,
            str(user) if user else "unknown",
            "DOWNLOAD FAILED",
        ],
    )
    return False


async def async_log_csv(filename, row_dict, headers=None):
    file_exists = os.path.isfile(filename)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers or row_dict.keys())

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
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
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
    try:
        tmp = f"{QUEUE_CACHE_FILE}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(live_queue["jobs"], f)
        os.replace(tmp, QUEUE_CACHE_FILE)
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to save: {e}")
