# event_scheduler.py
import asyncio
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

import os
import random
import re
import time

import discord

from constants import (
    DM_SCHEDULED_TRACKER_FILE,
    DM_SENT_TRACKER_FILE,
    FAILED_DM_LOG,
    REMINDER_MAP,
    REMINDER_TRACKING_FILE,
    REMINDER_WINDOWS,
    TEST_REMINDER_WINDOWS,
)
from core.discord_embed_limits import (
    MAX_DESCRIPTION_CHARACTERS,
    MAX_TITLE_CHARACTERS,
    require_valid_embed_payload,
    truncate_text,
)
from embed_utils import LocalTimeToggleView, fmt_short
from event_cache import get_all_upcoming_events
from file_utils import atomic_json_write, atomic_write_json
from registry.governor_registry import load_registry
from reminder_domain.kvk_candidates import (
    build_kvk_alert_projection,
    is_fight_event as _is_fight_event,
    make_event_id,
    normalized_event_type as _normalized_event_type,
    subscription_matches_event as _subscription_matches_event,
)
from reminder_task_registry import register_user_task
from services import event_delivery_service as delivery
from services.event_delivery_store import delivery_key
from services.legacy_export_snapshot_service import drain_thread
from subscription_tracker import get_all_subscribers, get_user_config
from utils import ensure_aware_utc, parse_isoformat_utc, utcnow


def is_fight_event(event: dict) -> bool:
    """Compatibility export backed by the shared pure KVK domain helper."""

    return _is_fight_event(event)


def subscription_matches_event(subscribed_types: list[str], event: dict) -> bool:
    """Compatibility export backed by the shared pure KVK domain helper."""

    return _subscription_matches_event(subscribed_types, event)


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


# Robust ISO-timestamp extraction helper
_ISO_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})")


def _extract_event_ts(event_id: str) -> str | None:
    """
    Extract the ISO timestamp substring from event_id robustly.
    Returns the ISO string (unchanged) or None if not found/valid.

    Supports forms:
      - "major:2025-11-20T00:00:00+00:00"
      - "major:slug_name:2025-11-20T00:00:00+00:00"
    """
    if not isinstance(event_id, str):
        return None
    # Fast path: right-split on colon to get last token
    try:
        maybe_ts = event_id.rsplit(":", 1)[-1]
        # Normalize 'Z' to "+00:00" for fromisoformat validation
        _ = datetime.fromisoformat(maybe_ts.replace("Z", "+00:00"))
        return maybe_ts
    except Exception:
        pass

    # Fallback: regex search for ISO-like timestamp and validate
    m = _ISO_TS_RE.search(event_id)
    if not m:
        return None
    ts = m.group(0)
    try:
        _ = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return ts
    except Exception:
        return None


sent_reminders = {}  # {event_id: set[timedelta]}
active_reminders = {}  # {event_id: discord.Message}
_unresolved_active = {}
_active_load_failed = False

EXPIRY_DELAY = 3600  # 1 hour in seconds

REHYDRATE_STALE_GRACE_SECONDS = (
    60  # grace window (seconds) for near-immediate sends when rehydrating
)

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

# Serialize tracker file writes to avoid concurrent os.replace collisions on Windows.
_DM_TRACKER_IO_LOCK = asyncio.Lock()


@dataclass(frozen=True, slots=True)
class KvkDmTrackerSnapshot:
    """One in-memory, read-only snapshot for player projection."""

    sent: dict
    scheduled: dict


def snapshot_dm_trackers() -> KvkDmTrackerSnapshot:
    """Copy both KVK tracker maps once without loading or writing persistence."""

    return KvkDmTrackerSnapshot(
        sent=copy.deepcopy(dm_sent_tracker),
        scheduled=copy.deepcopy(dm_scheduled_tracker),
    )


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


async def _save_trackers_coalesced_async(*, sent: bool = False, scheduled: bool = False):
    if not sent and not scheduled:
        return
    # because save_*_async already lock, this can just call sequentially
    if sent:
        await save_dm_sent_tracker_async()
    if scheduled:
        await save_dm_scheduled_tracker_async()


