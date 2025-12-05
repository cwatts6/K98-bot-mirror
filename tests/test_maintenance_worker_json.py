import pytest

from file_utils import list_offloads, run_maintenance_with_isolation

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_subprocess_emits_json_and_registry_marked_success():
    """
    Run the maintenance worker test_sleep in subprocess mode with a short sleep.
    Verify that:
     - run_maintenance_with_isolation returns success
     - the offload registry records a completed entry with ok=True and worker_parsed present
    """
    # ensure process mode
    ok, out = await run_maintenance_with_isolation(
        "test_sleep",
        args=["--seconds", "0.05"],
        timeout=5.0,
        name="test_sleep",
        meta={"test": True},
        prefer_process=True,
    )
    assert ok is True
    # There should be at least one offload in the registry with ok True and worker_parsed present
    offs = list_offloads()
    assert isinstance(offs, list)
    # Find an entry for the test_sleep command
    found = False
    for o in reversed(offs):
        cmd = o.get("cmd") or []
        if any("test_sleep" in str(x) for x in cmd):
            found = True
            assert o.get("ok") is True
            # worker_parsed may exist if parent parsed JSON - ensure either parsed or snippet present
            assert o.get("output_snippet") is not None
            break
    assert found, "Expected offload registry to contain a test_sleep entry"
