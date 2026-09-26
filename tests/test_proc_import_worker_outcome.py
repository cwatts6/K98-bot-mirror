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
