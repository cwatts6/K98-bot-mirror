# tests/test_stats_module_timeout.py
import asyncio
import json
import logging

import pytest

# Import the module under test
import stats_module as sm


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
        ok, msg, extra = await sm.run_sql_procedure(rank=1, seed=2, timeout_seconds=0.05)

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
