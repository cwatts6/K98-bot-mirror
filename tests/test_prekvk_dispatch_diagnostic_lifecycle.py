import ast
import asyncio
import builtins
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from test_prekvk_dispatch_diagnostics import Channel, harness as harness, run

from stats_alerts import dispatch_reservations
from stats_alerts.diagnostics import DiagnosticRunner
from stats_alerts.dispatch_reservations import DispatchUnavailable


@pytest.mark.asyncio
async def test_shutdown_drains_once_only_persistence_and_rejects_new_work(harness, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = []
    original = dispatch_reservations.ReservationStore.accept

    def slow_accept(store, *args):
        calls.append(args)
        started.set()
        assert release.wait(5)
        return original(store, *args)

    monkeypatch.setattr(dispatch_reservations.ReservationStore, "accept", slow_accept)
    runner = DiagnosticRunner()
    task = asyncio.create_task(run(harness, Channel(), runner=runner))
    async with asyncio.timeout(5):
        while not started.is_set():
            await asyncio.sleep(0.001)
    shutdown = asyncio.create_task(runner.shutdown())
    await asyncio.sleep(0.01)
    assert not shutdown.done()  # Event loop is responsive while the worker is draining.
    with pytest.raises(DispatchUnavailable):
        await run(harness, Channel(), runner=runner)
    release.set()
    await asyncio.wait_for(shutdown, 5)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(calls) == 1
    assert runner.active is None


@pytest.mark.asyncio
async def test_busy_rejection_does_not_allocate_second_session(harness):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def publish(session, receipt):
        entered.set()
        await release.wait()
        raise ValueError("known not delivered")

    runner = DiagnosticRunner()
    task = asyncio.create_task(run(harness, Channel(), runner=runner, publish=publish))
    await asyncio.wait_for(entered.wait(), 5)
    with pytest.raises(DispatchUnavailable):
        await run(harness, Channel(), runner=runner)
    assert len(list(harness.root.glob("*/*/*/session.json"))) == 1
    release.set()
    assert (await task).outcome == "failed"


def test_teardown_drains_diagnostics_before_other_teardown():
    tree = ast.parse(Path("bot_instance.py").read_text(encoding="utf-8"))
    teardown = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_graceful_teardown"
    )
    source = ast.unparse(teardown)
    assert source.index("await prekvk_diagnostic_runner.shutdown()") < source.index(
        "await task_monitor.stop()"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["import", "shutdown"])
async def test_diagnostic_failure_does_not_skip_remaining_teardown(failure):
    tree = ast.parse(Path("bot_instance.py").read_text(encoding="utf-8"))
    teardown = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_graceful_teardown"
    )
    diagnostic = SimpleNamespace(
        runner=SimpleNamespace(
            shutdown=AsyncMock(side_effect=RuntimeError("diagnostic shutdown failed"))
        )
    )
    reminders = SimpleNamespace(cancel_all_and_wait=AsyncMock(return_value=0))

    def controlled_import(name, *args, **kwargs):
        if name == "stats_alerts.diagnostics":
            if failure == "import":
                raise ImportError("diagnostic module unavailable")
            return diagnostic
        if name == "reminder_task_registry":
            return reminders
        return builtins.__import__(name, *args, **kwargs)

    tracker = SimpleNamespace(stop=AsyncMock())
    namespace = {
        "__builtins__": {**vars(builtins), "__import__": controlled_import},
        "_shutdown_once": asyncio.Event(),
        "logger": Mock(),
        "daily_summary": Mock(),
        "refresh_event_cache_task": Mock(),
        "_drain_shutdown_queues": AsyncMock(),
        "_flush_live_queue_state": AsyncMock(),
        "task_monitor": SimpleNamespace(stop=AsyncMock(), list=lambda: []),
        "_atomic_json_write": Mock(),
        "os": __import__("os"),
        "LOG_DIR": "unused",
        "_aware": lambda value: value,
        "utcnow": lambda: SimpleNamespace(isoformat=lambda: "2026-09-08T00:00:00+00:00"),
        "usage_tracker": lambda: tracker,
        "quiesce_logging": Mock(),
    }
    exec(
        compile(ast.Module(body=[teardown], type_ignores=[]), "bot_instance.py", "exec"), namespace
    )
    await namespace["_graceful_teardown"]()
    namespace["logger"].exception.assert_called_once_with(
        "[SHUTDOWN] Failed draining Pre-KVK diagnostics; preserve session evidence."
    )
    namespace["daily_summary"].stop.assert_called_once()
    namespace["refresh_event_cache_task"].stop.assert_called_once()
    namespace["_drain_shutdown_queues"].assert_awaited_once()
    namespace["_flush_live_queue_state"].assert_awaited_once()
    namespace["task_monitor"].stop.assert_awaited_once()
    reminders.cancel_all_and_wait.assert_awaited_once()
    namespace["_atomic_json_write"].assert_called_once()
    tracker.stop.assert_awaited_once()
    namespace["quiesce_logging"].assert_called_once()
