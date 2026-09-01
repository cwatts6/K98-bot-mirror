# reminder_task_registry.py
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
import json
import logging
import threading
from typing import Any
import weakref

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

# Prefer centralized telemetry emitter when available; fall back to safe shim.
try:
    from file_utils import emit_telemetry_event  # type: ignore
except Exception:

    def emit_telemetry_event(payload: dict, *, max_snippet: int = 2000) -> None:
        try:
            telemetry_logger.info(json.dumps(payload, default=str))
        except Exception:
            try:
                telemetry_logger.info(str(payload))
            except Exception:
                pass


# Mapping: uid -> set of asyncio.Task
_TASKS: dict[str, set[asyncio.Task[Any]]] = {}
# Lightweight metadata keyed by Task. Use WeakKeyDictionary so metadata doesn't keep Tasks alive
_META: weakref.WeakKeyDictionary[asyncio.Task[Any], dict[str, Any]] = weakref.WeakKeyDictionary()

# Thread-safe guard for internal structures (re-entrant)
_LOCK = threading.RLock()


def _uid(user_id) -> str:
    return str(user_id)


def register_user_task(
    user_id, task: asyncio.Task[Any], *, meta: dict[str, Any] | None = None
) -> asyncio.Task[Any]:
    """
    Register an already-created asyncio.Task against a user id.

    Notes:
    - This function is synchronous and uses a threading.RLock to guard the
      internal mappings. It's safe to call from the event loop or from other
      threads (fast lock acquisition assumed).
    - task.add_done_callback is used to remove the task and its metadata once
      it completes. The callback is defensive and logs failures.
    """
    uid = _uid(user_id)

    with _LOCK:
        bucket = _TASKS.setdefault(uid, set())
        bucket.add(task)
        if meta:
            # store meta + uid for easier diagnostics
            _META[task] = {"uid": uid, **meta}

    # Observability: debug log registration
    try:
        meta_keys = sorted(meta.keys()) if meta else None
    except Exception:
        meta_keys = None
    logger.debug(
        "[TASK_REGISTRY] Registered task uid=%s task=%s meta_keys=%s",
        uid,
        getattr(task, "get_name", lambda: f"id:{id(task)}")(),
        meta_keys,
    )

    def _cleanup(t: asyncio.Task[Any]):
        try:
            with _LOCK:
                # discard from the set; if empty remove the bucket
                bucket.discard(t)
                if not bucket:
                    _TASKS.pop(uid, None)
                # remove metadata, if any
                try:
                    _META.pop(t, None)
                except Exception:
                    # _META is a WeakKeyDictionary; safe-guard any odd cases
                    pass
            logger.debug(
                "[TASK_REGISTRY] cleanup complete uid=%s task=%s",
                uid,
                getattr(t, "get_name", lambda: f"id:{id(t)}")(),
            )
        except Exception:
            logger.exception("[TASK_REGISTRY] cleanup failed uid=%s", uid)

    try:
        task.add_done_callback(_cleanup)
    except Exception:
        # Worst case: still keep the registration; best-effort to attach cleanup.
        logger.exception("[TASK_REGISTRY] Failed to attach done callback for uid=%s", uid)

    return task


