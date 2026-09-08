import ast
import asyncio
from pathlib import Path
import threading

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
