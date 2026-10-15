"""Restart closure from immutable birth and exact Windows job lifecycle evidence."""

from copy import deepcopy
import hashlib
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.export_child_lifecycle import read_birth, validate_host_birth
from core.export_execution_host import HostBoundaryError, WindowsExecutionHost
from services.export_execution_authority import ExecutionUncertain, ExportExecutionAuthority
from services.export_execution_protocol import encode
from tests.test_export_execution_authority import DAL, Child
from tests.test_export_reconciliation_service import closed_stream_fixture


def host_birth(child_id=None):
    return dict(
        child_id=child_id or str(uuid4()),
        pid=123,
        job_name="Global\\K98ExportChild-" + "a" * 64,
        machine=dict(machine_guid=str(uuid4()), hostname="fixture"),
        authority_sid="S-1-5-21-1-2-3-4",
        limit_flags=0x2000,
        assigned=True,
    )


class PrivateStore:
    def __init__(self):
        self.documents = {}

    def put(self, data):
        key = uuid4()
        self.documents[str(key)] = data
        return SimpleNamespace(key=key.hex, sha256=hashlib.sha256(data).hexdigest())

    def read_reference(self, reference, expected_hash):
        data = self.documents[str(reference)]
        assert hashlib.sha256(data).digest() == expected_hash
        return data


def restarted_fixture():
    dal, store, children = DAL(), PrivateStore(), []

    def create(identity):
        child = Child(identity)
        child.birth_evidence = host_birth(identity)
        original_resume = child.resume

        def resume():
            # Both encrypted birth and committed SQL reference precede resume.
            assert store.documents and len(dal.streams) == 1
            read_birth(store, next(iter(dal.streams.values())))
            original_resume()

        child.resume = resume
        children.append(child)
        return child

    host = SimpleNamespace(create_suspended=create)
    original = ExportExecutionAuthority(
        dal=dal, store=store, host=host, budget_factory=Mock(), session_id=str(uuid4())
    )
    stream_id = str(uuid4())
    original.open_stream(
        stream_id=stream_id,
        scope=dict(
            AccountKey="account",
            OwnerKind="preparation",
            ObjectID=str(uuid4()),
            OwnerID=str(uuid4()),
            Fence=1,
            ClaimVersion=1,
            NestedToken=None,
            RegistrationHash=b"r" * 32,
            Epoch=None,
            SnapshotHash=b"s" * 32,
            Purpose="probe",
            ScopeJson=json.dumps(
                dict(
                    resources=[
                        dict(key="account:account", version=1),
                        dict(key="destination:file", version=1),
                    ]
                )
            ),
        ),
    )
    birth, _ = read_birth(store, dal.streams[stream_id])
    host.observe_retired_child = Mock(
        return_value=dict(
            child_id=birth["child_id"],
            pid=birth["pid"],
            job_empty=True,
            process_terminated=True,
            termination_method="named_job_destroyed",
            job_name_sha256=hashlib.sha256(birth["job_name"].encode()).hexdigest(),
        )
    )
    restarted = ExportExecutionAuthority(
        dal=dal, store=store, host=host, budget_factory=Mock(), session_id=str(uuid4())
    )
    return restarted, dal, store, stream_id, original, children[0]


@pytest.mark.parametrize("lost", [None, "freeze", "close"])
def test_restart_records_exact_old_read_closure_without_replay(lost):
    authority, dal, store, stream_id, original, child = restarted_fixture()
    dal.fail = lost
    if lost:
        with pytest.raises(RuntimeError):
            authority.recover_abandoned_read_closure(stream_id)
        dal.fail = None
    if dal.read_stream(stream_id)["State"] != "closed":
        authority.recover_abandoned_read_closure(stream_id)
    row = dal.read_stream(stream_id)
    assert row["State"] == "closed" and row["SessionID"] == original.session_id
    closure = json.loads(store.read_reference(row["ClosureReference"], row["ClosureHash"]))
    assert closure["closure"]["process_terminated"] and "process_signaled" not in closure["closure"]
    assert not child.calls and not authority._streams
    assert all(kind == "stream" for kind, _ in dal.calls)


