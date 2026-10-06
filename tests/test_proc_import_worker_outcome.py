import pytest

import maintenance_worker as worker


@pytest.mark.parametrize(
    "result, expected",
    [
        ((True, {"success": True}), 0),
        ((False, {"success": False, "partial_commits": ["config"]}), 3),
        ((True, {"success": False}), 3),
        (None, 3),
        (("False", {}), 3),
        ((False, "invalid report"), 3),
    ],
)
@pytest.mark.parametrize("async_callable", [False, True])
def test_worker_respects_import_outcome(monkeypatch, result, expected, async_callable):
    calls = []
    outputs = []
    telemetry = []

    def run():
        calls.append(1)
        return result

    async def run_async():
        return run()

    monkeypatch.setattr(worker, "import_proc_import", lambda: run_async if async_callable else run)
    monkeypatch.setattr(worker, "_print_result_json", lambda *a, **kw: outputs.append((a, kw)))
    monkeypatch.setattr(worker, "emit_telemetry_event", telemetry.append)
    assert worker.do_proc_import() == expected
    assert calls == [1]
    assert outputs[-1][0][1] == ("success" if expected == 0 else "failed")
    assert outputs[-1][1]["returncode"] == expected
    assert telemetry[-1]["status"] == ("success" if expected == 0 else "failed")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result, expected",
    [
        ((True, {"success": True}), True),
        ((False, {"success": False, "targets_master_outcome": "uncertain"}), False),
        ((True, {"success": False}), False),
        (None, False),
        (("False", {}), False),
        ((False, "invalid report"), False),
    ],
)
async def test_default_pipeline_thread_respects_import_outcome(monkeypatch, result, expected):
    import file_utils
    import processing_pipeline
    from services import legacy_export_snapshot_service

    calls = []
    telemetry = []

    async def run_thread(fn, **kwargs):
        calls.append(fn.__name__)
        return result

    async def unexpected_process(*args, **kwargs):
        pytest.fail("Default thread path must not start or retry through a process")

    monkeypatch.setattr(legacy_export_snapshot_service, "_writer_runtime", lambda: None)
    monkeypatch.setattr(processing_pipeline, "MAINT_WORKER_MODE", "thread")
    monkeypatch.setattr(file_utils, "run_blocking_in_thread", run_thread)
    monkeypatch.setattr(file_utils, "run_maintenance_subprocess", unexpected_process)
    monkeypatch.setattr(file_utils, "emit_telemetry_event", telemetry.append)
    ok, output = await processing_pipeline._run_proc_config_step({"fixture": True})
    assert ok is expected
    assert calls == ["run_proc_config_import"]
    completed = [e for e in telemetry if e["event"] == "maintenance_run.complete"]
    assert completed[-1]["ok"] is expected
    if not expected:
        assert "inspect durable state" in output
