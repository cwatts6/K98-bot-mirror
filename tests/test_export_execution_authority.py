from datetime import datetime
import hashlib
import json
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from services.export_execution_authority import ExecutionUncertain, ExportExecutionAuthority


class Store:
    def __init__(self):
        self.records = []

    def put(self, data):
        self.records.append(data)
        return SimpleNamespace(key=uuid4().hex, sha256=hashlib.sha256(data).hexdigest())


class DAL:
    def __init__(self):
        self.calls, self.requests = [], set()
        self.fail = None
        self.version = 0

    def transition(self, kind, **values):
        self.calls.append((kind, values))
        if kind == "event":
            self.requests.add(values["RequestID"])
        self.version += 1
        # Simulate a committed result whose acknowledgment is lost.
        if self.fail == values.get("State", values.get("Action")):
            raise RuntimeError("lost acknowledgment")
        return {"Version": self.version}

    def read_request(self, identifier):
        return ({"RequestID": identifier} if identifier in self.requests else None), []

    def stream_digest(self, stream_id):
        return len(self.requests), b"d" * 32


class Child:
    def __init__(self, identity):
        self.identity, self.calls = identity, []
        self.resumed = self.terminated = False
        self.fail = False

    def resume(self):
        self.resumed = True

    def execute(self, request):
        self.calls.append(request)
        if self.fail:
            raise TimeoutError("response lost")
        return dict(
            spreadsheetId="registered_file",
            updatedRange="Sheet1!A1",
            updatedRows=1,
            updatedColumns=1,
            updatedCells=1,
        )

    def terminate_and_observe(self):
        self.terminated = True
        return {"child_id": self.identity, "process_signaled": True, "job_empty": True}


@pytest.fixture
def runtime():
    dal, store = DAL(), Store()
    children = []

    def create(identity):
        child = Child(identity)
        children.append(child)
        return child

    class Budget:
        fail_reserve = fail_complete = False

        def __call__(self):
            if self.fail_reserve:
                raise RuntimeError("reserve unknown")

        def completed(self):
            if self.fail_complete:
                raise RuntimeError("checkpoint unknown")

    budget = Budget()
    authority = ExportExecutionAuthority(
        dal=dal,
        store=store,
        host=SimpleNamespace(create_suspended=create),
        budget_factory=lambda _: budget,
        session_id=str(uuid4()),
    )
    scope = dict(
        AccountKey="test",
        OwnerKind="job",
        ObjectID=str(uuid4()),
        OwnerID=str(uuid4()),
        Fence=1,
        ClaimVersion=1,
        NestedToken=None,
        RegistrationHash=b"r" * 32,
        Epoch=None,
        SnapshotHash=b"s" * 32,
        ScopeJson=json.dumps(
            {
                "resources": [
                    {"key": "account:test", "version": 1},
                    {"key": "destination:registered_file", "version": 1},
                ]
            }
        ),
        Purpose="mutation",
    )
    stream = str(uuid4())
    authority.open_stream(stream_id=stream, scope=scope)
    request = dict(
        version=1,
        request_id=str(uuid4()),
        stream_id=stream,
        operation="sheets.values.update",
        target="registered_file",
        arguments={"range": "Sheet1!A1", "valueInputOption": "RAW", "body": {"values": [[1]]}},
    )
    return authority, dal, store, children[0], budget, request


def test_success_commits_events_before_return_and_duplicate_does_not_send(runtime):
    authority, dal, store, child, budget, request = runtime
    assert authority.execute(request)["updatedCells"] == 1
    assert [v["State"] for k, v in dal.calls if k == "event"] == [
        "prepared",
        "dispatch_intent",
        "succeeded",
    ]
    with pytest.raises(ExecutionUncertain):
        authority.execute(request)
    assert len(child.calls) == 1
    assert len(store.records) == 4


