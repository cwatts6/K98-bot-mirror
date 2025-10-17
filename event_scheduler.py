# event_scheduler.py
import asyncio
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

import os
import random
import shutil
import time

import discord

from constants import (
    DM_SCHEDULED_TRACKER_FILE,
    DM_SENT_TRACKER_FILE,
    FAILED_DM_LOG,
    REMINDER_TRACKING_FILE,
)
from embed_utils import LocalTimeToggleView
from event_cache import get_all_upcoming_events
from governor_registry import load_registry
from reminder_task_registry import register_user_task
from subscription_tracker import DEFAULT_REMINDER_TIMES, get_all_subscribers
from utils import utcnow

# Per-user trackers (nested):
# dm_sent_tracker:      { event_id: { user_id: [delta_seconds, ...] } }
# dm_scheduled_tracker: { event_id: { user_id: set(delta_seconds) } }
dm_scheduled_tracker = {}

# --- Throttled logging helpers ---------------------------------------------
_LAST_TRACKER_STATS_LOG = 0.0


def _log_tracker_stats_if_due():
    """
    Log tracker sizes at most once per 60s to avoid spamming the logging sink.
    (Important for non-blocking event loop behaviour.)
    """
    global _LAST_TRACKER_STATS_LOG
    now = time.monotonic()
    if now - _LAST_TRACKER_STATS_LOG >= 60.0:
        try:
            logger.info(
                "[DM_TRACKER_STATS] Events with sent: %d | Events with scheduled: %d",
                len(dm_sent_tracker),
                len(dm_scheduled_tracker),
            )
        except Exception:
            # Never raise from logging
            pass
        _LAST_TRACKER_STATS_LOG = now
        return True
    return False


REMINDER_WINDOWS = [
    timedelta(hours=24),
    timedelta(hours=12),
    timedelta(hours=4),
    timedelta(hours=1),
    timedelta(minutes=0),
]

TEST_REMINDER_WINDOWS = [
    timedelta(minutes=1),
    timedelta(seconds=30),
    timedelta(seconds=10),
    timedelta(seconds=0),
]

sent_reminders = {}  # {event_id: set[timedelta]}
active_reminders = {}  # {event_id: discord.Message}

EXPIRY_DELAY = 3600  # 1 hour in seconds

# --- Quotes ---------------------------------------------------------------
# Personalized DM quotes — placeholders:
#   {name} -> Discord display name
#   {gov}  -> Main Governor Name (fallback to {name} if unknown)
DM_QUOTES: dict[str, list[str]] = {
    "ruins": [
        "Ruins incoming, {gov}! Time to claim what’s ours.",
        "The timer's up soon, {name}. March fast, earn that honour!",
        "Ruins window opening be there {gov}!",
    ],
    "altars": [
        "Altar fight brewing hold the line, {gov}!",
        "No surrender, {name}. We fight with purpose.",
        "Altar pressure wins wars. Be early, {gov}!",
    ],
    "major": [
        "Pass fight let’s get ready to rumble, {gov}!",
        "Its fighting time, {name}! Today we write history.",
        "Lets smash our enemy! Sharpen those spears, {gov}!",
    ],
    "chronicle": [
        "New page in the Chronicle, make your mark {name}.",
        "History remembers the bold. Be there, {gov}.",
        "Chronicle incoming get ready, {name}.",
    ],
    # Fallbacks if event['type'] is unexpected
    "_default": [
        "Opportunity knocks, {gov}. Answer in force.",
        "Discipline wins the day, {name}. Form up.",
        "Steel your resolve, {gov}.",
    ],
}

# Public quotes (non-personalized) shown only at T-1h and T-0 in channel reminders
PUBLIC_QUOTES: dict[str, list[str]] = {
    "ruins": [
        "Ruins window opens soon,  send your marches.",
        "Eye on Ruins: lets earn that honour!",
    ],
    "altars": [
        "Altar fight ahead, no surrender forward march!",
        "Hold the altar, destroy our enemy. Buffs, marches and heals ready.",
    ],
    "major": [
        "Pass fight prep — gather at staging, check rallies and markers.",
        "Big push soon — comms on, formations locked.",
    ],
    "chronicle": [
        "New Chronicle approaching — check out whats needed.",
        "New stage unlocking — watch objectives and timers.",
    ],
    "_default": [
        "Next event approaching — be ready.",
        "Countdown on — gear up and form ranks.",
    ],
}

