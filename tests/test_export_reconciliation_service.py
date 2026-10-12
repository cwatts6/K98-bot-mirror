"""Offline trust-boundary tests; no SQL, provider or process execution."""

from contextlib import nullcontext
import json
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import ExportCoordinationDAL
from services.export_execution_dal import ExportExecutionDAL


class ProofCursor:
    def __init__(self, proof, active=None):
        self.proof, self.active, self.statements = proof, active, []
        self.origins = [
            dict(FileID=file_id, Stage="eligible", PreparationState="completed")
            for file_id in json.loads(proof["MembershipJson"])["targets"]
        ]
        member = json.loads(proof["MembershipJson"])["probe"]
        self.catalogue = [
            dict(
                StreamID=member["stream_id"],
                Version=member["version"],
                State="closed",
                ActiveAccountKey=None,
                AccountKey=proof["AccountKey"],
                ClosureHash=b"c" * 32,
                EventDigest=b"e" * 32,
                Purpose="probe",
                SnapshotHash=proof["SnapshotHash"],
                RegistrationHash=proof["RegistrationHash"],
            )
        ]

    def execute(self, statement, *values):
        self.statements.append((statement, values))
        assert statement.startswith(
            ("SELECT", "WITH catalogue_scope")
        ), "Unexpected mutation before proof validation"
        if "SELECT o.*" in statement:
            self.description = tuple((k,) for k in self.origins[0]) if self.origins else ()
            self.batch = [tuple(r.values()) for r in self.origins]
            return self
        if "OPENJSON(s.ScopeJson" in statement:
            self.description = tuple((k,) for k in self.catalogue[0]) if self.catalogue else ()
            self.batch = [tuple(r.values()) for r in self.catalogue]
            return self
        row = self.active if "ActiveAccountKey" in statement else self.proof
        self.description = tuple((k,) for k in row) if row else ()
        self.row = tuple(row.values()) if row else None
        return self

    def fetchone(self):
        return self.row

    def fetchmany(self, size):
        result, self.batch = self.batch[:size], self.batch[size:]
        return result

    def fetchall(self):
        result, self.batch = self.batch, []
        return result


def proof_fixture():
    snapshot = dict(
        job=dict(
            JobID=str(uuid4()),
            AccountKey="account-a",
            State="confirmed",
            Version=7,
            ProvenanceJson="{}",
        ),
        resources=[],
        pool=dict(
            pool=dict(RegistrationHash="ab" * 32, IndexFileID="file-index"),
            slots=[dict(FileID="file-a", State="free"), dict(FileID="file-b", State="free")],
        ),
    )
    body = dict(
        snapshot_hash=digest(snapshot).hex(),
        state="damaged",
        writer_terminated=True,
        evidence_id=str(uuid4()),
    )
    row = dict(
        AccountKey="account-a",
        ProofKind="publication",
        SnapshotHash=digest(snapshot),
        RegistrationHash=bytes.fromhex("ab" * 32),
        Outcome="damaged",
        EvidenceJson=json.dumps(body),
    )
    import hashlib

    from services.export_execution_protocol import CATALOGUE_SEED

    membership = dict(
        version=2,
        targets=["file-a", "file-b", "file-index"],
        history=dict(count=0, sha256=CATALOGUE_SEED.hex()),
        probe=dict(stream_id=str(uuid4()), version=5),
    )
    row["MembershipJson"] = json.dumps(membership)
    row["MembershipHash"] = hashlib.sha256(row["MembershipJson"].encode("utf-16-le")).digest()
    reference = dict(proof_id=str(uuid4()), state="confirmed", writer_terminated=False)
    return snapshot, row, reference


