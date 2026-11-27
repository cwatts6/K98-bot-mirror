import ast
import asyncio
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

from player_self_service.stats_runtime import StatsRuntime


@pytest.mark.asyncio
@pytest.mark.parametrize("initialized", [False, True])
async def test_teardown_closes_first_use_stats_admission_before_drains(monkeypatch, initialized):
    from player_self_service import stats_runtime
    from services import upload_lifecycle

    monkeypatch.setattr(stats_runtime, "_runtime", StatsRuntime() if initialized else None)
    monkeypatch.setattr(upload_lifecycle, "close_admission", lambda: None)
    tree = ast.parse(Path("bot_instance.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if getattr(n, "name", None) == "_close_teardown_admission")
    namespace = dict(get_calendar_service=lambda: SimpleNamespace(close_admission=lambda: None))
    exec(compile(ast.Module(body=[node], type_ignores=[]), "bot_instance.py", "exec"), namespace)
    namespace["_close_teardown_admission"]()
    # Another component's drain may yield while the first Stats request arrives.
    await asyncio.sleep(0)
    runtime = stats_runtime.get_runtime()
    with pytest.raises(stats_runtime.PersonalStatsUnavailable):
        runtime.submit("dataset", lambda run: pytest.fail("Shutdown admitted native work"))
    assert runtime.closed and not runtime.jobs and runtime.render_executor is None
    assert await runtime.drain()


@pytest.mark.asyncio
async def test_repeated_teardown_preserves_first_failure():
    source = Path("bot_instance.py").read_text(encoding="utf-8")
    node = next(
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "_graceful_teardown"
    )
    calls = []
    failure = RuntimeError("cleanup unconfirmed")

    async def body():
        calls.append(1)
        raise failure

    namespace = dict(
        asyncio=asyncio,
        _teardown_task=None,
        _shutdown_once=asyncio.Event(),
        _perform_graceful_teardown=body,
        _close_teardown_admission=lambda: None,
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), "bot_instance.py", "exec"), namespace)
    for _ in range(3):
        with pytest.raises(RuntimeError) as caught:
            await namespace["_graceful_teardown"]()
        assert caught.value is failure
    assert calls == [1]


def test_installed_pycord_global_cancellation_waits_for_native_settlement():
    # Actual installed library cleanup, in a child process so pytest is never
    # included in its all_tasks cancellation set. No Discord client is created.
    script = """
import asyncio, threading, time
from discord.client import _cancel_tasks
from core.owned_work import drain_thread
loop = asyncio.new_event_loop()
started, released, finished = threading.Event(), threading.Event(), threading.Event()
def work():
    started.set()
    assert released.wait(4)
    finished.set()
task = loop.create_task(drain_thread(work))
async def enter():
    while not started.is_set(): await asyncio.sleep(.001)
loop.run_until_complete(enter())
timer = threading.Timer(.2, released.set)
timer.start()
began = time.monotonic()
_cancel_tasks(loop)
assert finished.is_set() and task.cancelled()
assert time.monotonic() - began >= .15
timer.join()
loop.run_until_complete(loop.shutdown_default_executor())
loop.close()
print("native settled before installed Pycord cleanup returned")
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], capture_output=True, text=True, timeout=12
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "native settled" in result.stdout


def test_pycord_global_cancellation_drains_owned_render_future():
    script = """
import asyncio, threading
from discord.client import _cancel_tasks
from player_self_service.stats_runtime import StatsRuntime
loop = asyncio.new_event_loop()
entered, release, finished = threading.Event(), threading.Event(), threading.Event()
def render(run):
    entered.set()
    assert release.wait(4)
    finished.set()
    return 'image'
async def setup():
    runtime = StatsRuntime()
    run = runtime.submit('render', render, executor=runtime.renderer_executor())
    while not entered.is_set(): await asyncio.sleep(0)
    await asyncio.sleep(0)
    return runtime, run
runtime, run = loop.run_until_complete(setup())
timer = threading.Timer(.1, release.set)
timer.start()
try:
    _cancel_tasks(loop)
    assert finished.is_set()
    assert run.task.cancelled() and not run.native_future.cancelled()
    assert run.settled and not runtime.jobs
    assert loop.run_until_complete(runtime.drain())
finally:
    release.set()
    timer.join()
    loop.run_until_complete(runtime.drain())
    loop.run_until_complete(loop.shutdown_default_executor())
    loop.close()
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], capture_output=True, text=True, timeout=12
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.asyncio
async def test_drain_cancellation_does_not_release_blocked_read_or_renderer():
    runtime = StatsRuntime()
    release = threading.Event()
    entered = threading.Event()

    def work(run):
        entered.set()
        assert release.wait(4)

    runtime.submit("dataset", work)
    runtime.submit("render", work, executor=runtime.renderer_executor())
    drain = asyncio.create_task(runtime.drain())
    try:
        # Render submission is now synchronous; its entry event no longer proves
        # that the drain Task has received its first turn. Test cancellation of
        # an entered drain, rather than cancelling an unstarted coroutine.
        await asyncio.sleep(0)
        async with asyncio.timeout(2):
            while not entered.is_set():
                await asyncio.sleep(0.001)
        for _ in range(3):
            drain.cancel()
            await asyncio.sleep(0.005)
            assert not drain.done()
            assert runtime.closed and len(runtime.jobs) == 2
    finally:
        release.set()
        await asyncio.gather(drain, return_exceptions=True)
    assert not runtime.jobs
    assert await runtime.drain()


@pytest.mark.asyncio
async def test_signal_drain_failure_does_not_close_client_or_logging():
    tree = ast.parse(Path("DL_bot.py").read_text(encoding="utf-8"))
    node = next(
        n
        for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "_graceful_shutdown"
    )
    calls = []

    async def markers(**kwargs):
        calls.append("markers")

    async def quiesce():
        raise RuntimeError("unconfirmed")

    namespace = dict(
        _write_shutdown_markers=markers,
        _quiesce_background_tasks=quiesce,
        flush_logs=lambda: calls.append("flush"),
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), "DL_bot.py", "exec"), namespace)
    with pytest.raises(RuntimeError, match="unconfirmed"):
        await namespace["_graceful_shutdown"]()
    assert calls == ["markers"]