reminder_stats = {"dm_success": 0, "dm_dm_disabled": 0, "dm_failed": 0}

dm_sent_tracker = {}  # {event_id: { user_id: [delta_seconds,...] }}


def _get_main_governor_name_for_user(user_id: int | str) -> str | None:
    """Return the Main governor name for a user (fallback to any registered)."""
    try:
        reg = load_registry()
        entry = reg.get(str(user_id)) or {}
        accounts = entry.get("accounts") or {}
        if "Main" in accounts:
            name = (accounts["Main"].get("GovernorName") or "").strip()
            return name or None
        # Fallback to the first account if Main not present
        for _label, acct in accounts.items():
            name = (acct.get("GovernorName") or "").strip()
            if name:
                return name
    except Exception:
        pass
    return None


def _ensure_parent(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def load_dm_sent_tracker():
    """Load and migrate dm_sent_tracker to per-user nested dict."""
    global dm_sent_tracker
    dm_sent_tracker = {}
    if not os.path.exists(DM_SENT_TRACKER_FILE):
        return
    try:
        with open(DM_SENT_TRACKER_FILE, encoding="utf-8") as f:
            raw = json.load(f) or {}
        migrated = {}
        for event_id, value in (raw.items() if isinstance(raw, dict) else []):
            if isinstance(value, list):
                # Old shape: drop (no user info to recover), start clean per event
                migrated[event_id] = {}
            elif isinstance(value, dict):
                per_user = {}
                for uid, lst in value.items():
                    if isinstance(lst, list):
                        per_user[str(uid)] = lst
                    else:
                        per_user[str(uid)] = []
                migrated[event_id] = per_user
            else:
                migrated[event_id] = {}
        dm_sent_tracker = migrated
        logger.info("[DM_TRACKER] Loaded dm_sent_tracker with migration.")
    except Exception as e:
        logger.warning(f"[DM_TRACKER] Failed to load dm_sent_tracker: {e}")
        dm_sent_tracker = {}


def save_dm_sent_tracker():
    """Persist dm_sent_tracker ensuring inner values are lists."""
    try:
        _ensure_parent(DM_SENT_TRACKER_FILE)
        temp_file = DM_SENT_TRACKER_FILE + ".tmp"
        serializable = {}
        for event_id, per_user in (
            dm_sent_tracker.items() if isinstance(dm_sent_tracker, dict) else []
        ):
            serializable[event_id] = {}
            for uid, lst in (per_user.items() if isinstance(per_user, dict) else []):
                serializable[event_id][str(uid)] = list(lst or [])
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)
        shutil.move(temp_file, DM_SENT_TRACKER_FILE)
        logger.info("[DM_TRACKER] Saved dm_sent_tracker to disk.")
    except Exception as e:
        logger.warning(f"[DM_TRACKER] Failed to save dm_sent_tracker: {e}")


def save_dm_scheduled_tracker():
    """Persist dm_scheduled_tracker ensuring inner sets are serialized to lists."""
    try:
        _ensure_parent(DM_SCHEDULED_TRACKER_FILE)
        temp_file = DM_SCHEDULED_TRACKER_FILE + ".tmp"
        serializable = {}
        for event_id, per_user in (
            dm_scheduled_tracker.items() if isinstance(dm_scheduled_tracker, dict) else []
        ):
            serializable[event_id] = {}
            for uid, s in (per_user.items() if isinstance(per_user, dict) else []):
                serializable[event_id][str(uid)] = list(s or set())
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)
        shutil.move(temp_file, DM_SCHEDULED_TRACKER_FILE)
        logger.info("[DM_TRACKER] Saved dm_scheduled_tracker to disk.")
    except Exception as e:
        logger.warning(f"[DM_TRACKER] Failed to save dm_scheduled_tracker: {e}")


