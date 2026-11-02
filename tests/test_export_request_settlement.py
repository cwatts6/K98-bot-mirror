"""Durable response/worker regressions; native SQL qualification is separate."""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from core.export_execution_host import HostBoundaryError, PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_contention import CoordinationLockRefused
from services.export_execution_authority import ExecutionUncertain, ExportExecutionAuthority
from services.export_execution_progress import ExecutionProgress
from services.export_execution_protocol import encode
from services.export_proof_progress import AuthorityProofBusy
from services.export_request_settlement import RequestSettlement, fixed_reference
from services.export_saved_result_recovery_dal import journal_digest


def busy():
    return CoordinationLockRefused(
        result=-1, session=1, transaction_state=0, transaction_count=0, resource_hash="a" * 64
    )


@pytest.mark.parametrize("hostname", ["fixture-host", "FiXtUrE-HoSt"])
def test_predecessor_host_lookup_normalizes_parameter_and_closes_connection(hostname):
    from services.export_execution_dal import ExportExecutionDAL

    cursor, connection = Mock(), Mock()
    cursor.description = [("SessionID",)]
    cursor.fetchall.return_value = [("original-session",)]
    connection.cursor.return_value = cursor
    assert ExportExecutionDAL(lambda: connection).open_host_sessions(hostname) == [
        dict(SessionID="original-session")
    ]
    assert cursor.execute.call_args.args[1] == "fixture-host"
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


class Ledger:
    """Inert SQL-contract state for end-to-end service/caller fault injection."""

    connect = staticmethod(lambda: pytest.fail("Unit ledger must not connect to SQL"))

    def __init__(self):
        self.streams, self.requests, self.events = {}, {}, {}
        self.fail_before = self.fail_after = None
        self.transitions = []

    def read_stream(self, identifier):
        return deepcopy(self.streams.get(identifier))

    def read_request(self, identifier):
        return deepcopy(self.requests.get(identifier)), deepcopy(self.events.get(identifier, []))

    def last_request(self, identifier):
        return next(
            (
                key
                for key, value in reversed(tuple(self.requests.items()))
                if value["StreamID"] == identifier
            ),
            None,
        )

    def request_records(self, identifier):
        for key, value in self.requests.items():
            if value["StreamID"] == identifier:
                yield key, deepcopy(value), deepcopy(self.events[key])

    def stream_digest(self, identifier):
        return journal_digest(self.request_records(identifier))

    def transition(self, kind, **values):
        stage = values.get("State", values.get("Action"))
        if self.fail_before == stage:
            self.fail_before = None
            raise busy()
        identifier = values["StreamID"]
        if kind == "stream" and stage == "open":
            row = dict(
                StreamID=identifier,
                SessionID=values["SessionID"],
                ChildIdentity=values["ChildIdentity"],
                AccountKey=values["AccountKey"],
                ActiveAccountKey=values["AccountKey"],
                JobID=values["ObjectID"],
                PreparationID=None,
                OutputOperationID=None,
                OwnerID=values["OwnerID"],
                Fence=values["Fence"],
                ClaimVersion=values["ClaimVersion"],
                NestedToken=None,
                RegistrationHash=values["RegistrationHash"],
                Epoch=None,
                SnapshotHash=values["SnapshotHash"],
                ScopeJson=values["ScopeJson"],
                Purpose=values["Purpose"],
                State="open",
                Version=1,
                LastSequence=0,
                ClosureHash=None,
                ClosureReference=None,
                EventDigest=None,
                CreatedUTC=datetime(2026, 11, 2),
                ClosedUTC=None,
            )
            self.streams[identifier] = row
        else:
            row = self.streams[identifier]
            assert row["Version"] == values["ExpectedVersion"]
            row["Version"] += 1
            if kind == "event":
                request_id = values["RequestID"]
                if stage == "prepared":
                    row["LastSequence"] += 1
                    self.requests[request_id] = dict(
                        RequestID=request_id,
                        StreamID=identifier,
                        Sequence=row["LastSequence"],
                        **{
                            k: values[k]
                            for k in (
                                "Operation",
                                "RequestKind",
                                "TargetID",
                                "PayloadHash",
                                "PayloadReference",
                            )
                        },
                    )
                    self.events[request_id] = []
                events = self.events[request_id]
                events.append(
                    dict(
                        EventSequence=len(events) + 1,
                        **{
                            k: values[k]
                            for k in (
                                "EventID",
                                "RequestID",
                                "State",
                                "EvidenceHash",
                                "EvidenceReference",
                            )
                        },
                    )
                )
            elif stage == "freeze":
                row["State"] = "frozen"
            elif stage == "close":
                assert all(
                    events[-1]["State"] in {"succeeded", "not_sent"}
                    for events in self.events.values()
                )
                row.update(
                    State="closed",
                    ActiveAccountKey=None,
                    ClosedUTC=datetime(2026, 11, 2),
                    **{k: values[k] for k in ("ClosureHash", "ClosureReference", "EventDigest")},
                )
        self.transitions.append(stage)
        if self.fail_after == stage:
            self.fail_after = None
            raise OSError("committed reply lost")
        return deepcopy(row)