@pytest.mark.parametrize(
    "failure, sends", [("prepared", 0), ("dispatch_intent", 0), ("succeeded", 1)]
)
def test_lost_sql_ack_never_replays_provider(runtime, failure, sends):
    authority, dal, store, child, budget, request = runtime
    dal.fail = failure
    with pytest.raises(ExecutionUncertain):
        authority.execute(request)
    with pytest.raises(ExecutionUncertain):
        authority.execute(request | {"request_id": str(uuid4())})
    assert len(child.calls) == sends
    assert not any(v.get("State") == "not_sent" for _, v in dal.calls)


@pytest.mark.parametrize("location", ["provider", "budget_reserve", "budget_complete"])
def test_interruption_retains_stream_and_never_guesses_absence(runtime, location):
    authority, dal, store, child, budget, request = runtime
    child.fail = location == "provider"
    budget.fail_reserve = location == "budget_reserve"
    budget.fail_complete = location == "budget_complete"
    with pytest.raises(ExecutionUncertain):
        authority.execute(request)
    assert authority._streams[request["stream_id"]].uncertain
    assert not any(v.get("State") == "not_sent" for _, v in dal.calls)
    if location == "budget_complete":
        assert dal.calls[-1][1]["State"] == "succeeded"


def test_close_freezes_before_observing_child_then_closes_sql(runtime):
    authority, dal, store, child, budget, request = runtime
    authority.execute(request)
    result = authority.close_stream(request["stream_id"])
    assert child.terminated and result["stream_id"] == request["stream_id"]
    assert [v.get("Action") for k, v in dal.calls if k == "stream"] == [
        "open",
        "freeze",
        "close",
    ]
    with pytest.raises(ExecutionUncertain):
        authority.execute(request | {"request_id": str(uuid4())})


def test_lost_freeze_ack_does_not_claim_process_termination(runtime):
    authority, dal, store, child, budget, request = runtime
    dal.fail = "freeze"
    with pytest.raises(ExecutionUncertain):
        authority.close_stream(request["stream_id"])
    assert not child.terminated
    assert not any(v.get("Action") == "close" for _, v in dal.calls)


def test_restart_does_not_adopt_an_old_stream(runtime):
    old, dal, store, child, budget, request = runtime
    new = ExportExecutionAuthority(
        dal=dal,
        store=store,
        host=old.host,
        budget_factory=lambda _: budget,
        session_id=str(uuid4()),
    )
    with pytest.raises(ExecutionUncertain):
        new.execute(request)
    assert not child.calls


def test_probe_cannot_mutate_and_destination_cannot_escape(runtime):
    authority, dal, store, child, budget, request = runtime
    authority._streams[request["stream_id"]].purpose = "probe"
    with pytest.raises(ValueError):
        authority.execute(request)
    authority._streams[request["stream_id"]].purpose = "mutation"
    with pytest.raises(ValueError):
        authority.execute(request | {"target": "other_file"})
    assert not child.calls


def test_shutdown_closes_admission_but_drains_owned_delivery(runtime):
    authority, dal, store, child, budget, request = runtime
    authority.stop()
    assert authority.execute(request)["updatedCells"] == 1
    authority.close_stream(request["stream_id"])
    assert child.terminated
    with pytest.raises(ExecutionUncertain):
        authority.execute(request | {"request_id": str(uuid4())})


def test_execution_uncertainty_uses_worker_claim_retention_contract():
    from services.export_request_budget import BudgetCompletionUnknown

    assert isinstance(ExecutionUncertain("unresolved"), BudgetCompletionUnknown)


def test_shutdown_drains_live_child_but_never_closes_uncertain_freeze(runtime):
    authority, dal, store, child, budget, request = runtime
    assert authority.drain() is True
    assert child.terminated
    assert authority._streams[request["stream_id"]].closed is True
    with pytest.raises(ExecutionUncertain):
        authority.open_stream(stream_id=str(uuid4()), scope={})