@pytest.mark.parametrize(
    "kind",
    ["publication", "retirement", "retirement_recovery", "rollover_drain", "rollover_complete"],
)
@pytest.mark.parametrize(
    "failure",
    [None, "probe", "stale", "foreign_host", "private_readback", "commit_unknown", "boundary"],
)
def test_fixed_issuer_uses_private_observation_and_exact_sql_identity_only(
    monkeypatch, tmp_path, kind, failure
):
    from dataclasses import make_dataclass
    from pathlib import Path
    import threading
    from types import SimpleNamespace

    from core.export_execution_host import DeploymentBoundary, HostBoundaryError
    from scripts.run_export_authority import AuthorityBroker
    from services.export_execution_dal import EvidenceCommitUnknown
    from services.export_reconciliation_service import TrustedProofIssuer
    from services.export_runtime_composition import LocalAuthorityClient, RuntimeRegistration
    from services.export_snapshot_store import SnapshotReceipt
    from tests.test_export_execution_host import deployment_fixture

    manifest, _, reads = deployment_fixture(tmp_path)
    boundary = DeploymentBoundary(manifest, **reads)
    registration = RuntimeRegistration(manifest["runtime_registration"])
    pool = dict(AccountKey="account-a", IndexFileID="index-0", RegistrationHash="a" * 64)
    context = dict(pool=pool, slots=[dict(FileID="slot-0-0"), dict(FileID="slot-0-1")])
    job = dict(
        JobID=str(uuid4()),
        AccountKey="account-a",
        OwnerID=str(uuid4()),
        Fence=2,
        Version=3,
        IntentID=str(uuid4()),
    )
    operator = dict(job=job, pool=context, resources=[])
    snapshot = context if kind == "retirement" else operator
    consumed = context if kind == "rollover_drain" else snapshot
    fingerprint = digest(consumed).hex()
    current, old = (str(uuid4()), str(uuid4())) if kind == "retirement" else (None, None)
    observed = SimpleNamespace(
        state="confirmed",
        snapshot_hash=fingerprint,
        registration_hash="a" * 64,
        receipt_json='{"byte_exact":"receipt"}',
        original_clears_json='{"file":"clear"}',
        setup_json='{"setup":"marker"}',
    )
    # Existing producer suites test the real evaluator/replay. This test exercises
    # all issuer branches and the boundary/transaction seam without any SDK or SQL.
    Observation = make_dataclass("FixtureObservation", [(k, str) for k in vars(observed)])
    observation = Observation(**vars(observed))
    attr, module, name = {
        "publication": (
            "publication",
            "services.export_reconciliation_service",
            "PublicationProbe",
        ),
        "retirement": ("retirement", "services.export_retirement_evidence", "RetirementProbe"),
        "retirement_recovery": (
            "recovery",
            "services.export_retirement_recovery_evidence",
            "RetirementRecoveryProbe",
        ),
        "rollover_drain": ("drain", "services.export_rollover_evidence", "RolloverDrainProbe"),
        "rollover_complete": (
            "completion",
            "services.export_rollover_evidence",
            "RolloverCompletionProbe",
        ),
    }[kind]
    Sealed = make_dataclass("FixtureSealed", [(attr, Observation), ("membership_json", str)])
    sealed = Sealed(observation, '{"fixture":"sealed membership"}')
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = operator
    pools = Mock(execution_evidence=True)
    pools.operation_snapshot.return_value = operator
    pools.retirement_snapshot.return_value = context
    monkeypatch.setattr(RuntimeRegistration, "sheets", lambda *_: object())
    probe = Mock(return_value=sealed)
    if failure == "probe":
        probe.side_effect = SourceConflict("Unknown outcome in closed catalogue")
    monkeypatch.setattr(module + "." + name, lambda **_: SimpleNamespace(run=probe))
    stored = {}

    def put(data):
        import hashlib

        receipt = SnapshotReceipt(
            uuid4().hex, len(data), hashlib.sha256(data).hexdigest(), "fixture"
        )
        stored[receipt.key] = data
        return receipt

    dal = Mock()
    dal.read_catalogue.side_effect = lambda *_: (dict(SessionID=str(uuid4())) for _ in range(1))
    dal.read_session.return_value = dict(
        HostIdentity="foreign" if failure == "foreign_host" else "fixture-host"
    )
    if failure == "commit_unknown":
        dal.transition.side_effect = EvidenceCommitUnknown("Commit acknowledgement lost")
    authority = SimpleNamespace(
        dal=dal,
        store=SimpleNamespace(
            put=put,
            read=lambda receipt: (
                b"corrupt" if failure == "private_readback" else stored[receipt.key]
            ),
        ),
        _lock=threading.RLock(),
        _closed=False,
        session_id=str(uuid4()),
        enrollment_plan=None,
    )
    broker = AuthorityBroker(authority, registration)
    issuer = TrustedProofIssuer(
        authority=authority,
        boundary=boundary,
        registration=registration,
        coordinator=coordinator,
        pools=pools,
        client=LocalAuthorityClient(broker),
    )
    if failure == "boundary":
        Path(manifest["credentials_file"]).write_bytes(b"drift")
    args = dict(
        kind=kind,
        object_id=job["JobID"],
        snapshot_hash="f" * 64 if failure == "stale" else fingerprint,
        current_attempt_id=current,
        old_attempt_id=old,
    )
    if failure:
        with pytest.raises((SourceConflict, HostBoundaryError)):
            issuer.issue(**args)
        assert dal.transition.call_count == int(failure == "commit_unknown")
        if failure in {"stale", "boundary"}:
            probe.assert_not_called()
    else:
        result = issuer.issue(**args)
        values = dal.transition.call_args.kwargs
        assert dal.transition.call_count == 1 and dal.transition.call_args.args == ("proof",)
        assert values["ProofID"] == result["proof_id"]
        assert values["SessionID"] == authority.session_id
        assert values["SnapshotHash"] == bytes.fromhex(fingerprint)
        assert values["MembershipJson"] == sealed.membership_json
        assert json.loads(values["EvidenceJson"]) == {
            k: v for k, v in result.items() if k != "proof_id"
        }
        assert json.loads(stored[result["evidence_id"]])["deployment_hash"] == boundary.fingerprint
        assert result["state"] == ("completed" if kind == "rollover_complete" else "confirmed")


def test_settlement_ignores_all_caller_flags_and_loads_registration_bound_body():
    snapshot, row, reference = proof_fixture()
    cursor = ProofCursor(row)
    result = ExportExecutionDAL.settlement_proof(
        cursor, reference, snapshot=snapshot, account="account-a", kind="publication"
    )
    assert result["state"] == "damaged" and result["writer_terminated"] is True
    assert result["proof_id"] == reference["proof_id"]
    assert "proof_id" not in json.loads(row["EvidenceJson"])
    assert len(cursor.statements) == 4
    assert "UPDLOCK,HOLDLOCK" in cursor.statements[-1][0]


@pytest.mark.parametrize(
    "change",
    [
        {"AccountKey": "other"},
        {"ProofKind": "retirement"},
        {"SnapshotHash": b"x" * 32},
        {"RegistrationHash": b"x" * 32},
        {"Outcome": "confirmed"},
        {"EvidenceJson": "{}"},
    ],
)
def test_changed_proof_scope_or_body_cannot_authorize_settlement(change):
    snapshot, row, reference = proof_fixture()
    with pytest.raises(SourceConflict):
        ExportExecutionDAL.settlement_proof(
            ProofCursor(row | change),
            reference,
            snapshot=snapshot,
            account="account-a",
            kind="publication",
        )


@pytest.mark.parametrize("reference", [{}, {"proof_id": "invented"}, None])
def test_caller_proof_flags_are_not_a_proof_identity(reference):
    snapshot, row, _ = proof_fixture()
    cursor = ProofCursor(row)
    with pytest.raises(SourceConflict):
        ExportExecutionDAL.settlement_proof(
            cursor, reference, snapshot=snapshot, account="account-a", kind="publication"
        )
    assert not cursor.statements


def test_active_probe_blocks_even_an_immutable_matching_proof():
    snapshot, row, reference = proof_fixture()
    with pytest.raises(SourceConflict, match="still owns"):
        ExportExecutionDAL.settlement_proof(
            ProofCursor(row, active={"StreamID": str(uuid4())}),
            reference,
            snapshot=snapshot,
            account="account-a",
            kind="publication",
        )


@pytest.mark.parametrize(
    "damage",
    [
        "new_closed_writer",
        "changed_version",
        "changed_digest",
        "missing_probe",
        "wrong_probe",
        "unclosed",
    ],
)
def test_changed_catalogue_blocks_settlement_even_with_no_active_account(damage):
    snapshot, row, reference = proof_fixture()
    cursor = ProofCursor(row)
    if damage == "missing_probe":
        cursor.catalogue = []
    elif damage == "wrong_probe":
        cursor.catalogue[0]["Purpose"] = "mutation"
    elif damage == "changed_version":
        cursor.catalogue[0]["Version"] += 1
    elif damage == "unclosed":
        cursor.catalogue[0]["State"] = "frozen"
    else:
        # A different job/preparation/nested owner can leave no active stream
        # and no domain snapshot change. Its retained stream must still count.
        extra = dict(cursor.catalogue[0], StreamID=str(uuid4()), Purpose="mutation")
        cursor.catalogue.append(extra)
        if damage == "changed_digest":
            import hashlib

            from services.export_execution_protocol import CATALOGUE_SEED, catalogue_step

            member = json.loads(row["MembershipJson"])
            member["history"] = dict(
                count=1,
                sha256=catalogue_step(
                    CATALOGUE_SEED, extra["StreamID"], extra["Version"], b"e" * 32
                ).hex(),
            )
            row["MembershipJson"] = json.dumps(member)
            row["MembershipHash"] = hashlib.sha256(
                row["MembershipJson"].encode("utf-16-le")
            ).digest()
            extra["EventDigest"] = b"x" * 32
        cursor.catalogue.sort(key=lambda s: s["StreamID"])
    with pytest.raises(SourceConflict):
        ExportExecutionDAL.settlement_proof(
            cursor, reference, snapshot=snapshot, account="account-a", kind="publication"
        )
    assert all(sql.startswith(("SELECT", "WITH catalogue_scope")) for sql, _ in cursor.statements)