@pytest.fixture
def live(tmp_path):
    store = PrivateEvidenceStore(
        tmp_path,
        "fixture",
        protect=lambda raw: b"cipher:" + raw,
        unprotect=lambda raw: raw.removeprefix(b"cipher:"),
    )
    ledger = Ledger()
    completed = Mock()
    settlement = RequestSettlement(
        ledger, store, check_boundary=lambda: None, complete_request=completed
    )
    settlement.execution = ledger
    child = SimpleNamespace(
        identity=str(uuid4()),
        resume=Mock(),
        execute=Mock(return_value={"spreadsheetId": "file", "clearedRange": "A1"}),
    )
    child.birth_evidence = dict(
        child_id=child.identity,
        pid=123,
        job_name="Global\\K98ExportChild-" + "a" * 64,
        machine=dict(machine_guid=str(uuid4()), hostname="fixture-host"),
        authority_sid="S-1-5-21-1",
        limit_flags=0x2000,
        assigned=True,
    )
    child.terminate_and_observe = Mock(
        return_value={"child_id": child.identity, "process_signaled": True, "job_empty": True}
    )
    authority = ExportExecutionAuthority(
        dal=ledger,
        store=store,
        host=SimpleNamespace(create_suspended=lambda _: child),
        budget_factory=lambda _: Mock(),
        session_id=str(uuid4()),
        settlement=settlement,
    )
    scope = dict(
        AccountKey="account",
        OwnerKind="job",
        ObjectID=str(uuid4()),
        OwnerID=str(uuid4()),
        Fence=1,
        ClaimVersion=1,
        NestedToken=None,
        RegistrationHash=b"r" * 32,
        Epoch=None,
        SnapshotHash=b"s" * 32,
        Purpose="mutation",
        ScopeJson=json.dumps(
            {
                "resources": [
                    {"key": "account:account", "version": 1},
                    {"key": "destination:file", "version": 1},
                ]
            }
        ),
    )
    stream = str(uuid4())
    authority.open_stream(stream_id=stream, scope=scope)
    request = dict(
        version=1,
        request_id=str(uuid4()),
        stream_id=stream,
        operation="sheets.values.clear",
        target="file",
        arguments={"range": "A1", "body": {}},
    )
    return SimpleNamespace(
        authority=authority,
        settlement=settlement,
        ledger=ledger,
        store=store,
        completed=completed,
        child=child,
        request=request,
    )


@pytest.mark.parametrize("fault", ["none", "result_busy", "result_reply", "pacing_busy"])
def test_live_caller_converges_without_provider_resend(live, fault):
    f = live
    if fault == "result_busy":
        f.ledger.fail_before = "succeeded"
    if fault == "result_reply":
        f.ledger.fail_after = "succeeded"
    if fault == "pacing_busy":
        f.completed.side_effect = [busy(), None]
    response = f.authority.execute(f.request)
    assert response == f.child.execute.return_value
    assert f.child.execute.call_count == 1
    assert f.ledger.transitions.count("succeeded") == 1
    f.authority.close_stream(f.request["stream_id"])
    assert f.ledger.read_stream(f.request["stream_id"])["State"] == "closed"


