"""Own off-loop roster operations through their complete read/modify/write cycle.

All async roster mutation adapters share the event key. This preserves the
previous single-process serialization when moving synchronous services off-loop;
it is not a database transaction or cross-process ownership guarantee.
"""

import asyncio
from contextlib import contextmanager
from threading import Lock, RLock
from time import perf_counter
from weakref import WeakValueDictionary

from core.operation_timing import record_timing
from core.owned_work import drain_awaitable, drain_thread

_locks = WeakValueDictionary()
_thread_locks = WeakValueDictionary()
_registry_lock = Lock()


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
        yield


def _run_owned(event_key, function, args, kwargs):
    with roster_thread_owner(event_key):
        return function(*args, **kwargs)


async def run_roster_mutation(event_key, function, *args, **kwargs):
    lock = _locks.setdefault(int(event_key), asyncio.Lock())

    async def owned():
        started = perf_counter()
        async with lock:
            record_timing("mge_roster_owner_wait", perf_counter() - started)
            return await drain_thread(_run_owned, event_key, function, args, kwargs)

    return await drain_awaitable(owned())