@pytest.mark.parametrize("damage", ["targets", "hash", "old_list"])
def test_scope_truncation_or_old_membership_format_cannot_authorize_a_proof(damage):
    import hashlib

    snapshot, row, reference = proof_fixture()
    cursor = ProofCursor(row)
    if damage == "hash":
        row["MembershipHash"] = b"x" * 32
    else:
        member = json.loads(row["MembershipJson"])
        if damage == "targets":
            member["targets"].pop()
        else:
            member = [member["probe"]]
        row["MembershipJson"] = json.dumps(member)
        row["MembershipHash"] = hashlib.sha256(row["MembershipJson"].encode("utf-16-le")).digest()
    with pytest.raises(SourceConflict):
        ExportExecutionDAL.settlement_proof(
            cursor, reference, snapshot=snapshot, account="account-a", kind="publication"
        )


def test_reconcile_uses_same_locked_cursor_and_audits_only_sql_proof(monkeypatch):
    snapshot, row, reference = proof_fixture()
    cursor = ProofCursor(row)
    dal = ExportCoordinationDAL(
        Mock(), preparations=True, output_operations=True, execution_evidence=True
    )
    dal._account = Mock(return_value=nullcontext(cursor))
    dal._operator_snapshot = Mock(return_value=snapshot)
    update = Mock(return_value={"Version": 8})
    monkeypatch.setattr("services.export_coordination_dal._cas", update)
    assert dal.reconcile_operator(snapshot, reference, actor="operator")["state"] == "damaged"
    assert update.call_args.args[0] is cursor
    audited = json.loads(update.call_args.args[2])["reconciliations"][0]["proof"]
    assert audited["state"] == "damaged" and audited["proof_id"] == reference["proof_id"]
    assert audited["writer_terminated"] is True


def test_stale_locked_snapshot_fails_before_proof_lookup_or_mutation(monkeypatch):
    snapshot, row, reference = proof_fixture()
    cursor = ProofCursor(row)
    dal = ExportCoordinationDAL(
        Mock(), preparations=True, output_operations=True, execution_evidence=True
    )
    dal._account = Mock(return_value=nullcontext(cursor))
    dal._operator_snapshot = Mock(return_value={})
    update = Mock()
    monkeypatch.setattr("services.export_coordination_dal._cas", update)
    with pytest.raises(SourceConflict, match="snapshot changed"):
        dal.reconcile_operator(snapshot, reference, actor="operator")
    update.assert_not_called()
    assert not cursor.statements


def closed_stream_fixture(*, purpose="mutation"):
    import hashlib
    from types import SimpleNamespace

    from services.export_execution_protocol import encode
    from services.export_reconciliation_service import ClosedStreamVerifier

    stream_id, request_id, child_id = (str(uuid4()) for _ in range(3))
    documents = {}

    def retained(value):
        reference = str(uuid4())
        documents[reference] = encode(value)
        return reference, hashlib.sha256(documents[reference]).digest()

    def read(reference, expected_hash):
        raw = documents[reference]
        if hashlib.sha256(raw).digest() != expected_hash:
            raise SourceConflict("private hash mismatch")
        return raw

    payload = dict(
        version=1,
        stream_id=stream_id,
        request_id=request_id,
        operation="sheets.get" if purpose == "probe" else "sheets.values.clear",
        target="file-a",
        arguments={} if purpose == "probe" else {"range": "A1", "body": {}},
    )
    reference, value_hash = retained(payload)
    request = dict(
        RequestID=request_id,
        StreamID=stream_id,
        Sequence=1,
        Operation=payload["operation"],
        RequestKind="read" if purpose == "probe" else "mutation",
        TargetID="file-a",
        PayloadReference=reference,
        PayloadHash=value_hash,
    )
    response = dict(spreadsheetId="file-a")
    if purpose != "probe":
        response["clearedRange"] = "Sheet1!A1"
    events = []
    for index, state in enumerate(("prepared", "dispatch_intent", "succeeded"), 1):
        body = dict(request_id=request_id)
        if state == "prepared":
            body["payload_hash"] = value_hash.hex()
        if state == "succeeded":
            body["response"] = response
        reference, evidence_hash = retained(body)
        events.append(
            dict(
                EventID=str(uuid4()),
                RequestID=request_id,
                EventSequence=index,
                State=state,
                EvidenceReference=reference,
                EvidenceHash=evidence_hash,
            )
        )
    closure_reference, closure_hash = retained(
        dict(
            stream_id=stream_id,
            version=4,
            last_sequence=1,
            event_digest=(b"d" * 32).hex(),
            closure=dict(child_id=child_id, job_empty=True, process_signaled=True),
        )
    )
    stream = dict(
        StreamID=stream_id,
        State="closed",
        ActiveAccountKey=None,
        AccountKey="account-a",
        RegistrationHash=b"r" * 32,
        Purpose=purpose,
        LastSequence=1,
        EventDigest=b"d" * 32,
        Version=5,
        ChildIdentity=child_id,
        ClosureReference=closure_reference,
        ClosureHash=closure_hash,
    )

    def identities(_):
        yield request_id

    dal = SimpleNamespace(
        read_stream=Mock(return_value=stream),
        stream_digest=Mock(return_value=(1, b"d" * 32)),
        request_ids=identities,
        read_request=Mock(return_value=(request, events)),
    )
    verifier = ClosedStreamVerifier(dal=dal, store=SimpleNamespace(read_reference=read))
    return verifier, stream, request, events, documents