def test_locator_exists_before_provider_and_repeated_id_cannot_change_payload(live):
    f = live

    def provider(message):
        locator = f.settlement.locator(message["request_id"])
        assert locator["payload_sha256"] == hashlib.sha256(encode(message)).hexdigest()
        assert f.ledger.events[message["request_id"]][-1]["State"] == "dispatch_intent"
        return {"spreadsheetId": "file", "clearedRange": "A1"}

    f.child.execute.side_effect = provider
    result = f.authority.execute(f.request)
    assert f.authority.execute(f.request) == result
    changed = deepcopy(f.request)
    changed["arguments"]["range"] = "A2"
    with pytest.raises(ExecutionUncertain, match="different payload"):
        f.authority.execute(changed)
    assert f.child.execute.call_count == 1


@pytest.mark.parametrize("stage", ["freeze", "close"])
def test_closure_lost_reply_reconciles_exact_receipt_once(live, stage):
    f = live
    f.authority.execute(f.request)
    f.ledger.fail_after = stage
    f.authority.close_stream(f.request["stream_id"])
    assert f.ledger.transitions.count(stage) == 1
    assert f.child.execute.call_count == f.child.terminate_and_observe.call_count == 1


@pytest.mark.parametrize("failure", [FileNotFoundError, HostBoundaryError, SourceConflict])
@pytest.mark.parametrize("stage", ["locator", "run"])
def test_existing_request_failure_retains_uncertainty_without_dispatch(live, failure, stage):
    f = live
    f.authority.execute(f.request)
    before = deepcopy(f.ledger.transitions)
    error = failure("retained evidence unavailable")
    setattr(f.settlement, stage, Mock(side_effect=error))
    with pytest.raises(ExecutionUncertain, match="requires reconciliation") as raised:
        f.authority.execute(f.request)
    assert raised.value.__cause__ is error
    assert f.authority._streams[f.request["stream_id"]].uncertain
    with pytest.raises(ExecutionUncertain):
        f.authority.execute(dict(f.request, request_id=str(uuid4())))
    assert f.ledger.transitions == before
    assert f.child.execute.call_count == 1


def test_worker_start_failure_is_retained_attention_without_reconstruction(monkeypatch):
    issue = Mock()
    worker = ExecutionProgress(issue)
    selector = dict(action="execute", request=dict(request_id="request"))
    with monkeypatch.context() as patch:
        patch.setattr(
            "services.export_execution_progress.Thread.start",
            Mock(side_effect=RuntimeError("cannot start")),
        )
        with pytest.raises(RuntimeError, match="cannot start"):
            worker.start("request", "account", selector)
    status = worker.poll("request", selector)
    assert status["state"] == "unavailable" and status["needs_attention"] is True
    assert worker.start("request", "account", selector)["needs_attention"] is True
    assert not worker.busy()
    worker.drain()
    issue.assert_not_called()


def test_new_service_recovers_only_fixed_saved_result_without_provider(live):
    f = live
    original = f.settlement.run
    f.settlement.run = Mock(side_effect=RuntimeError("process interruption"))
    with pytest.raises(ExecutionUncertain):
        f.authority.execute(f.request)
    f.settlement.run = original
    fresh = RequestSettlement(
        f.ledger, f.store, check_boundary=lambda: None, complete_request=f.completed
    )
    fresh.execution = f.ledger
    result = fresh.run(f.request["request_id"])
    assert result["response"] == f.child.execute.return_value
    assert f.child.execute.call_count == 1


def test_fixed_storage_keeps_conflicting_and_partial_bytes(live):
    store = live.store
    reference = str(uuid4())
    store.put_fixed(reference, b"first")
    before = {p.name: p.read_bytes() for p in store._store.root.iterdir()}
    with pytest.raises(HostBoundaryError, match="Conflicting"):
        store.put_fixed(reference, b"second")
    assert before == {p.name: p.read_bytes() for p in store._store.root.iterdir()}
    partial = str(uuid4())
    path = store._store._path(UUID(partial).hex)
    path.write_bytes(b"")
    with pytest.raises(HostBoundaryError):
        store.put_fixed(partial, b"complete")
    assert path.read_bytes() == b""