def _ensure_parent(path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


_dm_startup_state = "not_started"
_dm_startup_error = None
_dm_startup_lock = asyncio.Lock()


def dm_startup_report():
    return {"state": _dm_startup_state, "error": _dm_startup_error}


def _read_dm_snapshot(path):
    try:
        with open(path, encoding="utf-8") as stream:
            raw = json.load(stream)
    except FileNotFoundError:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("Invalid DM tracker envelope")
    for value in raw.values():
        if not isinstance(value, (dict, list)):
            raise ValueError("Invalid DM tracker entry")
        if isinstance(value, dict) and any(not isinstance(items, list) for items in value.values()):
            raise ValueError("Invalid DM tracker markers")
    return raw


async def _ensure_dm_startup(bot):
    global _dm_startup_state, _dm_startup_error
    from event_cache import get_upcoming_event_cache_snapshot

    async with _dm_startup_lock:
        if _dm_startup_state == "complete":
            return True
        if _dm_startup_state in {"unconfirmed", "failed"}:
            return False
        try:
            if _dm_startup_state == "not_started":
                _dm_startup_state = "loading"
                await load_dm_sent_tracker_async()
                await load_dm_scheduled_tracker_async()
                _dm_startup_state = "waiting_for_events"
            while True:
                snapshot = get_upcoming_event_cache_snapshot()
                if snapshot.ok and snapshot.events:
                    break
                # No refresh, tracker pruning, or new scheduler while waiting.
                await asyncio.sleep(1)
            _dm_startup_state = "restoring"
            outcome = await rehydrate_dm_scheduled_tasks(bot)
            if not isinstance(outcome, dict) or outcome.get("status") != "complete":
                _dm_startup_state = "unconfirmed"
                return False
            _dm_startup_state = "complete"
            return True
        except asyncio.CancelledError:
            if _dm_startup_state != "waiting_for_events":
                _dm_startup_state = "unconfirmed"
            raise
        except Exception as exc:
            _dm_startup_error = type(exc).__name__
            _dm_startup_state = "unconfirmed"
            logger.warning("[DM_REHYDRATE] Startup unresolved error_type=%s", _dm_startup_error)
            return False


def _normalize_dm_snapshot(raw, *, scheduled=False):
    migrated = {}
    for event_id, value in (raw.items() if isinstance(raw, dict) else []):
        if isinstance(value, list):
            migrated[event_id] = {}
        elif isinstance(value, dict):
            per_user = {}
            for uid, lst in value.items():
                values = lst if isinstance(lst, list) else []
                per_user[str(uid)] = set(values) if scheduled else list(values)
            migrated[event_id] = per_user
        else:
            migrated[event_id] = {}
    return migrated


def load_dm_sent_tracker():
    """Synchronous compatibility entry; async startup publishes on the bot loop."""
    migrated = _normalize_dm_snapshot(_read_dm_snapshot(DM_SENT_TRACKER_FILE))
    dm_sent_tracker.clear()
    dm_sent_tracker.update(migrated)
    logger.info("[DM_TRACKER] Loaded dm_sent_tracker with migration.")


def save_dm_sent_tracker(snapshot=None):
    """Persist dm_sent_tracker ensuring inner values are lists."""
    serializable = {}
    for event_id, per_user in (dm_sent_tracker if snapshot is None else snapshot).items():
        serializable[event_id] = {}
        for uid, lst in (per_user.items() if isinstance(per_user, dict) else []):
            serializable[event_id][str(uid)] = list(lst or [])
    atomic_write_json(DM_SENT_TRACKER_FILE, serializable, ensure_parent_dir=True)
    logger.info("[DM_TRACKER] Saved dm_sent_tracker to disk.")


def save_dm_scheduled_tracker(snapshot=None):
    """Persist dm_scheduled_tracker ensuring inner sets are serialized to lists."""
    serializable = {}
    for event_id, per_user in (dm_scheduled_tracker if snapshot is None else snapshot).items():
        serializable[event_id] = {}
        for uid, s in (per_user.items() if isinstance(per_user, dict) else []):
            serializable[event_id][str(uid)] = list(s or set())
    atomic_write_json(DM_SCHEDULED_TRACKER_FILE, serializable, ensure_parent_dir=True)
    logger.info("[DM_TRACKER] Saved dm_scheduled_tracker to disk.")


def load_dm_scheduled_tracker():
    """Load and migrate dm_scheduled_tracker to per-user nested dict with sets."""
    migrated = _normalize_dm_snapshot(_read_dm_snapshot(DM_SCHEDULED_TRACKER_FILE), scheduled=True)
    dm_scheduled_tracker.clear()
    dm_scheduled_tracker.update(migrated)
    logger.info("[DM_TRACKER] Loaded dm_scheduled_tracker with migration.")


async def load_dm_sent_tracker_async():
    raw = await drain_thread(_read_dm_snapshot, DM_SENT_TRACKER_FILE)
    dm_sent_tracker.clear()
    dm_sent_tracker.update(_normalize_dm_snapshot(raw))


async def save_dm_sent_tracker_async():
    # lock is centralized here so ALL callsites are protected
    async with _DM_TRACKER_IO_LOCK:
        snapshot = copy.deepcopy(dm_sent_tracker)
        await drain_thread(save_dm_sent_tracker, snapshot)


async def load_dm_scheduled_tracker_async():
    raw = await drain_thread(_read_dm_snapshot, DM_SCHEDULED_TRACKER_FILE)
    dm_scheduled_tracker.clear()
    dm_scheduled_tracker.update(_normalize_dm_snapshot(raw, scheduled=True))


async def save_dm_scheduled_tracker_async():
    # lock is centralized here so ALL callsites are protected
    async with _DM_TRACKER_IO_LOCK:
        snapshot = copy.deepcopy(dm_scheduled_tracker)
        await drain_thread(save_dm_scheduled_tracker, snapshot)


async def release_cancelled_dm_schedules(user_id):
    """Release only undispatched, unowned windows after subscription removal."""
    from reminder_task_registry import user_task_snapshot

    uid = str(user_id)
    async with _DM_TRACKER_IO_LOCK:
        rows = await delivery.receipt_rows()
        retained = {
            (row.get("event"), row.get("window"))
            for row in rows
            if row["kind"] == "dm-send" and row["target"] == uid
        }
        owners = user_task_snapshot(uid).get(uid, [])
        # Unknown owner metadata cannot establish that any window is unowned.
        if any("event_id" not in meta or "delta_seconds" not in meta for meta in owners):
            return
        retained.update((meta["event_id"], meta["delta_seconds"]) for meta in owners)
        for eid, per_user in dm_scheduled_tracker.items():
            if uid in per_user:
                per_user[uid] = {
                    window
                    for window in per_user[uid]
                    if (eid, window) in retained
                    or window in dm_sent_tracker.get(eid, {}).get(uid, [])
                }
        await drain_thread(save_dm_scheduled_tracker, copy.deepcopy(dm_scheduled_tracker))


def log_failed_dm(user_id, event, delta, reason):
    log_entry = {
        "user_id": str(user_id),
        "event_name": event["name"],
        "event_time": (
            ensure_aware_utc(event["start_time"]).isoformat()
            if isinstance(event.get("start_time"), datetime)
            else str(event.get("start_time"))
        ),
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


async def cleanup_dm_scheduled_tracker_async(max_age_days=2):
    """Remove stale events and empty user buckets from the scheduled tracker."""
    now = utcnow()
    removed_events = 0
    try:
        for event_id in list(dm_scheduled_tracker.keys()):
            stale_event = False
            timestamp_str = _extract_event_ts(event_id)
            if not timestamp_str:
                logger.warning(f"[DM_SCHEDULE_TRACKER] Failed timestamp extract for {event_id}")
                stale_event = True
            else:
                try:
                    event_time = ensure_aware_utc(parse_isoformat_utc(timestamp_str))
                    if now - event_time > timedelta(days=max_age_days):
                        stale_event = True
                except Exception as e:
                    logger.warning(
                        f"[DM_SCHEDULE_TRACKER] Failed timestamp parse for {event_id}: {e}"
                    )
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
            await save_dm_scheduled_tracker_async()
            logger.info(
                "[DM_SCHEDULED_TRACKER] Removed %d stale/empty scheduled entries.", removed_events
            )
    except Exception as e:
        logger.error(f"[DM_SCHEDULED_TRACKER] Cleanup failed: {e}")


async def cleanup_dm_sent_tracker_async(max_age_days=2):
    """Remove stale events and empty user buckets from dm_sent_tracker."""
    now = utcnow()
    removed_events = 0
    try:
        for event_id in list(dm_sent_tracker.keys()):
            stale_event = False
            timestamp_str = _extract_event_ts(event_id)
            if not timestamp_str:
                logger.warning(f"[DM_TRACKER_FAILED] TS extract failed for {event_id}")
                stale_event = True
            else:
                try:
                    event_time = ensure_aware_utc(parse_isoformat_utc(timestamp_str))
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
            await save_dm_sent_tracker_async()
            logger.info(
                "[DM_TRACKER] Removed %d stale/empty entries from dm_sent_tracker.", removed_events
            )
    except Exception as e:
        logger.error(f"[DM_TRACKER_FAILED] Failed to clean dm_sent_tracker: {e}")


def get_event_thumbnail(event_type: str) -> str:
    raw = (event_type or "").lower()
    typ = {
        "next ruins": "ruins",
        "ruins": "ruins",
        "next altar fight": "altars",
        "altar": "altars",
        "altars": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }.get(raw, raw)
    thumbs = {
        "ruins": "https://i.ibb.co/CsK1GNVv/Ruins.jpg",
        "altars": "https://i.ibb.co/cKxCkTpW/altar.jpg",
        "major": "https://i.ibb.co/ksjMLzPN/rise-of-kingdoms-best-leonidas-builds.jpg",
        "chronicle": "https://i.ibb.co/CK0Lr5vL/chronicle-event.png",
    }
    return thumbs.get(typ, "https://i.ibb.co/0jM8R7GW/kvk-mistakes.jpg")


def save_active_reminders():
    try:
        if _active_load_failed:
            raise RuntimeError("Active reminder load unresolved; preserve original file")
        dirpath = os.path.dirname(REMINDER_TRACKING_FILE) or "."
        os.makedirs(dirpath, exist_ok=True)
        to_save = copy.deepcopy(_unresolved_active)

        for eid, msg in active_reminders.items():
            base = {"channel_id": msg.channel.id, "message_id": msg.id}

            event = next((e for e in get_all_upcoming_events() if make_event_id(e) == eid), None)

            if event:
                base["event"] = {
                    k: (ensure_aware_utc(v).isoformat() if isinstance(v, datetime) else v)
                    for k, v in event.items()
                }
            else:
                logger.warning(
                    f"[REMINDER_CACHE] No event found for {eid} — saving basic info only."
                )

            to_save[eid] = base

        # Keep the legacy JSON format and strict serialization failure behavior.
        atomic_json_write(
            REMINDER_TRACKING_FILE, to_save, ensure_ascii=True, sort_keys=True, default=None
        )

        logger.debug("[REMINDER_CACHE] Saved active reminders to disk.")

    except Exception as e:
        logger.warning(f"[REMINDER_CACHE] Failed to save: {e}")


async def safe_delete_reminder(event_id: str, expected_message_id=None):
    async with delivery.operation_lock(("public", event_id)):
        return await _delete_reminder(event_id, expected_message_id)


async def _delete_reminder(event_id, expected_message_id=None):
    msg = active_reminders.get(event_id)
    if event_id in _unresolved_active:
        return "unconfirmed"
    if not msg or (expected_message_id is not None and msg.id != expected_message_id):
        return "not_current"
    key = delivery_key("public-delete", msg.channel.id, msg.id)
    if not await delivery.begin(
        key, kind="public-delete", target=msg.channel.id, event=event_id, message_id=msg.id
    ):
        receipt = await delivery.read(key)
        if not receipt or receipt["state"] not in {"acknowledged", "not_found"}:
            return "unconfirmed"
    else:
        try:
            await msg.delete()
        except discord.NotFound as exc:
            if exc.code != 10008:
                return "unconfirmed"
            await delivery.finish(key, "not_found", message_id=msg.id, channel_id=msg.channel.id)
        except Exception as exc:
            logger.warning("[REMINDER_CACHE] delete_unconfirmed error_type=%s", type(exc).__name__)
            return "unconfirmed"
        else:
            await delivery.finish(key, "acknowledged", message_id=msg.id, channel_id=msg.channel.id)
    if active_reminders.get(event_id) is msg:
        active_reminders.pop(event_id, None)
        save_active_reminders()
    return "removed"


async def load_active_reminders(bot):
    global _unresolved_active, _active_load_failed
    raw_ids = set()

    try:
        raw = {}
        if os.path.exists(REMINDER_TRACKING_FILE):
            with open(REMINDER_TRACKING_FILE, encoding="utf-8") as f:
                raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("Invalid active reminder tracker")
        rows = await delivery.receipt_rows()
        indexed = {row["key"]: row for row in rows}
        live_ids = {}
        conflicts = set()
        for row in rows:
            if row["kind"] != "public-send" or row["state"] != "acknowledged":
                continue
            deleted = indexed.get(
                delivery_key("public-delete", row["channel_id"], row["message_id"])
            )
            if deleted and deleted["state"] in {"acknowledged", "not_found"}:
                old = raw.get(row["event"], {})
                if isinstance(old, dict) and old.get("message_id") == row["message_id"]:
                    raw.pop(row["event"], None)
                continue
            old = raw.get(row["event"], {})
            identity = (row["channel_id"], row["message_id"])
            if row["event"] in live_ids and live_ids[row["event"]] != identity:
                conflicts.add(row["event"])
            live_ids[row["event"]] = identity
            if isinstance(old, dict) and old.get("message_id") not in {None, row["message_id"]}:
                previous_delete = indexed.get(
                    delivery_key("public-delete", old.get("channel_id"), old["message_id"])
                )
                if not previous_delete or previous_delete["state"] not in {
                    "acknowledged",
                    "not_found",
                }:
                    conflicts.add(row["event"])
            if row["event"] in conflicts:
                # The journal already retains its competing identity. Preserve
                # the original projection across unrelated saves and restarts.
                continue
            raw[row["event"]] = {
                **(old if isinstance(old, dict) else {}),
                "channel_id": row["channel_id"],
                "message_id": row["message_id"],
            }
            if row.get("event_data"):
                raw[row["event"]]["event"] = row["event_data"]
        _unresolved_active = copy.deepcopy(raw)
        _active_load_failed = False

        required_keys = {"channel_id", "message_id"}

        for eid, data in raw.items():
            raw_ids.add(eid)  # Track even if broken
            if eid in conflicts:
                logger.warning("[REMINDER_CACHE] Conflicting receipt identities; restoration held")
                continue

            if not isinstance(data, dict):
                logger.warning(f"[REMINDER_CACHE] Invalid data type for {eid}: {data}")
                continue

            if not required_keys.issubset(data):
                logger.warning(f"[REMINDER_CACHE] Incomplete data for {eid}: {data}")
                continue

            try:
                channel = await bot.fetch_channel(data["channel_id"])
                try:
                    msg = await channel.fetch_message(data["message_id"])
                except discord.NotFound as exc:
                    if exc.code != 10008:
                        raise
                    # Only this exact message fetch proves absence. A channel
                    # failure or other 404 cannot release the retained identity.
                    key = delivery_key("public-delete", data["channel_id"], data["message_id"])
                    if await delivery.begin(
                        key,
                        kind="public-delete",
                        target=data["channel_id"],
                        event=eid,
                        message_id=data["message_id"],
                    ):
                        await delivery.finish(
                            key,
                            "not_found",
                            message_id=data["message_id"],
                            channel_id=data["channel_id"],
                        )
                    receipt = await delivery.read(key)
                    if receipt and receipt["state"] in {"acknowledged", "not_found"}:
                        current = active_reminders.get(eid)
                        if current is not None and (
                            current.id != data["message_id"]
                            or current.channel.id != data["channel_id"]
                        ):
                            continue
                        active_reminders.pop(eid, None)
                        _unresolved_active.pop(eid, None)
                        save_active_reminders()
                        logger.info("[REMINDER_CACHE] restoration disposition=confirmed_absent")
                    continue

                # Try to match from live event cache
                matched_event = next(
                    (e for e in get_all_upcoming_events() if make_event_id(e) == eid), None
                )

                # Fallback to stored event metadata
                if not matched_event and "event" in data:
                    try:
                        event_data = data["event"]
                        event_data["start_time"] = parse_isoformat_utc(event_data["start_time"])
                        if event_data.get("end_time"):
                            event_data["end_time"] = parse_isoformat_utc(event_data["end_time"])
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
                    view = LocalTimeToggleView(
                        events=[matched_event], prefix=prefix, complete_event_packing=True
                    )
                    restore_key = delivery_key("public-restore", msg.channel.id, msg.id, prefix)
                    if await delivery.begin(
                        restore_key,
                        kind="public-restore",
                        target=msg.channel.id,
                        event=eid,
                        message_id=msg.id,
                    ):
                        await msg.edit(view=view)
                        await delivery.finish(
                            restore_key,
                            "acknowledged",
                            message_id=msg.id,
                            channel_id=msg.channel.id,
                        )
                    else:
                        receipt = await delivery.read(restore_key)
                        if not receipt or receipt["state"] != "acknowledged":
                            raise RuntimeError("Previous restoration edit unconfirmed")
                    # Remote edit receipts survive restart; Python handlers do not.
                    bot.add_view(view, message_id=msg.id)
                    logger.info(
                        f"[REMINDER_CACHE_REHYDRATE] Re-attached reminder view for {eid} with prefix {prefix}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[REMINDER_CACHE_REHYDRATE] Failed to reattach view for {eid}: {e}"
                    )

                active_reminders[eid] = msg
                _unresolved_active.pop(eid, None)
                logger.debug(f"[REMINDER_CACHE] Restored message {data['message_id']} for {eid}")

            except discord.NotFound:
                logger.warning(f"[REMINDER_CACHE] Message not found for {eid}")
            except Exception as e:
                logger.warning(f"[REMINDER_CACHE] Failed to restore {eid}: {e}")

        logger.info(f"[REMINDER_CACHE] Loaded {len(active_reminders)} active reminders.")
        return raw_ids

    except Exception as e:
        _active_load_failed = True
        logger.warning(f"[REMINDER_CACHE] Failed to load reminders from disk: {e}")
        return set()


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


def build_public_reminder_embed(event, time_remaining, *, starts_now, add_public_quote):
    event_start = ensure_aware_utc(event["start_time"])
    description = (
        "**Starts NOW**" if starts_now else f"**Starts <t:{int(event_start.timestamp())}:R>**"
    )
    if add_public_quote:
        event_type = (event.get("type") or "").lower().strip()
        candidates = PUBLIC_QUOTES.get(event_type) or PUBLIC_QUOTES["_default"]
        description = f"{description}\n\n💬 *{random.choice(candidates)}*"

    raw_name = " ".join(str(event.get("name") or "Unnamed Event").split())
    name = truncate_text(raw_name, MAX_TITLE_CHARACTERS - len("📣 "))
    embed = discord.Embed(
        title=f"📣 {name}",
        description=truncate_text(description, MAX_DESCRIPTION_CHARACTERS),
        color=get_embed_color(time_remaining),
    )
    try:
        embed.set_footer(text=f"Event starts: {fmt_short(event_start)}")
    except Exception:
        embed.set_footer(text=f"Event starts: {event_start.strftime('%A, %d %B %Y at %H:%M UTC')}")
    usage = require_valid_embed_payload(embed)
    logger.info(
        "[EMBED_PAYLOAD] renderer=public_event_reminder fields=%d chars=%d max_field_value=0 compacted_events=%d omitted_events=0",
        usage.field_counts[0],
        usage.total_characters,
        int(name != raw_name),
    )
    return embed


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
    delay = (ensure_aware_utc(event["start_time"]) - delta - utcnow()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    async with delivery.operation_lock(("public", make_event_id(event))):
        if delivery.is_closed():
            return "closed"
        if _active_load_failed or make_event_id(event) in _unresolved_active:
            return "restoration_unconfirmed"
        return await _send_reminder_at(bot, channel_id, event, delta)


async def _send_reminder_at(bot, channel_id, event, delta):
    event_start = ensure_aware_utc(event["start_time"])
    seconds_until = (event_start - delta - utcnow()).total_seconds()
    if seconds_until > 0:
        await asyncio.sleep(seconds_until)

    event_id = make_event_id(event)
    logger.debug(f"[REMINDER_CACHE] Triggered send_reminder_at for {event_id} at T-{delta}")

    try:
        now = utcnow()
        time_remaining = ensure_aware_utc(event["start_time"]) - now
        is_now = abs(time_remaining.total_seconds()) < 60

        # 🚫 Skip false T-0s
        if delta == timedelta(0) and not is_now:
            logger.warning(
                f"[REMINDER_CACHE] Event {event_id} triggered at T-0 but it's not now: {time_remaining}"
            )
            return

        # Add a non-personalized hype quote at T-1h and T-0
        add_public_quote = delta in (timedelta(hours=1), timedelta(seconds=0))
        embed = build_public_reminder_embed(
            event,
            time_remaining,
            starts_now=delta == timedelta(0) and is_now,
            add_public_quote=add_public_quote,
        )

        mention = "@everyone" if delta in [timedelta(hours=1), timedelta(minutes=0)] else None

        key = delivery_key("public-send", channel_id, event_id, int(delta.total_seconds()))
        if await delivery.read(key):
            return "retained"
        rows = await drain_thread(delivery.store.rows)
        if any(
            r["kind"] == "public-send"
            and r["event"] == event_id
            and r["target"] == str(channel_id)
            and r["state"] == "entered"
            for r in rows
        ):
            return "unconfirmed"
        channel = bot.get_channel(channel_id)
        if not channel:
            logger.warning("[REMINDER_CACHE] channel_unavailable; no replacement attempted")
            return "channel_unavailable"
        # A settled send can outlive cancellation before the legacy projection
        # is saved. Recover that exact identity before considering replacement.
        live = []
        indexed = {row["key"]: row for row in rows}
        for row in rows:
            if (
                row["kind"] != "public-send"
                or row.get("event") != event_id
                or row["target"] != str(channel_id)
                or row["state"] != "acknowledged"
            ):
                continue
            deleted = indexed.get(delivery_key("public-delete", channel_id, row["message_id"]))
            if not deleted or deleted["state"] not in {"acknowledged", "not_found"}:
                live.append(row)
        if len(live) > 1:
            return "identity_conflict"
        if live:
            message_id = live[0]["message_id"]
            previous = active_reminders.get(event_id)
            if previous and previous.id != message_id:
                return "identity_conflict"
            if not previous:
                try:
                    active_reminders[event_id] = await channel.fetch_message(message_id)
                except discord.NotFound as exc:
                    if exc.code != 10008:
                        return "unconfirmed"
                    delete_key = delivery_key("public-delete", channel_id, message_id)
                    if not await delivery.begin(
                        delete_key,
                        kind="public-delete",
                        target=channel_id,
                        event=event_id,
                        message_id=message_id,
                    ):
                        return "unconfirmed"
                    await delivery.finish(
                        delete_key, "not_found", message_id=message_id, channel_id=channel_id
                    )
        # Delete previous reminder only after ruling out duplicate delivery.
        prev_msg = active_reminders.get(event_id)
        if prev_msg:
            if await _delete_reminder(event_id, prev_msg.id) != "removed":
                return "unconfirmed"

        prefix = f"reminder_{event['type'].replace(' ', '_')}"
        view = LocalTimeToggleView(events=[event], prefix=prefix, complete_event_packing=True)
        if not await delivery.begin(
            key,
            kind="public-send",
            target=channel_id,
            event=event_id,
            window=int(delta.total_seconds()),
            event_data={
                k: (ensure_aware_utc(v).isoformat() if isinstance(v, datetime) else v)
                for k, v in event.items()
                if k in {"name", "type", "start_time", "end_time"}
            },
        ):
            return "retained"
        if delivery.is_closed():
            return "closed"
        msg = await channel.send(content=mention, embed=embed, view=view)
        await delivery.finish(key, "acknowledged", message_id=msg.id, channel_id=msg.channel.id)
        active_reminders[event_id] = msg
        save_active_reminders()
        logger.debug(f"[REMINDER_CACHE] Sent new reminder for {event_id} at T-{delta}")

        if delta == timedelta(0) and event.get("end_time"):
            expiry_seconds = (
                ensure_aware_utc(event["end_time"]) - utcnow()
            ).total_seconds() + EXPIRY_DELAY
            delivery.own(
                expire_single_reminder(event_id, expiry_seconds, msg.id),
                name="public-reminder-expiry",
            )
        return "acknowledged"

    except Exception as e:
        logger.error(
            f"[REMINDER_CACHE_CRITICAL] Failed to send reminder for {event_id} at T-{delta}: {e}"
        )


async def expire_single_reminder(event_id, delay_seconds, expected_message_id=None):
    await asyncio.sleep(delay_seconds)
    await safe_delete_reminder(event_id, expected_message_id)


# Insert the new rehydration function somewhere near the top-level async helpers
# (e.g. after expire_single_reminder or after delayed_user_dm). Replace or insert exactly.


async def rehydrate_dm_scheduled_tasks(bot):
    """
    Recreate delayed_user_dm / immediate send tasks for persisted dm_scheduled_tracker entries.

    Behavior:
      - For each event_id / uid / delta_seconds in dm_scheduled_tracker:
        - Try to find a matching event in get_all_upcoming_events().
        - If no matching event or event >48h in future or event already long-past: remove marker.
        - Else compute seconds_until = start_time - delta - now
            - If seconds_until > 0: create delayed_user_dm task and register it
            - If seconds_until <= 0 and >= -REHYDRATE_STALE_GRACE_SECONDS: schedule immediate send_user_reminder task
            - If seconds_until < -REHYDRATE_STALE_GRACE_SECONDS: treat as stale and remove marker
      - Save dm_scheduled_tracker after pruning/restoring.
    """
    from event_cache import get_upcoming_event_cache_snapshot

    snapshot = get_upcoming_event_cache_snapshot()
    if not snapshot.ok or not snapshot.events:
        return {"status": "deferred", "reason": "event_data_unavailable_or_empty"}
    failed = 0
    held = 0
    try:
        if not dm_scheduled_tracker:
            logger.debug("[DM_REHYDRATE] No persisted scheduled DM markers to rehydrate.")
            return {"status": "complete", "restored": 0}

        logger.info("[DM_REHYDRATE] Attempting to rehydrate persisted scheduled DMs from disk.")
        # Build a mapping of event_id -> event for quick lookup
        upcoming = list(snapshot.events)
        event_map = {make_event_id(e): e for e in upcoming}

        now = utcnow()
        removed_any = False
        restored_count = 0

        # Iterate a copy to allow safe mutation
        for event_id, per_event in list(dm_scheduled_tracker.items()):
            # per_event: { uid: set(delta_seconds, ...) }
            # If event missing in current event cache, we'll attempt to use stored event info? (keep simple: prune)
            event = event_map.get(event_id)
            # If event not found, try to parse event_time from event_id — but prefer pruning to avoid spurious resends.
            if not event:
                # Remove all markers for this event
                logger.info(
                    "[DM_REHYDRATE] No matching upcoming event for %s — removing %d scheduled marker(s).",
                    event_id,
                    sum(len(s) for s in per_event.values()) if isinstance(per_event, dict) else 0,
                )
                dm_scheduled_tracker.pop(event_id, None)
                removed_any = True
                continue

            # Resolve start time
            try:
                start_time = ensure_aware_utc(event["start_time"])
            except Exception:
                logger.warning(
                    "[DM_REHYDRATE] Could not parse start_time for %s — removing markers.", event_id
                )
                dm_scheduled_tracker.pop(event_id, None)
                removed_any = True
                continue

            # Skip events >48h out (we will allow scheduler to handle them later)
            if start_time - now > timedelta(hours=48):
                logger.debug(
                    "[DM_REHYDRATE] Event %s >48h away — leaving markers for normal scheduling.",
                    event_id,
                )
                continue

            # For each user and each delta
            for uid, delta_set in list(per_event.items()):
                # iterate copy of set to allow mutation
                for delta_seconds in list(delta_set):
                    try:
                        delta = timedelta(seconds=int(delta_seconds))
                        receipt = await delivery.read(
                            delivery_key("dm-send", str(uid), event_id, int(delta_seconds))
                        )
                        if receipt and receipt["state"] == "entered":
                            held += 1
                            continue
                        if receipt and receipt["state"] == "acknowledged":
                            sent = dm_sent_tracker.setdefault(event_id, {}).setdefault(str(uid), [])
                            if int(delta_seconds) not in sent:
                                sent.append(int(delta_seconds))
                            await save_dm_sent_tracker_async()
                        if receipt or not _dm_eligible(uid, event, delta):
                            delta_set.discard(delta_seconds)
                            removed_any = True
                            continue
                        seconds_until = (start_time - delta - utcnow()).total_seconds()

                        # Case: in future -> recreate a delayed task
                        if seconds_until > 0:
                            try:
                                user = await bot.fetch_user(int(uid))
                            except Exception as e:
                                # Existing policy disposes this marker. A successful
                                # save below confirms cleanup, not uncertain work.
                                logger.warning(
                                    "[DM_REHYDRATE] Failed to fetch user %s for %s: %s — removing marker.",
                                    uid,
                                    event_id,
                                    e,
                                )
                                # remove the marker to avoid permanent blocking
                                dm_scheduled_tracker.get(event_id, {}).get(uid, set()).discard(
                                    delta_seconds
                                )
                                removed_any = True
                                continue

                            task = asyncio.create_task(
                                delayed_user_dm(bot, user, event, delta, seconds_until)
                            )
                            register_user_task(
                                user.id,
                                task,
                                meta={"event_id": event_id, "delta_seconds": int(delta_seconds)},
                            )
                            logger.info(
                                "[DM_REHYDRATE] Restored scheduled DM for user %s for %s at T-%s in %ds",
                                uid,
                                event_id,
                                delta,
                                int(seconds_until),
                            )
                            restored_count += 1
                            # Leave the persisted marker in place — it's already correct
                            continue

                        # Case: overdue but within grace window -> immediate send
                        if seconds_until >= -REHYDRATE_STALE_GRACE_SECONDS:
                            try:
                                user = await bot.fetch_user(int(uid))
                            except Exception as e:
                                # Count failed persistence below, not completed
                                # cleanup under the existing marker policy.
                                logger.warning(
                                    "[DM_REHYDRATE] Failed to fetch user %s for immediate send for %s: %s — removing marker.",
                                    uid,
                                    event_id,
                                    e,
                                )
                                dm_scheduled_tracker.get(event_id, {}).get(uid, set()).discard(
                                    delta_seconds
                                )
                                removed_any = True
                                continue

                            # Schedule immediate send via register_user_task
                            task = asyncio.create_task(send_user_reminder(user, event, delta))
                            register_user_task(
                                user.id,
                                task,
                                meta={"event_id": event_id, "delta_seconds": int(delta_seconds)},
                            )
                            logger.info(
                                "[DM_REHYDRATE] Scheduled immediate rehydrated DM to user %s for %s at T-%s (late by %ds)",
                                uid,
                                event_id,
                                delta,
                                int(-seconds_until),
                            )
                            restored_count += 1
                            # record will be kept by dm_sent_tracker when send_user_reminder succeeds
                            continue

                        # Case: stale beyond grace window -> remove
                        logger.info(
                            "[DM_REHYDRATE] Scheduled marker for %s user %s at T-%s is stale (%.1fs) — removing.",
                            event_id,
                            uid,
                            delta,
                            seconds_until,
                        )
                        dm_scheduled_tracker.get(event_id, {}).get(uid, set()).discard(
                            delta_seconds
                        )
                        removed_any = True

                    except Exception as e:
                        failed += 1
                        # Defensive: don't abort rehydration on per-item error
                        logger.warning(
                            "[DM_REHYDRATE] Error rehydrating marker %s / %s / %s: %s",
                            event_id,
                            uid,
                            delta_seconds,
                            e,
                        )
                        # Preserve unresolved markers; failure is not disposal evidence.

                # If user's set is empty, remove the uid entry
                if not dm_scheduled_tracker.get(event_id, {}).get(uid):
                    dm_scheduled_tracker.get(event_id, {}).pop(uid, None)
                    removed_any = True

            # If event bucket is empty after removals, remove it
            if not dm_scheduled_tracker.get(event_id):
                dm_scheduled_tracker.pop(event_id, None)
                removed_any = True

        if removed_any:
            try:
                await save_dm_scheduled_tracker_async()
            except Exception as e:
                failed += 1
                logger.warning(
                    "[DM_REHYDRATE] Failed to save dm_scheduled_tracker after pruning: %s", e
                )

        logger.info(
            "[DM_REHYDRATE] Rehydration complete — restored=%d removed_markers=%s",
            restored_count,
            removed_any,
        )
        return {
            "status": "partial" if failed else "complete",
            "restored": restored_count,
            "failed": failed,
            "held": held,
        }
    except Exception as e:
        # Fail-safe: never crash the scheduler due to rehydrate errors
        logger.exception("[DM_REHYDRATE] Unexpected error during DM rehydration: %s", e)
        return {"status": "unconfirmed", "error": type(e).__name__}


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
    # Cancellation while sleeping keeps the durable schedule for restart. At send
    # entry the current subscription is checked again; unsubscribe cannot replay it.


def build_user_reminder_embed(*, event, discord_name, main_governor, quote):
    raw_name = " ".join(str(event.get("name") or "Unnamed Event").split())
    name = truncate_text(raw_name, MAX_TITLE_CHARACTERS - len("📬  – Reminder"))
    safe_discord_name = truncate_text(" ".join(str(discord_name).split()), 128)
    safe_governor = truncate_text(" ".join(str(main_governor).split()), 128)
    starts_at = int(ensure_aware_utc(event["start_time"]).timestamp())
    fixed = f"Hey **** (())!\n⏰ Starts <t:{starts_at}:R>\n\n💬 **"
    quote_limit = (
        MAX_DESCRIPTION_CHARACTERS - len(fixed) - len(safe_discord_name) - len(safe_governor)
    )
    safe_quote = truncate_text(" ".join(str(quote).split()), quote_limit)
    description = (
        f"Hey **{safe_discord_name}** ({safe_governor})!\n"
        f"⏰ Starts <t:{starts_at}:R>\n\n"
        f"💬 *{safe_quote}*"
    )
    embed = discord.Embed(
        title=f"📬 {name} – Reminder",
        description=description,
        color=discord.Color.green(),
    )
    embed.set_footer(text="Manage with /modify_subscription or /unsubscribe")
    usage = require_valid_embed_payload(embed)
    logger.info(
        "[EMBED_PAYLOAD] renderer=legacy_reminder_dm fields=%d chars=%d max_field_value=0 compacted_events=%d omitted_events=0",
        usage.field_counts[0],
        usage.total_characters,
        int(
            name != raw_name
            or safe_discord_name != str(discord_name)
            or safe_governor != str(main_governor)
            or safe_quote != str(quote)
        ),
    )
    return embed


async def send_user_reminder(user, event, delta):
    scope = ("dm", make_event_id(event), str(user.id), int(delta.total_seconds()))
    async with delivery.operation_lock(scope):
        if delivery.is_closed():
            return "closed"
        return await _send_user_reminder(user, event, delta)


def _dm_eligible(user_id, event, delta):
    config = get_user_config(user_id)
    return bool(
        config
        and subscription_matches_event(config.get("subscriptions", []), event)
        and any(REMINDER_MAP.get(key) == delta for key in config.get("reminder_times", []))
    )


async def _send_user_reminder(user, event, delta):
    event_id = make_event_id(event)
    uid = str(user.id)
    delta_seconds = int(delta.total_seconds())

    sent_changed = False
    sched_changed = False
    settled = False
    key = delivery_key("dm-send", uid, event_id, delta_seconds)

    try:
        # 🚫 SKIP IF ALREADY SENT (per-user)
        if delta_seconds in dm_sent_tracker.get(event_id, {}).get(uid, []):
            logger.info(
                "[DM_REMINDER] ⚠️ Skipping duplicate DM to %s for %s at T-%s", user, event_id, delta
            )
            return

        receipt = await delivery.read(key)
        if receipt:
            if receipt["state"] == "acknowledged":
                dm_sent_tracker.setdefault(event_id, {}).setdefault(uid, []).append(delta_seconds)
                sent_changed = True
                settled = True
            elif receipt["state"] == "refused":
                settled = True
            return receipt["state"]
        if not _dm_eligible(user.id, event, delta):
            settled = True
            return "not_subscribed"

        # Names for personalization
        discord_name = getattr(user, "display_name", None) or str(user)
        main_gov = _get_main_governor_name_for_user(user.id) or discord_name

        # Select a quote by event type
        etype = (event.get("type") or "").lower().strip()
        candidates = DM_QUOTES.get(etype) or DM_QUOTES["_default"]
        quote_tpl = random.choice(candidates)
        quote = quote_tpl.format(name=discord_name, gov=main_gov)

        embed = build_user_reminder_embed(
            event=event,
            discord_name=discord_name,
            main_governor=main_gov,
            quote=quote,
        )

        if not await delivery.begin(
            key, kind="dm-send", target=uid, event=event_id, window=delta_seconds
        ):
            return "retained"
        if not _dm_eligible(user.id, event, delta) or delivery.is_closed():
            await delivery.finish(key, "refused")
            settled = True
            return "cancelled_before_send"
        msg = await user.send(embed=embed)
        await delivery.finish(key, "acknowledged", message_id=msg.id, channel_id=msg.channel.id)
        settled = True

        # ✅ Record successful send (per-user)
        dm_sent_tracker.setdefault(event_id, {}).setdefault(uid, [])
        if delta_seconds not in dm_sent_tracker[event_id][uid]:
            dm_sent_tracker[event_id][uid].append(delta_seconds)
            sent_changed = True

        reminder_stats["dm_success"] += 1
        logger.info("[DM_REMINDER] ✅ Sent DM to %s for %s at T-%s", user, event_id, delta)

        if reminder_stats["dm_success"] % 10 == 0:
            logger.info(
                f"[DM_REMINDER_SUMMARY] Running total — Sent: {reminder_stats['dm_success']}, "
                f"Blocked: {reminder_stats['dm_dm_disabled']}, Failed: {reminder_stats['dm_failed']}"
            )

    except discord.Forbidden:
        await delivery.finish(key, "refused")
        settled = True
        logger.warning("[DM_REMINDER] Cannot DM user %s — DMs disabled.", user)
        reminder_stats["dm_dm_disabled"] += 1
        log_failed_dm(user.id, event, delta, "DMs disabled")
    except Exception as e:
        logger.exception("[DM_REMINDER] Failed to DM user %s for %s: %s", user, event_id, e)
        reminder_stats["dm_failed"] += 1
        log_failed_dm(user.id, event, delta, str(e))
    finally:
        # Ambiguous/cancelled sends retain both journal and scheduled evidence.
        per_user_sched = dm_scheduled_tracker.get(event_id, {}).get(uid, set())
        if settled and delta_seconds in per_user_sched:
            per_user_sched.discard(delta_seconds)
            sched_changed = True

        # Persist with one locked section (both files if needed)
        if sent_changed or sched_changed:
            await _save_trackers_coalesced_async(sent=sent_changed, scheduled=sched_changed)


async def schedule_event_reminders(bot, notify_channel_id, test_mode=False, test_user_id=None):
    if not test_mode and not await _ensure_dm_startup(bot):
        logger.warning("[DM_REHYDRATE] Scheduler blocked by unresolved startup; no replay")
        return

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
            event_type = _normalized_event_type(event)
            if event_type not in {"ruins", "altars", "major", "chronicle"}:
                continue

            event_id = make_event_id(event)
            start_time = ensure_aware_utc(event["start_time"])

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

                delivery.own(
                    send_reminder_at(bot, notify_channel_id, event, delta),
                    name="public-reminder-send",
                )
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

                projection = build_kvk_alert_projection(
                    events=(event,),
                    config=config,
                    user_id=user.id,
                    sent_tracker=dm_sent_tracker,
                    scheduled_tracker=dm_scheduled_tracker,
                    now_utc=now,
                )
                for candidate in projection.candidates:
                    delta = REMINDER_MAP[candidate.lead_time_key]

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

                    seconds_until = (candidate.scheduled_for_utc - now).total_seconds()
                    logger.debug(
                        "[DM_REMINDER_DEBUG] User %s | Event: %s | Delta: %s | Seconds until: %d",
                        user_id,
                        event_id,
                        delta,
                        int(seconds_until),
                    )

                    user_sched.add(delta_seconds)
                    await save_dm_scheduled_tracker_async()

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

        await cleanup_dm_scheduled_tracker_async()
        await cleanup_dm_sent_tracker_async()
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
                ts = _extract_event_ts(eid)
                if not ts:
                    raise ValueError(f"Failed to extract timestamp for {eid}")
                event_time = parse_isoformat_utc(ts)
                if now > event_time + timedelta(minutes=15):
                    if await safe_delete_reminder(eid) == "removed":
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
        failed = 0
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
            time_remaining = ensure_aware_utc(event["start_time"]) - now
            is_now = abs(time_remaining.total_seconds()) < 60

            embed = build_public_reminder_embed(
                event,
                time_remaining,
                starts_now=is_now,
                add_public_quote=time_remaining <= timedelta(hours=1),
            )

            try:
                async with delivery.operation_lock(("public", event_id)):
                    if active_reminders.get(event_id) is not msg or delivery.is_closed():
                        continue
                    # One format restoration per physical message; never re-edit
                    # an uncertain original through a different generated quote.
                    key = delivery_key("public-format", msg.channel.id, msg.id)
                    if await delivery.begin(
                        key,
                        kind="public-format",
                        target=msg.channel.id,
                        event=event_id,
                        message_id=msg.id,
                    ):
                        await msg.edit(embed=embed)  # keep existing view
                        await delivery.finish(
                            key, "acknowledged", message_id=msg.id, channel_id=msg.channel.id
                        )
                    else:
                        receipt = await delivery.read(key)
                        if not receipt or receipt["state"] != "acknowledged":
                            failed += 1
                            continue
                updated += 1
            except Exception as e:
                failed += 1
                logger.error(f"[SCHEDULE_CACHE_REFRESH] Failed to edit message for {event_id}: {e}")

        logger.info(
            f"[SCHEDULE_CACHE_REFRESH] Reminder update complete. Edited {updated} messages."
        )
        return {"status": "partial" if failed else "complete", "updated": updated, "failed": failed}
    except Exception as e:
        logger.error(f"[SCHEDULE_CACHE_REFRESH] Entire function failed: {e}")

        return {"status": "unconfirmed", "error": type(e).__name__}
