"""Render submission and native custody across owner scheduling failures."""

import asyncio
from contextvars import ContextVar
import threading

import pytest

from player_self_service.stats_models import PersonalStatsUnavailable
from player_self_service.stats_runtime import StatsRuntime


@pytest.mark.asyncio
async def test_renderer_can_progress_before_event_loop_yields():
    runtime = StatsRuntime()
    started, release = threading.Event(), threading.Event()
    context = ContextVar("render_submission_fixture", default="missing")
    context.set("copied")

    def render(run):
        assert context.get() == "copied"
        started.set()
        assert release.wait(5)
        return "image"

    try:
        run = runtime.submit("render", render, executor=runtime.renderer_executor())
        # Deliberately hold the event-loop thread. The old extra owner-task hop
        # prevented native entry until this wait ended and consumed the deadline.
        assert started.wait(3), "renderer was not submitted before the loop yielded"
        assert not run.task.done()
    finally:
        release.set()
        assert await runtime.drain()
    assert await run.task == "image"


@pytest.mark.asyncio
async def test_cancelled_unstarted_owners_keep_two_native_slots_and_drain():
    runtime = StatsRuntime()
    release = threading.Event()

    def render(run):
        assert release.wait(5)
        return "image"

    runs = []
    try:
        for _ in range(2):
            run = runtime.submit("render", render, executor=runtime.renderer_executor())
            runs.append(run)
            run.task.cancel()  # owner Task has never had an event-loop turn
        await asyncio.gather(*(run.task for run in runs), return_exceptions=True)
        assert len(runtime.jobs) == 2
        with pytest.raises(PersonalStatsUnavailable):
            runtime.submit("render", lambda run: pytest.fail("third render submitted"))
        draining = asyncio.create_task(runtime.drain())
        await asyncio.sleep(0)
        assert not draining.done()
        assert len(runtime.jobs) == 2
    finally:
        release.set()
        assert await runtime.drain()
        if "draining" in locals():
            assert await draining
    assert all(run.settled for run in runs)


@pytest.mark.asyncio
async def test_owner_task_creation_failure_does_not_abandon_submitted_render(monkeypatch):
    runtime = StatsRuntime()
    release = threading.Event()

    def render(run):
        assert release.wait(5)
        raise ValueError("fixture render failed")

    def reject_task(coroutine):
        raise RuntimeError("fixture task allocation failed")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(runtime.loop, "create_task", reject_task)
            with pytest.raises(RuntimeError, match="task allocation"):
                runtime.submit("render", render, executor=runtime.renderer_executor())
        assert len(runtime.jobs) == 1
        run = next(iter(runtime.jobs.values()))
        assert run.task is None
        draining = asyncio.create_task(runtime.drain())
        await asyncio.sleep(0)
        assert not draining.done()
    finally:
        release.set()
        assert await runtime.drain()
        if "draining" in locals():
            assert await draining
    assert run.settled and isinstance(run.error, ValueError)


@pytest.mark.asyncio
async def test_executor_rejection_releases_only_unsubmitted_reservation():
    runtime = StatsRuntime()

    class RejectedExecutor:
        def submit(self, *args, **kwargs):
            raise RuntimeError("fixture executor rejected")

    with pytest.raises(RuntimeError, match="executor rejected"):
        runtime.submit(
            "render", lambda run: pytest.fail("not submitted"), executor=RejectedExecutor()
        )
    assert not runtime.jobs
    assert await runtime.drain()
