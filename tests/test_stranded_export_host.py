"""Real Windows named-job and retained-handle checks on disposable sleepers only."""

import hashlib
import os
import subprocess
import sys
from uuid import uuid4

import pytest

from core.export_execution_host import HostBoundaryError
from core.stranded_export_host import RecoveryHost

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native Windows job evidence")


@pytest.fixture
def writer():
    import win32api
    import win32job
    import win32process

    from core.export_execution_host import current_sid, machine_identity
    from core.export_process_identity import process_snapshot

    binding = process_snapshot(win32api.GetCurrentProcess())
    name = "Global\\K98ExportChild-" + hashlib.sha256(uuid4().bytes).hexdigest()
    job = win32job.CreateJobObject(None, name)
    limits = win32job.QueryInformationJobObject(job, 9)
    limits["BasicLimitInformation"]["LimitFlags"] = 0x2000
    win32job.SetInformationJobObject(job, 9, limits)
    process = thread = None
    try:
        environment = {
            k: v
            for k, v in os.environ.items()
            if k.upper()
            not in {"__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE", "PYTHONHOME", "PYTHONPATH"}
        }
        environment["__PYVENV_LAUNCHER__"] = sys.executable
        process, thread, pid, _ = win32process.CreateProcess(
            binding["executable"],
            subprocess.list2cmdline(
                [binding["executable"], "-I", "-S", "-c", "import time; time.sleep(60)"]
            ),
            None,
            None,
            False,
            0x4 | 0x08000000 | 0x400,
            environment,
            None,
            win32process.STARTUPINFO(),
        )
        win32job.AssignProcessToJobObject(job, process)
        win32process.ResumeThread(thread)
        birth = dict(
            child_id=str(uuid4()),
            pid=pid,
            job_name=name,
            machine=machine_identity(),
            authority_sid=current_sid(),
            limit_flags=0x2000,
            assigned=True,
        )
        yield RecoveryHost(binding), birth, job, process
    finally:
        if process is not None:
            win32job.TerminateJobObject(job, 1)
            process.Close()
        if thread is not None:
            thread.Close()
        job.Close()


def test_native_inspect_leaves_writer_live_then_exact_termination_is_observed(writer):
    import win32event
    import win32job

    host, birth, job, process = writer
    with host.retain(birth) as retained:
        retained.inspect()
    assert win32event.WaitForSingleObject(process, 0) == 258
    with host.retain(birth) as retained:
        receipt = retained.terminate_and_observe()
    assert receipt["process_signaled"] and receipt["job_empty"]
    assert win32event.WaitForSingleObject(process, 0) == 0
    assert win32job.QueryInformationJobObject(job, 1)["ActiveProcesses"] == 0
    host.verify_terminated(birth, receipt)


def test_native_wrong_pid_does_not_terminate_writer(writer):
    import os

    import win32event

    host, birth, _, process = writer
    with pytest.raises((HostBoundaryError, ValueError)):
        with host.retain(dict(birth, pid=os.getpid())):
            pytest.fail("Unrelated process was admitted")
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_native_changed_job_limits_fail_before_termination(writer):
    import win32event
    import win32job

    host, birth, job, process = writer
    limits = win32job.QueryInformationJobObject(job, 9)
    limits["BasicLimitInformation"]["LimitFlags"] = 0
    win32job.SetInformationJobObject(job, 9, limits)
    with pytest.raises(HostBoundaryError):
        with host.retain(birth):
            pytest.fail("Changed containment was admitted")
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_native_live_job_cannot_validate_saved_termination(writer):
    host, birth, _, _ = writer
    receipt = dict(
        child_id=birth["child_id"],
        pid=birth["pid"],
        job_empty=True,
        process_signaled=True,
        job_name_sha256=hashlib.sha256(birth["job_name"].encode()).hexdigest(),
    )
    with pytest.raises(HostBoundaryError):
        host.verify_terminated(birth, receipt)
