import pytest

# These tests exercise the run_maintenance_subprocess helper to ensure the
# subprocess mode can be timed out and killed. They require the maintenance_worker.py
# file to be present next to file_utils.py in the repository.

pytestmark = pytest.mark.asyncio


async def test_maintenance_subprocess_timeout(tmp_path, monkeypatch):
    """
    Run maintenance_worker.test_sleep with --seconds 5 but timeout=1 and assert
    the subprocess is killed and we get a failure response.
    """
    # Ensure we run in process mode to use subprocess path
    monkeypatch.setenv("MAINT_WORKER_MODE", "process")

    from file_utils import run_maintenance_subprocess

    success, output = await run_maintenance_subprocess(
        "test_sleep",
        args=["--seconds", "5"],
        timeout=1.0,
        name="test_sleep",
        meta={"test": "timeout"},
    )

    assert not success, "Expected subprocess to be killed due to timeout"
    assert "Timed out" in output or "timed out" in output.lower() or "killed" in output.lower()


async def test_maintenance_subprocess_success(tmp_path, monkeypatch):
    """
    Run maintenance_worker.test_sleep with --seconds 1 and timeout=5 and assert success.
    """
    monkeypatch.setenv("MAINT_WORKER_MODE", "process")

    from file_utils import run_maintenance_subprocess

    success, output = await run_maintenance_subprocess(
        "test_sleep",
        args=["--seconds", "1"],
        timeout=5.0,
        name="test_sleep",
        meta={"test": "success"},
    )

    # success should be True and worker should print TEST_SLEEP_DONE to stdout
    assert success, f"Expected subprocess to succeed, got output: {output}"
    assert "TEST_SLEEP_DONE" in output
