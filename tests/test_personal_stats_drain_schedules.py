"""Bounded D5a.1 investigation; no runtime repair or external/native SQL work.

Each schedule runs once in a child process. Use -x for the approved investigation:
the first failed invariant stops the remaining schedules, including focused suites.
The controlled-ready schedule uses real executor futures and normal callbacks;
only the release of the second inert worker is coordinated with drain wakeup.
"""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

CASES = (
    "01_normal_first_second",
    "02_normal_second_first",
    "03_ready_before_settlement",
    "04_held_reverse_settlement",
    "05_both_done_callbacks_held",
    "06_concurrent_drain_a_first",
    "07_concurrent_drain_b_first",
    "08_one_error_one_active",
    "09_repeated_drain_cancel",
    "10_task_allocation_failure",
    "11_executor_rejection",
    "12_shutdown_failure",
)


class _Probe:
    """Finite, process-local event trace; never an operational logger."""

    def __init__(self, case):
        self.case = case
        self.events = []
        self.lock = threading.Lock()
        self.began = time.monotonic()

    def record(self, event, **facts):
        with self.lock:
            assert len(self.events) < 300, "trace event bound exceeded"
            self.events.append(
                dict(
                    sequence=len(self.events),
                    seconds=round(time.monotonic() - self.began, 6),
                    event=event,
                    thread=threading.current_thread().name,
                    **facts,
                )
            )

    def dump(self):
        value = json.dumps(dict(case=self.case, pid=os.getpid(), events=self.events))
        assert len(value.encode()) <= 65536, "per-case trace bound exceeded"
        print(value, flush=True)