@pytest.mark.parametrize(
    "bad", ["live", "missing", "child", "session", "account", "mutation", "same_session"]
)
def test_restart_refuses_unverifiable_or_wrong_birth_before_closure(bad):
    authority, dal, store, stream_id, original, child = restarted_fixture()
    row = dal.streams[stream_id]
    if bad == "live":
        authority.host.observe_retired_child.side_effect = HostBoundaryError("Still live")
    elif bad == "missing":
        store.documents.clear()
    elif bad == "child":
        row["ChildIdentity"] = str(uuid4())
    elif bad == "session":
        row["SessionID"] = str(uuid4())
    elif bad == "account":
        row["AccountKey"] = "foreign"
    elif bad == "mutation":
        row["Purpose"] = "mutation"
    else:
        row["SessionID"] = authority.session_id
    before = deepcopy(dal.calls)
    with pytest.raises((ValueError, KeyError, HostBoundaryError, ExecutionUncertain)):
        authority.recover_abandoned_read_closure(stream_id)
    assert dal.calls == before and not child.calls


def test_caller_cannot_inject_a_private_birth_binding():
    authority, dal, _, stream_id, _, _ = restarted_fixture()
    opening = dict(dal.calls[0][1])
    for key in ("SessionID", "StreamID", "Action", "ExpectedVersion", "ChildIdentity"):
        opening.pop(key)
    before = deepcopy(dal.calls)
    with pytest.raises(ValueError, match="registered resource"):
        authority.open_stream(stream_id=str(uuid4()), scope=opening)
    assert dal.calls == before


@pytest.mark.parametrize("error", [HostBoundaryError("Hash differs"), RuntimeError("DPAPI failed")])
def test_private_birth_io_failure_is_unavailable_without_process_or_sql_changes(error):
    authority, dal, store, stream_id, _, child = restarted_fixture()
    store.read_reference = Mock(side_effect=error)
    before = deepcopy(dal.calls)
    with pytest.raises(ValueError, match="Private child birth is unavailable") as caught:
        read_birth(store, dal.streams[stream_id])
    assert caught.value.__cause__ is error
    assert dal.calls == before and not child.calls
    authority.host.observe_retired_child.assert_not_called()


@pytest.mark.parametrize(
    "result", ["destroyed", "empty", "live", "denied", "other_error", "changed_limits"]
)
def test_windows_observation_uses_exact_global_job_and_fails_closed(monkeypatch, result):
    birth = host_birth()
    host = object.__new__(WindowsExecutionHost)
    host.sid = birth["authority_sid"]
    monkeypatch.setattr("core.export_execution_host.machine_identity", lambda: birth["machine"])

    class Error(Exception):
        def __init__(self, code):
            self.winerror = code

    handle = SimpleNamespace(Close=Mock())
    open_job = Mock(return_value=handle)
    if result in {"destroyed", "denied", "other_error"}:
        open_job.side_effect = Error({"destroyed": 2, "denied": 5, "other_error": 6}[result])
    query = Mock(
        side_effect=lambda _, kind: (
            dict(BasicLimitInformation=dict(LimitFlags=0 if result == "changed_limits" else 0x2000))
            if kind == 9
            else dict(ActiveProcesses=int(result == "live"))
        )
    )
    monkeypatch.setitem(sys.modules, "pywintypes", SimpleNamespace(error=Error))
    monkeypatch.setitem(
        sys.modules,
        "win32job",
        SimpleNamespace(OpenJobObject=open_job, QueryInformationJobObject=query),
    )
    if result in {"destroyed", "empty"}:
        observed = host.observe_retired_child(birth)
        assert observed["process_terminated"] and observed["job_empty"]
    else:
        with pytest.raises(HostBoundaryError):
            host.observe_retired_child(birth)
    open_job.assert_called_once_with(4, False, birth["job_name"])
    if result in {"empty", "live", "changed_limits"}:
        handle.Close.assert_called_once()