def test_shutdown_keeps_unacknowledged_closure_retained(runtime):
    authority, dal, store, child, budget, request = runtime
    dal.fail = "freeze"
    assert authority.drain() is False
    assert authority._streams[request["stream_id"]].uncertain
    assert not child.terminated


def test_dal_does_not_acknowledge_row_before_commit_completion():
    from services.export_execution_dal import EvidenceCommitUnknown, ExportExecutionDAL

    class Cursor:
        description = (("Version",),)

        def execute(self, *_):
            return self

        def fetchone(self):
            return (1,)

        def fetchall(self):
            return []

        def nextset(self):
            raise RuntimeError("commit acknowledgment lost after SELECT")

        def close(self):
            pass

    connection = SimpleNamespace(autocommit=False, cursor=Cursor, close=lambda: None)
    dal = ExportExecutionDAL(lambda: connection)
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition("session", SessionID=str(uuid4()), Action="open", ExpectedVersion=0)


@pytest.fixture
def proof_persistence():
    from services.export_execution_dal import ExportExecutionDAL

    values = dict(
        SessionID=str(uuid4()),
        ProofID=str(uuid4()),
        AccountKey="shared:account",
        SnapshotHash=b"s" * 32,
        RegistrationHash=b"r" * 32,
        ProofKind="publication",
        Outcome="confirmed",
        MembershipJson=json.dumps(
            dict(
                version=2,
                targets=["index_file", "slot_file_a", "slot_file_b"],
                history=dict(count=3, sha256="a" * 64),
                probe=dict(stream_id=str(uuid4()), version=4),
            ),
            indent=2,
        ),
        EvidenceJson=json.dumps(
            dict(state="confirmed", snapshot_hash=(b"s" * 32).hex(), receipt="line\n\u00e9"),
            indent=2,
        ),
    )
    row = dict(
        values,
        MembershipHash=hashlib.sha256(values["MembershipJson"].encode("utf-16-le")).digest(),
        CreatedUTC=datetime(2026, 9, 24, 12, 0, 0, 123000),
    )
    state = SimpleNamespace(
        values=values,
        row=row,
        calls=[],
        fault=None,
        completed=False,
        cursor_closed=False,
        connection_closed=False,
        connects=0,
    )

    class Cursor:
        description = None

        def execute(self, sql, *params):
            state.calls.append((sql, params))
            self.description = tuple((name,) for name in row)
            if state.fault == "duplicate_column":
                self.description += (("ProofID",),)
            return self

        def fetchone(self):
            if state.fault == "missing_row":
                return None
            return tuple(row[name] for (name,) in self.description)

        def fetchall(self):
            if state.fault == "duplicate_row" or self.description == (("Unexpected",),):
                return [(1,)]
            return []

        def nextset(self):
            if state.fault == "lost_commit":
                raise RuntimeError("COMMIT acknowledgment lost after SELECT")
            if state.fault == "extra_result":
                self.description = (("Unexpected",),)
                return True
            state.completed = True
            return None

        def close(self):
            state.cursor_closed = True

    def close():
        state.connection_closed = True

    connection = SimpleNamespace(autocommit=False, cursor=Cursor, close=close)

    def connect():
        state.connects += 1
        return connection

    state.dal = ExportExecutionDAL(connect)
    return state


@pytest.mark.parametrize(
    "kind,outcome",
    [
        ("publication", "confirmed"),
        ("publication", "absent"),
        ("publication", "damaged"),
        ("retirement", "confirmed"),
        ("retirement_recovery", "confirmed"),
        ("rollover_drain", "confirmed"),
        ("rollover_complete", "completed"),
    ],
)
@pytest.mark.parametrize("sql_uuid", [str.upper, UUID])
def test_proof_acknowledgment_binds_exact_receipts_after_commit(
    proof_persistence, kind, outcome, sql_uuid
):
    state = proof_persistence
    state.values.update(ProofKind=kind, Outcome=outcome)
    state.values["EvidenceJson"] = state.values["EvidenceJson"].replace("confirmed", outcome)
    state.row.update(state.values)
    for name in ("SessionID", "ProofID"):
        state.row[name] = sql_uuid(state.row[name])
    state.row["MembershipHash"] = memoryview(state.row["MembershipHash"])
    result = state.dal.transition("proof", **state.values)
    assert {name: result[name] for name in state.values} == state.values
    assert state.completed and state.cursor_closed and state.connection_closed
    assert state.connects == len(state.calls) == 1
    sql, params = state.calls[0]
    assert sql.startswith("EXEC dbo.usp_ExportReconciliationProofIssue ")
    assert params == tuple(state.values.values())
    assert state.values["MembershipJson"] not in sql
    assert state.values["EvidenceJson"] not in sql


