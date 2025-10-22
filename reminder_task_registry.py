# reminder_task_registry.py
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)
_TASKS: dict[str, set[asyncio.Task]] = {}
# Store lightweight metadata per task so we can selectively cancel
_META: dict[asyncio.Task, dict[str, Any]] = {}


def _uid(user_id) -> str:
    return str(user_id)


def register_user_task(
    user_id, task: asyncio.Task, *, meta: dict[str, Any] | None = None
) -> asyncio.Task:
    uid = _uid(user_id)
    bucket = _TASKS.setdefault(uid, set())
    bucket.add(task)
    if meta:
        _META[task] = {"uid": uid, **meta}

    def _cleanup(t: asyncio.Task):
        try:
            bucket.discard(t)
            if not bucket:
                _TASKS.pop(uid, None)
            _META.pop(t, None)
        except Exception:
            logger.exception("[TASK_REGISTRY] cleanup failed uid=%s", uid)

    task.add_done_callback(_cleanup)
    return task


def schedule_for_user(user_id, coro) -> asyncio.Task:
    return register_user_task(user_id, asyncio.create_task(coro))


def cancel_user_reminder_tasks(user_id) -> int:
    uid = _uid(user_id)
    tasks = list(_TASKS.get(uid, ()))
    count = 0
    for t in tasks:
        if not t.done() and not t.cancelled():
            t.cancel()
            count += 1
    if count:
        logger.info("[TASK_REGISTRY] Cancelled %d tasks for user %s", count, uid)
    return count


def cancel_user_tasks_for_event(user_id, event_id: str) -> int:
    """Cancel only tasks for a given user tied to event_id."""
    uid = _uid(user_id)
    tasks = list(_TASKS.get(uid, ()))
    count = 0
    for t in tasks:
        meta = _META.get(t) or {}
        if meta.get("event_id") == event_id and (not t.done() and not t.cancelled()):
            t.cancel()
            count += 1
    if count:
        logger.info("[TASK_REGISTRY] Cancelled %d tasks for user %s event=%s", count, uid, event_id)
    return count


def cancel_user_tasks_for_event_delta(user_id, event_id: str, delta_seconds: int) -> int:
    """Cancel only tasks for a given user + event + delta (in seconds)."""
    uid = _uid(user_id)
    tasks = list(_TASKS.get(uid, ()))
    count = 0
    for t in tasks:
        meta = _META.get(t) or {}
        if (
            meta.get("event_id") == event_id
            and int(meta.get("delta_seconds", -1)) == int(delta_seconds)
            and (not t.done() and not t.cancelled())
        ):
            t.cancel()
            count += 1
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
    if user_id is None:
        return sum(1 for s in _TASKS.values() for t in s if not t.done())
    return sum(1 for t in _TASKS.get(_uid(user_id), ()) if not t.done())


def user_task_snapshot(user_id: int | str | None = None) -> dict[str, Any]:
    """
    Debug helper: returns a summary of active tasks and their metadata.
    If user_id is provided, limits to that user.
    """
    snap: dict[str, Any] = {}
    if user_id is None:
        for uid, tasks in _TASKS.items():
            snap[uid] = [_META.get(t, {}) for t in tasks if not t.done()]
    else:
        uid = _uid(user_id)
        snap[uid] = [_META.get(t, {}) for t in _TASKS.get(uid, ()) if not t.done()]
    return snap
