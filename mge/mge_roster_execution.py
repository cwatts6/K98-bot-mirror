"""Own off-loop roster operations through their complete read/modify/write cycle.

All async roster mutation adapters share the event key. This preserves the
previous single-process serialization when moving synchronous services off-loop;
it is not a database transaction or cross-process ownership guarantee.
"""

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock, RLock
from time import perf_counter
from weakref import WeakValueDictionary

from core.operation_timing import record_timing
from core.owned_work import drain_awaitable, drain_thread

_locks = WeakValueDictionary()
_thread_locks = WeakValueDictionary()
_registry_lock = Lock()
_event = ContextVar("mge_roster_event", default=None)


def expected_event():
    return _event.get()


@contextmanager
def roster_thread_owner(event_key):
    """Serialize preparation (which can self-heal) with owned roster workers.

    Reentrant within one worker. Never held across an await/Discord operation.
    This adds no cross-process guarantee or transaction/replay behavior.
    """
    with _registry_lock:
        lock = _thread_locks.setdefault(int(event_key), RLock())
    started = perf_counter()
    with lock:
        record_timing("mge_roster_thread_wait", perf_counter() - started)
        token = _event.set(int(event_key))
        try:
            yield
        finally:
            _event.reset(token)


def _run_owned(event_key, function, args, kwargs):
    with roster_thread_owner(event_key):
        if "award_id" in kwargs:
            from mge.dal.mge_roster_dal import fetch_award_by_id
            from mge.mge_action_result import ActionDisposition, ActionEvidence, ActionFailure

            row = fetch_award_by_id(kwargs["award_id"])
            if not row:
                evidence = ActionEvidence(ActionDisposition.UNKNOWN)
                return ActionFailure(False, evidence.message(""), evidence)
            if row.get("EventId") != int(event_key):
                evidence = ActionEvidence(ActionDisposition.NOT_ENTERED)
                return ActionFailure(
                    False,
                    "The selected row belongs to a different event. Reopen the roster.",
                    evidence,
                )
        return function(*args, **kwargs)


async def run_roster_mutation(event_key, function, *args, **kwargs):
    lock = _locks.setdefault(int(event_key), asyncio.Lock())

    async def owned():
        started = perf_counter()
        async with lock:
            record_timing("mge_roster_owner_wait", perf_counter() - started)
            return await drain_thread(_run_owned, event_key, function, args, kwargs)

    return await drain_awaitable(owned())
