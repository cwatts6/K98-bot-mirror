import os
import subprocess
import sys
import time

from file_utils import (
    cancel_offload,
    list_offloads,
    record_process_offload,
    start_offload,
)

pytest_plugins = ("pytest_asyncio",)


def test_cancel_offload_by_pid(tmp_path):
    """
    Start a maintenance_worker test_sleep process using subprocess.Popen, register it
    in the persistent registry, then call cancel_offload by pid and assert the process is terminated.
    """
    # Build command
    # Use the maintenance_worker script present in repo root (assumes it's on same path)
    worker = os.path.join(os.path.dirname(__file__), "..", "maintenance_worker.py")
    worker = os.path.abspath(worker)
    if not os.path.exists(worker):
        # fallback to module invocation (works if installed in PYTHONPATH)
        worker = "maintenance_worker.py"

    cmd = [sys.executable, worker, "test_sleep", "--seconds", "30"]
    # Start subprocess
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid = proc.pid
    assert pid is not None

    # Register offload in registry
    off_id = start_offload(meta={"test": True, "tag": "cancel_test"})
    record_process_offload(off_id, pid, cmd)

    # Ensure registry persisted
    offs = list_offloads()
    assert any(o.get("offload_id") == off_id for o in offs)

    # Cancel by pid
    res = cancel_offload(pid=pid, actor="test_suite", grace_period=2.0)
    assert isinstance(res, dict)
    # process should be gone after cancellation attempt
    time.sleep(0.2)
    ret = proc.poll()
    assert ret is not None

    # Registry updated (entry exists)
    info = None
    for o in list_offloads():
        if o.get("offload_id") == off_id:
            info = o
            break
    assert info is not None
    assert info.get("cancel_requested") in (True, None) or info.get("ok") is False