def catalogue_fixture():
    import hashlib
    from types import SimpleNamespace

    from services.export_reconciliation_service import CatalogueVerifier

    old, old_stream, old_request, old_events, old_documents = closed_stream_fixture()
    fresh, fresh_stream, fresh_request, fresh_events, fresh_documents = closed_stream_fixture(
        purpose="probe"
    )
    snapshot, _, _ = proof_fixture()
    snapshot["pool"]["pool"]["RegistrationHash"] = (b"r" * 32).hex()
    fresh_stream["SnapshotHash"] = digest(snapshot)
    old_stream["SnapshotHash"] = b"o" * 32
    streams = {s["StreamID"]: s for s in (old_stream, fresh_stream)}
    requests = {
        r["RequestID"]: (r, e)
        for r, e in ((old_request, old_events), (fresh_request, fresh_events))
    }
    docs = old_documents | fresh_documents
    visible = [old_stream]

    def catalogue(account, targets):
        assert account == "account-a" and targets == ["file-a", "file-b", "file-index"]
        yield from sorted(visible, key=lambda s: s["StreamID"])

    def identities(stream_id):
        yield from (r["RequestID"] for r, _ in requests.values() if r["StreamID"] == stream_id)

    def read(reference, expected_hash):
        body = docs[reference]
        if hashlib.sha256(body).digest() != expected_hash:
            raise SourceConflict("private hash mismatch")
        return body

    dal = SimpleNamespace(
        read_catalogue=catalogue,
        read_stream=lambda identifier: streams[identifier],
        stream_digest=lambda _: (1, b"d" * 32),
        request_ids=identities,
        read_request=lambda identifier: requests[identifier],
    )
    verifier = CatalogueVerifier(dal=dal, store=SimpleNamespace(read_reference=read))
    return verifier, snapshot, old_stream, fresh_stream, visible, docs, requests


def test_complete_private_history_and_fresh_probe_produce_inventory_only():
    verifier, snapshot, old, probe, visible, docs, requests = catalogue_fixture()
    history = verifier.before_probe(snapshot=snapshot, account="account-a")
    assert history.count == 1
    visible.append(probe)
    membership = verifier.bind_probe(history, snapshot=snapshot, stream_id=probe["StreamID"])
    assert membership["history"] == dict(count=1, sha256=history.sha256)
    assert membership["probe"] == dict(stream_id=probe["StreamID"], version=probe["Version"])
    assert "proof_id" not in membership and "state" not in membership


def probe_replay_fixture():
    from services.export_execution_protocol import decode
    from services.export_reconciliation_service import ClosedProbeReplay

    verifier, snapshot, _old, probe, _visible, documents, requests = catalogue_fixture()
    request = next(r for r, _ in requests.values() if r["StreamID"] == probe["StreamID"])
    message = decode(documents[request["PayloadReference"]])
    replay = ClosedProbeReplay(
        dal=verifier.dal,
        store=verifier.closed.store,
        stream_id=probe["StreamID"],
        snapshot=snapshot,
        account="account-a",
    )
    return replay, message, probe, documents, requests


def test_actual_sdk_read_description_uses_sealed_probe_without_provider_or_transition():
    from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration

    replay, _message, probe, _documents, _requests = probe_replay_fixture()
    transport = GoogleSheetsTransport.from_authority(
        registration=SheetsRegistration(
            "file-index",
            ("file-a", "file-b"),
            "owner@example.invalid",
            "test@example.iam.gserviceaccount.com",
        ),
        reuse_guard=lambda *_: False,
        protected_file_ids=(),
        execution=replay.execute,
        stream_id=probe["StreamID"],
        authorize=lambda **_: None,
    )
    # Static discovery constructs the SDK request; its HTTP object denies network.
    # The fixture DAL deliberately has no transition method or provider client.
    with replay:
        result = transport._execute(transport.sheets.spreadsheets().get(spreadsheetId="file-a"))
    assert result == {"spreadsheetId": "file-a"}
    with pytest.raises(SourceConflict, match="reopened"):
        with replay:
            pass


@pytest.mark.parametrize("damage", ["snapshot", "registration", "account", "mutation_stream"])
def test_replayed_observations_require_exact_snapshot_registration_and_probe(damage):
    replay, _message, probe, _documents, _requests = probe_replay_fixture()
    if damage == "snapshot":
        probe["SnapshotHash"] = b"x" * 32
    elif damage == "registration":
        probe["RegistrationHash"] = b"x" * 32
    elif damage == "account":
        replay.account = "other"
    else:
        probe["Purpose"] = "mutation"
    with pytest.raises(SourceConflict):
        with replay:
            pass


@pytest.mark.parametrize("damage", ["file", "projection", "method", "mutation", "stream"])
def test_evaluator_cannot_substitute_a_read_or_swallow_a_rejected_observation(damage):
    replay, message, _probe, _documents, _requests = probe_replay_fixture()
    if damage == "file":
        message["target"] = "file-b"
    elif damage == "projection":
        message["arguments"] = {"fields": "sheets.properties"}
    elif damage == "method":
        message.update(operation="drive.files.get", arguments={})
    elif damage == "mutation":
        message.update(operation="sheets.values.clear", arguments={"range": "A1", "body": {}})
    else:
        message["stream_id"] = str(uuid4())
    with pytest.raises(SourceConflict, match="invalidates"):
        with replay:
            with pytest.raises(SourceConflict):
                replay.execute(message)


def test_probe_evaluator_must_consume_every_observation():
    replay, _message, _probe, _documents, _requests = probe_replay_fixture()
    with pytest.raises(SourceConflict, match="unevaluated"):
        with replay:
            pass


def test_probe_response_bytes_are_rechecked_when_evaluated():
    replay, message, probe, documents, requests = probe_replay_fixture()
    events = next(e for r, e in requests.values() if r["StreamID"] == probe["StreamID"])
    with pytest.raises(SourceConflict, match="private hash"):
        with replay:
            documents[events[-1]["EvidenceReference"]] = b"{}"
            replay.execute(message)


@pytest.mark.parametrize(
    "damage", ["omission", "insert", "unknown", "private_bytes", "snapshot", "registration"]
)
def test_omitted_changed_or_unknown_catalogue_never_becomes_history_proof(damage):
    verifier, snapshot, old, probe, visible, docs, requests = catalogue_fixture()
    history = verifier.before_probe(snapshot=snapshot, account="account-a")
    visible.append(probe)
    if damage == "omission":
        visible.remove(old)
    elif damage == "insert":
        # A second historical probe is just as observable as a mutation stream.
        visible.append(dict(old, StreamID=str(uuid4())))
        verifier.dal.read_stream = lambda identifier: next(
            s for s in visible if s["StreamID"] == identifier
        )
    elif damage == "unknown":
        next(
            events
            for request, events in requests.values()
            if request["StreamID"] == old["StreamID"]
        )[-1]["State"] = "unknown"
    elif damage == "private_bytes":
        docs[old["ClosureReference"]] = b"{}"
    elif damage == "snapshot":
        probe["SnapshotHash"] = b"x" * 32
    else:
        probe["RegistrationHash"] = b"x" * 32
    with pytest.raises(SourceConflict):
        verifier.bind_probe(history, snapshot=snapshot, stream_id=probe["StreamID"])


