"""One process presentation owner for refresh and publication identity transitions."""

import asyncio
from contextlib import asynccontextmanager
from weakref import WeakValueDictionary

from core.operation_evidence import local_owner, owner_wait
from core.operation_timing import clock, elapsed

_locks = WeakValueDictionary()


@asynccontextmanager
async def presentation_owner(bot, event_id):
    lock = _locks.setdefault((id(bot), int(event_id)), asyncio.Lock())
    started = clock()
    owner_wait(lock, "mge_board_owner_wait")
    async with lock:
        with local_owner(lock, "mge_board_owner_wait"):
            elapsed("mge_board_owner_wait", started)
            yield
