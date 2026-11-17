"""Settlement acknowledgements must preserve errors and retained uncertainty."""

import asyncio
from concurrent.futures import Future

import pytest

from player_self_service.stats_runtime import StatsRuntime


@pytest.mark.asyncio
async def test_already_completed_render_publishes_once_across_concurrent_drains():
    class ImmediateExecutor:
        def submit(self, function, *args):
            future = Future()
            future.set_result(function(*args))
            return future

    runtime = StatsRuntime()
    publications = []
    run = runtime.submit(
        "render",
        lambda run: "image",
        executor=ImmediateExecutor(),
        publish=lambda run: publications.append(run.result),
    )
    run.task.cancel()
    assert await asyncio.gather(runtime.drain(), runtime.drain()) == [True, True]
    await asyncio.gather(run.task, return_exceptions=True)
    assert run.settlement_future.done() and run.settled
    assert publications == ["image"] and not runtime.jobs


@pytest.mark.asyncio
async def test_render_unknown_cleanup_acknowledges_disposition_without_releasing_owner():
    runtime = StatsRuntime()
    retained = object()

    def render(run):
        run.outcome.cleanup = "unconfirmed"
        run.outcome.retained_connection = retained
        return "private"

    run = runtime.submit("render", render, executor=runtime.renderer_executor())
    try:
        assert not await runtime.drain()
        assert not await runtime.drain()
        assert run.settlement_future.done() and run.settled
        assert run.outcome.retained_connection is retained
        assert runtime.jobs[id(run)] is run and runtime.closed
        assert runtime.close_reason == "cleanup_uncertain" and run.result is None
    finally:
        # The retained object is an inert sentinel. Join test threads without
        # clearing the deliberately retained uncertain ownership record.
        await asyncio.gather(run.task, return_exceptions=True)
        runtime.render_executor.shutdown(wait=True)


@pytest.mark.asyncio
async def test_native_error_and_repeated_cancellation_still_join_queued_settlement(monkeypatch):
    runtime = StatsRuntime()
    failure = ValueError("inert render failed")
    held = []
    original_soon = runtime.loop.call_soon

    def hold_callback(callback, *args, context=None):
        if getattr(callback, "__qualname__", "").endswith("render_completed"):
            return original_soon(lambda: held.append((callback, args, context)))
        return original_soon(callback, *args, context=context)

    def fail(run):
        raise failure

    with monkeypatch.context() as patch:
        patch.setattr(runtime.loop, "call_soon", hold_callback)
        run = runtime.submit("render", fail, executor=runtime.renderer_executor())
        task = asyncio.create_task(runtime.drain())
        try:
            async with asyncio.timeout(3):
                while not held:
                    await asyncio.sleep(0)
            assert run.native_future.done() and run.error is failure
            assert not run.settlement_future.done()
            for _ in range(3):
                task.cancel()
                await asyncio.sleep(0)
                assert not task.done() and runtime.jobs[id(run)] is run
                assert not run.settlement_future.cancelled()
        finally:
            patch.setattr(runtime.loop, "call_soon", original_soon)
            for callback, args, context in held:
                original_soon(callback, *args, context=context)
            await asyncio.gather(run.task, task, return_exceptions=True)
            assert await runtime.drain()
    assert run.error is failure and run.settlement_future.done()
    assert task.result() is True and not runtime.jobs
