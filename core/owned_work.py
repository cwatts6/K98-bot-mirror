"""Cancellation-safe ownership of finite asynchronous and blocking work.

This does not retry, deduplicate, impose a timeout, or establish a durable outcome.
The caller retains its admission/lock until the child actually settles.
"""

import asyncio
from time import perf_counter

from core.operation_timing import record_timing, timed_stage


async def drain_awaitable(awaitable):
    pending = asyncio.ensure_future(awaitable)
    try:
        return await asyncio.shield(pending)
    except asyncio.CancelledError:
        while not pending.done():
            try:
                await asyncio.shield(pending)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if not pending.cancelled():
            pending.exception()
        raise


async def drain_thread(function, *args, **kwargs):
    """Run exactly once; cancellation waits for the thread, then propagates."""
    queued = perf_counter()

    def run():
        record_timing("worker_queue_wait", perf_counter() - queued)
        with timed_stage("worker_execution"):
            return function(*args, **kwargs)

    return await drain_awaitable(asyncio.to_thread(run))