async def _schedule(case, probe):
    from player_self_service.stats_models import PersonalStatsUnavailable
    from player_self_service.stats_runtime import StatsRuntime

    loop = asyncio.get_running_loop()
    runtime = StatsRuntime()
    probe.record("case_enter", loop=id(loop))
    release = [threading.Event(), threading.Event()]
    entered = [threading.Event(), threading.Event()]
    native_done = [threading.Event(), threading.Event()]
    runs, physical, drains, held = [], [], [], []
    scheduled_ready = False
    original_soon = loop.call_soon
    original_settle = runtime._settle
    executor = runtime.renderer_executor()
    original_submit = executor.submit
    original_shutdown = executor.shutdown

    def state():
        return dict(
            jobs=len(runtime.jobs),
            native_done=[f.done() for f in physical],
            async_done=[r.native_future.done() for r in runs],
            settled=[r.settled for r in runs],
        )

    def submit(*args, **kwargs):
        future = original_submit(*args, **kwargs)
        physical.append(future)
        return future

    def settle(run, publish):
        probe.record("settlement_enter", job=runs.index(run) if run in runs else -1, **state())
        original_settle(run, publish)
        probe.record("settlement_return", **state())

    def shutdown(*args, **kwargs):
        probe.record("executor_shutdown_enter", **state())
        if case == CASES[11]:
            raise RuntimeError("injected executor shutdown failure")
        result = original_shutdown(*args, **kwargs)
        probe.record("executor_shutdown_return", **state())
        return result

    def soon(callback, *args, context=None):
        nonlocal scheduled_ready
        name = getattr(callback, "__qualname__", type(callback).__name__)
        if name.endswith("render_completed"):
            probe.record("settlement_callback_queued", **state())
            if case in (CASES[3], CASES[4]):
                # Explicit artificial callback hold; not evidence of natural cause.
                def retain():
                    held.append((callback, args, context))
                    probe.record("synthetic_callback_hold", **state())

                return original_soon(retain, context=context)
        target = getattr(callback, "__self__", None)
        if case == CASES[2] and drains and target is drains[0] and not scheduled_ready:
            scheduled_ready = True
            probe.record("before_first_drain_wakeup", **state())
            release[1].set()
            # Registered after asyncio's chain callback: acknowledgment means
            # normal _set_state is queued, not just that a worker returned.
            assert native_done[1].wait(3), "second native completion not acknowledged"
            probe.record("second_state_queued_before_drain_wakeup", **state())
        return original_soon(callback, *args, context=context)

    executor.submit = submit
    executor.shutdown = shutdown
    runtime._settle = settle
    loop.call_soon = soon

    def work(index):
        def render(run):
            probe.record("thread_enter", job=index)
            entered[index].set()
            assert release[index].wait(5), "inert render release guard expired"
            probe.record("thread_return", job=index)
            if case == CASES[7] and index == 0:
                raise ValueError("injected render error")
            return f"inert-image-{index}"

        return render

    def start(index):
        probe.record("submit", job=index)
        run = runtime.submit("render", work(index), executor=executor)
        runs.append(run)
        physical[-1].add_done_callback(lambda f: native_done[index].set())
        run.task.cancel()
        probe.record("owner_cancel_before_first_turn", job=index)
        return run

    async def drain(label):
        probe.record("drain_enter", label=label, **state())
        value = await runtime.drain()
        probe.record("drain_return", label=label, result=value, **state())
        return value

    def start_drain(label):
        task = asyncio.create_task(drain(label))
        drains.append(task)
        return task

    async def completed(index):
        async with asyncio.timeout(3):
            while not native_done[index].is_set():
                await asyncio.sleep(0.001)
        # Yield to normal future completion/settlement callbacks.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    def release_callbacks():
        # Release this harness's artificial holds, never runtime ownership.
        for callback, args, context in held:
            original_soon(callback, *args, context=context)
        held.clear()

    try:
        if case == CASES[10]:

            def reject(*args, **kwargs):
                raise RuntimeError("injected executor rejection")

            executor.submit = reject
            with pytest.raises(RuntimeError, match="executor rejection"):
                runtime.submit("render", work(0), executor=executor)
            assert not runtime.jobs and not physical
            assert await drain("rejected")
            return

        if case == CASES[9]:
            original_create = loop.create_task

            def reject_task(coroutine, **kwargs):
                raise RuntimeError("injected task allocation failure")

            loop.create_task = reject_task
            try:
                with pytest.raises(RuntimeError, match="task allocation failure"):
                    runtime.submit("render", work(0), executor=executor)
            finally:
                loop.create_task = original_create
            run = next(iter(runtime.jobs.values()))
            runs.append(run)
            physical[0].add_done_callback(lambda f: native_done[0].set())
            assert run.task is None and not run.settled
            task = start_drain("allocation_failed")
            await asyncio.sleep(0)
            assert not task.done() and len(runtime.jobs) == 1
            release[0].set()
            assert await task
            return

        for index in range(2):
            start(index)
        assert all(event.wait(3) for event in entered), "native worker did not enter"
        await asyncio.gather(*(r.task for r in runs), return_exceptions=True)
        assert len(runtime.jobs) == 2 and not any(r.settled for r in runs)
        with pytest.raises(PersonalStatsUnavailable):
            runtime.submit("render", lambda run: pytest.fail("third render entered"))
        probe.record("third_render_refused", **state())

        if case == CASES[4]:
            for event in release:
                event.set()
            await completed(0)
            await completed(1)
            assert all(r.native_future.done() for r in runs) and len(held) == 2
            task = start_drain("both_done")
            await asyncio.sleep(0)
            assert not task.done() and len(runtime.jobs) == 2
            probe.record("drain_waits_for_held_callbacks", **state())
            release_callbacks()
            assert await task
            return

        first, second = (1, 0) if case in (CASES[1], CASES[3]) else (0, 1)
        labels = ("B", "A") if case == CASES[6] else ("A", "B")
        start_drain(labels[0])
        if case in (CASES[2], CASES[5], CASES[6]):
            start_drain(labels[1])
        await asyncio.sleep(0)
        assert all(not task.done() for task in drains)
        if case == CASES[8]:
            for _ in range(3):
                drains[0].cancel()
                await asyncio.sleep(0)
                assert not drains[0].done() and len(runtime.jobs) == 2
                assert all(not r.native_future.cancelled() for r in runs)
        release[first].set()
        if case == CASES[2]:
            results = await asyncio.gather(*drains)
            assert scheduled_ready, "controlled-ready ordering was not reached"
        else:
            await completed(first)
            if case == CASES[7]:
                assert isinstance(runs[0].error, ValueError)
                assert id(runs[1]) in runtime.jobs and not physical[1].done()
            release[second].set()
            if case == CASES[3]:
                await completed(second)
                assert len(held) == 2 and all(not task.done() for task in drains)
                probe.record("drain_waits_for_held_callbacks", **state())
                release_callbacks()
            if case == CASES[11]:
                with pytest.raises(RuntimeError, match="executor shutdown failure"):
                    await drains[0]
                probe.record("shutdown_failure_propagated", **state())
                return
            results = await asyncio.gather(*drains)
        probe.record("observed_results", results=results, **state())
        assert all(results), "physically completed renders returned false drain"
        assert not runtime.jobs and all(r.settled for r in runs)
    finally:
        # Restore instrumentation, release only our barriers, execute retained
        # callbacks and join actual workers. Never clear a jobs/hold registry.
        loop.call_soon = original_soon
        executor.submit = original_submit
        executor.shutdown = original_shutdown
        for event in release:
            event.set()
        release_callbacks()
        await asyncio.gather(*drains, return_exceptions=True)
        await asyncio.gather(*(r.task for r in runs if r.task), return_exceptions=True)
        await asyncio.gather(*(r.native_future for r in runs), return_exceptions=True)
        await asyncio.sleep(0)
        cleanup = await runtime.drain()
        # Joining a completed test executor also proves every worker exited.
        assert cleanup and not runtime.jobs
        assert all(f.done() for f in physical)
        probe.record("cleanup_confirmed", **state())


def _child(case):
    assert case in CASES
    probe = _Probe(case)
    try:
        asyncio.run(_schedule(case, probe))
    finally:
        probe.dump()


@pytest.mark.parametrize("case", CASES)
@pytest.mark.skipif(
    os.getenv("K98_D5_DRAIN_SCHEDULES") != "1",
    reason="bounded D5a.1 investigation requires its explicit run envelope",
)
def test_bounded_drain_schedule(case):
    # Argument list only; no shell, SQL, network client or operational file.
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import sys; from tests.test_personal_stats_drain_schedules import _child; "
            "_child(sys.argv[1])",
            case,
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=12,
    )
    print(result.stdout, end="")
    assert result.returncode == 0, result.stderr
