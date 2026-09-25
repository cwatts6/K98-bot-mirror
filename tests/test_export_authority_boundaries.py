"""Offline security boundary regressions; native I/O and ACL calls are fakes."""

import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import core.export_execution_host as host
import scripts.run_export_authority as launcher


def source_tree(tmp_path, monkeypatch):
    source = tmp_path / "services" / "sample.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "source_hashes": {
                    "services/sample.py": hashlib.sha256(source.read_bytes()).hexdigest()
                }
            }
        )
    )
    state = SimpleNamespace(flags=SimpleNamespace(isolated=1), path=[], dont_write_bytecode=False)
    monkeypatch.setattr(launcher, "sys", state)
    return source, manifest, state


@pytest.mark.parametrize(
    "artifact",
    [
        "sample.pyd",
        "sample.cp311-win_amd64.pyd",
        "sample.pyc",
        "sample.so",
        "__pycache__/sample.cpython-311.pyc",
    ],
)
def test_bootstrap_rejects_shadow_import_artifacts_before_publishing_path(
    tmp_path, monkeypatch, artifact
):
    source, manifest, state = source_tree(tmp_path, monkeypatch)
    shadow = source.parent / artifact
    shadow.parent.mkdir(exist_ok=True)
    shadow.write_bytes(b"inert; never loaded")
    with pytest.raises(launcher.AuthorityStartupError, match=r"artifact|bytecode"):
        launcher.bootstrap(
            manifest, script=tmp_path / "scripts/entry.py", inspect_path=lambda p, **_: Path(p)
        )
    assert state.path == []


@pytest.mark.parametrize("right", [0x2, 0x4, 0x40000, 0x40])
def test_bootstrap_rejects_create_only_import_directory_before_import(tmp_path, monkeypatch, right):
    source, manifest, state = source_tree(tmp_path, monkeypatch)
    authority, bot = "S-1-5-21-1-2-3-1001", "S-1-5-21-1-2-3-1002"

    class ACL:
        def __init__(self, path):
            self.path = Path(path)

        def GetAceCount(self):
            return 1

        def GetAce(self, _):
            return (
                ((0, 0), right, bot)
                if self.path == source.parent
                else ((0, 0), 0x1F01FF, authority)
            )

    class Descriptor:
        def __init__(self, path):
            self.path = path

        def GetSecurityDescriptorOwner(self):
            return authority

        def GetSecurityDescriptorDacl(self):
            return ACL(self.path)

    monkeypatch.setitem(sys.modules, "win32file", SimpleNamespace(GetFileAttributes=lambda _: 0))
    monkeypatch.setitem(
        sys.modules,
        "win32security",
        SimpleNamespace(
            LookupAccountName=lambda *_: ("installer", None, None),
            ConvertSidToStringSid=str,
            GetNamedSecurityInfo=lambda path, *_: Descriptor(path),
        ),
    )
    monkeypatch.setattr(launcher, "windows_sid", lambda: authority)
    with pytest.raises(launcher.AuthorityStartupError, match="Untrusted"):
        launcher.bootstrap(manifest, script=tmp_path / "scripts/entry.py")
    assert state.path == []


def test_bootstrap_protected_source_checks_complete_before_path_is_added(tmp_path, monkeypatch):
    source, manifest, state = source_tree(tmp_path, monkeypatch)
    checked = []

    def inspect(path, **_):
        assert not state.path
        checked.append(Path(path))
        return Path(path)

    launcher.bootstrap(manifest, script=tmp_path / "scripts/entry.py", inspect_path=inspect)
    assert source in checked and source.parent in checked and tmp_path in checked
    assert state.path == [str(tmp_path)] and state.dont_write_bytecode


@pytest.mark.parametrize("damage", ["hash", "inventory", "isolation"])
def test_bootstrap_fails_closed_on_source_or_interpreter_mismatch(tmp_path, monkeypatch, damage):
    source, manifest, state = source_tree(tmp_path, monkeypatch)
    if damage == "hash":
        source.write_text("changed")
    elif damage == "inventory":
        (source.parent / "extra.py").write_text("extra")
    else:
        state.flags.isolated = 0
    with pytest.raises(launcher.AuthorityStartupError):
        launcher.bootstrap(
            manifest, script=tmp_path / "scripts/entry.py", inspect_path=lambda p, **_: Path(p)
        )
    assert state.path == []


