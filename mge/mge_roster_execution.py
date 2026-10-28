"""Own off-loop roster operations through their complete read/modify/write cycle.

All async roster mutation adapters share the event key. This preserves the
previous single-process serialization when moving synchronous services off-loop;
it is not a database transaction or cross-process ownership guarantee.
"""

import asyncio
from weakref import WeakValueDictionary

from core.owned_work import drain_awaitable, drain_thread

_locks = WeakValueDictionary()


async def run_roster_mutation(event_key, function, *args, **kwargs):
    lock = _locks.setdefault(int(event_key), asyncio.Lock())

    async def owned():
        async with lock:
            return await drain_thread(function, *args, **kwargs)

    return await drain_awaitable(owned())
