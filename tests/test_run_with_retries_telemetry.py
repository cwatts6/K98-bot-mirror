# tests/test_run_with_retries_telemetry.py
import json
import logging

import pytest

from file_utils import run_with_retries


@pytest.mark.asyncio
async def test_run_with_retries_emits_telemetry(caplog):
    caplog.set_level(logging.INFO, logger="telemetry")

    state = {"calls": 0}

    def flaky(x):
        state["calls"] += 1
        if state["calls"] == 1:
            raise TimeoutError("simulated-lock")
        return f"ok:{x}"

    res = await run_with_retries(
        flaky, "v", retries=2, base_backoff=0.01, max_backoff=0.02, retry_exceptions=(TimeoutError,)
    )
    assert res == "ok:v"

    # Check that telemetry logger captured a retry_attempt info record
    found = False
    for rec in caplog.records:
        if rec.name == "telemetry" and "retry_attempt" in rec.getMessage():
            # try parse JSON
            try:
                payload = json.loads(rec.getMessage())
                if payload.get("event") == "retry_attempt" and payload.get("func") == "flaky":
                    found = True
                    break
            except Exception:
                continue
    assert found, "Expected telemetry retry_attempt event logged"
