import pytest

from file_utils import list_offloads, run_maintenance_with_isolation

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_run_maintenance_with_isolation_timeout_and_registry():
    """
    Invoke a long-running test_sleep with a small timeout, expecting timeout.
    Ensure telemetry/registry contains an offload entry with pid and marked failed/completed.
    """
    ok, out = await run_maintenance_with_isolation(
        "test_sleep",
        args=["--seconds", "2.0"],
        timeout=0.2,
        name="test_sleep",
        meta={"test": True},
        prefer_process=True,
    )
    assert ok is False
    # Validate registry contains an offload with ok==False (timeout/failure) and a pid
    offs = list_offloads()
    assert isinstance(offs, list)
    # Find an entry for the test_sleep command
    found = False
    for o in reversed(offs):
        cmd = o.get("cmd") or []
        if any("test_sleep" in str(x) for x in cmd):
            found = True
            # pid should be present (the parent recorded it)
            assert o.get("pid") is not None
            # on timeout we mark completion as False
            assert o.get("ok") in (False, None)
            break
    assert found, "Expected offload registry to contain a test_sleep entry"