def schedule_for_user(
    user_id,
    coro: Coroutine[Any, Any, Any],
    *,
    meta: dict[str, Any] | None = None,
    name: str | None = None,
) -> asyncio.Task[Any]:
    """
    Convenience: create & register a Task for the given user's coroutine.

    - meta: optional metadata dict (e.g. {"event_id": "...", "delta_seconds": 3600})
    - name: optional task name (Python 3.8+). Provided when you want readable task names.

    Raises:
      RuntimeError if called outside of a running event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Safer error message than the raw asyncio one
        raise RuntimeError(
            "schedule_for_user must be called from a running event loop (use asyncio.run / ensure a loop is running)"
        )

    try:
        # prefer named task when available
        if name is not None:
            task = loop.create_task(coro, name=name)  # type: ignore[arg-type]
        else:
            task = loop.create_task(coro)
    except Exception:
        logger.exception("[TASK_REGISTRY] create_task failed for uid=%s", _uid(user_id))
        raise

    return register_user_task(user_id, task, meta=meta)


def cancel_user_reminder_tasks(user_id) -> int:
    """
    Cancel all tasks registered for user_id (non-blocking).
    Returns the number of tasks that were requested to cancel.
    """
    uid = _uid(user_id)
    with _LOCK:
        tasks = list(_TASKS.get(uid, ()))

    count = 0
    cancelled = []
    for t in tasks:
        with _LOCK:
            meta = _META.get(t) or {}
        if not t.done() and not t.cancelled():
            try:
                t.cancel()
                count += 1
                cancelled.append((t, meta))
            except Exception:
                logger.exception("[TASK_REGISTRY] Failed to cancel task uid=%s task=%s", uid, t)

    if count:
        # log meta summary for observability (don't log full meta - keep it compact)
        try:
            meta_summary = [
                {k: meta.get(k) for k in ("event_id", "delta_seconds") if k in meta} or None
                for _, meta in cancelled
            ]
        except Exception:
            meta_summary = None
        logger.info(
            "[TASK_REGISTRY] Cancelled %d tasks for user %s meta_summary=%s",
            count,
            uid,
            meta_summary,
        )
    return count


def cancel_user_tasks_for_event(user_id, event_id: str) -> int:
    """Cancel only tasks for a given user tied to event_id."""
    uid = _uid(user_id)
    with _LOCK:
        tasks = list(_TASKS.get(uid, ()))

    count = 0
    cancelled = []
    for t in tasks:
        meta = _META.get(t) or {}
        if meta.get("event_id") == event_id and (not t.done() and not t.cancelled()):
            try:
                t.cancel()
                count += 1
                cancelled.append((t, meta))
            except Exception:
                logger.exception(
                    "[TASK_REGISTRY] Failed to cancel task uid=%s event=%s task=%s",
                    uid,
                    event_id,
                    t,
                )

    if count:
        logger.info(
            "[TASK_REGISTRY] Cancelled %d tasks for user %s event=%s",
            count,
            uid,
            event_id,
        )
    return count


def cancel_user_tasks_for_event_delta(user_id, event_id: str, delta_seconds: int) -> int:
    """Cancel only tasks for a given user + event + delta (in seconds)."""
    uid = _uid(user_id)
    with _LOCK:
        tasks = list(_TASKS.get(uid, ()))

    count = 0
    cancelled = []
    for t in tasks:
        meta = _META.get(t) or {}
        try:
            meta_delta = int(meta.get("delta_seconds", -1))
        except Exception:
            meta_delta = -1
        if (
            meta.get("event_id") == event_id
            and meta_delta == int(delta_seconds)
            and (not t.done() and not t.cancelled())
        ):
            try:
                t.cancel()
                count += 1
                cancelled.append((t, meta))
            except Exception:
                logger.exception(
                    "[TASK_REGISTRY] Failed to cancel task uid=%s event=%s delta=%s task=%s",
                    uid,
                    event_id,
                    delta_seconds,
                    t,
                )

    if count:
        logger.info(
            "[TASK_REGISTRY] Cancelled %d tasks for user %s event=%s delta=%s",
            count,
            uid,
            event_id,
            delta_seconds,
        )
    return count


def active_task_count(user_id: int | str | None = None) -> int:
    """Return number of active (not done) tasks for a user or overall if user_id is None."""
    if user_id is None:
        with _LOCK:
            return sum(1 for s in _TASKS.values() for t in s if not t.done())
    return sum(1 for t in _TASKS.get(_uid(user_id), ()) if not t.done())


def user_task_snapshot(user_id: int | str | None = None) -> dict[str, Any]:
    """
    Debug helper: returns a summary of active tasks and their metadata.
    If user_id is provided, limits to that user.
    """
    snap: dict[str, Any] = {}
    if user_id is None:
        with _LOCK:
            items = list(_TASKS.items())
        for uid, tasks in items:
            snap[uid] = [_META.get(t, {}) for t in tasks if not t.done()]
    else:
        uid = _uid(user_id)
        with _LOCK:
            tasks = list(_TASKS.get(uid, ()))
        snap[uid] = [_META.get(t, {}) for t in tasks if not t.done()]
    return snap


# ----------------- Async cancellation helpers for graceful shutdown --------------
async def cancel_and_wait_user_tasks(user_id: int | str, timeout: float | None = None) -> int:
    """
    Cancel tasks for a user and wait for them to complete (best-effort).
    Returns number of tasks that were cancelled (or already done while we waited).
    """
    uid = _uid(user_id)
    with _LOCK:
        tasks = [t for t in _TASKS.get(uid, set()) if not t.done()]

    if not tasks:
        return 0

    # request cancellation
    for t in tasks:
        try:
            t.cancel()
        except Exception:
            logger.exception(
                "[TASK_REGISTRY] cancel_and_wait: failed to cancel task uid=%s task=%s", uid, t
            )

    # await completion with timeout
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
    except TimeoutError:
        logger.warning(
            "[TASK_REGISTRY] cancel_and_wait timed out for uid=%s timeout=%s", uid, timeout
        )
        emit_telemetry_event(
            {
                "event": "cancel_and_wait",
                "status": "timeout",
                "uid": uid,
                "timeout": timeout,
                "tasks_may_still_run": True,
                "orphaned_offload_possible": False,
            }
        )
    except Exception:
        logger.exception("[TASK_REGISTRY] cancel_and_wait encountered an error for uid=%s", uid)

    # compute how many are now done/cancelled
    with _LOCK:
        final_tasks = [t for t in _TASKS.get(uid, set()) if not t.done()]
    cancelled_count = max(0, len(tasks) - len(final_tasks))
    logger.info(
        "[TASK_REGISTRY] cancel_and_wait completed for uid=%s cancelled=%d", uid, cancelled_count
    )
    return cancelled_count


async def cancel_all_and_wait(timeout: float | None = None) -> int:
    """
    Cancel all registered tasks across all users and wait for them to complete.
    Returns number of tasks requested to cancel.
    """
    with _LOCK:
        tasks = [t for s in _TASKS.values() for t in s if not t.done()]

    if not tasks:
        return 0

    for t in tasks:
        try:
            t.cancel()
        except Exception:
            logger.exception("[TASK_REGISTRY] cancel_all_and_wait: failed to cancel task %s", t)

    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
    except TimeoutError:
        logger.warning("[TASK_REGISTRY] cancel_all_and_wait timed out timeout=%s", timeout)
        emit_telemetry_event(
            {
                "event": "cancel_all_and_wait",
                "status": "timeout",
                "timeout": timeout,
                "tasks_may_still_run": True,
                "orphaned_offload_possible": False,
            }
        )
    except Exception:
        logger.exception("[TASK_REGISTRY] cancel_all_and_wait encountered an error")

    # count how many were requested to cancel (best-effort)
    cancelled = sum(1 for t in tasks if t.cancelled() or t.done())
    logger.info("[TASK_REGISTRY] cancel_all_and_wait completed requested_cancel=%d", cancelled)
    return cancelled


# Back-compat TaskRegistry class (some callers import TaskRegistry)
class TaskRegistry:
    """
    Backwards compatibility wrapper exposing a minimal class API used in other modules.
    """

    @classmethod
    async def cancel_all(cls, timeout: float | None = 5.0) -> int:
        return await cancel_all_and_wait(timeout=timeout)

    @classmethod
    async def cancel_user_and_wait(cls, user_id: int | str, timeout: float | None = 5.0) -> int:
        return await cancel_and_wait_user_tasks(user_id, timeout=timeout)
