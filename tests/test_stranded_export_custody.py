"""Native custody inspection against disposable children, never real exports."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest

from core.stranded_export_custody import CustodyUnavailable, _command_matches, inspect_custody

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native Windows custody")


@pytest.fixture
def custody(tmp_path):
    import win32api
    import win32job
    import win32process

    from core.export_process_identity import process_snapshot

    binding = process_snapshot(win32api.GetCurrentProcess())
    script, manifest = tmp_path / "sleeper.py", tmp_path / "manifest.json"
    script.write_text("import time; time.sleep(90)")
    manifest.write_text("{}")
    child_id = str(uuid4())
    job = win32job.CreateJobObject(
        None, "Global\\K98ExportChild-" + hashlib.sha256(uuid4().bytes).hexdigest()
    )
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
        argv = [
            binding["executable"],
            "-I",
            str(script),
            "--manifest",
            str(manifest),
            "--pipe",
            "\\\\.\\pipe\\K98Export-" + child_id,
            "--child-id",
            child_id,
        ]
        process, thread, _, _ = win32process.CreateProcess(
            binding["executable"],
            subprocess.list2cmdline(argv),
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
        yield dict(
            binding=binding, child_script=script, manifest_path=manifest, child_id=child_id
        ), job, process, argv
    finally:
        if process is not None:
            win32job.TerminateJobObject(job, 1)
            process.Close()
        if thread is not None:
            thread.Close()
        job.Close()


def test_native_custody_is_positive_and_does_not_terminate(custody):
    import win32event
    import win32job

    args, job, process, _ = custody
    before = win32job.QueryInformationJobObject(job, 9)
    result = inspect_custody(**args)
    assert result["authority_holds_writer_job"] is True
    assert result["termination_authorized"] is False
    assert result["birth_evidence_created"] is False
    assert win32event.WaitForSingleObject(process, 0) == 258
    assert (
        win32job.QueryInformationJobObject(job, 9)["BasicLimitInformation"]
        == before["BasicLimitInformation"]
    )


@pytest.mark.parametrize("field", ["child_id", "manifest_path", "child_script"])
def test_wrong_exact_startup_binding_stops_without_mutation(custody, field):
    import win32event

    args, _, process, _ = custody
    changed = dict(args, **{field: str(uuid4()) if field == "child_id" else Path("C:/different")})
    with pytest.raises(CustodyUnavailable, match="Exactly one original live writer"):
        inspect_custody(**changed)
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_changed_containment_limits_stop_without_killing(custody):
    import win32event
    import win32job

    args, job, process, _ = custody
    limits = win32job.QueryInformationJobObject(job, 9)
    limits["BasicLimitInformation"]["LimitFlags"] = 0
    win32job.SetInformationJobObject(job, 9, limits)
    with pytest.raises(CustodyUnavailable, match="containment changed"):
        inspect_custody(**args)
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_exited_writer_is_not_absence_proof(custody):
    import win32event
    import win32job

    args, job, process, _ = custody
    win32job.TerminateJobObject(job, 1)
    assert win32event.WaitForSingleObject(process, 5000) == 0
    with pytest.raises(CustodyUnavailable):
        inspect_custody(**args)


def test_extra_command_argument_is_not_accepted(custody):
    args, _, _, argv = custody
    assert not _command_matches([*argv, "--unreviewed"], **args)


def test_ambiguous_live_writer_is_rejected(custody, monkeypatch):
    import psutil
    import win32event

    args, _, process, _ = custody
    original = psutil.Process.children
    monkeypatch.setattr(psutil.Process, "children", lambda self, **kw: original(self, **kw) * 2)
    with pytest.raises(CustodyUnavailable, match="Exactly one original live writer"):
        inspect_custody(**args)
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_job_not_in_authority_inventory_is_rejected(custody, monkeypatch):
    import win32event

    import core.stranded_export_custody as module

    args, job, process, _ = custody
    original = module._handles
    monkeypatch.setattr(
        module, "_handles", lambda: [row for row in original() if row[1] != int(job)]
    )
    with pytest.raises(CustodyUnavailable, match="authority-owned private writer Job"):
        inspect_custody(**args)
    assert win32event.WaitForSingleObject(process, 0) == 258


def test_parent_mismatch_is_rejected(custody, monkeypatch):
    import win32event

    args, _, process, _ = custody
    monkeypatch.setattr("core.stranded_export_custody._parent", lambda _: 0)
    with pytest.raises(CustodyUnavailable, match="incarnation differs"):
        inspect_custody(**args)
    assert win32event.WaitForSingleObject(process, 0) == 258