def test_catalogue_keyset_reads_close_sql_before_yielding_evidence_work():

    values = [
        dict(StreamID="10000000-0000-0000-0000-000000000001"),
        dict(StreamID="f0000000-0000-0000-0000-000000000001"),
    ]
    connections = []

    def connect():
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.description = [("StreamID",)]
        cursor.fetchall.return_value = [(v["StreamID"],) for v in values] if not connections else []
        connections.append(connection)
        return connection

    dal = ExportExecutionDAL(connect)
    iterator = dal.read_catalogue("account-a", ["file-a"])
    assert next(iterator) == values[0]
    connections[0].close.assert_called_once()
    connections[0].cursor().close.assert_called_once()
    assert list(iterator) == values[1:]
    assert len(connections) == 2
    query, account, targets, after = connections[1].cursor().execute.call_args.args
    assert "LOWER(CONVERT(varchar(36),s.StreamID))" in query
    assert "OPENJSON(s.ScopeJson,'$.resources')" in query
    assert (account, json.loads(targets), after) == (
        "account-a",
        ["file-a"],
        values[-1]["StreamID"],
    )
    connections[1].close.assert_called_once()


@pytest.mark.parametrize("gap", [False, True])
def test_request_pages_close_sql_before_private_reads_and_reject_gaps(gap):
    identifiers = [str(uuid4()), str(uuid4())]
    connections = []

    def connect():
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchall.return_value = (
            [(1, identifiers[0]), (3 if gap else 2, identifiers[1])] if not connections else []
        )
        connections.append(connection)
        return connection

    stream_id = str(uuid4())
    iterator = ExportExecutionDAL(connect).request_ids(stream_id)
    assert next(iterator) == identifiers[0]
    connections[0].close.assert_called_once()
    connections[0].cursor().close.assert_called_once()
    if gap:
        with pytest.raises(SourceConflict, match="gap"):
            list(iterator)
    else:
        assert list(iterator) == identifiers[1:]
        assert connections[1].cursor().execute.call_args.args[1:] == (stream_id, 2)
        connections[1].close.assert_called_once()


@pytest.mark.parametrize("purpose", ["mutation", "probe"])
def test_closed_journal_verifies_exact_private_payload_response_and_os_seal(purpose):
    verifier, stream, request, events, documents = closed_stream_fixture(purpose=purpose)
    result = verifier.verify(stream["StreamID"], account="account-a", registration_hash=b"r" * 32)
    assert result.request_count == 1
    assert result.dispatched_mutations == (purpose == "mutation")
    assert result.successful_reads == (purpose == "probe")
    # A verified journal does not manufacture a ProofID or settle an owner.
    assert not hasattr(result, "proof_id")


@pytest.mark.parametrize(
    "damage",
    [
        "unknown",
        "missing_terminal",
        "wrong_sequence",
        "reordered",
        "private_bytes",
        "membership",
        "wrong_child",
        "active",
    ],
)
def test_journal_gaps_unknowns_and_tampering_remain_unresolved(damage):
    verifier, stream, request, events, documents = closed_stream_fixture()
    if damage == "unknown":
        events[-1]["State"] = "unknown"
    elif damage == "missing_terminal":
        events.pop()
    elif damage == "wrong_sequence":
        events[-1]["EventSequence"] = 4
    elif damage == "reordered":
        events.reverse()
    elif damage == "private_bytes":
        documents[events[-1]["EvidenceReference"]] = b"{}"
    elif damage == "membership":
        stream["LastSequence"] = 2
    elif damage == "wrong_child":
        stream["ChildIdentity"] = str(uuid4())
    elif damage == "active":
        stream["ActiveAccountKey"] = "account-a"
    with pytest.raises(SourceConflict):
        verifier.verify(stream["StreamID"], account="account-a", registration_hash=b"r" * 32)


@pytest.mark.parametrize(
    "route,kind",
    [
        ("repair", "publication"),
        ("retirement", "retirement"),
        ("recovery", "retirement_recovery"),
        ("rollover", "rollover_complete"),
        ("drain", "rollover_drain"),
    ],
)
def test_each_other_settlement_requires_sql_proof_before_mutation(monkeypatch, route, kind):
    from types import SimpleNamespace

    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL

    class Cursor:
        description = ()

        def execute(self, statement, *args):
            assert statement.startswith("SELECT"), "Settlement mutated before proof validation"

        def fetchone(self):
            return None

        def fetchall(self):
            return []

    cursor = Cursor()
    lookup = Mock(side_effect=SourceConflict("untrusted proof"))
    monkeypatch.setattr(ExportExecutionDAL, "settlement_proof", lookup)
    monkeypatch.setattr("kvk.dal.source_output_pool_dal._mutex", Mock())
    coordinator = ExportCoordinationDAL(
        Mock(), preparations=True, output_operations=True, execution_evidence=True
    )
    coordinator._account = Mock(return_value=nullcontext(cursor))
    pool = dict(PoolID="pool-id", IndexFileID="index-id", PoolState="active")
    pools = SourceOutputPoolDAL(Mock(), execution_evidence=True)
    pools._locked = Mock(return_value=nullcontext((cursor, pool)))
    reference = dict(proof_id=str(uuid4()))
    if route == "repair":
        snapshot, _, _ = proof_fixture()
        coordinator._operator_snapshot = Mock(return_value=snapshot)
        invoke = lambda: coordinator.admit_repair(
            str(uuid4()), dict(snapshot=snapshot, proof=reference)
        )
    elif route == "retirement":
        snapshot = dict(pool=pool, slots=[])
        pools._retirement_owned = Mock(return_value=nullcontext((cursor, {}, snapshot)))
        monkeypatch.setattr("kvk.dal.source_output_pool_dal.reusable_attempts", lambda *_: ["old"])
        claim = SimpleNamespace(account="account-a")
        invoke = lambda: pools.retire_generation(
            coordinator, claim, "current", snapshot, "old", reference
        )
    elif route == "recovery":
        snapshot = dict(
            job=dict(JobID="job", AccountKey="account-a", State="uncertain"),
            pool=dict(pool=pool, slots=[]),
            resources=[
                dict(ResourceKey="account:account-a"),
                dict(ResourceKey="destination:index-id"),
            ],
        )
        coordinator._operator_snapshot = Mock(return_value=snapshot)
        monkeypatch.setattr(
            "kvk.dal.source_output_pool_dal.pending_retirements", lambda *_: ["pending"]
        )
        invoke = lambda: pools.claim_retirement_recovery(
            coordinator, snapshot, reference, actor="admin"
        )
    elif route == "rollover":
        op = dict(OperationID="op", PoolID="pool-id", AccountKey="account-a", State="uncertain")
        snapshot = dict(operation=op, resources=[], pool=dict(pool=pool, slots=[]))
        pools._operation = Mock(return_value=op)
        pools._snapshot = Mock(return_value=snapshot["pool"])
        invoke = lambda: pools.reconcile_complete(snapshot, reference, actor="admin")
    else:
        snapshot = dict(pool=pool, jobs=[], legacy_receipts=[])
        pools.operation = Mock(return_value=dict(PoolID="pool-id"))
        pools._operation = Mock(return_value=dict(State="closing", AccountKey="account-a"))
        pools._snapshot = Mock(return_value=snapshot)
        invoke = lambda: pools.ready("operation", snapshot, reference)
    with pytest.raises(SourceConflict, match="untrusted proof"):
        invoke()
    lookup.assert_called_once_with(
        cursor, reference, snapshot=snapshot, account="account-a", kind=kind
    )


