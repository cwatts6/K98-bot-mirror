"""Owned local Windows pipes and inert requests; no SQL, service or provider work."""

import os
import sys
from threading import Event, Thread
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core import export_execution_host as host
from scripts import run_export_authority as launcher

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or os.getenv("K98_D2J_NATIVE_PIPE") != "LOCAL_FIXTURE_ONLY",
    reason="Explicit uniquely owned local Windows pipe qualification",
)


@pytest.mark.parametrize("lost_reply", [False, True])
def test_native_saturation_mutation_progress_and_original_reply_custody(lost_reply):
    import pywintypes
    import win32api
    import win32file
    import win32pipe

    ready, entered, release, stop = Event(), Event(), Event(), Event()
    sid, pipe_id = host.current_sid(), str(uuid4())
    name = "\\\\.\\pipe\\K98Export-" + pipe_id
    handles, clients, calls, failures, authenticated = [], [], [], [], []

    def make(name, **kwargs):
        if stop.is_set():
            raise KeyboardInterrupt()
        handle = host.create_private_pipe(name, **kwargs)
        handles.append(handle)
        ready.set()
        return handle

    def authenticate(handle, expected, **_):
        # This controlled transport fixture authenticates the current SID and
        # exact fixture PID. Production token/profile policy is tested separately.
        try:
            host.authenticated_peer(handle, expected, expected_pid=os.getpid())
        except Exception as error:
            failures.append(error)
            raise
        authenticated.append(int(handle))

    def dispatch(message):
        if message["action"] == "fixture_stop":
            raise KeyboardInterrupt()
        calls.append(message)
        if message["action"] == "inspect_target_recovery":
            entered.set()
            assert release.wait(8)
            return message["job_id"]
        return "mutation progressed"

    broker = SimpleNamespace(dispatch=dispatch)

    def server():
        try:
            launcher.serve(
                manifest=dict(pipe_id=pipe_id, authority_sid=sid, bot_sid=sid),
                authority=None,
                make_pipe=make,
                authenticate=authenticate,
                broker=broker,
            )
        except KeyboardInterrupt:
            pass
        except BaseException as error:
            failures.append(error)

    def send(message):
        deadline = monotonic() + 3
        while True:
            try:
                handle = win32file.CreateFile(
                    name, host.PIPE_CLIENT_ACCESS, 0, None, 3, 0x40000000, None
                )
                break
            except pywintypes.error as error:
                if error.winerror not in (2, 231) or monotonic() >= deadline:
                    raise
                sleep(0.01)
        clients.append(handle)
        win32pipe.SetNamedPipeHandleState(handle, 2, None, None)
        pipe = host.MessagePipe(handle, timeout_ms=3000)
        pipe.send(message)
        return pipe

    def observe(key):
        return dict(version=1, action="inspect_target_recovery", job_id=key)

    thread = Thread(target=server, daemon=False)
    thread.start()
    try:
        assert ready.wait(3)
        first = send(observe("one"))
        assert entered.wait(3), failures
        if lost_reply:
            first.handle.Close()
        second = send(observe("two"))
        deadline = monotonic() + 3
        while broker.observation_progress.snapshot()["waiting"] != 1 and monotonic() < deadline:
            sleep(0.01)
        assert broker.observation_progress.snapshot()["waiting"] == 1
        busy = send(observe("three"))
        assert busy.receive() == dict(version=1, error="authority_busy")
        control = send(dict(version=1, action="fixture_mutation"))
        assert control.receive() == dict(version=1, result="mutation progressed")
        assert len(calls) == 2  # One active read plus the serial mutation.
        release.set()
        if not lost_reply:
            assert first.receive() == dict(version=1, result="one")
        assert second.receive() == dict(version=1, result="two")
        send(dict(version=1, action="fixture_stop"))
        thread.join(5)
        assert not thread.is_alive()
        assert not failures
        assert len(authenticated) == 5
        assert [m.get("job_id") for m in calls] == ["one", None, "two"]
        assert broker.observation_progress.drain(timeout=0)
        for handle in handles:
            with pytest.raises(pywintypes.error):
                win32api.GetHandleInformation(handle)
    finally:
        release.set()
        stop.set()
        if thread.is_alive():
            try:
                send(dict(version=1, action="fixture_stop"))
            except Exception:
                pass
            thread.join(35)
        for handle in clients:
            try:
                handle.Close()
            except pywintypes.error:
                pass
        assert not thread.is_alive()