def test_other_host_and_invalid_birth_cannot_query_job(monkeypatch):
    host = object.__new__(WindowsExecutionHost)
    birth = host_birth()
    host.sid = birth["authority_sid"]
    monkeypatch.setattr(
        "core.export_execution_host.machine_identity",
        lambda: dict(machine_guid=str(uuid4()), hostname="other"),
    )
    with pytest.raises(HostBoundaryError):
        host.observe_retired_child(birth)
    for key, value in (
        ("limit_flags", 0x2800),
        ("assigned", False),
        ("job_name", "Local\\other"),
        ("pid", True),
    ):
        with pytest.raises(ValueError):
            validate_host_birth(dict(birth, **{key: value}))


def test_private_verifier_requires_bound_birth_for_restarted_closure():
    verifier, stream, _, _, documents = closed_stream_fixture(purpose="probe")
    stream["SessionID"] = str(uuid4())
    birth = host_birth(stream["ChildIdentity"])
    raw = encode(
        dict(
            kind="provider_child_birth/1",
            stream_id=stream["StreamID"],
            session_id=stream["SessionID"],
            account=stream["AccountKey"],
            host=birth,
        )
    )
    reference, birth_hash = str(uuid4()), hashlib.sha256(raw).hexdigest()
    documents[reference] = raw
    stream["ScopeJson"] = json.dumps(
        dict(resources=[], host_birth=dict(reference=reference, sha256=birth_hash))
    )
    closure = json.loads(documents[stream["ClosureReference"]])
    closure["closure"] = dict(
        child_id=birth["child_id"],
        pid=birth["pid"],
        job_empty=True,
        process_terminated=True,
        termination_method="named_job_destroyed",
        birth_sha256=birth_hash,
        job_name_sha256=hashlib.sha256(birth["job_name"].encode()).hexdigest(),
    )
    documents[stream["ClosureReference"]] = encode(closure)
    stream["ClosureHash"] = hashlib.sha256(encode(closure)).digest()
    assert (
        verifier.verify(
            stream["StreamID"], account=stream["AccountKey"], registration_hash=b"r" * 32
        ).successful_reads
        == 1
    )
    stream["SessionID"] = str(uuid4())
    with pytest.raises(Exception, match="restarted-child"):
        verifier.verify(
            stream["StreamID"], account=stream["AccountKey"], registration_hash=b"r" * 32
        )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows named-job API")
def test_real_windows_job_lifecycle_for_disposable_suspended_child():
    """No provider script, manifest, credentials, network or existing process is used."""
    import win32event
    import win32job
    import win32process

    from core.export_execution_host import current_sid, machine_identity

    host = object.__new__(WindowsExecutionHost)
    host.sid = current_sid()
    birth = host_birth()
    birth.update(
        authority_sid=host.sid,
        machine=machine_identity(),
        job_name="Global\\K98ExportChild-" + uuid4().hex + uuid4().hex,
    )
    job = win32job.CreateJobObject(None, birth["job_name"])
    process = thread = None
    try:
        limits = win32job.QueryInformationJobObject(job, 9)
        limits["BasicLimitInformation"]["LimitFlags"] = 0x2000
        win32job.SetInformationJobObject(job, 9, limits)
        process, thread, pid, _ = win32process.CreateProcess(
            sys.executable,
            '"' + sys.executable + '" -c "pass"',
            None,
            None,
            False,
            0x4 | 0x8000000,
            None,
            None,
            win32process.STARTUPINFO(),
        )
        win32job.AssignProcessToJobObject(job, process)
        birth["pid"] = pid
        with pytest.raises(HostBoundaryError, match="live"):
            host.observe_retired_child(birth)
        win32job.TerminateJobObject(job, 1)
        assert win32event.WaitForSingleObject(process, 5000) == 0
        assert host.observe_retired_child(birth)["termination_method"] == "named_job_empty"
        job.Close()
        job = None
        assert host.observe_retired_child(birth)["termination_method"] == "named_job_destroyed"
    finally:
        if process is not None:
            if win32event.WaitForSingleObject(process, 0) != 0:
                win32process.TerminateProcess(process, 1)
                win32event.WaitForSingleObject(process, 5000)
            process.Close()
        if thread is not None:
            thread.Close()
        if job is not None:
            job.Close()
