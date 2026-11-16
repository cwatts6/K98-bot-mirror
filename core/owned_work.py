"""Cancellation-safe ownership of finite asynchronous and blocking work.

This does not retry, deduplicate, impose a timeout, or establish a durable outcome.
The caller retains its admission/lock until the child actually settles.
"""

import asyncio
from contextvars import copy_context

from core.operation_evidence import child_scope, emit, optional, worker_result
from core.operation_timing import clock, elapsed


async def drain_awaitable(awaitable):
    pending = asyncio.ensure_future(awaitable)
    try:
        return await asyncio.shield(pending)
    except asyncio.CancelledError:
        emit("worker_observer", "cancelled_draining")
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
    queued = clock()

    def run():
        optional(elapsed, "worker_queue_wait", queued)
        emit("worker_execution", "entered")
        started = clock()
        disposition = "completed"
        try:
            result = function(*args, **kwargs)
            optional(worker_result, result)
            return result
        except BaseException as exc:
            disposition = "interrupted"
            emit("worker_execution", "failed", error=exc)
            raise
        finally:
            optional(elapsed, "worker_execution", started, disposition)

    with child_scope():
        # A to_thread Task can itself be cancelled by loop-wide shutdown, even
        # when its parent shields it. Executor Futures are not all_tasks members.
        context = copy_context()
        future = asyncio.get_running_loop().run_in_executor(None, context.run, run)
        return await drain_awaitable(future)