@pytest.mark.parametrize(
    "name",
    [
        "SessionID",
        "ProofID",
        "AccountKey",
        "SnapshotHash",
        "RegistrationHash",
        "ProofKind",
        "Outcome",
        "MembershipJson",
        "EvidenceJson",
        "MembershipHash",
        "CreatedUTC",
    ],
)
def test_proof_acknowledgment_rejects_missing_columns(proof_persistence, name):
    from services.export_execution_dal import EvidenceCommitUnknown

    state = proof_persistence
    state.row.pop(name)
    with pytest.raises(EvidenceCommitUnknown):
        state.dal.transition("proof", **state.values)
    assert state.connects == len(state.calls) == 1
    assert state.cursor_closed and state.connection_closed


@pytest.mark.parametrize(
    "name,value",
    [
        ("SessionID", str(uuid4())),
        ("ProofID", str(uuid4())),
        ("ProofID", 42),
        ("AccountKey", "SHARED:account"),
        ("SnapshotHash", b"x" * 32),
        ("RegistrationHash", b"x" * 32),
        ("SnapshotHash", [115] * 32),
        ("RegistrationHash", b"r" * 31),
        ("ProofKind", "retirement"),
        ("Outcome", "absent"),
        ("MembershipHash", b"x" * 32),
        ("MembershipHash", b"x" * 31),
        ("CreatedUTC", "2026-09-24T12:00:00.123"),
        ("CreatedUTC", None),
        ("Extra", "value"),
        ("MembershipJson", "reserialized"),
        ("EvidenceJson", "reserialized"),
    ],
)
def test_proof_acknowledgment_rejects_changed_identity_without_retry(
    proof_persistence, name, value
):
    from services.export_execution_dal import EvidenceCommitUnknown

    state = proof_persistence
    state.row[name] = (
        json.dumps(json.loads(state.values[name]), sort_keys=True)
        if value == "reserialized"
        else value
    )
    with pytest.raises(EvidenceCommitUnknown):
        state.dal.transition("proof", **state.values)
    assert state.completed
    assert state.connects == len(state.calls) == 1
    assert state.cursor_closed and state.connection_closed


@pytest.mark.parametrize(
    "fault", ["missing_row", "duplicate_row", "duplicate_column", "extra_result", "lost_commit"]
)
def test_proof_acknowledgment_retains_uncertainty_after_batch_failure(proof_persistence, fault):
    from services.export_execution_dal import EvidenceCommitUnknown

    state = proof_persistence
    state.fault = fault
    with pytest.raises(EvidenceCommitUnknown):
        state.dal.transition("proof", **state.values)
    assert state.connects == len(state.calls) == 1
    assert state.cursor_closed and state.connection_closed