@pytest.mark.parametrize(
    "module", ["scripts.run_export_provider_child", "scripts.enroll_export_output_pool"]
)
def test_child_and_enrollment_load_exact_trusted_launcher_before_package_import(
    monkeypatch, module
):
    import importlib
    import runpy

    entry = importlib.import_module(module)
    check = Mock()
    load = Mock(return_value={"bootstrap": check})
    monkeypatch.setattr(runpy, "run_path", load)
    entry.bootstrap("protected-manifest")
    load.assert_called_once_with(
        str(Path(entry.__file__).absolute().with_name("run_export_authority.py"))
    )
    check.assert_called_once_with("protected-manifest", script=entry.__file__)


@pytest.mark.parametrize(
    "failure", ["decode", "disconnect", "authenticate", "dispatch", "reply", "timeout"]
)
def test_bad_peer_closes_and_next_valid_peer_completes_without_replay(monkeypatch, failure):
    handles = [SimpleNamespace(Close=Mock()), SimpleNamespace(Close=Mock())]
    pipes = [
        SimpleNamespace(connect=Mock(), receive=Mock(return_value={"version": 1}), send=Mock())
        for _ in handles
    ]
    broker = SimpleNamespace(dispatch=Mock(return_value={"ready": True}))
    authenticate = Mock()
    if failure in {"decode", "disconnect", "timeout"}:
        pipes[0].receive.side_effect = ValueError("invalid or missing frame")
    elif failure == "authenticate":
        authenticate.side_effect = [ValueError("identity"), None]
    elif failure == "dispatch":
        broker.dispatch.side_effect = [ValueError("unresolved"), {"ready": True}]
    else:
        pipes[0].send.side_effect = EOFError("gone")
    make = Mock(side_effect=[*handles, KeyboardInterrupt()])
    pipe_factory = Mock(side_effect=pipes)
    monkeypatch.setattr(host, "MessagePipe", pipe_factory)
    with pytest.raises(KeyboardInterrupt):
        launcher.serve(
            manifest=dict(pipe_id="fixture", authority_sid="authority", bot_sid="bot"),
            authority=Mock(),
            make_pipe=make,
            authenticate=authenticate,
            broker=broker,
        )
    for handle in handles:
        handle.Close.assert_called_once()
    pipes[1].send.assert_called_once_with({"version": 1, "result": {"ready": True}})
    assert broker.dispatch.call_count == (2 if failure in {"dispatch", "reply"} else 1)
    if failure == "reply":
        pipes[0].send.assert_called_once()
    assert all(call.kwargs["timeout_ms"] == 30000 for call in pipe_factory.call_args_list)
    assert all(call.kwargs["overlapped"] for call in make.call_args_list)


class WinError(Exception):
    def __init__(self, code):
        self.winerror = code


def bounded_pipe(*, status=997, wait=0, result=2, cancel_race=False):
    events = []
    event = SimpleNamespace(Close=lambda: events.append("close-event"))

    def finish(_handle, _operation, drain):
        events.append("drain" if drain else "result")
        if drain and not cancel_race:
            raise WinError(995)
        return result

    def cancel(*_):
        events.append("cancel")

    def read(_handle, buffer, _operation):
        buffer[:2] = b"{}"
        events.append("read")
        return status, buffer

    api = SimpleNamespace(
        AllocateReadBuffer=bytearray,
        ReadFile=read,
        WriteFile=lambda *_: (status, 0),
        GetOverlappedResult=finish,
        CancelIo=cancel,
    )
    event_api = SimpleNamespace(CreateEvent=lambda *_: event, WaitForSingleObject=lambda *_: wait)
    pipe = host.MessagePipe(
        1, api=api, timeout_ms=30, event_api=event_api, overlapped=SimpleNamespace
    )
    return pipe, events


@pytest.mark.parametrize("operation", ["read", "write"])
@pytest.mark.parametrize("cancel_race", [False, True])
def test_stalled_io_cancels_and_drains_before_releasing_buffer(operation, cancel_race):
    pipe, events = bounded_pipe(wait=258, cancel_race=cancel_race)
    with pytest.raises(host.HostBoundaryError, match="deadline"):
        pipe.receive() if operation == "read" else pipe.send({})
    assert events[-3:] == ["cancel", "drain", "close-event"]


@pytest.mark.parametrize("status", [0, 997])
def test_bounded_valid_frame_keeps_single_read_and_exact_message(status):
    pipe, events = bounded_pipe(status=status)
    assert pipe.receive() == {}
    pipe.send({})
    assert events.count("read") == 1 and "cancel" not in events


def test_oversized_bounded_message_is_rejected_without_another_chunk_deadline():
    pipe, events = bounded_pipe(status=234)
    with pytest.raises(host.HostBoundaryError):
        pipe.receive()
    assert events == ["read", "close-event"]


