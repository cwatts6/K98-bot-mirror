# tests/test_stats_module_cancelled.py
import asyncio
import json
import logging

import pytest

# Import the module under test
import stats_module as sm


@pytest.mark.asyncio
async def test_run_sql_procedure_cancelled_propagates(caplog):
    """
    Simulate asyncio.CancelledError in run_sql_procedure by patching stats_module.asyncio.to_thread
    to immediately raise CancelledError when awaited.

    Asserts:
      - run_sql_procedure re-raises asyncio.CancelledError (propagates cancellation)
      - no telemetry "sql_proc" timeout/failed event was emitted (cancellation path should not emit the same telemetry)
    """
    # Capture telemetry logger messages
    caplog.set_level(logging.INFO, logger="telemetry")

    # Backup original to_thread and replace with a fake that raises CancelledError
    original_to_thread = sm.asyncio.to_thread

    async def fake_to_thread(fn, *args, **kwargs):
        raise asyncio.CancelledError()

    sm.asyncio.to_thread = fake_to_thread

    try:
        with pytest.raises(asyncio.CancelledError):
            await sm.run_sql_procedure(rank=1, seed=2, timeout_seconds=0.5)

        # Ensure no telemetry sql_proc timeout/failed payload was emitted
        telemetry_records = [r for r in caplog.records if r.name == "telemetry"]
        for rec in telemetry_records:
            try:
                payload = json.loads(rec.getMessage())
            except Exception:
                continue
            # Fail the test if any sql_proc event was recorded (timeout/failed)
            assert payload.get("event") != "sql_proc"
    finally:
        # restore original helper
        sm.asyncio.to_thread = original_to_thread
