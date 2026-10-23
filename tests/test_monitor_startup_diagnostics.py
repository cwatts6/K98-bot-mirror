import ast
import asyncio
from contextlib import contextmanager
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core import startup_diagnostics as startup
from services import recovery_health as health, recovery_runtime as runtime
from services.stats_import_outcome_dal import ImportExecutionActive


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(startup, "_steps", {})
    monkeypatch.setattr(health, "_checks", [])
    monkeypatch.setattr(health, "_cycle", None)


@pytest.mark.asyncio
async def test_deadline_drains_worker_without_retry_or_false_failure(caplog):
    finished = asyncio.Event()

    async def work():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            await asyncio.sleep(0.01)
            finished.set()
            raise

    await startup.run(work(), 0.001, "cache")
    assert finished.is_set()
    assert startup.report()[0]["state"] == "deadline_elapsed_outcome_unconfirmed"
    assert "deferring" not in caplog.text
    assert "does not establish failure" in caplog.text
    assert "drain finished" not in caplog.text


@pytest.mark.asyncio
async def test_startup_blocking_worker_is_drained_before_timeout_returns():
    # Exercise the actual startup helper without starting the Discord bot.
    source = Path(__file__).resolve().parents[1] / "bot_instance.py"
    definition = next(
        node
        for node in ast.parse(source.read_text(encoding="utf-8")).body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_blocking"
    )
    namespace = {}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(source), "exec"), namespace)
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()

    def worker():
        entered.set()
        release.wait(timeout=5)
        finished.set()

    task = asyncio.create_task(startup.run(namespace["run_blocking"](worker), 0.001, "cache"))
    try:
        for _ in range(100):
            if entered.is_set() and startup.report()[0]["state"] == "deadline_elapsed_draining":
                break
            await asyncio.sleep(0.001)
        assert entered.is_set()
        await asyncio.sleep(0.01)
        assert not task.done()
        assert not finished.is_set()
    finally:
        release.set()
        await task
    assert finished.is_set()
    assert startup.report()[0]["state"] == "deadline_elapsed_outcome_unconfirmed"


@pytest.mark.asyncio
async def test_completed_after_deadline_keeps_actual_result():
    async def work():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return "completed"

    assert await startup.run(work(), 0.001, "cache") == "completed"
    assert startup.report()[0]["state"] == "completed_after_deadline"


@pytest.mark.asyncio
async def test_worker_timeout_is_failure_not_wrapper_deadline():
    async def work():
        raise TimeoutError("password=private")

    await startup.run(work(), 10, "cache")
    row = startup.report()[0]
    assert row["state"] == "failed"
    assert row["diagnostic"]["frames"][-1]["function"] == "work"
    assert "password" not in str(row)


@pytest.mark.asyncio
async def test_shutdown_cancellation_drains_and_propagates():
    started, finished = asyncio.Event(), asyncio.Event()

    async def work():
        started.set()
        try:
            await asyncio.sleep(10)
        finally:
            await asyncio.sleep(0.01)
            finished.set()

    task = asyncio.create_task(startup.run(work(), 10, "cache"))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set()
    assert startup.report()[0]["state"] == "cancelled_outcome_unconfirmed"


@pytest.mark.parametrize("active", [True, False])
def test_existing_incident_distinguishes_busy_and_original_failure(monkeypatch, active):
    def refresh(_):
        if active:
            raise ImportExecutionActive("private input")
        raise ValueError("private input")

    store = SimpleNamespace(
        scope="scope",
        list_open=lambda **_: [dict(IncidentID="one", SourceKind="stats_import")],
        check_failed=Mock(),
        has_failed_checks=lambda: False,
    )
    adapter = SimpleNamespace(pending_recovery=lambda **_: [])

    @contextmanager
    def service():
        yield SimpleNamespace(
            store=store, adapters={"stats_import": adapter}, recover_automatic=refresh
        )

    monkeypatch.setattr(runtime, "recovery_service", service)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    health.begin_cycle()
    failures = runtime.observe_recovery()
    assert bool(failures) is not active
    assert store.check_failed.called is not active
    result = health.report()["checks"]
    assert result[0]["waiting"] is active
    assert result[0]["frames"][-1]["function"] == "refresh"
    assert "private input" not in str(result)
    # The aggregate wrapper cannot destroy the original check diagnostics.
    health.record_failure(RuntimeError()) if failures else health.record_success()
    assert health.report()["checks"] == result


def test_absent_successor_is_pending_only_after_parent_custody(tmp_path):
    from scripts.verify_k98_update_pair import PairPublicationPending, successor_path

    validate = Mock(side_effect=lambda path, **_: path)
    missing = tmp_path / "future.json"
    with pytest.raises(PairPublicationPending):
        successor_path(missing, validate=validate)
    validate.assert_called_once_with(tmp_path, private=True)
    validate.side_effect = PermissionError()
    with pytest.raises(PermissionError):
        successor_path(missing, validate=validate)
    existing = tmp_path / "present.json"
    existing.write_text("bad data")
    with pytest.raises(PermissionError):
        successor_path(existing, validate=validate)


def test_diagnostic_observations_are_bounded_and_detached():
    health.begin_cycle()
    for _ in range(130):
        health.record_check("check", ValueError())
    result = health.report()
    assert len(result["checks"]) == 100
    assert result["cycle"]["failed_checks"] == 130
    result["checks"][0]["frames"].append("modified")
    assert health.report()["checks"][0]["frames"] == []


def test_monitor_retains_driver_codes_without_private_prose():
    import pyodbc

    error = pyodbc.ProgrammingError("42000", "private SQL secret (1222)")
    health.begin_cycle()
    detail = health.record_check("existing_incident_checks:queue_admission", error)
    health.record_failure(RuntimeError("aggregate unavailable"))
    assert detail["sqlstates"] == ["42000"]
    assert detail["sql_numbers"] == [1222]
    assert health.report()["checks"][0] == detail
    assert "private SQL secret" not in str(health.report())
    assert not health.report()["healthy"]


def test_monitor_rechecks_persisted_failures_outside_rotating_page(monkeypatch):
    row = dict(IncidentID="failed", SourceKind="stats_import")
    failed = [row]
    seen = []

    def refresh(identifier):
        seen.append(identifier)
        failed.clear()  # Successful observation, not elapsed time, clears it.

    store = SimpleNamespace(
        scope="scope",
        list_open=lambda **kw: list(failed) if kw.get("failed_checks_only") else [],
        has_failed_checks=lambda: bool(failed),
        check_failed=Mock(),
    )

    @contextmanager
    def service():
        yield SimpleNamespace(
            store=store,
            adapters={"stats_import": SimpleNamespace(pending_recovery=lambda **_: [])},
            recover_automatic=refresh,
        )

    monkeypatch.setattr(runtime, "recovery_service", service)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    health.begin_cycle()
    assert runtime.observe_recovery() == []
    assert seen == ["failed"]