@pytest.mark.parametrize("status", [0, 535, 997])
def test_bounded_accept_handles_pywin32_return_codes(monkeypatch, status):
    pipe, events = bounded_pipe()
    monkeypatch.setitem(
        sys.modules, "win32pipe", SimpleNamespace(ConnectNamedPipe=lambda *_: status)
    )
    pipe.connect()
    assert "cancel" not in events
    assert ("result" in events) == (status != 535)


@pytest.mark.parametrize("raw", [b"\xff", b"[]", b'{"version":1,"version":2}', b"{"])
def test_bounded_frame_uses_real_protocol_rejection(raw):
    pipe, events = bounded_pipe(status=0, result=len(raw))

    def read(_handle, buffer, _operation):
        buffer[: len(raw)] = raw
        return 0, buffer

    pipe.api.ReadFile = read
    with pytest.raises(ValueError):
        pipe.receive()
    assert events[-1] == "close-event"


def test_shutdown_during_pending_io_drains_cancellation_then_propagates():
    pipe, events = bounded_pipe()

    def interrupt(*_):
        raise KeyboardInterrupt

    pipe.events.WaitForSingleObject = interrupt
    with pytest.raises(KeyboardInterrupt):
        pipe.receive()
    assert events[-3:] == ["cancel", "drain", "close-event"]


@pytest.mark.parametrize("operation", ["connect", "read"])
@pytest.mark.parametrize("wait", [0, 258])
def test_child_handshake_exit_or_stall_cancels_pending_io(monkeypatch, operation, wait):
    pipe, events = bounded_pipe()
    process = object()
    pipe.process = process
    waits = []

    def observe(handles, all_handles, timeout):
        assert handles[0] is process and all_handles is False
        waits.append(timeout)
        return wait

    pipe.events.WaitForMultipleObjects = observe
    monkeypatch.setitem(sys.modules, "win32pipe", SimpleNamespace(ConnectNamedPipe=lambda *_: 997))
    with pytest.raises(host.HostBoundaryError, match=r"exited|deadline"):
        pipe.connect() if operation == "connect" else pipe.receive()
    assert waits == [30]
    assert events[-3:] == ["cancel", "drain", "close-event"]


def test_child_response_after_handshake_still_observes_exact_process():
    pipe, events = bounded_pipe()
    process = object()
    pipe.process, pipe.timeout_ms = process, None
    pipe.events.WaitForMultipleObjects = Mock(return_value=1)
    assert pipe.receive() == {}
    handles, all_handles, timeout = pipe.events.WaitForMultipleObjects.call_args.args
    assert handles[0] is process and all_handles is False and timeout == 0xFFFFFFFF
    assert "cancel" not in events


@pytest.mark.parametrize("failure", [None, "connect", "hello", "identity"])
def test_child_resume_uses_bounded_handshake_and_keeps_handles_on_failure(monkeypatch, failure):
    pipe = SimpleNamespace(
        handle=SimpleNamespace(Close=Mock()),
        connect=Mock(),
        receive=Mock(return_value={"child_id": "child", "version": 1}),
        timeout_ms=30000,
    )
    if failure in {"connect", "hello"}:
        getattr(pipe, "connect" if failure == "connect" else "receive").side_effect = (
            host.HostBoundaryError("deadline")
        )
    elif failure == "identity":
        pipe.receive.return_value = {"child_id": "different", "version": 1}
    authenticate = Mock()
    monkeypatch.setattr(host, "authenticated_peer", authenticate)
    child = host.WindowsProviderChild(
        identity="child",
        process=SimpleNamespace(Close=Mock()),
        thread=SimpleNamespace(Close=Mock()),
        job=SimpleNamespace(Close=Mock()),
        pid=17,
        pipe=pipe,
        sid="sid",
        api={"process": SimpleNamespace(ResumeThread=Mock())},
    )
    if failure:
        with pytest.raises(host.HostBoundaryError):
            child.resume()
        assert pipe.timeout_ms == 30000
    else:
        child.resume()
        assert pipe.timeout_ms is None
        authenticate.assert_called_once_with(pipe.handle, "sid", expected_pid=17)
    assert child.resumed and not child.terminated
    child.process.Close.assert_not_called()
    child.job.Close.assert_not_called()
    pipe.handle.Close.assert_not_called()
    with pytest.raises(host.HostBoundaryError, match="again"):
        child.resume()