def publication_observation_fixture(monkeypatch, *, public=False, retained=True):
    """Populate an in-memory provider with the real pinned delivery/readback path."""
    from dataclasses import replace
    from threading import Event
    from types import SimpleNamespace

    from kvk.services.new_source_delivery_service import deliver_coordinated_export
    from services.export_coordination_dal import bounded_json
    from tests.test_export_runtime_composition import recorded_google_memory

    args, api, messages = recorded_google_memory()
    transport, stream = args["transport"], args["authority_stream"]
    if public:
        transport.registration = replace(transport.registration, audience="public_viewer")
    generation = args["generation"]
    monkeypatch.setattr(
        "kvk.services.new_source_export_service.load_intent_generation", lambda **_: generation
    )
    job_id, owner, attempt_id = (str(uuid4()) for _ in range(3))
    job = dict(
        JobID=job_id,
        OwnerID=owner,
        Fence=10,
        Version=7,
        ConsumerKind="new_source",
        IntentID=str(uuid4()),
        InputHash=b"a" * 32,
        AccountKey="account-a",
        KVK_NO=16,
        PoolEpoch=1,
        State="uncertain",
        DestinationSetHash=digest(tuple(sorted(("fake-index", "fake-1", "fake-2")))),
    )
    claim = SimpleNamespace(job_id=job_id, owner_id=owner, fence=10)
    dal = Mock(execution_evidence=True, output_operations=False)
    pinned = {}

    def begin(_claim, manifest, parts):
        pinned.update(generation=manifest, parts=parts)
        return attempt_id

    dal.begin_attempt.side_effect = begin
    stream.client.close_stream.side_effect = lambda identifier: dict(
        stream_id=identifier, version=3
    )
    receipt = deliver_coordinated_export(
        job=job,
        claim=claim,
        dal=dal,
        transport=transport,
        connect=None,
        budget=Mock(side_effect=AssertionError("local budget escaped")),
        stop=Event(),
        authority_stream=stream,
    )
    registration = transport.registration
    job.update(InputHash=(b"a" * 32).hex(), DestinationSetHash=job["DestinationSetHash"].hex())
    attempt = dict(
        AttemptID=attempt_id,
        JobID=job_id,
        OwnerID=owner,
        Fence=10,
        Epoch=1,
        ConsumerKind="new_source",
        PartCount=len(pinned["parts"]),
        ManifestJson=bounded_json(pinned),
        ManifestHash=digest(pinned).hex(),
        ReceiptJson=bounded_json(receipt) if retained else None,
    )
    parts = [
        dict(
            AttemptID=attempt_id,
            PartNo=n,
            PartCount=attempt["PartCount"],
            FileID=p["file_id"],
            Role=p["role"],
            ManifestHash=p["manifest_hash"],
            GridCount=p["grids"],
            RowCount=p["rows"],
            CellCount=p["cells"],
        )
        for n, p in enumerate(pinned["parts"], 1)
    ]
    pool = dict(
        IndexFileID=registration.index_file_id,
        ExpectedOwner=registration.owner_email,
        AccountKey="account-a",
        ActiveKVK=16,
        Epoch=1,
        RegistrationJson='{"fixture":"publication"}',
        RegistrationHash=digest({"fixture": "publication"}).hex(),
    )
    snapshot = dict(
        job=job,
        attempts=[attempt],
        parts=parts,
        pool=dict(
            pool=pool,
            slots=[dict(FileID=f, State="active") for f in registration.slot_file_ids],
        ),
    )
    observations = []

    def execute(message):
        from copy import deepcopy

        from services.export_execution_protocol import ProviderRequest

        assert not ProviderRequest.parse(message).mutation
        response = stream.client.execute(message)
        observations.append((deepcopy(message), deepcopy(response)))
        return response

    return (
        dict(
            snapshot=snapshot,
            registration=registration,
            protected_file_ids=transport.protected,
            execute=execute,
            stream_id=str(uuid4()),
        ),
        api,
        observations,
        receipt,
    )


@pytest.mark.parametrize("public", [False, True])
@pytest.mark.parametrize("retained", [False, True])
def test_publication_observation_reuses_real_readback_and_preserves_exact_receipt(
    monkeypatch, public, retained
):
    from services.export_coordination_dal import bounded_json
    from services.export_reconciliation_service import observe_publication

    args, api, observations, receipt = publication_observation_fixture(
        monkeypatch, public=public, retained=retained
    )
    result = observe_publication(**args)
    assert result.receipt_json == bounded_json(receipt)
    assert result.snapshot_hash == digest(args["snapshot"]).hex()
    assert result.probe_stream_id == args["stream_id"]
    assert (
        observations
        and not hasattr(result, "proof_id")
        and not hasattr(result, "writer_terminated")
    )


@pytest.mark.parametrize("damage", ["pointer", "content", "url", "manifest", "audience"])
def test_contradictory_publication_readback_is_unresolved_never_absence_or_damage(
    monkeypatch, damage
):
    from services.export_reconciliation_service import observe_publication

    args, api, observations, _receipt = publication_observation_fixture(monkeypatch, public=True)
    if damage == "pointer":
        api.values["fake-index", "Sheet1"][0][1] = "9"
    elif damage == "url":
        api.values["fake-index", "Sheet1"][0][2] = "https://example.invalid/other"
    elif damage == "manifest":
        document = json.loads(api.files_data["fake-1"]["description"])
        next(iter(document.values()))["sha256"] = "f" * 64
        api.files_data["fake-1"]["description"] = json.dumps(document)
    elif damage == "audience":
        api.files_data["fake-index"]["permissions"] = [
            p for p in api.files_data["fake-index"]["permissions"] if p["type"] != "anyone"
        ]
    else:
        title = next(
            t for file_id, t in api.values if file_id == "fake-1" and not t.endswith("DIRECTORY")
        )
        api.values["fake-1", title][0][0] = "different header"
    with pytest.raises(SourceConflict, match="unresolved"):
        observe_publication(**args)
    assert observations