def test_owned_worker_poll_is_passive_duplicate_start_is_one_and_drain_joins():
    entered, release, drained = Event(), Event(), Event()
    calls = []

    def issue(selector, progress):
        calls.append(selector)
        progress("waiting", False)
        entered.set()
        assert release.wait(5)
        return {"ok": True}

    worker = ExecutionProgress(issue)
    selector = {"action": "execute", "request": "fixed"}
    worker.start("request", "account", selector)
    assert entered.wait(2)
    for _ in range(10):
        assert worker.poll("request", selector)["state"] == "waiting"
        worker.start("request", "account", selector)
    with pytest.raises(AuthorityProofBusy):
        worker.start("other", "account", selector)
    thread = Thread(target=lambda: (worker.drain(), drained.set()))
    thread.start()
    assert not drained.wait(0.05)
    release.set()
    thread.join(3)
    assert drained.is_set() and len(calls) == 1
    assert worker.poll("request", selector)["state"] == "complete"


@pytest.mark.parametrize(
    "damage", ["response_missing", "response_id", "payload", "version", "owner", "session", "event"]
)
def test_saved_result_rejects_changed_evidence_without_terminal_write(live, damage):
    f = live
    f.settlement.run = Mock(side_effect=RuntimeError("interrupted"))
    with pytest.raises(ExecutionUncertain):
        f.authority.execute(f.request)
    fresh = RequestSettlement(
        f.ledger, f.store, check_boundary=lambda: None, complete_request=f.completed
    )
    fresh.execution = f.ledger
    request_id = f.request["request_id"]
    row = f.ledger.streams[f.request["stream_id"]]
    if damage.startswith("response"):
        from services.export_evidence_storage import EvidenceCopies

        wrong_id = str(uuid4())
        for key in EvidenceCopies.keys(fixed_reference("response", request_id)):
            path = f.store._store._path(key)
            if damage == "response_missing":
                path.unlink()
            else:
                path.write_bytes(
                    b"cipher:"
                    + encode(dict(request_id=wrong_id, response=f.child.execute.return_value))
                )
    elif damage == "payload":
        f.ledger.requests[request_id]["PayloadHash"] = b"x" * 32
    elif damage == "version":
        row["Version"] += 1
    elif damage in {"owner", "session"}:
        row[{"owner": "OwnerID", "session": "SessionID"}[damage]] = str(uuid4())
    else:
        f.ledger.events[request_id][1]["EventSequence"] = 3
    with pytest.raises((SourceConflict, FileNotFoundError)):
        fresh.run(request_id)
    assert f.ledger.transitions.count("succeeded") == 0
    assert f.child.execute.call_count == 1
    f.completed.assert_not_called()


@pytest.mark.parametrize("partial", [False, True])
def test_saved_response_surviving_replica_is_used_without_overwrite(live, partial):
    f = live
    f.authority.execute(f.request)
    primary = f.store._store._path(UUID(fixed_reference("response", f.request["request_id"])).hex)
    if partial:
        primary.write_bytes(b"")
    else:
        primary.unlink()
    result = f.settlement.run(f.request["request_id"])
    assert result["response"] == f.child.execute.return_value
    assert primary.read_bytes() == b"" if partial else not primary.exists()
    assert f.child.execute.call_count == 1