@pytest.mark.parametrize(
    "name,value",
    [
        ("SessionID", "invalid"),
        ("ProofID", UUID(int=1)),
        ("AccountKey", "account "),
        ("AccountKey", "a" * 129),
        ("AccountKey", None),
        ("SnapshotHash", [115] * 32),
        ("SnapshotHash", b"s" * 33),
        ("RegistrationHash", b"r" * 31),
        ("ProofKind", "unknown"),
        ("ProofKind", []),
        ("Outcome", "completed"),
        ("MembershipJson", "{}"),
        pytest.param("MembershipJson", " " * 65537, id="membership-oversize"),
        ("EvidenceJson", "{}"),
        ("EvidenceJson", "[]"),
        pytest.param("EvidenceJson", " " * 65537, id="evidence-oversize"),
        ("EvidenceJson", '{"state":"confirmed","state":"absent"}'),
        ("EvidenceJson", '{"number":NaN}'),
        ("EvidenceJson", None),
    ],
)
def test_proof_request_rejected_before_sql(proof_persistence, name, value):
    state = proof_persistence
    state.values[name] = value
    with pytest.raises(ValueError):
        state.dal.transition("proof", **state.values)
    assert state.connects == 0 and state.calls == []


@pytest.mark.parametrize(
    "missing",
    [
        "SessionID",
        "ProofID",
        "AccountKey",
        "SnapshotHash",
        "RegistrationHash",
        "ProofKind",
        "Outcome",
        "MembershipJson",
        "EvidenceJson",
    ],
)
def test_proof_request_requires_complete_identity_before_sql(proof_persistence, missing):
    state = proof_persistence
    state.values.pop(missing)
    with pytest.raises(ValueError):
        state.dal.transition("proof", **state.values)
    assert state.connects == 0 and state.calls == []


def test_proof_request_freezes_mutable_hashes_before_opening_sql(proof_persistence):
    state = proof_persistence
    snapshot, registration = bytearray(b"s" * 32), bytearray(b"r" * 32)
    state.values.update(SnapshotHash=snapshot, RegistrationHash=memoryview(registration))
    original_connect = state.dal.connect

    def connect():
        snapshot[:] = b"x" * 32
        registration[:] = b"x" * 32
        return original_connect()

    state.dal.connect = connect
    result = state.dal.transition("proof", **state.values)
    assert result["SnapshotHash"] == b"s" * 32
    assert result["RegistrationHash"] == b"r" * 32
    assert state.calls[0][1][3:5] == (b"s" * 32, b"r" * 32)


def test_freeze_and_dispatch_are_serialized(runtime):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    authority, dal, store, child, budget, request = runtime
    entered, release = threading.Event(), threading.Event()
    original = child.execute

    def blocked(message):
        entered.set()
        assert release.wait(5)
        return original(message)

    child.execute = blocked
    with ThreadPoolExecutor(max_workers=2) as pool:
        sending = pool.submit(authority.execute, request)
        assert entered.wait(5)
        closing = pool.submit(authority.close_stream, request["stream_id"])
        assert not child.terminated
        release.set()
        sending.result(timeout=5)
        closing.result(timeout=5)
    order = [v.get("State", v.get("Action")) for _, v in dal.calls]
    assert order.index("succeeded") < order.index("freeze") < order.index("close")


def test_child_handshake_failure_retains_claim_and_returns_authority_control(runtime, monkeypatch):
    from core.export_execution_host import HostBoundaryError

    authority, dal, store, child, budget, request = runtime
    scope = {
        k: v
        for k, v in dal.calls[0][1].items()
        if k not in {"SessionID", "StreamID", "Action", "ExpectedVersion", "ChildIdentity"}
    }
    stream_id = str(uuid4())
    original = Child.resume

    def stalled(_):
        raise HostBoundaryError("IPC deadline expired")

    monkeypatch.setattr(Child, "resume", stalled)
    with pytest.raises(ExecutionUncertain, match="startup"):
        authority.open_stream(stream_id=stream_id, scope=scope)
    retained = authority._streams[stream_id]
    assert retained.frozen and retained.uncertain and retained.child.terminated
    assert [v["Action"] for kind, v in dal.calls if kind == "stream"] == ["open", "open"]
    assert not any(kind == "event" for kind, _ in dal.calls)
    monkeypatch.setattr(Child, "resume", original)
    next_id = str(uuid4())
    assert authority.open_stream(stream_id=next_id, scope=scope) == next_id
