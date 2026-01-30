import asyncio

import pytest

import proc_config_import as pci


@pytest.mark.asyncio
async def test_offload_cancellation_propagates(monkeypatch):
    """
    Ensure cancelling run_proc_config_import_offload cancels the underlying
    run_maintenance_with_isolation coroutine that the wrapper prefers.
    """
    cancelled_flag = {"called": False}

    async def fake_run_maintenance_with_isolation(callable_fn, *args, **kwargs):
        # Simulate a long-running offload that responds to cancellation by marking the flag
        try:
            # Wait indefinitely until cancelled
            await asyncio.Event().wait()
            # If it ever returns normally, return the expected result signature
            return await callable_fn(*args, **kwargs)
        except asyncio.CancelledError:
            cancelled_flag["called"] = True
            # Reraise so the wrapper sees cancellation
            raise

    # Inject fake run_maintenance_with_isolation into module so wrapper will use it
    monkeypatch.setattr(
        pci, "run_maintenance_with_isolation", fake_run_maintenance_with_isolation, raising=False
    )

    # Run the offload wrapper in a Task and cancel it shortly after
    task = asyncio.create_task(
        pci.run_proc_config_import_offload(dry_run=True, prefer_process=True, meta={"test": True})
    )
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        # expected
        pass

    # Give a small tick for the injected coroutine's cancellation handler to run
    await asyncio.sleep(0.01)

    assert (
        cancelled_flag["called"] is True
    ), "Expected the fake run_maintenance_with_isolation to receive cancellation"


def test_offload_uses_run_maintenance_with_isolation(monkeypatch):
    # Prepare fake result
    expected = (True, {"ok": True})

    async def fake_run_maintenance_with_isolation(
        fn, dry_run, name=None, prefer_process=True, meta=None
    ):
        # Mimic returning (result, meta) tuple
        return expected

    monkeypatch.setattr("proc_config_import.run_proc_config_import", lambda d: expected)
    monkeypatch.setattr(
        "proc_config_import.run_maintenance_with_isolation",
        fake_run_maintenance_with_isolation,
        raising=False,
    )

    # monkeypatch via module import path inside wrapper (already imported locally)
    # To ensure wrapper picks this up, we patch file_utils.run_maintenance_with_isolation inside the file_utils module path
    import file_utils

    monkeypatch.setattr(
        file_utils, "run_maintenance_with_isolation", fake_run_maintenance_with_isolation
    )

    import asyncio

    async def _run():
        return await pci.run_proc_config_import_offload(dry_run=False)

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(_run())
    assert isinstance(out, tuple)
    assert out == expected


def test_offload_fallback_to_to_thread(monkeypatch):
    # Ensure no offload helpers are available
    monkeypatch.setattr("proc_config_import.run_maintenance_with_isolation", None, raising=False)
    monkeypatch.setattr("proc_config_import.start_callable_offload", None, raising=False)
    monkeypatch.setattr("proc_config_import.run_blocking_in_thread", None, raising=False)

    # Replace the synchronous function to a simple known-return function
    def fake_sync(dry_run):
        return True, {"called": True}

    monkeypatch.setattr(pci, "run_proc_config_import", fake_sync)

    import asyncio

    async def _run():
        return await pci.run_proc_config_import_offload(dry_run=True)

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(_run())
    assert out[0] is True
    assert out[1]["called"] is True
