"""Selected event/reminder delivery ownership and passive, redacted evidence."""

import asyncio
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
import logging
from pathlib import Path
from weakref import WeakValueDictionary

from constants import DATA_DIR
from core.owned_work import drain_thread
from services.event_delivery_store import EventDeliveryStore

logger = logging.getLogger(__name__)
store = EventDeliveryStore(Path(DATA_DIR) / "event_delivery_receipts.json")
_locks = WeakValueDictionary()
_children = set()
_closed = False
_observation = {"observed_utc": None, "counts": {}, "changes_since_observation": False}
_observation_revision = 0


def _changed():
    global _observation_revision
    _observation_revision += 1
    _observation["changes_since_observation"] = True


def operation_lock(scope):
    # Scope identities are bounded to the selected callers, not a global scheduler.
    return _locks.setdefault(scope, asyncio.Lock())


def is_closed():
    return _closed


def close_admission():
    global _closed
    _closed = True


def own(coro, *, name):
    if _closed:
        coro.close()
        return None
    task = asyncio.create_task(coro, name=name)
    _children.add(task)

    def finished(done):
        _children.discard(done)
        if not done.cancelled() and done.exception() is not None:
            logger.error(
                "[EVENT_DELIVERY] child_failed name=%s error_type=%s",
                name,
                type(done.exception()).__name__,
            )

    task.add_done_callback(finished)
    return task


async def shutdown():
    close_admission()
    tasks = tuple(_children)
    for task in tasks:
        task.cancel()
    if tasks:
        waiter = asyncio.gather(*tasks, return_exceptions=True)
        while not waiter.done():
            try:
                await asyncio.shield(waiter)
            except asyncio.CancelledError:
                continue


async def read(key):
    return await drain_thread(store.get, key)


async def begin(key, **context):
    if _closed:
        return False
    _changed()
    try:
        return await drain_thread(store.begin, key, **context)
    finally:
        _changed()


async def finish(key, state, **receipt):
    _changed()
    try:
        return await drain_thread(store.finish, key, state, **receipt)
    finally:
        _changed()


async def receipt_rows():
    revision = _observation_revision
    rows = await drain_thread(store.rows)
    _observation.update(
        observed_utc=datetime.now(UTC).isoformat(),
        counts=dict(Counter(row["state"] for row in rows)),
        changes_since_observation=revision != _observation_revision,
    )
    return rows


def report():
    return {
        **deepcopy(_observation),
        "owned_children": len(_children),
        "closed": _closed,
        "verification": "Last journal observation only; changes_since_observation requires a fresh read. Not visual or end-to-end acceptance.",
    }


async def evidence_summary():
    """Read evidence only: never refresh, dispatch, reconcile or discard work."""
    try:
        rows = await receipt_rows()
        counts = Counter(row["state"] for row in rows)
        return (
            f"Selected event deliveries: acknowledged={counts['acknowledged']}, "
            f"unconfirmed={counts['entered']}, refused={counts['refused']}, "
            f"confirmed absent={counts['not_found']}. "
            "Acknowledgement is not visual or end-to-end acceptance."
        )
    except Exception as exc:
        logger.warning("[EVENT_DELIVERY] evidence_unavailable error_type=%s", type(exc).__name__)
        return "Selected event delivery evidence unavailable; retained work has not been replayed."