@pytest.mark.parametrize("saved_seal", [False, True])
@pytest.mark.parametrize("missing_locator", [False, True])
def test_restart_settles_original_request_and_verifies_full_closure(
    live, saved_seal, missing_locator
):
    from services.export_saved_result_restart import SavedResultRestart

    f = live
    if saved_seal:
        f.authority.execute(f.request)
        # Save the original process-handle seal but deny the SQL close itself.
        transition = f.ledger.transition

        def fail_close(kind, **values):
            if values.get("Action") == "close":
                raise ValueError("deny close")
            return transition(kind, **values)

        f.ledger.transition = fail_close
        with pytest.raises(ExecutionUncertain):
            f.authority.close_stream(f.request["stream_id"])
        f.ledger.transition = transition
    else:
        original = f.settlement.run
        f.settlement.run = Mock(side_effect=RuntimeError("interrupted"))
        with pytest.raises(ExecutionUncertain):
            f.authority.execute(f.request)
        f.settlement.run = original
    row = f.ledger.read_stream(f.request["stream_id"])
    f.ledger.open_host_sessions = Mock(
        return_value=[dict(SessionID=row["SessionID"], ManifestHash=b"m" * 32)]
    )
    f.ledger.session_streams = Mock(return_value=[row])

    def retired(birth):
        return dict(
            child_id=birth["child_id"],
            pid=birth["pid"],
            job_empty=True,
            process_terminated=True,
            termination_method="named_job_destroyed",
            job_name_sha256=hashlib.sha256(birth["job_name"].encode()).hexdigest(),
        )

    termination = SimpleNamespace(verify=Mock())
    recovery = SavedResultRestart(
        f.settlement, account="account", hostname="fixture-host", observe_retired=retired
    )
    if missing_locator:
        from services.export_evidence_storage import EvidenceCopies

        for key in EvidenceCopies.keys(fixed_reference("locator", f.request["request_id"])):
            f.store._store._path(key).unlink()
        before = deepcopy(f.ledger.transitions)
        with pytest.raises(SourceConflict, match="Original request locator unavailable"):
            recovery((b"m" * 32).hex(), termination)
        assert f.ledger.transitions == before
        assert f.ledger.read_stream(f.request["stream_id"])["State"] != "closed"
        assert f.child.execute.call_count == 1
        return
    assert recovery((b"m" * 32).hex(), termination) == [f.request["stream_id"]]
    assert f.ledger.read_stream(f.request["stream_id"])["State"] == "closed"
    assert f.ledger.transitions.count("succeeded") == f.ledger.transitions.count("close") == 1
    assert f.child.execute.call_count == 1
    assert termination.verify.call_count >= 3


def test_corrupt_completion_marker_cannot_trigger_another_pacing_write(live):
    f = live
    f.authority.execute(f.request)
    from services.export_evidence_storage import EvidenceCopies

    for key in EvidenceCopies.keys(fixed_reference("settled", f.request["request_id"])):
        f.store._store._path(key).write_bytes(b"")
    with pytest.raises(HostBoundaryError):
        f.settlement.run(f.request["request_id"])
    assert f.completed.call_count == 1


def test_failed_connection_cleanup_refuses_fresh_receipt_connection():
    from services.export_saved_result_recovery_dal import RecoveryConnections

    inner = SimpleNamespace(close=Mock(side_effect=OSError("cleanup unknown")))
    factory = Mock(return_value=inner)
    custody = RecoveryConnections(factory)
    connection = custody.connect()
    with pytest.raises(OSError, match="cleanup unknown"):
        connection.close()
    with pytest.raises(SourceConflict, match="cleanup is unconfirmed"):
        custody.connect()
    assert factory.call_count == 1


def test_unconfirmed_cleanup_is_not_retryable_even_after_transient_failure():
    from services.export_request_settlement import transient

    try:
        raise SourceConflict("cleanup is unconfirmed") from busy()
    except SourceConflict as error:
        assert transient(error) is False


def test_known_commit_wrapper_allows_only_its_retryable_cause():
    from services.export_execution_dal import EvidenceCommitUnknown
    from services.export_request_settlement import transient

    for cause, expected in [(busy(), True), (SourceConflict("binding changed"), False)]:
        try:
            raise EvidenceCommitUnknown("receipt required") from cause
        except EvidenceCommitUnknown as error:
            assert transient(error) is expected


