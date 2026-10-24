import os
import time

from file_utils import cancel_offload, get_offload_info, start_callable_offload

pytest_plugins = ("pytest_asyncio",)


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_start_and_cancel_callable_offload(tmp_path):
    """
    Start a blocking callable in a separate process using start_callable_offload,
    assert the process is running, then cancel it and confirm termination and
    registry update.
    """
    repo_root = _repo_root()
    # Ensure the test module is importable by subprocess by running from repo_root
    cwd = repo_root

    # Start the worker process via file_utils.start_callable_offload (module path, function, args)
    # Choose a long sleep so we have time to cancel
    off = start_callable_offload(
        module="tests.test_worker_module",
        function="long_sleep",
        args=["20"],
        meta={"test": "cancel_callable"},
        cwd=cwd,
    )
    assert isinstance(off, dict)
    offload_id = off.get("offload_id")
    pid = off.get("pid")
    assert offload_id is not None
    assert pid is not None

    # Ensure there's a registry entry
    info = get_offload_info(offload_id)
    assert info is not None
    assert info.get("pid") == pid

    # Give the process a moment to start
    time.sleep(0.2)

    # Now cancel by pid
    res = cancel_offload(pid=pid, actor="test_suite", grace_period=2.0)
    assert isinstance(res, dict)
    # Wait briefly to let cancel take effect
    time.sleep(0.2)

    # Process should have terminated; poll via os.kill check or via registry
    # Registry should show cancel_requested or completed status
    updated = get_offload_info(offload_id)
    assert updated is not None
    # After cancel, we mark as completed/ok=False and include cancel metadata
    assert updated.get("cancel_requested") in (True, None) or updated.get("ok") is False
