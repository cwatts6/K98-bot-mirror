# tests/test_maintenance_fallback.py
"""Unit test to ensure run_maintenance_with_isolation falls back to thread
when given a nested (non-importable) callable and does not spawn a subprocess.
"""


import pytest

# Import the function under test
from file_utils import run_maintenance_with_isolation  # type: ignore


@pytest.mark.asyncio
async def test_fallback_for_nested_callable(monkeypatch):
    events = []

    # Capture telemetry events emitted by file_utils.emit_telemetry_event
    def _capture_event(payload, *, max_snippet: int = 2000):
        events.append(payload)

    monkeypatch.setattr("file_utils.emit_telemetry_event", _capture_event)

    # Create a nested/local function which is NOT a module-level attribute
    def make_nested():
        def _inner():
            return "ran-in-thread"

        return _inner

    nested_fn = make_nested()

    # Also ensure subprocess creation would error if attempted (defensive)
    async def _fail_create(*args, **kwargs):
        raise AssertionError("create_subprocess_exec should not be called during fallback")

    monkeypatch.setattr("asyncio.create_subprocess_exec", _fail_create)

    # Run the maintenance wrapper with prefer_process=True so validation runs
    ok, result = await run_maintenance_with_isolation(
        nested_fn,
        args=None,
        kwargs=None,
        timeout=5,
        name="test_nested",
        meta={"test": True},
        prefer_process=True,
    )

    # Expect fallback to thread and the callable to have executed
    assert ok is True, "Expected threaded execution to succeed"
    # result should contain the callable return value or its repr
    assert "ran-in-thread" in str(result)

    # Ensure telemetry includes the fallback marker
    found_fallback = any(
        e.get("event") == "maintenance_run.fallback_non_importable" for e in events
    )
    assert (
        found_fallback
    ), "Expected telemetry event 'maintenance_run.fallback_non_importable' to be emitted"
