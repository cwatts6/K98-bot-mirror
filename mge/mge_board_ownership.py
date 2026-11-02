"""One process presentation owner for refresh and publication identity transitions."""

import asyncio
from contextlib import asynccontextmanager
from time import perf_counter
from weakref import WeakValueDictionary

from core.operation_timing import record_timing

_locks = WeakValueDictionary()


@asynccontextmanager
async def presentation_owner(bot, event_id):
    lock = _locks.setdefault((id(bot), int(event_id)), asyncio.Lock())
    started = perf_counter()
    async with lock:
        record_timing("mge_board_owner_wait", perf_counter() - started)
        yield