def load_dm_scheduled_tracker():
    """Load and migrate dm_scheduled_tracker to per-user nested dict with sets."""
    global dm_scheduled_tracker
    dm_scheduled_tracker = {}
    if not os.path.exists(DM_SCHEDULED_TRACKER_FILE):
        return
    try:
        with open(DM_SCHEDULED_TRACKER_FILE, encoding="utf-8") as f:
            raw = json.load(f) or {}
        migrated = {}
        for event_id, value in (raw.items() if isinstance(raw, dict) else []):
            if isinstance(value, list):
                # Old shape: drop (no user info), start clean
                migrated[event_id] = {}
            elif isinstance(value, dict):
                per_user = {}
                for uid, lst in value.items():
                    if isinstance(lst, list):
                        per_user[str(uid)] = set(lst)
                    else:
                        per_user[str(uid)] = set()
                migrated[event_id] = per_user
            else:
                migrated[event_id] = {}
        dm_scheduled_tracker = migrated
        logger.info("[DM_TRACKER] Loaded dm_scheduled_tracker with migration.")
    except Exception as e:
        logger.warning(f"[DM_TRACKER] Failed to load dm_scheduled_tracker: {e}")


def log_failed_dm(user_id, event, delta, reason):
    log_entry = {
        "user_id": str(user_id),
        "event_name": event["name"],
        "event_time": event["start_time"].isoformat(),
        "delta_seconds": int(delta.total_seconds()),
        "reason": reason,
        "timestamp": utcnow().isoformat(),
    }

    try:
        if os.path.exists(FAILED_DM_LOG):
            with open(FAILED_DM_LOG, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(log_entry)

        with open(FAILED_DM_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        logger.error(f"[DM_REMINDER_LOG_FAILED] Could not log DM failure: {e}")


def cleanup_dm_scheduled_tracker(max_age_days=2):
    """Remove stale events and empty user buckets from the scheduled tracker."""
    now = utcnow()
    removed_events = 0
    try:
        for event_id in list(dm_scheduled_tracker.keys()):
            stale_event = False
            try:
                timestamp_str = event_id.split(":", 1)[-1]
                event_time = datetime.fromisoformat(timestamp_str)
                if now - event_time > timedelta(days=max_age_days):
                    stale_event = True
            except Exception as e:
                logger.warning(f"[DM_SCHEDULE_TRACKER] Failed timestamp parse for {event_id}: {e}")
                stale_event = True

            if stale_event:
                dm_scheduled_tracker.pop(event_id, None)
                removed_events += 1
                continue

            # prune empty users
            per_user = dm_scheduled_tracker.get(event_id, {})
            for uid in [u for u, s in per_user.items() if not s]:
                per_user.pop(uid, None)
            if not per_user:
                dm_scheduled_tracker.pop(event_id, None)
                removed_events += 1

        if removed_events > 0:
            save_dm_scheduled_tracker()
            logger.info(
                f"[DM_SCHEDULED_TRACKER] Removed {removed_events} stale/empty scheduled entries."
            )
    except Exception as e:
        logger.error(f"[DM_SCHEDULED_TRACKER] Cleanup failed: {e}")


def cleanup_dm_sent_tracker(max_age_days=2):
    """Remove stale events and empty user buckets from dm_sent_tracker."""
    now = utcnow()
    removed_events = 0
    try:
        for event_id in list(dm_sent_tracker.keys()):
            stale_event = False
            try:
                timestamp_str = event_id.split(":", 1)[-1]
                event_time = datetime.fromisoformat(timestamp_str)
                if now - event_time > timedelta(days=max_age_days):
                    stale_event = True
            except Exception as e:
                logger.warning(f"[DM_TRACKER_FAILED] TS parse failed for {event_id}: {e}")
                stale_event = True

            if stale_event:
                dm_sent_tracker.pop(event_id, None)
                removed_events += 1
                continue

            # prune empty users
            per_user = dm_sent_tracker.get(event_id, {})
            for uid in [u for u, lst in per_user.items() if not lst]:
                per_user.pop(uid, None)
            if not per_user:
                dm_sent_tracker.pop(event_id, None)
                removed_events += 1

        if removed_events > 0:
            save_dm_sent_tracker()
            logger.info(
                f"[DM_TRACKER] Removed {removed_events} stale/empty entries from dm_sent_tracker."
            )
    except Exception as e:
        logger.error(f"[DM_TRACKER_FAILED] Failed to clean dm_sent_tracker: {e}")


def get_embed_color(delta):
    total_seconds = delta.total_seconds()
    if total_seconds >= 12 * 3600:
        return 0x3498DB  # Blue
    elif total_seconds >= 4 * 3600:
        return 0x2ECC71  # Green
    elif total_seconds >= 1 * 3600:
        return 0xE67E22  # Orange
    else:
        return 0xE74C3C  # Red


def make_event_id(event):
    return f"{event['type']}:{event['start_time'].isoformat()}"


def save_active_reminders():
    try:
        dirpath = os.path.dirname(REMINDER_TRACKING_FILE) or "."
        os.makedirs(dirpath, exist_ok=True)
        to_save = {}

        for eid, msg in active_reminders.items():
            base = {"channel_id": msg.channel.id, "message_id": msg.id}

            event = next((e for e in get_all_upcoming_events() if make_event_id(e) == eid), None)

            if event:
                base["event"] = {
                    k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in event.items()
                }
            else:
                logger.warning(
                    f"[REMINDER_CACHE] No event found for {eid} — saving basic info only."
                )

            to_save[eid] = base

        with open(REMINDER_TRACKING_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2, sort_keys=True)

        logger.debug("[REMINDER_CACHE] Saved active reminders to disk.")

    except Exception as e:
        logger.warning(f"[REMINDER_CACHE] Failed to save: {e}")


async def safe_delete_reminder(event_id: str):
    msg = active_reminders.get(event_id)
    if not msg:
        return

    try:
        await msg.delete()
        logger.debug(f"[REMINDER_CACHE] Deleted reminder for {event_id}")
    except discord.NotFound:
        logger.warning(f"[REMINDER_CACHE] Reminder already deleted for {event_id}")
    except Exception as e:
        logger.warning(f"[REMINDER_CACHE] Error deleting reminder for {event_id}: {e}")
    finally:
        active_reminders.pop(event_id, None)
        save_active_reminders()


async def load_active_reminders(bot):
    raw_ids = set()

    try:
        if not os.path.exists(REMINDER_TRACKING_FILE):
            return set()

        with open(REMINDER_TRACKING_FILE, encoding="utf-8") as f:
            raw = json.load(f)

        required_keys = {"channel_id", "message_id"}

        for eid, data in raw.items():
            raw_ids.add(eid)  # Track even if broken

            if not isinstance(data, dict):
                logger.warning(f"[REMINDER_CACHE] Invalid data type for {eid}: {data}")
                continue

            if not required_keys.issubset(data):
                logger.warning(f"[REMINDER_CACHE] Incomplete data for {eid}: {data}")
                continue

            try:
                channel = await bot.fetch_channel(data["channel_id"])
                msg = await channel.fetch_message(data["message_id"])

                # Try to match from live event cache
                matched_event = next(
                    (e for e in get_all_upcoming_events() if make_event_id(e) == eid), None
                )

                # Fallback to stored event metadata
                if not matched_event and "event" in data:
                    try:
                        event_data = data["event"]
                        event_data["start_time"] = datetime.fromisoformat(event_data["start_time"])
                        event_data["end_time"] = datetime.fromisoformat(event_data["end_time"])
                        matched_event = event_data
                        logger.debug(f"[REMINDER_CACHE] Used stored event data for {eid}")
                    except Exception as parse_error:
                        logger.warning(
                            f"[REMINDER_CACHE] Failed to parse stored event for {eid}: {parse_error}"
                        )

                if not matched_event:
                    logger.warning(
                        f"[REMINDER_CACHE] Could not find matching event for {eid} — skipping view reattachment."
                    )
                    continue

                raw_type = matched_event.get("type", "unknown").replace(" ", "_")
                prefix = f"reminder_{raw_type}"

                try:
                    view = LocalTimeToggleView(events=[matched_event], prefix=prefix)
                    await msg.edit(view=view)
                    logger.info(
                        f"[REMINDER_CACHE_REHYDRATE] Re-attached reminder view for {eid} with prefix {prefix}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[REMINDER_CACHE_REHYDRATE] Failed to reattach view for {eid}: {e}"
                    )

                active_reminders[eid] = msg
                logger.debug(f"[REMINDER_CACHE] Restored message {data['message_id']} for {eid}")

            except discord.NotFound:
                logger.warning(f"[REMINDER_CACHE] Message not found for {eid}")
            except Exception as e:
                logger.warning(f"[REMINDER_CACHE] Failed to restore {eid}: {e}")

        logger.info(f"[REMINDER_CACHE] Loaded {len(active_reminders)} active reminders.")
        return raw_ids

    except Exception as e:
        logger.warning(f"[REMINDER_CACHE] Failed to load reminders from disk: {e}")
        return set()


async def cleanup_orphaned_reminders(loaded_ids: set):
    upcoming_events = get_all_upcoming_events()

    if not upcoming_events:
        logger.warning(
            "[REMINDER_CACHE] Skipping orphan cleanup — event cache is empty or not ready."
        )
        return

    valid_ids = {make_event_id(e) for e in upcoming_events}
    orphaned = [eid for eid in loaded_ids if eid not in valid_ids]

    for eid in orphaned:
        await safe_delete_reminder(eid)

    if orphaned:
        save_active_reminders()


async def send_reminder_at(bot, channel_id, event, delta):
    seconds_until = (event["start_time"] - delta - utcnow()).total_seconds()
    if seconds_until > 0:
        await asyncio.sleep(seconds_until)

    event_id = make_event_id(event)
    logger.debug(f"[REMINDER_CACHE] Triggered send_reminder_at for {event_id} at T-{delta}")

    try:
        now = utcnow()
        time_remaining = event["start_time"] - now
        is_now = abs(time_remaining.total_seconds()) < 60
        embed_color = get_embed_color(time_remaining)

        # 🚫 Skip false T-0s
        if delta == timedelta(0) and not is_now:
            logger.warning(
                f"[REMINDER_CACHE] Event {event_id} triggered at T-0 but it's not now: {time_remaining}"
            )
            return

        description = (
            "**Starts NOW**"
            if delta == timedelta(0) and is_now
            else f"**Starts <t:{int(event['start_time'].timestamp())}:R>**"
        )

        # Add a non-personalized hype quote at T-1h and T-0
        add_public_quote = delta in (timedelta(hours=1), timedelta(seconds=0))
        if add_public_quote:
            etype = (event.get("type") or "").lower().strip()
            pub_candidates = PUBLIC_QUOTES.get(etype) or PUBLIC_QUOTES["_default"]
            pub_quote = random.choice(pub_candidates)
            description = f"{description}\n\n💬 *{pub_quote}*"

        embed = discord.Embed(
            title=f"\U0001f4e3 {event['name']}", description=description, color=embed_color
        )
        embed.set_footer(
            text=f"Event starts: {event['start_time'].strftime('%A, %d %B %Y at %H:%M UTC')}"
        )

        mention = "@everyone" if delta in [timedelta(hours=1), timedelta(minutes=0)] else None

        # Delete previous reminder for this event
        prev_msg = active_reminders.get(event_id)
        if prev_msg:
            try:
                await prev_msg.delete()
                logger.debug(f"[REMINDER_CACHE] Deleted previous reminder for {event_id}")
            except Exception as e:
                logger.warning(
                    f"[REMINDER_CACHE] Failed to delete previous reminder for {event_id}: {e}"
                )

        channel = bot.get_channel(channel_id)
        if not channel:
            logger.warning(f"[REMINDER_CACHE_WARNING] Channel {channel_id} not found.")
            return

        prefix = f"reminder_{event['type'].replace(' ', '_')}"
        view = LocalTimeToggleView(events=[event], prefix=prefix)
        msg = await channel.send(content=mention, embed=embed, view=view)
        active_reminders[event_id] = msg
        save_active_reminders()
        logger.debug(f"[REMINDER_CACHE] Sent new reminder for {event_id} at T-{delta}")

        if delta == timedelta(0) and event.get("end_time"):
            expiry_seconds = (event["end_time"] - utcnow()).total_seconds() + EXPIRY_DELAY
            asyncio.create_task(expire_single_reminder(event_id, expiry_seconds))

    except Exception as e:
        logger.error(
            f"[REMINDER_CACHE_CRITICAL] Failed to send reminder for {event_id} at T-{delta}: {e}"
        )


async def expire_single_reminder(event_id, delay_seconds):
    await asyncio.sleep(delay_seconds)
    await safe_delete_reminder(event_id)


async def delayed_user_dm(bot, user, event, delta, seconds_until):
    event_id = make_event_id(event)
    uid = str(user.id)
    delta_seconds = int(delta.total_seconds())

    # Skip if already sent to this user
    if delta_seconds in dm_sent_tracker.get(event_id, {}).get(uid, []):
        logger.info(
            "[DM_REMINDER_SKIP_DELAYED] Skipping delayed task for %s %s at T-%s",
            user.id,
            event_id,
            delta,
        )
        return

    try:
        await asyncio.sleep(seconds_until)
        await send_user_reminder(user, event, delta)
    except Exception as e:
        logger.error(
            "[DM_REMINDER_DELAYED_FAILED] Error while waiting/sending DM to %s for %s at T-%s: %s",
            user.id,
            event_id,
            delta,
            e,
        )
    finally:
        # Remove from this user's scheduled bucket
        try:
            dm_scheduled_tracker.get(event_id, {}).get(uid, set()).discard(delta_seconds)
        finally:
            save_dm_scheduled_tracker()


async def send_user_reminder(user, event, delta):
    event_id = make_event_id(event)
    uid = str(user.id)
    delta_seconds = int(delta.total_seconds())

    try:
        # 🚫 SKIP IF ALREADY SENT (per-user)
        if delta_seconds in dm_sent_tracker.get(event_id, {}).get(uid, []):
            logger.info(
                "[DM_REMINDER] ⚠️ Skipping duplicate DM to %s for %s at T-%s", user, event_id, delta
            )
            return

        # Names for personalization
        discord_name = getattr(user, "display_name", None) or str(user)
        main_gov = _get_main_governor_name_for_user(user.id) or discord_name

        # Select a quote by event type
        etype = (event.get("type") or "").lower().strip()
        candidates = DM_QUOTES.get(etype) or DM_QUOTES["_default"]
        quote_tpl = random.choice(candidates)
        quote = quote_tpl.format(name=discord_name, gov=main_gov)

        starts_at = int(event["start_time"].timestamp())
        t0 = timedelta(0)
        is_now = delta == t0

        # Build DM embed
        _title_suffix = (
            "NOW"
            if is_now
            else f"in {((event['start_time'] - utcnow()).total_seconds() // 60):.0f} min"
        )
        title = f"📬 {event['name']} – Reminder"

        # Friendly line at top + quote below
        greeting = f"Hey **{discord_name}** ({main_gov})!"
        description = f"{greeting}\n" f"⏰ Starts <t:{starts_at}:R>\n\n" f"💬 *{quote}*"

        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        embed.set_footer(text="Manage with /modify_subscription or /unsubscribe")

        await user.send(embed=embed)

        # ✅ Record successful send (per-user)
        dm_sent_tracker.setdefault(event_id, {}).setdefault(uid, [])
        if delta_seconds not in dm_sent_tracker[event_id][uid]:
            dm_sent_tracker[event_id][uid].append(delta_seconds)
            save_dm_sent_tracker()

        reminder_stats["dm_success"] += 1
        logger.info("[DM_REMINDER] ✅ Sent DM to %s for %s at T-%s", user, event_id, delta)

        if reminder_stats["dm_success"] % 10 == 0:
            logger.info(
                f"[DM_REMINDER_SUMMARY] Running total — Sent: {reminder_stats['dm_success']}, "
                f"Blocked: {reminder_stats['dm_dm_disabled']}, Failed: {reminder_stats['dm_failed']}"
            )

    except discord.Forbidden:
        logger.warning("[DM_REMINDER] Cannot DM user %s — DMs disabled.", user)
        reminder_stats["dm_dm_disabled"] += 1
        log_failed_dm(user.id, event, delta, "DMs disabled")
    except Exception as e:
        logger.exception("[DM_REMINDER] Failed to DM user %s for %s: %s", user, event_id, e)
        reminder_stats["dm_failed"] += 1
        log_failed_dm(user.id, event, delta, str(e))
    finally:
        dm_scheduled_tracker.get(event_id, {}).get(uid, set()).discard(delta_seconds)
        save_dm_scheduled_tracker()


async def schedule_event_reminders(bot, notify_channel_id, test_mode=False, test_user_id=None):
    load_dm_sent_tracker()
    load_dm_scheduled_tracker()

    if test_mode:
        now = utcnow()
        test_event = {
            "name": "Test Ruins",
            "type": "ruins",
            "start_time": now + timedelta(minutes=2),
            "end_time": now + timedelta(minutes=2, seconds=30),
            "zone": "Test Zone",
        }
        for delta in TEST_REMINDER_WINDOWS:
            asyncio.create_task(send_reminder_at(bot, notify_channel_id, test_event, delta))
        return

    while True:
        all_events = get_all_upcoming_events()
        now = utcnow()
        subscribers = get_all_subscribers()
        logger.debug("[DM_REMINDER_SCHEDULER] Loaded %d subscribers", len(subscribers))

        for event in all_events:
            raw_type = (event["type"] or "").lower().strip()
            if raw_type not in {"ruins", "altars", "major", "chronicle"}:
                continue
            event_type = raw_type  # already normalized by the loader

            event_id = make_event_id(event)
            start_time = event["start_time"]

            if start_time - now > timedelta(hours=48):
                continue

            if event_id not in sent_reminders:
                sent_reminders[event_id] = set()

            for delta in REMINDER_WINDOWS:
                reminder_time = start_time - delta

                if not (now <= reminder_time <= now + timedelta(minutes=5)):
                    continue

                if delta in sent_reminders[event_id]:
                    continue

                asyncio.create_task(send_reminder_at(bot, notify_channel_id, event, delta))
                sent_reminders[event_id].add(delta)
                logger.debug("[SCHEDULE_CACHE] Reminder for %s scheduled at T-%s", event_id, delta)

            # yield a tick between events to keep the loop responsive
            await asyncio.sleep(0)

            for user_id, config in subscribers.items():
                try:
                    user = await bot.fetch_user(int(user_id))
                    logger.debug("[DM_REMINDER_USER] USER ID found %s", user_id)
                except Exception as e:
                    logger.error("[DM_REMINDER] Failed to fetch user %s: %s", user_id, e)
                    continue

                if not user:
                    logger.error("[DM_REMINDER] Could not fetch user object for ID %s", user_id)
                    continue

                subscribed_types = config.get("subscriptions", [])
                reminder_times = config.get("reminder_times", DEFAULT_REMINDER_TIMES)

                expanded_types = set(subscribed_types)
                if "fights" in expanded_types:
                    expanded_types.update(["altars", "major"])
                if "all" in expanded_types:
                    expanded_types.update(
                        ["ruins", "altars", "major"]
                    )  # (add "chronicle" if you want)

                if event_type not in expanded_types:
                    continue

                for rt in reminder_times:
                    delta = {
                        "24h": timedelta(hours=24),
                        "12h": timedelta(hours=12),
                        "4h": timedelta(hours=4),
                        "1h": timedelta(hours=1),
                        "now": timedelta(seconds=0),
                    }.get(rt)

                    if not delta:
                        continue

                    # Ensure per-user buckets exist
                    dm_sent_tracker.setdefault(event_id, {}).setdefault(str(user.id), [])
                    dm_scheduled_tracker.setdefault(event_id, {}).setdefault(str(user.id), set())

                    delta_seconds = int(delta.total_seconds())
                    user_sent = dm_sent_tracker[event_id][str(user.id)]
                    user_sched = dm_scheduled_tracker[event_id][str(user.id)]

                    if delta_seconds in user_sent:
                        logger.debug(
                            "[DM_REMINDER_DUPLICATE] Skipping %s for %s at T-%s — already sent.",
                            user_id,
                            event_id,
                            delta,
                        )
                        continue

                    if delta_seconds in user_sched:
                        logger.debug(
                            "[DM_REMINDER_DUPLICATE_TASK] Already scheduled for %s at %s T-%s",
                            user_id,
                            event_id,
                            delta,
                        )
                        continue

                    seconds_until = (start_time - delta - now).total_seconds()
                    logger.debug(
                        "[DM_REMINDER_DEBUG] User %s | Event: %s | Delta: %s | Seconds until: %d",
                        user_id,
                        event_id,
                        delta,
                        int(seconds_until),
                    )

                    user_sched.add(delta_seconds)
                    save_dm_scheduled_tracker()

                    if seconds_until <= 0:
                        logger.info(
                            "[DM_REMINDER_LATE] Sending immediate DM to %s for %s at T-%s",
                            user_id,
                            event_id,
                            delta,
                        )
                        register_user_task(
                            user.id,
                            asyncio.create_task(send_user_reminder(user, event, delta)),
                            meta={
                                "event_id": event_id,
                                "delta_seconds": int(delta.total_seconds()),
                            },
                        )
                    else:
                        logger.debug(
                            "[DM_REMINDER_SCHEDULED] Scheduling DM to %s for %s at T-%s in %ds",
                            user_id,
                            event_id,
                            delta,
                            int(seconds_until),
                        )
                        register_user_task(
                            user.id,
                            asyncio.create_task(
                                delayed_user_dm(bot, user, event, delta, seconds_until)
                            ),
                            meta={
                                "event_id": event_id,
                                "delta_seconds": int(delta.total_seconds()),
                            },
                        )

                # small yield within the per-user loop to avoid long bursts
                await asyncio.sleep(0)

        reminder_stats["dm_success"] = 0
        reminder_stats["dm_dm_disabled"] = 0
        reminder_stats["dm_failed"] = 0

        cleanup_dm_scheduled_tracker()
        cleanup_dm_sent_tracker()
        _log_tracker_stats_if_due()
        # yield once after logging, then sleep normally
        await asyncio.sleep(0)
        await asyncio.sleep(300)


async def reminder_cleanup_loop():
    while True:
        now = utcnow()
        expired = []

        for eid in list(active_reminders):
            try:
                event_time = datetime.fromisoformat(eid.split(":", 1)[1])
                if now > event_time + timedelta(minutes=15):
                    await safe_delete_reminder(eid)
                    expired.append(eid)
            except Exception as e:
                logger.error(
                    f"[SCHEDULE_CACHE_CLEANUP] Failed to parse or clean reminder {eid}: {e}"
                )

        if expired:
            logger.info(
                f"[SCHEDULE_CACHE_CLEANUP] Cleanup loop removed {len(expired)} expired reminders."
            )
        await asyncio.sleep(600)


async def refresh_reminder_format(bot, notify_channel_id):
    try:
        updated = 0
        # Build a quick lookup of upcoming events by event_id
        events = {make_event_id(e): e for e in get_all_upcoming_events()}

        for event_id, msg in list(active_reminders.items()):
            # Find event (prefer live cache, else skip)
            event = events.get(event_id)
            if not event:
                logger.debug(f"[SCHEDULE_CACHE_REFRESH] No live event for {event_id}; skipping.")
                continue

            # Only refresh the kinds we show
            etype = (event.get("type") or "").lower().strip()
            if etype not in {"ruins", "altars", "major", "chronicle"}:
                continue

            now = utcnow()
            time_remaining = event["start_time"] - now
            is_now = abs(time_remaining.total_seconds()) < 60

            # Build description same as send_reminder_at
            description = (
                "**Starts NOW**"
                if is_now
                else f"**Starts <t:{int(event['start_time'].timestamp())}:R>**"
            )

            # Add non-personalized quote at T-1h or NOW
            if time_remaining <= timedelta(hours=1):
                pub_candidates = PUBLIC_QUOTES.get(etype) or PUBLIC_QUOTES["_default"]
                pub_quote = random.choice(pub_candidates)
                description = f"{description}\n\n💬 *{pub_quote}*"

            embed_color = get_embed_color(time_remaining)
            embed = discord.Embed(
                title=f"\U0001f4e3 {event['name']}", description=description, color=embed_color
            )
            embed.set_footer(
                text=f"Event starts: {event['start_time'].strftime('%A, %d %B %Y at %H:%M UTC')}"
            )

            try:
                await msg.edit(embed=embed)  # keep existing view
                updated += 1
            except Exception as e:
                logger.error(f"[SCHEDULE_CACHE_REFRESH] Failed to edit message for {event_id}: {e}")

        logger.info(
            f"[SCHEDULE_CACHE_REFRESH] Reminder update complete. Edited {updated} messages."
        )
    except Exception as e:
        logger.error(f"[SCHEDULE_CACHE_REFRESH] Entire function failed: {e}")