@pytest.mark.parametrize("changed", [False, True])
def test_confirmed_content_assessment_seals_positive_mismatch_and_original_receipt(
    monkeypatch, changed
):
    from services.export_reconciliation_service import (
        observe_closed_publication,
        observe_publication,
    )

    args, api, observations, _ = publication_observation_fixture(monkeypatch, public=True)
    args["snapshot"]["job"]["State"] = "confirmed"
    args["snapshot"]["attempts"][0]["Phase"] = "published"
    retained = args["snapshot"]["attempts"][0]["ReceiptJson"]
    if changed:
        title = next(
            t for file_id, t in api.values if file_id == "fake-1" and not t.endswith("DIRECTORY")
        )
        api.values["fake-1", title][0][0] = "different header"
    result = observe_publication(**args)
    assert result.state == ("damaged" if changed else "confirmed")
    assert result.receipt_json == retained
    dal, store, _, _ = sealed_publication_fixture(args, observations)
    assert (
        observe_closed_publication(
            dal=dal, store=store, **{k: v for k, v in args.items() if k != "execute"}
        )
        == result
    )


@pytest.mark.parametrize("damage", ["pointer", "manifest", "audience", "structure"])
def test_confirmed_assessment_never_relabels_unknown_structure_identity_or_acl(monkeypatch, damage):
    from services.export_reconciliation_service import observe_publication

    args, api, _, _ = publication_observation_fixture(monkeypatch, public=True)
    args["snapshot"]["job"]["State"] = "confirmed"
    if damage == "pointer":
        api.values["fake-index", "Sheet1"][0][1] = "999"
    elif damage == "manifest":
        api.files_data["fake-1"]["description"] = "{}"
    elif damage == "audience":
        api.files_data["fake-index"]["permissions"] = [
            p for p in api.files_data["fake-index"]["permissions"] if p["type"] != "anyone"
        ]
    else:
        # A different directory is an unresolved physical representation, not a
        # complete positive content comparison against the retained receipt.
        title = next(
            t for file_id, t in api.values if file_id == "fake-1" and t.endswith("DIRECTORY")
        )
        api.values["fake-1", title][0][0] = "changed directory"
    with pytest.raises(SourceConflict):
        observe_publication(**args)


def test_absence_observation_requires_no_dispatch_prerequisite_and_sealed_reads(monkeypatch):
    from services.export_reconciliation_service import (
        observe_closed_publication,
        observe_publication,
    )

    args, api, observations, _ = publication_observation_fixture(monkeypatch, retained=False)
    for file in api.files_data.values():
        file.get("appProperties", {}).pop("k98Generation", None)
    api.values["fake-index", "Sheet1"] = []
    with pytest.raises(SourceConflict):
        observe_publication(**args)
    observations.clear()
    result = observe_publication(**args, allow_absent=True)
    assert result.state == "absent" and result.receipt_json is None
    assert not hasattr(result, "no_delayed_effect") and not hasattr(result, "proof_id")
    dal, store, _, _ = sealed_publication_fixture(args, observations)
    assert (
        observe_closed_publication(
            dal=dal,
            store=store,
            allow_absent=True,
            **{k: v for k, v in args.items() if k != "execute"},
        )
        == result
    )


@pytest.mark.parametrize(
    "damage", ["hash", "parts", "owner", "epoch", "registration", "retained_bytes"]
)
def test_publication_observation_rejects_changed_pins_and_retained_receipts(monkeypatch, damage):
    from services.export_reconciliation_service import observe_publication

    args, _api, observations, _receipt = publication_observation_fixture(monkeypatch)
    snapshot = args["snapshot"]
    if damage == "hash":
        snapshot["attempts"][0]["ManifestHash"] = "f" * 64
    elif damage == "parts":
        snapshot["parts"][0]["CellCount"] += 1
    elif damage == "owner":
        snapshot["attempts"][0]["OwnerID"] = str(uuid4())
    elif damage == "epoch":
        snapshot["job"]["PoolEpoch"] += 1
    elif damage == "registration":
        snapshot["pool"]["pool"]["ExpectedOwner"] = "other@example.invalid"
    else:
        snapshot["attempts"][0]["ReceiptJson"] += " "
    with pytest.raises(SourceConflict):
        observe_publication(**args)
    if damage != "retained_bytes":
        assert observations == []


def sealed_publication_fixture(args, observations):
    import hashlib
    from types import SimpleNamespace

    from services.export_execution_protocol import encode

    documents, requests = {}, {}

    def retain(value):
        ref = str(uuid4())
        documents[ref] = encode(value)
        return ref, hashlib.sha256(documents[ref]).digest()

    def read(reference, expected_hash):
        raw = documents[reference]
        assert hashlib.sha256(raw).digest() == expected_hash
        return raw

    for sequence, (message, response) in enumerate(observations, 1):
        identifier = message["request_id"]
        payload_ref, payload_hash = retain(message)
        request = dict(
            RequestID=identifier,
            StreamID=args["stream_id"],
            Sequence=sequence,
            Operation=message["operation"],
            RequestKind="read",
            TargetID=message["target"],
            PayloadReference=payload_ref,
            PayloadHash=payload_hash,
        )
        events = []
        for index, state in enumerate(("prepared", "dispatch_intent", "succeeded"), 1):
            body = dict(request_id=identifier)
            if state == "prepared":
                body["payload_hash"] = payload_hash.hex()
            elif state == "succeeded":
                body["response"] = response
            ref, value_hash = retain(body)
            events.append(
                dict(
                    EventID=str(uuid4()),
                    RequestID=identifier,
                    EventSequence=index,
                    State=state,
                    EvidenceReference=ref,
                    EvidenceHash=value_hash,
                )
            )
        requests[identifier] = request, events
    version, child = len(requests) * 3 + 3, str(uuid4())
    closure_ref, closure_hash = retain(
        dict(
            stream_id=args["stream_id"],
            version=version - 1,
            last_sequence=len(requests),
            event_digest=(b"d" * 32).hex(),
            closure=dict(child_id=child, job_empty=True, process_signaled=True),
        )
    )
    pool = args["snapshot"]["pool"]
    pool = pool.get("pool", pool)
    stream = dict(
        StreamID=args["stream_id"],
        State="closed",
        ActiveAccountKey=None,
        AccountKey="account-a",
        RegistrationHash=bytes.fromhex(pool["RegistrationHash"]),
        Purpose="probe",
        Version=version,
        SnapshotHash=digest(args["snapshot"]),
        LastSequence=len(requests),
        EventDigest=b"d" * 32,
        ClosureReference=closure_ref,
        ClosureHash=closure_hash,
        ChildIdentity=child,
    )
    dal = SimpleNamespace(
        read_stream=lambda _: stream,
        stream_digest=lambda _: (len(requests), b"d" * 32),
        request_ids=lambda _: (r for r in requests),
        read_request=lambda r: requests[r],
    )
    return dal, SimpleNamespace(read_reference=read), stream, documents


