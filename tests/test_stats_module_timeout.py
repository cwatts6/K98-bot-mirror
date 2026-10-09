# tests/test_stats_module_timeout.py
import asyncio
import json
import logging

import pytest

# Import the module under test
import stats_module as sm


@pytest.mark.asyncio
async def test_coordinated_timeout_waits_for_actual_sql_thread():
    from threading import Event

    from services.legacy_export_snapshot_service import use_runtime

    started, release = Event(), Event()

    def producer():
        started.set()
        assert release.wait(5)

    async def invoke():
        with use_runtime(object()):
            await asyncio.wait_for(sm._offload_callable_py(producer), timeout=0.03)

    task = asyncio.create_task(invoke())
    assert await asyncio.to_thread(started.wait, 5)
    await asyncio.sleep(0.06)
    assert not task.done()
    release.set()
    with pytest.raises(TimeoutError):
        await task


COMPLETED_FILENAME = "stats_0123456789abcdef0123456789abcdef.ready.csv"


@pytest.mark.asyncio
@pytest.mark.parametrize("setting_fails", [False, True])
async def test_import_sets_connection_timeout_before_cursor(monkeypatch, setting_fails):
    from core import export_sql_connection
    from services import legacy_export_snapshot_service

    events = []

    class Cursor:
        __slots__ = ()  # A real pyodbc cursor has no writable timeout attribute.

    class Connection:
        autocommit = False
        _timeout = 15

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        @property
        def timeout(self):
            return self._timeout

        @timeout.setter
        def timeout(self, value):
            events.append(("timeout", value))
            if setting_fails:
                raise RuntimeError("timeout configuration refused")
            self._timeout = value

        def cursor(self):
            events.append(("cursor", self.timeout))
            return Cursor()

    connection = Connection()
    monkeypatch.setattr(export_sql_connection, "producer_connection", lambda _: connection)
    monkeypatch.setattr(legacy_export_snapshot_service, "admitted_writer", lambda _: lambda f: f)
    monkeypatch.setattr(legacy_export_snapshot_service, "verify_producer_cursor", lambda _: None)

    def before_procedure(*args):
        events.append(("counter", connection.timeout))
        raise RuntimeError("stop before executing import")

    monkeypatch.setattr(sm, "fetch_update_all2_last_counter", before_procedure)
    monkeypatch.setattr(sm, "_fetch_immutable_import_outcome", lambda _: None)
    with legacy_export_snapshot_service.use_runtime(object()):
        ok, _, _ = await sm.run_sql_procedure(
            rank=1590, seed="C", completed_filename=COMPLETED_FILENAME, timeout_seconds=600
        )
    assert not ok
    assert events == (
        [("timeout", 595)]
        if setting_fails
        else [("timeout", 595), ("cursor", 595), ("counter", 595)]
    )


@pytest.mark.skip(reason="Integration test requiring live DB — not suitable for unit test suite")
@pytest.mark.asyncio
async def test_run_sql_procedure_timeout_emits_telemetry(caplog):
    """
    Simulate a wait_for timeout in run_sql_procedure by patching stats_module.asyncio.to_thread
    with a coroutine that sleeps longer than the provided timeout_seconds.

    Asserts:
      - function returns a timeout-style result (ok False, message contains TIMEOUT)
      - a telemetry event was emitted to the "telemetry" logger indicating a timeout
      - telemetry payload contains 'event': 'sql_proc', 'status': 'timeout', and orphaned_offload_possible True
    """
    # Capture telemetry logger messages
    caplog.set_level(logging.INFO, logger="telemetry")

    # Backup original to_thread and replace with a fake that hangs longer than the timeout
    original_to_thread = sm.asyncio.to_thread

    async def fake_to_thread(fn, *args, **kwargs):
        # Simulate a long-running worker that will not complete within the wait_for window.
        # We await here so that asyncio.wait_for(...) in the production code sees a timeout.
        await asyncio.sleep(0.2)
        # If it ever completes, return a placeholder (not expected)
        return None

    sm.asyncio.to_thread = fake_to_thread

    try:
        # Use a very small timeout so the fake_to_thread will cause asyncio.TimeoutError
        ok, msg, extra = await sm.run_sql_procedure(
            rank=1,
            seed=2,
            completed_filename=COMPLETED_FILENAME,
            timeout_seconds=0.05,
        )

        # Ensure the call returned a timeout-style failure
        assert ok is False, "Expected run_sql_procedure to report failure on timeout"
        assert isinstance(msg, str) and "TIMEOUT" in msg.upper()

        # Find telemetry record
        telemetry_records = [r for r in caplog.records if r.name == "telemetry"]
        assert telemetry_records, "No telemetry records emitted"

        # Look for sql_proc timeout payload
        found = False
        for rec in telemetry_records:
            text = rec.getMessage()
            # telemetry logger writes JSON strings in the codebase; try to parse
            try:
                payload = json.loads(text)
            except Exception:
                continue
            if payload.get("event") == "sql_proc" and payload.get("status") == "timeout":
                assert payload.get("orphaned_offload_possible") is True
                found = True
                break

        assert found, "Expected telemetry sql_proc timeout event not found"
    finally:
        # restore original helper
        sm.asyncio.to_thread = original_to_thread