@pytest.mark.parametrize("kind", ["response", "settled"])
def test_replica_write_failure_after_saved_primary_returns_original_response(live, kind):
    f = live
    write = f.store._store.put_fixed
    replica = "replica_" + UUID(fixed_reference(kind, f.request["request_id"])).hex

    def interrupted(key, data):
        if key == replica:
            raise OSError("replica interrupted")
        return write(key, data)

    f.store._store.put_fixed = interrupted
    assert f.authority.execute(f.request) == f.child.execute.return_value
    assert f.child.execute.call_count == 1
    assert f.ledger.transitions.count("succeeded") == 1
    assert f.completed.call_count == 1


def test_close_finishes_pacing_after_terminal_commit_without_resending(live):
    f = live
    f.completed.side_effect = ValueError("pacing interrupted")
    with pytest.raises(ExecutionUncertain):
        f.authority.execute(f.request)
    assert f.ledger.transitions.count("succeeded") == 1
    f.completed.side_effect = None
    f.authority.close_stream(f.request["stream_id"])
    assert f.completed.call_count == 2
    assert f.ledger.read_stream(f.request["stream_id"])["State"] == "closed"
    assert f.child.execute.call_count == 1


def test_drain_retires_every_child_when_one_saved_response_is_missing(live):
    from services.export_execution_authority import OwnedStream

    f = live
    f.settlement.run = Mock(side_effect=FileNotFoundError("response unavailable"))
    with pytest.raises(ExecutionUncertain):
        f.authority.execute(f.request)
    # An independent owned child must still be retired after the first failure.
    other_id = str(uuid4())
    other = SimpleNamespace(identity=str(uuid4()), terminate_and_observe=Mock(return_value={}))
    f.authority._streams[other_id] = OwnedStream(
        other_id, "other-account", 1, other, "mutation", frozenset()
    )
    assert f.authority.drain() is False
    assert f.settlement.stop.is_set()
    assert f.child.terminate_and_observe.call_count == other.terminate_and_observe.call_count == 1
    assert f.ledger.read_stream(f.request["stream_id"])["ActiveAccountKey"] == "account"
    assert f.ledger.transitions.count("succeeded") == 0


@pytest.mark.parametrize("fault", ["initial_read", "close_reply_read", "closure_replica"])
def test_restart_retries_receipt_reads_without_repeating_committed_closure(live, fault):
    from services.export_saved_result_restart import SavedResultRestart

    f = live
    f.authority.execute(f.request)
    initial = f.ledger.read_stream(f.request["stream_id"])
    read, transition = f.ledger.read_stream, f.ledger.transition
    if fault == "closure_replica":
        original_write = f.store._store.put_fixed
        replica = "replica_" + UUID(fixed_reference("closure-5", f.request["stream_id"])).hex

        def write(key, raw):
            if key == replica:
                raise OSError("closure replica interrupted")
            return original_write(key, raw)

        f.store._store.put_fixed = write
    failed = [fault == "initial_read"]

    def receipt(identifier):
        if failed[0]:
            failed[0] = False
            raise busy()
        return read(identifier)

    def close(kind, **values):
        result = transition(kind, **values)
        if fault == "close_reply_read" and values.get("Action") == "close":
            failed[0] = True
            raise OSError("committed close reply lost")
        return result

    f.ledger.read_stream, f.ledger.transition = receipt, close
    termination = SimpleNamespace(verify=Mock())
    recovery = SavedResultRestart(
        f.settlement, account="account", hostname="fixture-host", observe_retired=Mock()
    )
    recovery._close(initial, f.child.terminate_and_observe(), termination)
    assert read(f.request["stream_id"])["State"] == "closed"
    assert f.ledger.transitions.count("close") == 1
    assert f.child.execute.call_count == 1
    assert termination.verify.call_count >= 3


def test_live_closure_reconciles_saved_primary_without_repeating_provider(live):
    f = live
    f.authority.execute(f.request)
    original = f.store._store.put_fixed
    replica = "replica_" + UUID(fixed_reference("closure-5", f.request["stream_id"])).hex

    def write(key, raw):
        if key == replica:
            raise OSError("closure replica interrupted")
        return original(key, raw)

    f.store._store.put_fixed = write
    f.authority.close_stream(f.request["stream_id"])
    assert f.ledger.transitions.count("close") == f.child.execute.call_count == 1