def test_sealed_publication_transcript_replays_actual_complete_readback_without_provider(
    monkeypatch,
):
    from services.export_reconciliation_service import (
        observe_closed_publication,
        observe_publication,
    )

    args, api, observations, _receipt = publication_observation_fixture(monkeypatch)
    original = observe_publication(**args)
    dal, store, _stream, _documents = sealed_publication_fixture(args, observations)
    calls = len(api.calls)
    replayed = observe_closed_publication(
        dal=dal,
        store=store,
        **{k: v for k, v in args.items() if k != "execute"},
    )
    assert replayed == original and len(api.calls) == calls


def stub_origin_journal(monkeypatch, failure=None, on_recheck=None):
    """Isolate probe sequencing; actual enrollment journals are tested separately."""
    first = {"fixture_origin": "first"}
    reader = Mock(return_value=first)
    if failure == "origin":
        reader.side_effect = SourceConflict("Managed origins are unavailable.")
    elif failure == "origin_drift":
        reader.side_effect = [first, {"fixture_origin": "changed"}]
    elif failure == "origin_snapshot":

        def read(**_):
            if reader.call_count == 2:
                on_recheck()
            return first

        reader.side_effect = read
    monkeypatch.setattr("services.export_enrollment_service.ManagedOriginVerifier.verify", reader)
    return reader, digest(first).hex()


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "readback",
        "close",
        "snapshot",
        "catalogue",
        "bytes",
        "origin",
        "origin_drift",
        "origin_snapshot",
    ],
)
def test_publication_probe_closes_and_seals_before_returning_observation(monkeypatch, failure):
    from contextlib import contextmanager
    from copy import deepcopy
    from types import SimpleNamespace

    from services.export_execution_authority import ExecutionUncertain
    from services.export_execution_protocol import CATALOGUE_SEED
    from services.export_reconciliation_service import PublicationProbe

    args, api, observations, receipt = publication_observation_fixture(monkeypatch)
    snapshot = deepcopy(args["snapshot"])
    origins, origin_hash = stub_origin_journal(
        monkeypatch,
        failure,
        lambda: snapshot["job"].update(Version=snapshot["job"]["Version"] + 1),
    )
    job_id = snapshot["job"]["JobID"]
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.side_effect = lambda _: deepcopy(snapshot)
    rows, sealed, steps = [], {}, []

    def read_private(reference, expected_hash):
        steps.append("private")
        if failure == "bytes":
            raise SourceConflict("Private response bytes changed.")
        return sealed["store"].read_reference(reference, expected_hash)

    dal = SimpleNamespace(
        read_catalogue=lambda *_: (r for r in rows),
        read_stream=lambda identifier: next(r for r in rows if r["StreamID"] == identifier),
        stream_digest=lambda identifier: sealed["dal"].stream_digest(identifier),
        request_ids=lambda identifier: sealed["dal"].request_ids(identifier),
        read_request=lambda identifier: sealed["dal"].read_request(identifier),
    )

    @contextmanager
    def probe(actual):
        assert origins.call_count == 1
        assert actual == snapshot
        steps.append("open")
        try:
            yield SimpleNamespace(stream_id=args["stream_id"], execute=args["execute"])
        finally:
            steps.append("close")
            if failure == "close":
                raise ExecutionUncertain("Closure acknowledgment lost.")
            sealed_dal, store, stream, _documents = sealed_publication_fixture(args, observations)
            sealed.update(dal=sealed_dal, store=store)
            rows.append(stream)
            if failure == "snapshot":
                snapshot["job"]["Version"] += 1
            elif failure == "catalogue":
                rows.append(dict(stream, StreamID=str(uuid4()), State="open"))
                rows.sort(key=lambda r: r["StreamID"])

    if failure == "readback":
        api.values["fake-index", "Sheet1"][0][1] = "9"
    service = PublicationProbe(
        coordinator=coordinator,
        streams=SimpleNamespace(coordinator=coordinator, probe=probe),
        dal=dal,
        store=SimpleNamespace(read_reference=read_private),
        registration=args["registration"],
        protected_file_ids=args["protected_file_ids"],
    )
    if failure:
        with pytest.raises((SourceConflict, ExecutionUncertain)):
            service.run(job_id)
    else:
        result = service.run(job_id)
        assert result.origin_hash == origin_hash and origins.call_count == 2
        assert json.loads(result.publication.receipt_json) == receipt
        member = json.loads(result.membership_json)
        assert member["history"] == dict(count=0, sha256=CATALOGUE_SEED.hex())
        assert member["probe"]["stream_id"] == args["stream_id"]
        assert not hasattr(result, "proof_id") and not hasattr(result, "writer_terminated")
        assert steps.index("close") < steps.index("private")
    assert steps.count("open") == steps.count("close") == (0 if failure == "origin" else 1)
    assert bool(observations) == (failure != "origin")


@pytest.mark.parametrize("wrong", ["evidence", "operations", "coordinator"])
def test_publication_probe_refuses_mixed_or_incomplete_composition(wrong):
    from services.export_reconciliation_service import PublicationProbe

    coordinator = Mock(execution_evidence=True, output_operations=True)
    streams = Mock(coordinator=coordinator)
    if wrong == "coordinator":
        streams.coordinator = Mock()
    else:
        setattr(
            coordinator, "execution_evidence" if wrong == "evidence" else "output_operations", False
        )
    with pytest.raises(SourceConflict, match="same complete"):
        PublicationProbe(
            coordinator=coordinator,
            streams=streams,
            dal=Mock(),
            store=Mock(),
            registration=Mock(),
            protected_file_ids=(),
        )
    coordinator.operator_snapshot.assert_not_called()
    streams.probe.assert_not_called()


def test_publication_probe_with_no_actual_origins_stops_before_catalogue_or_provider(monkeypatch):
    from services.export_reconciliation_service import PublicationProbe

    args, api, observations, _ = publication_observation_fixture(monkeypatch, public=True)
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = args["snapshot"]
    streams = Mock(coordinator=coordinator)
    dal = Mock(read_origins=Mock(return_value=[]))
    service = PublicationProbe(
        coordinator=coordinator,
        streams=streams,
        dal=dal,
        store=Mock(),
        registration=args["registration"],
        protected_file_ids=args["protected_file_ids"],
    )
    before = len(api.calls)
    with pytest.raises(SourceConflict, match="Unproven old files"):
        service.run(args["snapshot"]["job"]["JobID"])
    assert len(api.calls) == before and not observations
    dal.read_catalogue.assert_not_called()
    streams.probe.assert_not_called()
