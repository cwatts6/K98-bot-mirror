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


@pytest.mark.asyncio
async def test_offload_uses_run_maintenance_with_isolation(monkeypatch):
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

    out = await pci.run_proc_config_import_offload(dry_run=False)
    assert isinstance(out, tuple)
    assert out == expected


@pytest.mark.asyncio
async def test_offload_fallback_to_to_thread(monkeypatch):
    # Ensure no offload helpers are available
    monkeypatch.setattr("proc_config_import.run_maintenance_with_isolation", None, raising=False)
    monkeypatch.setattr("proc_config_import.start_callable_offload", None, raising=False)
    monkeypatch.setattr("proc_config_import.run_blocking_in_thread", None, raising=False)

    # Replace the synchronous function to a simple known-return function
    def fake_sync(dry_run):
        return True, {"called": True}

    monkeypatch.setattr(pci, "run_proc_config_import", fake_sync)

    out = await pci.run_proc_config_import_offload(dry_run=True)
    assert out[0] is True
    assert out[1]["called"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["isolation_process", "thread", "asyncio"])
async def test_offload_forwards_source_audit_context(monkeypatch, path):
    from unittest.mock import Mock

    actor = "discord:123"
    provenance = {"trigger": "ops.import_proc_config", "guild_id": "456"}
    target = Mock(return_value=(True, {}))
    monkeypatch.setattr(pci, "run_proc_config_import", target)
    for helper in (
        "run_maintenance_with_isolation",
        "start_callable_offload",
        "run_blocking_in_thread",
    ):
        monkeypatch.setattr(pci, helper, None, raising=False)

    async def isolation(fn, args, **options):
        assert args == [dict(dry_run=False, source_actor=actor, source_provenance=provenance)]
        assert options["prefer_process"]
        result = fn(*args)
        return list(result), {"result": list(result)}

    async def thread(fn, *args, name, meta, **kwargs):
        return fn(*args, **kwargs)

    if path.startswith("isolation"):
        monkeypatch.setattr(pci, "run_maintenance_with_isolation", isolation)
    elif path == "thread":
        monkeypatch.setattr(pci, "run_blocking_in_thread", thread)
    assert await pci.run_proc_config_import_offload(
        prefer_process=path == "isolation_process", source_actor=actor, source_provenance=provenance
    ) == (True, {})
    if path == "isolation_process":
        target.assert_called_once_with(
            dry_run=False, source_actor=actor, source_provenance=provenance
        )
    else:
        target.assert_called_once_with(False, source_actor=actor, source_provenance=provenance)


@pytest.mark.asyncio
async def test_real_worker_payload_preserves_audit_and_failed_import(monkeypatch, tmp_path):
    from unittest.mock import Mock

    import file_utils
    import maintenance_worker

    target = Mock(return_value=(False, {"success": False, "errors": ["synthetic"]}))
    monkeypatch.setattr(pci, "run_proc_config_import", target)
    # Other worker tests reload this module with a fake normalizer; restore the real
    # imported dependency for this integration test without changing shared code.
    monkeypatch.setattr(
        maintenance_worker,
        "normalize_args_for_maintenance",
        file_utils.normalize_args_for_maintenance,
    )
    monkeypatch.setenv("MAINT_SPEC_ALLOWLIST", "proc_config_import:run_proc_config_import_payload")
    monkeypatch.setenv("MAINT_ALLOW_ALL", "0")
    received = []
    monkeypatch.setattr(
        maintenance_worker, "_print_result_json", lambda *a, **kw: received.append(kw)
    )
    payload = dict(dry_run=True, source_actor="discord:123", source_provenance={"trigger": "test"})
    tokens, paths = file_utils.serialize_args_for_subprocess([payload], tmp_dir=str(tmp_path))
    assert (
        maintenance_worker.run_callable_spec(
            "proc_config_import:run_proc_config_import_payload", tokens
        )
        == 0
    )
    target.assert_called_once_with(**payload)
    result = received[-1]["result"]

    async def subprocess(*args, **kwargs):
        assert kwargs["kwargs"] is None
        return list(result), {"result": list(result)}

    monkeypatch.setattr(file_utils, "run_maintenance_subprocess", subprocess)
    monkeypatch.setattr(
        pci,
        "run_maintenance_with_isolation",
        file_utils.run_maintenance_with_isolation,
        raising=False,
    )
    assert (
        await pci.run_proc_config_import_offload(
            dry_run=True, source_actor="discord:123", source_provenance={"trigger": "test"}
        )
        == result
    )


@pytest.mark.asyncio
async def test_explicit_thread_bypasses_lossy_maintenance_special_case(monkeypatch):
    from unittest.mock import Mock

    import file_utils

    target = Mock(return_value=(True, {}))
    monkeypatch.setattr(pci, "run_proc_config_import", target)
    monkeypatch.setattr(
        pci,
        "run_maintenance_with_isolation",
        Mock(side_effect=AssertionError("lossy path")),
        raising=False,
    )
    monkeypatch.setattr(
        pci, "run_blocking_in_thread", file_utils.run_blocking_in_thread, raising=False
    )
    assert await pci.run_proc_config_import_offload(
        dry_run=True, prefer_process=False, source_actor="discord:123"
    ) == (True, {})
    target.assert_called_once_with(True, source_actor="discord:123")


@pytest.mark.asyncio
@pytest.mark.parametrize("success", [True, False])
async def test_large_process_report_survives_real_worker_emission(monkeypatch, capfd, success):
    import json

    import file_utils
    import maintenance_worker

    report = {
        "success": success,
        "tables": [{"rows": 100, "detail": "synthetic" * 300}] * 8,
        "errors": [] if success else ["failure" * 1000],
        "manifest_path": "synthetic-report.json",
    }
    monkeypatch.setattr(pci, "run_proc_config_import", lambda **kw: (success, report))
    monkeypatch.setattr(maintenance_worker, "_MAX_RESULT_SNIPPET", 1000)
    result = pci.run_proc_config_import_payload({"dry_run": True})
    maintenance_worker._print_result_json(
        "proc_config_import:run_proc_config_import_payload", "success", result=result
    )
    emitted = json.loads(capfd.readouterr().out.strip().splitlines()[-1])
    assert "result_summary" not in emitted
    assert emitted["result"][0] is success
    assert emitted["result"][1]["manifest_path"] == "synthetic-report.json"
    assert len(json.dumps(emitted["result"])) <= 900

    async def subprocess(*args, **kwargs):
        return emitted["result"], emitted

    monkeypatch.setattr(file_utils, "run_maintenance_subprocess", subprocess)
    monkeypatch.setattr(
        pci,
        "run_maintenance_with_isolation",
        file_utils.run_maintenance_with_isolation,
        raising=False,
    )
    actual = await pci.run_proc_config_import_offload(dry_run=True)
    assert actual[0] is success and actual[1]["report_summary"]
    assert bool(actual[1]["errors"]) is (not success)
