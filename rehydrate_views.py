# rehydrate_views.py
"""
Robust view tracker helpers and startup rehydration with enhanced telemetry/logging.

Enhancements in this file:
- emits structured telemetry events to logger "telemetry" for summary and key actions
- includes lockfile/process info when lock acquisition timeouts occur (uses file_utils.get_lockfile_info)
- emits per-entry telemetry on prune / failed / rehydrated events
- prefers file_utils.run_step when available (instead of direct run_blocking_in_thread) for consistent telemetry naming
- keeps small back-compat aliases for historical private names used in tests
- migrated save/remove tracker file operations to run_maintenance_with_isolation(prefer_process=True)
  with safe fallbacks to run_blocking_in_thread and asyncio.to_thread
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import json
import logging
import random
import re
import time
from typing import Any

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

# Import discord types if available
try:
    import discord

    DISCORD_AVAILABLE = True
except Exception:
    discord = None  # type: ignore
    DISCORD_AVAILABLE = False

from ark.dal.ark_dal import get_config, get_match
from ark.registration_flow import ArkRegistrationController
from constants import (
    VIEW_PRUNE_ON_FORBIDDEN,
    VIEW_TRACKER_LOCK_POLL,
    VIEW_TRACKER_LOCK_TIMEOUT,
    VIEW_TRACKING_FILE,
)

# Import centralized sanitizer from embed_utils
from embed_utils import LocalTimeToggleView, sanitize_view_prefix
from ui.views.ark_views import ArkRegistrationView

# Back-compat alias: some callers/tests reference the historical _sanitize_prefix name.
_sanitize_prefix = sanitize_view_prefix

# Use centralized event helpers and file utils (including run_with_retries + get_lockfile_info)
from event_utils import events_from_persisted, events_to_persisted

# Prefer run_step where possible; fallback to run_blocking_in_thread or asyncio.to_thread
try:
    from file_utils import (
        acquire_lock,
        atomic_write_json,
        get_lockfile_info,
        read_json_safe,
        run_step,
        run_with_retries,
    )  # type: ignore

    _HAS_RUN_STEP = True
except Exception:
    # Fallback set; import the other helpers without run_step
    from file_utils import (
        acquire_lock,
        atomic_write_json,
        get_lockfile_info,
        read_json_safe,
        run_with_retries,
    )  # type: ignore

    run_step = None  # type: ignore
    _HAS_RUN_STEP = False

# Try new isolation helpers (optional). We'll use them when available, with safe fallbacks.
try:
    from file_utils import run_maintenance_with_isolation  # type: ignore
except Exception:
    run_maintenance_with_isolation = None  # type: ignore

try:
    from file_utils import run_blocking_in_thread  # type: ignore
except Exception:
    run_blocking_in_thread = None  # type: ignore

_LOCK_PATH = f"{VIEW_TRACKING_FILE}.lock"

REHYDRATE_MIN_DELAY = 0.06  # seconds
REHYDRATE_FETCH_MAX_ATTEMPTS = 3
REHYDRATE_FETCH_BACKOFF_BASE = 0.25
REHYDRATE_FETCH_BACKOFF_MAX = 2.0

_PREFIX_MAX_LEN = 64


def _compute_match_datetime(match: dict) -> datetime:
    weekend = match.get("ArkWeekendDate")
    match_day = (match.get("MatchDay") or "").lower()
    match_time = match.get("MatchTimeUtc")

    if not weekend or not match_time:
        return datetime.now(UTC)

    base_date = weekend
    if match_day.startswith("sun"):
        base_date = weekend + timedelta(days=1)

    return datetime.combine(base_date, match_time, tzinfo=UTC)


async def _build_ark_registration_view(match_id: int) -> ArkRegistrationView | None:
    config = await get_config()
    if not config:
        return None

    match = await get_match(match_id)
    if not match:
        return None

    match_dt = _compute_match_datetime(match)
    match_name = f"Ark Match — {(match.get('Alliance') or '').strip() or match_id}"

    controller = ArkRegistrationController(match_id=match_id, config=config)
    return ArkRegistrationView(
        match_id=match_id,
        match_name=match_name,
        match_datetime_utc=match_dt,
        on_join_player=controller.join_player,
        on_join_sub=controller.join_sub,
        on_leave=controller.leave,
        on_switch=controller.switch,
        on_admin_add=controller.admin_add,
        on_admin_remove=controller.admin_remove,
        on_admin_move=controller.admin_move,
        timeout=None,
    )


def _build_rehydrated_view(key: str, normalized_entry: dict[str, Any]):
    """Build the correct persistent view class for a tracked entry.

    /nextfight and /nextevent require their specialized views so button callbacks
    keep working after restart. Other tracked entries continue to use
    LocalTimeToggleView.
    """
    safe_prefix = sanitize_view_prefix(
        normalized_entry.get("prefix") or key, max_len=_PREFIX_MAX_LEN
    )
    events = normalized_entry.get("events") or []
    initial_limit = normalized_entry.get("initial_limit", 1)
    try:
        initial_limit = max(1, int(initial_limit))
    except Exception:
        initial_limit = 1

    if key == "nextfight" or safe_prefix == "nextfight":
        from ui.views.events_views import NextFightView

        return NextFightView(initial_limit=initial_limit, prefix="nextfight"), safe_prefix

    if key == "nextevent" or safe_prefix == "nextevent":
        from ui.views.events_views import NextEventView

        return (
            NextEventView(initial_limit=initial_limit, prefix="nextevent", preloaded=events),
            safe_prefix,
        )

    return LocalTimeToggleView(events, prefix=safe_prefix, timeout=None), safe_prefix


def _validate_tracker_shape(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        logger.warning("[VIEW] Tracker file root is not a dict; ignoring contents.")
        return {}
    return raw


# Small helper to produce an ISO8601 string ending with 'Z' for UTC timestamps
def _to_iso_z(dt: Any) -> str:
    try:
        if isinstance(dt, str):
            return dt
        if isinstance(dt, datetime):
            d = dt
            if d.tzinfo is None:
                d = d.replace(tzinfo=UTC)
            s = d.isoformat()
            if s.endswith("+00:00"):
                s = s[:-6] + "Z"
            return s
        iso = getattr(dt, "isoformat", None)
        if callable(iso):
            s = iso()
            if isinstance(s, str):
                if s.endswith("+00:00"):
                    s = s[:-6] + "Z"
                return s
        return str(dt)
    except Exception:
        try:
            return str(dt)
        except Exception:
            return ""


def serialize_event(ev: dict) -> dict:
    """
    Convert an event dict (may contain datetime objects) into a JSON-serializable
    persisted form. Currently converts 'start_time' to an ISO string with 'Z'
    for UTC timestamps and preserves other keys as-is (defensive shallow copy).
    """
    out: dict[str, Any] = {}
    try:
        if not isinstance(ev, dict):
            return {}
        out = dict(ev)
        if "start_time" in out:
            out["start_time"] = _to_iso_z(out["start_time"])
    except Exception:
        logger.exception("[VIEW] serialize_event failed", exc_info=True)
    return out


def load_view_tracker() -> dict:
    try:
        raw = read_json_safe(VIEW_TRACKING_FILE, default={}) or {}
        return _validate_tracker_shape(raw)
    except Exception:
        logger.exception("[VIEW] Unexpected error while loading view tracker.")
        return {}


def _is_prunable_fetch_exception(exc: Exception) -> bool:
    try:
        if not DISCORD_AVAILABLE:
            return False
        if isinstance(exc, discord.NotFound):
            return True
        if isinstance(exc, discord.Forbidden):
            return bool(VIEW_PRUNE_ON_FORBIDDEN)
        if isinstance(exc, discord.HTTPException):
            status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
            try:
                return int(status) == 404
            except Exception:
                return False
    except Exception:
        return False
    return False


def validate_tracker_entry(entry: Any) -> tuple[bool, dict[str, Any] | str]:
    if not isinstance(entry, dict):
        return False, "entry not a dict"

    channel_id = entry.get("channel_id")
    message_id = entry.get("message_id")
    if channel_id is None or message_id is None:
        return False, "missing channel_id or message_id"

    try:
        channel_id_int = int(channel_id)
    except Exception:
        return False, f"channel_id not convertible to int: {channel_id!r}"
    try:
        message_id_int = int(message_id)
    except Exception:
        return False, f"message_id not convertible to int: {message_id!r}"

    events_raw = entry.get("events", [])
    if not isinstance(events_raw, list) or not events_raw:
        return False, "events must be a non-empty list"

    try:
        parsed_events = events_from_persisted(events_raw)
    except Exception as e:
        return False, f"events parsing failed: {e}"

    if not parsed_events:
        return False, "parsed events empty"

    normalized: dict[str, Any] = {
        "channel_id": channel_id_int,
        "message_id": message_id_int,
        "events": parsed_events,
    }
    for optional in ("created_at", "prefix"):
        if optional in entry:
            normalized[optional] = entry.get(optional)

    if "initial_limit" in entry:
        try:
            normalized["initial_limit"] = max(1, int(entry.get("initial_limit")))
        except Exception:
            normalized["initial_limit"] = 1

    return True, normalized


async def _attempt_fetch_channel_and_message(bot, channel_id: int, message_id: int):
    attempt = 0
    last_exc: Exception | None = None
    while attempt < REHYDRATE_FETCH_MAX_ATTEMPTS:
        attempt += 1
        try:
            channel = await bot.fetch_channel(int(channel_id))
            msg = await channel.fetch_message(int(message_id))
            if attempt > 1:
                logger.debug(
                    "[VIEW] Fetch succeeded on retry attempt=%d for channel=%s message=%s",
                    attempt,
                    channel_id,
                    message_id,
                )
            return channel, msg
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            last_exc = exc
            if _is_prunable_fetch_exception(exc):
                raise
            if attempt >= REHYDRATE_FETCH_MAX_ATTEMPTS:
                raise
            exp = REHYDRATE_FETCH_BACKOFF_BASE * (2 ** (attempt - 1))
            wait = min(exp, REHYDRATE_FETCH_BACKOFF_MAX)
            jitter = random.uniform(0, wait)
            logger.debug(
                "[VIEW] Transient fetch error (attempt %d/%d) for channel=%s message=%s: %s -- sleeping %.3fs before retry",
                attempt,
                REHYDRATE_FETCH_MAX_ATTEMPTS,
                channel_id,
                message_id,
                type(exc).__name__,
                jitter,
            )
            await asyncio.sleep(jitter)
    raise last_exc or RuntimeError("Unknown fetch failure")


async def rehydrate_tracked_views(bot) -> dict:
    """
    Rehydrate views from persistent tracker file. Returns summary dict:
      {"rehydrated": int, "pruned": int, "failed": int, "entries_total": int}
    """
    start_ts = time.monotonic()
    summary = {"rehydrated": 0, "pruned": 0, "failed": 0, "entries_total": 0}

    # Prefer run_step for telemetry; fall back to run_maintenance_with_isolation,
    # run_blocking_in_thread, or asyncio.to_thread
    try:
        if _HAS_RUN_STEP and run_step is not None:
            view_data = await run_step(load_view_tracker, name="load_view_tracker", meta={})
        else:
            if run_maintenance_with_isolation is not None:
                try:
                    res = await run_maintenance_with_isolation(
                        load_view_tracker, name="load_view_tracker", prefer_process=True, meta={}
                    )
                    # support helpers that return (value, meta)
                    if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
                        view_data = res[0]
                    else:
                        view_data = res
                except Exception:
                    # fallback to thread
                    if run_blocking_in_thread is not None:
                        view_data = await run_blocking_in_thread(
                            load_view_tracker, name="load_view_tracker"
                        )
                    else:
                        view_data = await asyncio.to_thread(load_view_tracker)
            elif run_blocking_in_thread is not None:
                view_data = await run_blocking_in_thread(
                    load_view_tracker, name="load_view_tracker"
                )
            else:
                view_data = await asyncio.to_thread(load_view_tracker)
    except Exception:
        view_data = await asyncio.to_thread(load_view_tracker)

    if not view_data:
        logger.info("[VIEW] No tracked views to rehydrate.")
        telemetry_logger.info(
            json.dumps({"event": "rehydration_start", "entries": 0, "timestamp": time.time()})
        )
        return summary

    summary["entries_total"] = len(view_data)
    logger.info("[VIEW] Starting rehydration of %d tracked view(s)...", len(view_data))
    telemetry_logger.info(
        json.dumps(
            {"event": "rehydration_start", "entries": len(view_data), "timestamp": time.time()}
        )
    )

    async def _offload_remove_entry(key: str):
        # Centralized offload for removing tracker entries: prefer run_step, then maintenance (process), then thread, then to_thread
        try:
            if _HAS_RUN_STEP and run_step is not None:
                await run_step(
                    remove_view_tracker_entry,
                    key,
                    name="remove_view_tracker_entry",
                    meta={"key": key},
                )
                return
        except Exception:
            pass

        if run_maintenance_with_isolation is not None:
            try:
                res = await run_maintenance_with_isolation(
                    remove_view_tracker_entry,
                    key,
                    name="remove_view_tracker_entry",
                    prefer_process=True,
                    meta={"key": key},
                )
                # support helpers that return (value, meta)
                if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
                    return res[0]
                return res
            except Exception:
                # fallback; continue to try other offloads
                pass

        if run_blocking_in_thread is not None:
            return await run_blocking_in_thread(
                remove_view_tracker_entry, key, name="remove_view_tracker_entry", meta={"key": key}
            )
        return await asyncio.to_thread(remove_view_tracker_entry, key)

    for key, entry in list(view_data.items()):
        try:
            if asyncio.current_task() and asyncio.current_task().cancelled():
                raise asyncio.CancelledError()

            if not isinstance(entry, dict):
                logger.warning("[VIEW] Skipping invalid tracker entry for key=%s", key)
                # use run_step if available, else maintenance offload helper
                await _offload_remove_entry(key)

                summary["pruned"] += 1
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "pruned_entry",
                            "key": key,
                            "reason": "not_dict",
                            "timestamp": time.time(),
                        }
                    )
                )
                await asyncio.sleep(REHYDRATE_MIN_DELAY)
                continue

            valid, result = validate_tracker_entry(entry)
            if not valid:
                reason = result
                logger.warning(
                    "[VIEW] Tracker entry invalid for key=%s: %s -- pruning.", key, reason
                )
                await _offload_remove_entry(key)

                summary["pruned"] += 1
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "pruned_entry",
                            "key": key,
                            "reason": str(reason),
                            "timestamp": time.time(),
                        }
                    )
                )
                await asyncio.sleep(REHYDRATE_MIN_DELAY)
                continue

            normalized_entry: dict = result
            channel_id = normalized_entry["channel_id"]
            message_id = normalized_entry["message_id"]

            try:
                channel, _message = await _attempt_fetch_channel_and_message(
                    bot, int(channel_id), int(message_id)
                )
            except asyncio.CancelledError:
                logger.info("[VIEW] Rehydration cancelled while fetching for key=%s", key)
                raise
            except Exception as fetch_exc:
                if _is_prunable_fetch_exception(fetch_exc):
                    logger.warning(
                        "[VIEW] Channel/message not accessible for key=%s channel=%s message=%s (pruning). exc=%s status=%s",
                        key,
                        channel_id,
                        message_id,
                        type(fetch_exc).__name__,
                        getattr(fetch_exc, "status", getattr(fetch_exc, "status_code", None)),
                    )
                    await _offload_remove_entry(key)

                    summary["pruned"] += 1
                    telemetry_logger.info(
                        json.dumps(
                            {
                                "event": "pruned_entry",
                                "key": key,
                                "channel_id": channel_id,
                                "message_id": message_id,
                                "reason": "inaccessible",
                                "exc": type(fetch_exc).__name__,
                                "timestamp": time.time(),
                            }
                        )
                    )
                else:
                    logger.warning(
                        "[VIEW] Transient error fetching (attempts=%d) for key=%s channel=%s message=%s: %s",
                        REHYDRATE_FETCH_MAX_ATTEMPTS,
                        key,
                        channel_id,
                        message_id,
                        type(fetch_exc).__name__,
                    )
                    summary["failed"] += 1
                    telemetry_logger.info(
                        json.dumps(
                            {
                                "event": "fetch_failed",
                                "key": key,
                                "channel_id": channel_id,
                                "message_id": message_id,
                                "exc": type(fetch_exc).__name__,
                                "timestamp": time.time(),
                            }
                        )
                    )
                await asyncio.sleep(REHYDRATE_MIN_DELAY)
                continue

            try:
                safe_prefix = sanitize_view_prefix(
                    normalized_entry.get("prefix") or key, max_len=_PREFIX_MAX_LEN
                )

                if key.startswith("arkmatch_") or safe_prefix.startswith("arkmatch_"):
                    match_id = None

                    # Prefer the key (usually clean: "arkmatch_1")
                    if key.startswith("arkmatch_"):
                        m = re.match(r"^arkmatch_(\d+)", key)
                        if m:
                            match_id = int(m.group(1))

                    # Fallback: prefix may be "arkmatch_1_abcdef"
                    if match_id is None:
                        m = re.match(r"^arkmatch_(\d+)", safe_prefix)
                        if m:
                            match_id = int(m.group(1))

                    if match_id:
                        view = await _build_ark_registration_view(match_id)
                        if view:
                            try:
                                bot.add_view(view, message_id=int(message_id))
                            except (TypeError, AttributeError):
                                await _message.edit(view=view)

                            logger.info(
                                "[VIEW] Rehydrated Ark registration view for match_id=%s channel=%s message=%s",
                                match_id,
                                channel_id,
                                message_id,
                            )
                            summary["rehydrated"] += 1
                            telemetry_logger.info(
                                json.dumps(
                                    {
                                        "event": "rehydrated",
                                        "key": key,
                                        "channel_id": channel_id,
                                        "message_id": message_id,
                                        "prefix": safe_prefix,
                                        "timestamp": time.time(),
                                    }
                                )
                            )
                            continue
                view, safe_prefix = _build_rehydrated_view(key, normalized_entry)
                try:
                    try:
                        bot.add_view(view, message_id=int(message_id))
                    except (TypeError, AttributeError):
                        try:
                            await _message.edit(view=view)
                        except asyncio.CancelledError:
                            logger.info(
                                "[VIEW] Rehydration cancelled while editing message for key=%s", key
                            )
                            raise
                        except Exception as edit_exc:
                            if _is_prunable_fetch_exception(edit_exc):
                                logger.warning(
                                    "[VIEW] Failed to attach view (message inaccessible) for key=%s channel=%s message=%s (pruning). exc=%s",
                                    key,
                                    channel_id,
                                    message_id,
                                    type(edit_exc).__name__,
                                )
                                await _offload_remove_entry(key)

                                summary["pruned"] += 1
                                telemetry_logger.info(
                                    json.dumps(
                                        {
                                            "event": "pruned_entry",
                                            "key": key,
                                            "reason": "attach_inaccessible",
                                            "exc": type(edit_exc).__name__,
                                            "timestamp": time.time(),
                                        }
                                    )
                                )
                                await asyncio.sleep(REHYDRATE_MIN_DELAY)
                                continue
                            logger.exception(
                                "[VIEW] Failed to attach view by editing message for key=%s channel=%s message=%s: %s",
                                key,
                                channel_id,
                                message_id,
                                edit_exc,
                            )
                            summary["failed"] += 1
                            telemetry_logger.info(
                                json.dumps(
                                    {
                                        "event": "attach_failed",
                                        "key": key,
                                        "exc": type(edit_exc).__name__,
                                        "timestamp": time.time(),
                                    }
                                )
                            )
                            await asyncio.sleep(REHYDRATE_MIN_DELAY)
                            continue

                except Exception:
                    logger.exception(
                        "[VIEW] Unexpected error while registering view for key=%s channel=%s message=%s",
                        key,
                        channel_id,
                        message_id,
                    )
                    summary["failed"] += 1
                    telemetry_logger.info(
                        json.dumps(
                            {
                                "event": "register_failed",
                                "key": key,
                                "channel_id": channel_id,
                                "message_id": message_id,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    await asyncio.sleep(REHYDRATE_MIN_DELAY)
                    continue

                logger.info(
                    "[VIEW] Rehydrated view for key=%s (prefix=%s) channel=%s message=%s",
                    key,
                    safe_prefix,
                    channel_id,
                    message_id,
                )
                summary["rehydrated"] += 1
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "rehydrated",
                            "key": key,
                            "channel_id": channel_id,
                            "message_id": message_id,
                            "prefix": safe_prefix,
                            "timestamp": time.time(),
                        }
                    )
                )

            except asyncio.CancelledError:
                logger.info(
                    "[VIEW] Rehydration cancelled while instantiating/registering view for %s", key
                )
                raise
            except Exception:
                logger.exception(
                    "[VIEW] Failed to instantiate/register view for key=%s channel=%s message=%s",
                    key,
                    channel_id,
                    message_id,
                )
                summary["failed"] += 1
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "instantiate_failed",
                            "key": key,
                            "exc": "exception",
                            "timestamp": time.time(),
                        }
                    )
                )

        except asyncio.CancelledError:
            logger.info("[VIEW] Rehydration cancelled (outer). Aborting remaining work.")
            raise
        except Exception:
            logger.exception("[VIEW] Unexpected error while rehydrating key=%s", key)
            summary["failed"] += 1
            telemetry_logger.info(
                json.dumps({"event": "unexpected_error", "key": key, "timestamp": time.time()})
            )
        await asyncio.sleep(REHYDRATE_MIN_DELAY)

    elapsed = time.monotonic() - start_ts
    logger.info(
        "[VIEW] Rehydration complete. rehydrated=%d pruned=%d failed=%d elapsed=%.2fs",
        summary["rehydrated"],
        summary["pruned"],
        summary["failed"],
        elapsed,
    )
    telemetry_logger.info(
        json.dumps(
            {
                "event": "rehydration_summary",
                "rehydrated": summary["rehydrated"],
                "pruned": summary["pruned"],
                "failed": summary["failed"],
                "total": summary["entries_total"],
                "elapsed_s": elapsed,
                "timestamp": time.time(),
            }
        )
    )
    return summary


class LockAcquireTimeout(Exception):
    def __init__(
        self,
        message: str,
        lockfile: str | None = None,
        lock_content: str | None = None,
        lock_info: dict | None = None,
    ):
        super().__init__(message)
        self.lockfile = lockfile
        self.lock_content = lock_content
        self.lock_info = lock_info


def save_view_tracker(key: str, entry: dict):
    if not key:
        raise ValueError("key is required")

    entry_copy = dict(entry or {})
    if "events" in entry_copy:
        entry_copy["events"] = events_to_persisted(entry_copy.get("events", []))
        if not entry_copy["events"]:
            logger.error("[VIEW] Attempt to save tracker entry with empty events for key=%s", key)
            raise ValueError("events must be a non-empty list when saving a tracker entry")

        # Ensure start_time uses trailing 'Z' for UTC rather than '+00:00' to preserve
        # the persisted format produced by serialize_event used in tests.
        try:
            for ev in entry_copy["events"]:
                if isinstance(ev, dict) and "start_time" in ev:
                    st = ev.get("start_time")
                    if isinstance(st, str) and st.endswith("+00:00"):
                        ev["start_time"] = st[:-6] + "Z"
        except Exception:
            # best-effort normalization only
            pass

    valid, result = validate_tracker_entry(entry_copy)
    if not valid:
        raise ValueError(f"Invalid tracker entry for key={key}: {result}")

    try:
        with acquire_lock(
            _LOCK_PATH, timeout=float(VIEW_TRACKER_LOCK_TIMEOUT), poll=float(VIEW_TRACKER_LOCK_POLL)
        ):
            tracker = read_json_safe(VIEW_TRACKING_FILE, default={}) or {}
            if not isinstance(tracker, dict):
                tracker = {}
            tracker[str(key)] = entry_copy
            atomic_write_json(VIEW_TRACKING_FILE, tracker)
            logger.debug("[VIEW] Saved tracker entry for key=%s", key)
    except TimeoutError:
        # gather lockfile info for telemetry
        lock_info = get_lockfile_info(_LOCK_PATH)
        try:
            lock_content = lock_info.get("content", "<unreadable>")
        except Exception:
            lock_content = "<unreadable>"
        msg = f"Timeout acquiring lock when saving tracker for key={key} lockfile={_LOCK_PATH} info={lock_info}"
        logger.exception("[VIEW] %s", msg)
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "lock_timeout",
                    "key": key,
                    "lockfile": str(_LOCK_PATH),
                    "lock_info": lock_info,
                    "timestamp": time.time(),
                }
            )
        )
        raise LockAcquireTimeout(
            msg, lockfile=_LOCK_PATH, lock_content=lock_content, lock_info=lock_info
        )
    except Exception:
        logger.exception("[VIEW] Failed to save view tracker for key=%s", key)
        raise


# Async wrapper to avoid blocking the event loop.
async def save_view_tracker_async(key: str, entry: dict) -> None:
    try:
        if _HAS_RUN_STEP and run_step is not None:
            # pass both key and entry through to run_step for correct invocation
            await run_step(
                save_view_tracker, key, entry, name="save_view_tracker", meta={"key": key}
            )
            return
    except Exception:
        pass

    # Prefer process-isolated maintenance offload when available, then thread, then to_thread
    if run_maintenance_with_isolation is not None:
        try:
            await run_maintenance_with_isolation(
                save_view_tracker,
                key,
                entry,
                name="save_view_tracker",
                prefer_process=True,
                meta={"key": key},
            )
            return
        except Exception:
            # fall through to thread fallback
            pass

    if run_blocking_in_thread is not None:
        # ensure both key and entry are forwarded
        await run_blocking_in_thread(save_view_tracker, key, entry, name="save_view_tracker")
    else:
        # fallback to asyncio.to_thread; forward both args
        await asyncio.to_thread(save_view_tracker, key, entry)


def save_view_tracker_with_retries(
    key: str,
    entry: dict,
    *,
    retries: int = 3,
    base_backoff: float = 0.05,
    max_backoff: float = 0.5,
) -> None:
    # synchronous wrapper for run_with_retries (keeps compatibility with callers)
    return run_with_retries(
        save_view_tracker,
        key,
        entry,
        retries=retries,
        base_backoff=base_backoff,
        max_backoff=max_backoff,
        retry_exceptions=(TimeoutError, LockAcquireTimeout),
    )


def remove_view_tracker_entry(key: str) -> bool:
    try:
        with acquire_lock(
            _LOCK_PATH, timeout=float(VIEW_TRACKER_LOCK_TIMEOUT), poll=float(VIEW_TRACKER_LOCK_POLL)
        ):
            tracker = read_json_safe(VIEW_TRACKING_FILE, default={}) or {}
            if not isinstance(tracker, dict):
                tracker = {}
            existed = tracker.pop(str(key), None) is not None
            atomic_write_json(VIEW_TRACKING_FILE, tracker)
            if existed:
                logger.info("[VIEW] Pruned tracker entry for key=%s", key)
            return existed
    except TimeoutError:
        lock_info = get_lockfile_info(_LOCK_PATH)
        logger.exception(
            "[VIEW] Timeout acquiring lock when removing tracker key=%s lockfile=%s info=%s",
            key,
            _LOCK_PATH,
            lock_info,
        )
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "lock_timeout_remove",
                    "key": key,
                    "lockfile": str(_LOCK_PATH),
                    "lock_info": lock_info,
                    "timestamp": time.time(),
                }
            )
        )
        return False
    except Exception:
        logger.exception("[VIEW] Failed removing tracker key=%s", key)
        return False