def test_locator_replica_failure_still_prevents_provider_dispatch(live):
    f = live
    original = f.store._store.put_fixed
    replica = "replica_" + UUID(fixed_reference("locator", f.request["request_id"])).hex

    def write(key, raw):
        if key == replica:
            raise OSError("locator replica interrupted")
        return original(key, raw)

    f.store._store.put_fixed = write
    with pytest.raises(ExecutionUncertain):
        f.authority.execute(f.request)
    f.child.execute.assert_not_called()
    assert "dispatch_intent" not in f.ledger.transitions


@pytest.mark.parametrize("fault", ["sql_read", "private_evidence"])
def test_replacement_drain_retires_children_and_continues_parent_on_failure(
    live, monkeypatch, fault
):
    from services.export_execution_authority import OwnedStream
    from services.export_replacement_verification import ReplacementVerificationPlan

    f = live
    f.authority.enrollment_plan = Mock(spec=ReplacementVerificationPlan, digest=b"r" * 32)
    if fault == "sql_read":
        f.ledger.read_stream = Mock(side_effect=OSError("SQL unavailable"))
    else:
        f.ledger.streams[f.request["stream_id"]]["State"] = "read_contained"
        monkeypatch.setattr(
            "services.export_replacement_read_containment.verify_discarded_replacement",
            Mock(side_effect=SourceConflict("private evidence missing")),
        )
    parent = ExportExecutionAuthority(
        dal=f.ledger,
        store=f.store,
        host=Mock(),
        budget_factory=Mock(),
        session_id=str(uuid4()),
        settlement=f.settlement,
    )
    sibling = Mock()
    sibling.drain.return_value = True
    parent._replacement_readers.update(failed=f.authority, sibling=sibling)
    other_id = str(uuid4())
    other = SimpleNamespace(identity=str(uuid4()), terminate_and_observe=Mock(return_value={}))
    parent._streams[other_id] = OwnedStream(other_id, "other", 1, other, "mutation", frozenset())
    assert parent.drain() is False
    assert f.child.terminate_and_observe.call_count == other.terminate_and_observe.call_count == 1
    sibling.drain.assert_called_once()
    assert not f.authority._streams[f.request["stream_id"]].closed
    assert "close" not in f.ledger.transitions


def test_long_contention_reports_once_and_diagnostic_failure_cannot_change_result(
    live, monkeypatch
):
    f = live
    now, delays = [0], []
    f.settlement.clock = lambda: now[0]

    def wait(delay):
        delays.append(delay)
        now[0] += 310
        return False

    f.settlement.stop = SimpleNamespace(wait=wait)
    original = f.ledger.transition
    remaining = [3]

    def transition(kind, **values):
        if values.get("State") == "succeeded" and remaining[0]:
            remaining[0] -= 1
            raise busy()
        return original(kind, **values)

    f.ledger.transition = transition
    notices = []

    def diagnostic(stage, **kwargs):
        if stage == "AUTHORITY_RESULT_SETTLEMENT_WAITING":
            notices.append(stage)
            raise OSError("diagnostic unavailable")

    monkeypatch.setattr("services.export_authority_diagnostics.report_authority_event", diagnostic)
    progress = Mock()
    f.authority._progress.callback = progress
    assert f.authority.execute(f.request) == f.child.execute.return_value
    assert notices == ["AUTHORITY_RESULT_SETTLEMENT_WAITING"]
    assert delays == [0.25, 30, 30]
    progress.assert_any_call("waiting", True)
    assert f.child.execute.call_count == 1


def test_request_and_stream_ids_can_match_without_progress_collision():
    from time import monotonic, sleep

    calls = []
    worker = ExecutionProgress(lambda selector, _: calls.append(selector["action"]) or {})
    identifier = str(uuid4())
    for action in ("execute", "close"):
        selector = dict(action=action)
        worker.start(identifier, "account", selector)
        deadline = monotonic() + 3
        while worker.busy() and monotonic() < deadline:
            sleep(0.001)
        assert worker.poll(identifier, selector)["state"] == "complete"
    worker.drain()
    assert calls == ["execute", "close"]
