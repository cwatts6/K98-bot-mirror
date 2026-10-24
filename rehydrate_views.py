# rehydrate_views.py
"""Persistent-view factories and identity-checked startup restoration adapters."""

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

from uuid import uuid4

from ark.dal.rehydration_dal import get_registration_rehydration_data
from ark.registration_flow import ArkRegistrationController
from constants import (
    VIEW_PRUNE_ON_FORBIDDEN,
    VIEW_TRACKER_LOCK_POLL,
    VIEW_TRACKER_LOCK_TIMEOUT,
    VIEW_TRACKING_FILE,
)

# Import centralized sanitizer from embed_utils
from embed_utils import LocalTimeToggleView, sanitize_view_prefix
from services.legacy_export_snapshot_service import drain_thread
from services.tracked_view_rehydration_service import EntryOutcome, restore_tracked_views
from services.tracked_view_store import (
    EDIT_RECEIPT,
    TrackedViewStore,
    fingerprint,
    preserve_edit_receipt,
    tracker_lock,
)
from ui.views.ark_views import ArkRegistrationView

# Back-compat alias: some callers/tests reference the historical _sanitize_prefix name.
_sanitize_prefix = sanitize_view_prefix

# Use centralized event helpers and file utils (including run_with_retries + get_lockfile_info)
from event_utils import events_from_persisted, events_to_persisted
from file_utils import atomic_write_json, get_lockfile_info, read_json_safe, run_with_retries

_LOCK_PATH = f"{VIEW_TRACKING_FILE}.lock"

REHYDRATE_MIN_DELAY = 0.06  # seconds
REHYDRATE_FETCH_MAX_ATTEMPTS = 3
REHYDRATE_FETCH_TIMEOUT = 10.0
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
    config, match = await get_registration_rehydration_data(match_id)
    if not config:
        return None

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

    complete_event_packing = key == "daily_kvk_overview" or safe_prefix == "daily_kvk_overview"
    return (
        LocalTimeToggleView(
            events,
            prefix=safe_prefix,
            timeout=None,
            complete_event_packing=complete_event_packing,
        ),
        safe_prefix,
    )


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
            channel = await asyncio.wait_for(
                bot.fetch_channel(int(channel_id)), REHYDRATE_FETCH_TIMEOUT
            )
            msg = await asyncio.wait_for(
                channel.fetch_message(int(message_id)), REHYDRATE_FETCH_TIMEOUT
            )
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


def _tracker_store():
    return TrackedViewStore(
        VIEW_TRACKING_FILE,
        _LOCK_PATH,
        timeout=float(VIEW_TRACKER_LOCK_TIMEOUT),
        poll=float(VIEW_TRACKER_LOCK_POLL),
    )


async def _restore_tracked_entry(bot, store, key, entry):
    async def prune(reason):
        receipt = entry.get(EDIT_RECEIPT) if isinstance(entry, dict) else None
        if receipt is not None and (
            not isinstance(receipt, dict) or receipt.get("state") != "acknowledged"
        ):
            return EntryOutcome("outcome_unconfirmed", "prior_edit_unconfirmed")
        state = await store.prune(key, entry)
        return EntryOutcome(
            state, "prior_edit_unconfirmed" if state == "outcome_unconfirmed" else reason
        )

    valid, normalized = validate_tracker_entry(entry)
    if not valid:
        return await prune("invalid_entry")
    try:
        _, message = await _attempt_fetch_channel_and_message(
            bot, normalized["channel_id"], normalized["message_id"]
        )
    except Exception as exc:
        if _is_prunable_fetch_exception(exc):
            return await prune("inaccessible")
        return EntryOutcome("failed", "fetch_" + type(exc).__name__)

    safe_prefix = sanitize_view_prefix(normalized.get("prefix") or key, max_len=_PREFIX_MAX_LEN)
    if key.startswith("arkmatch_") or safe_prefix.startswith("arkmatch_"):
        match = re.match(r"^arkmatch_(\d+)", key) or re.match(r"^arkmatch_(\d+)", safe_prefix)
        if not match:
            return EntryOutcome("failed", "invalid_ark_identity")
        # This adapter's SQL worker is bounded by driver timeouts and drains on
        # cancellation. Never retry through another executor after its entry.
        view = await _build_ark_registration_view(int(match.group(1)))
        if view is None:
            return EntryOutcome("failed", "ark_data_unavailable")
    else:
        view, _ = _build_rehydrated_view(key, normalized)

    async with store.locked():
        data = await store.snapshot()
        if not store.matches(data, key, entry):
            return EntryOutcome("superseded", "tracker_changed")
        try:
            # No await between final identity check and local registration.
            bot.add_view(view, message_id=normalized["message_id"])
            return EntryOutcome("attached")
        except (TypeError, AttributeError):
            pass  # The historical compatibility path below is receipt guarded.

        previous = data[key].get(EDIT_RECEIPT)
        if previous is not None and (
            not isinstance(previous, dict) or previous.get("state") != "acknowledged"
        ):
            return EntryOutcome("outcome_unconfirmed", "prior_edit_unconfirmed")
        receipt = {
            "attempt_id": str(uuid4()),
            "fingerprint": fingerprint(entry),
            "state": "prepared",
        }
        data[key][EDIT_RECEIPT] = receipt
        await store.write(data)
        try:
            await asyncio.wait_for(message.edit(view=view), timeout=REHYDRATE_FETCH_TIMEOUT)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if _is_prunable_fetch_exception(exc):
                del data[key]
                await store.write(data)
                return EntryOutcome("pruned", "edit_inaccessible")
            return EntryOutcome("outcome_unconfirmed", "edit_" + type(exc).__name__)
        receipt["state"] = "acknowledged"
        try:
            await store.write(data)
        except Exception:
            return EntryOutcome("outcome_unconfirmed", "edit_receipt_unconfirmed")
        return EntryOutcome("attached")


async def rehydrate_tracked_views(bot) -> dict:
    """One supervised restoration per bot process, including reconnects."""
    task = getattr(bot, "_k98_tracked_view_restoration", None)
    owner = task is None
    if owner:
        store = _tracker_store()
        task = asyncio.create_task(
            restore_tracked_views(
                store.snapshot,
                lambda key, entry: _restore_tracked_entry(bot, store, key, entry),
                pause=REHYDRATE_MIN_DELAY,
            ),
            name="tracked_view_restoration_pass",
        )
        bot._k98_tracked_view_restoration = task
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        if owner:
            task.cancel()
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    break
            if not task.cancelled():
                task.exception()
        raise


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
        with tracker_lock(
            _LOCK_PATH, timeout=float(VIEW_TRACKER_LOCK_TIMEOUT), poll=float(VIEW_TRACKER_LOCK_POLL)
        ):
            tracker = _tracker_store().read()
            tracker[str(key)] = preserve_edit_receipt(tracker.get(str(key)), entry_copy)
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
    await drain_thread(save_view_tracker, key, entry)


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
        with tracker_lock(
            _LOCK_PATH, timeout=float(VIEW_TRACKER_LOCK_TIMEOUT), poll=float(VIEW_TRACKER_LOCK_POLL)
        ):
            tracker = _tracker_store().read()
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