def test_skipped_directory_alias_is_checked_before_walk_can_omit_it(tmp_path, monkeypatch):
    # A directory symlink appears in dirnames but is never yielded by os.walk
    # with followlinks=False. Do not create a native link in this offline test.
    monkeypatch.setattr(
        launcher.os, "walk", lambda *_, **__: iter([(str(tmp_path), ["requests"], ["entry.py"])])
    )

    def inspect(path):
        if path == tmp_path / "requests":
            raise launcher.AuthorityStartupError("Reparse points are forbidden")
        return path

    with pytest.raises(launcher.AuthorityStartupError, match="Reparse"):
        launcher.code_files(tmp_path, inspect_directory=inspect)


def test_windows_case_variant_package_initializer_is_part_of_exact_inventory(tmp_path, monkeypatch):
    source, manifest, state = source_tree(tmp_path, monkeypatch)
    shadow = source.parent / "sample"
    shadow.mkdir()
    (shadow / "__init__.PY").write_text("VALUE = 'unpinned package'")
    with pytest.raises(launcher.AuthorityStartupError, match="inventory"):
        launcher.bootstrap(
            manifest, script=tmp_path / "scripts/entry.py", inspect_path=lambda p, **_: Path(p)
        )
    assert state.path == []


def test_unlistable_import_directory_cannot_be_silently_omitted(tmp_path, monkeypatch):
    def walk(_root, *, followlinks, onerror):
        assert followlinks is False
        yield str(tmp_path), ["requests"], ["entry.py"]
        onerror(PermissionError("directory cannot be listed"))

    monkeypatch.setattr(launcher.os, "walk", walk)
    with pytest.raises(launcher.AuthorityStartupError, match="cannot be enumerated"):
        launcher.code_files(tmp_path, inspect_directory=lambda p: p)


@pytest.mark.parametrize("mode_error", [None, ValueError("mode refused"), KeyboardInterrupt()])
def test_message_mode_access_and_failed_setup_cleanup(monkeypatch, mode_error):
    handle = SimpleNamespace(Close=Mock())
    opened = Mock(return_value=handle)
    monkeypatch.setitem(sys.modules, "win32file", SimpleNamespace(CreateFile=opened))

    def set_mode(actual, mode, count, timeout):
        access = opened.call_args.args[1]
        assert actual is handle and (mode, count, timeout) == (2, None, None)
        assert access & 0x100  # FILE_WRITE_ATTRIBUTES required to set message mode
        assert access & 0x3 == 0x3 and not access & 0x4
        if mode_error is not None:
            raise mode_error

    monkeypatch.setitem(sys.modules, "win32pipe", SimpleNamespace(SetNamedPipeHandleState=set_mode))
    if mode_error is None:
        assert host.open_message_pipe("fixture-pipe") is handle
        handle.Close.assert_not_called()
    else:
        with pytest.raises(type(mode_error)):
            host.open_message_pipe("fixture-pipe")
        handle.Close.assert_called_once()


def test_server_grants_exact_client_rights_without_pipe_instance_creation(monkeypatch):
    descriptor = Mock(return_value="fixture-descriptor")
    create = Mock(return_value="fixture-handle")
    monkeypatch.setitem(
        sys.modules, "pywintypes", SimpleNamespace(SECURITY_ATTRIBUTES=SimpleNamespace)
    )
    monkeypatch.setitem(sys.modules, "win32pipe", SimpleNamespace(CreateNamedPipe=create))
    monkeypatch.setitem(
        sys.modules,
        "win32security",
        SimpleNamespace(
            ConvertSidToStringSid=str,
            ConvertStringSidToSid=str,
            ConvertStringSecurityDescriptorToSecurityDescriptor=descriptor,
        ),
    )
    assert (
        host.create_private_pipe(
            r"\\.\pipe\K98Export-fixture",
            authority_sid="authority",
            client_sid="bot",
            overlapped=True,
        )
        == "fixture-handle"
    )
    sddl = descriptor.call_args.args[0]
    granted = int(sddl.split("(A;;0x")[1].split(";")[0], 16)
    assert granted == host.PIPE_CLIENT_ACCESS and granted & 0x100 and not granted & 0x4
    assert create.call_args.args[1] & 0x40000000


def test_bot_client_uses_the_shared_message_mode_boundary(monkeypatch):
    from services.export_runtime_composition import AuthorityClient

    connect = Mock(return_value="fixture-handle")
    monkeypatch.setattr(host, "open_message_pipe", connect)
    client = AuthorityClient(
        pipe_id="00000000-0000-0000-0000-000000000001",
        authority_sid="S-1-5-21-1",
        bot_sid="S-1-5-21-2",
    )
    assert client._connect_pipe() == "fixture-handle"
    connect.assert_called_once_with(r"\\.\pipe\K98Export-00000000-0000-0000-0000-000000000001")
