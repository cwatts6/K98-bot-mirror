"""Pinned native launch regressions; no SQL, credentials or provider requests."""

import hashlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

import core.export_execution_host as host_module


def fixture_host(tmp_path, monkeypatch, **damage):
    files = {
        name: tmp_path / name
        for name in ("launcher.exe", "native.exe", "child.py", "manifest.json")
    }
    for file in files.values():
        file.write_bytes(b"fixture only")
    monkeypatch.setattr(host_module, "assert_protected_path", lambda p, **_: Path(p))
    values = dict(
        python=files["launcher.exe"],
        child_script=files["child.py"],
        manifest=files["manifest.json"],
        authority_sid="S-1-5-21-1-2-3-1001",
        native_python=files["native.exe"],
        native_python_sha256=hashlib.sha256(files["native.exe"].read_bytes()).hexdigest(),
    )
    values.update(damage)
    return host_module.WindowsExecutionHost(**values), files


@pytest.mark.parametrize(
    "damage",
    [{"native_python_sha256": "0" * 64}, {"native_python_sha256": None}, {"native_python": None}],
)
def test_native_launcher_requires_matching_protected_image(tmp_path, monkeypatch, damage):
    with pytest.raises(host_module.HostBoundaryError):
        fixture_host(tmp_path, monkeypatch, **damage)


def test_direct_native_launch_preserves_venv_without_redirector_pid(tmp_path, monkeypatch):
    host, files = fixture_host(tmp_path, monkeypatch)
    process, thread, job, pipe = (Mock() for _ in range(4))
    api = SimpleNamespace(
        CreateProcess=Mock(return_value=(process, thread, 123, 456)), STARTUPINFO=Mock()
    )
    jobs = SimpleNamespace(
        CreateJobObject=Mock(return_value=job),
        QueryInformationJobObject=Mock(return_value={"BasicLimitInformation": {}}),
        SetInformationJobObject=Mock(),
        AssignProcessToJobObject=Mock(),
    )
    for name, value in {
        "pywintypes": SimpleNamespace(error=RuntimeError),
        "win32event": Mock(),
        "win32job": jobs,
        "win32pipe": Mock(),
        "win32process": api,
    }.items():
        monkeypatch.setitem(sys.modules, name, value)
    monkeypatch.setattr(host_module, "create_private_pipe", Mock(return_value=pipe))
    monkeypatch.setattr(host_module, "MessagePipe", lambda handle, **_: handle)
    monkeypatch.setenv("PYTHONEXECUTABLE", "unreviewed-image")
    monkeypatch.setenv("__PYVENV_LAUNCHER__", "unreviewed-venv")
    monkeypatch.setenv("PYTHONPATH", "unreviewed-path")
    child = host.create_suspended(str(uuid4()))
    args = api.CreateProcess.call_args.args
    assert args[0] == str(files["native.exe"])
    assert args[1].startswith('"' + str(files["native.exe"]) + '"') or args[1].startswith(
        str(files["native.exe"])
    )
    assert args[5] & 0x4 and args[5] & 0x400 and args[5] & 0x8000000
    assert args[6]["__PYVENV_LAUNCHER__"] == str(files["launcher.exe"])
    assert not {"PYTHONEXECUTABLE", "PYTHONHOME", "PYTHONPATH"} & {key.upper() for key in args[6]}
    assert child.pid == 123 and child.process is process
    jobs.AssignProcessToJobObject.assert_called_once_with(job, process)
    files["native.exe"].write_bytes(b"changed after host construction")
    with pytest.raises(host_module.HostBoundaryError, match="Native interpreter differs"):
        host.create_suspended(str(uuid4()))
    assert api.CreateProcess.call_count == 1


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows pipe/job regression")
def test_real_local_native_pid_pipe_venv_and_job_containment(tmp_path, monkeypatch):
    if os.environ.get("K98_S11_VENV_PROBE_AUTHORIZED") != "LOCAL_FIXTURE_ONLY":
        pytest.skip("Separately enabled disposable local native probe; no production operation")
    import win32api
    import win32security

    root = Path(__file__).resolve().parents[1]
    child_script = tmp_path / "fixture_child.py"
    child_script.write_text(
        "import sys;sys.dont_write_bytecode=True\n"
        + "sys.path.insert(0,"
        + repr(str(root))
        + ")\n"
        + "import argparse,os,win32api\n"
        + "from core.export_execution_host import MessagePipe,open_message_pipe\n"
        + "p=argparse.ArgumentParser();p.add_argument('--manifest');p.add_argument('--pipe');p.add_argument('--child-id');a=p.parse_args()\n"
        + "handle=open_message_pipe(a.pipe,timeout_ms=5000);pipe=MessagePipe(handle)\n"
        + "pipe.send({'version':1,'child_id':a.child_id});request=pipe.receive()\n"
        + "pipe.send({'request_id':request['request_id'],'result':{'pid':os.getpid(),'prefix':sys.prefix,'executable':sys.executable,'isolated':sys.flags.isolated,'pywin32':win32api.__file__}})\n"
        + "pipe.receive()\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "fixture_manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 8)
    try:
        sid = win32security.ConvertSidToStringSid(
            win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        )
    finally:
        token.Close()
    # Only fixture path inspection is substituted; native CreateProcess, pipe
    # authentication, retained handles and Job Object termination are real.
    # This is no claim about installed production ACLs or future identities.
    monkeypatch.setattr(host_module, "assert_protected_path", lambda p, **_: Path(p))
    monkeypatch.setenv("PYTHONEXECUTABLE", "unreviewed-image")
    native = Path(sys._base_executable)
    host = host_module.WindowsExecutionHost(
        python=sys.executable,
        native_python=native,
        native_python_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
        child_script=child_script,
        manifest=manifest,
        authority_sid=sid,
    )
    child = host.create_suspended(str(uuid4()))
    try:
        child.resume()
        value = child.execute({"request_id": str(uuid4())})
        assert value["pid"] == child.pid
        assert Path(value["executable"]) == Path(sys.executable)
        assert Path(value["prefix"]) == Path(sys.prefix)
        assert Path(value["pywin32"]).is_relative_to(Path(sys.prefix))
        assert value["isolated"] == 1
        receipt = child.terminate_and_observe()
        assert receipt["job_empty"] and receipt["process_signaled"]
    finally:
        if not child.terminated:
            child.terminate_and_observe()
