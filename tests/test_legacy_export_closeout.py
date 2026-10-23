"""Keep stable URLs after partial delivery; independently verify retained execution."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from test_export_reconciliation_service import closed_stream_fixture

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_execution_protocol import encode
from services.legacy_export_closeout import ACTION, LegacyExportCloseout
from services.legacy_export_snapshot_service import configuration_digest


@pytest.fixture
def recovery():
    verifier, stream, request, events, docs = closed_stream_fixture()
    job_id, owner, session = (str(uuid4()) for _ in range(3))
    config = dict(consumer="scan_data", destinations=["file-a"])
    registration_hash = configuration_digest(config)
    membership = ["account:account-a", "destination:file-a"]
    stream.update(
        JobID=job_id,
        OwnerID=owner,
        Fence=2,
        SessionID=session,
        PreparationID=None,
        OutputOperationID=None,
        Epoch=None,
        NestedToken=None,
        ClaimVersion=6,
        RegistrationHash=bytes.fromhex(registration_hash),
        ScopeJson=json.dumps(dict(resources=[dict(key=k, version=3) for k in membership])),
    )
    wire = {k: v.hex() if isinstance(v, bytes) else v for k, v in stream.items()}
    state = dict(
        job=dict(
            JobID=job_id,
            AccountKey="account-a",
            StorageOwner="disk",
            ConsumerKind="scan_data",
            State="uncertain",
            OwnerID=owner,
            Fence=2,
            Version=7,
            UpdatedUTC="2026-10-01T00:01:00",
            InputHash=digest("retained").hex(),
            DestinationSetHash=digest(["file-a"]).hex(),
            ProvenanceJson=json.dumps(dict(registration_sha256=registration_hash)),
        ),
        membership=membership,
        streams=[wire],
        sessions=[dict(SessionID=session, AuthorityPrincipal="authority")],
        principal="authority",
        attempts=[dict(AttemptID=str(uuid4()), Phase="uncertain")],
        receipt=None,
        closeout=None,
        contained_targets=[],
        replacements=[],
        resources=[
            dict(
                ResourceKey=k,
                ActiveJobID=job_id,
                OwnerID=owner,
                Fence=2,
                Version=3,
                ActivePreparationID=None,
                ActiveOutputOperationID=None,
            )
            for k in membership
        ],
    )

    def put(raw):
        key = str(uuid4())
        docs[key] = raw
        return SimpleNamespace(key=key, sha256=hashlib.sha256(raw).hexdigest())

    verifier.store.put = put

    def settle(expected, *, action_id, token, marker, actor, reason):
        assert expected == state
        state["closeout"] = dict(
            ActionID=action_id,
            JobID=job_id,
            AccountKey="account-a",
            ContainmentID=state["receipt"]["ContainmentID"] if state["receipt"] else None,
            OwnerVersion=7,
            SnapshotHash=token,
            ReceiptReference=marker["reference"],
            ReceiptHash=marker["sha256"],
            Actor=actor,
            Reason=reason,
        )
        job = state["job"]
        provenance = json.loads(job["ProvenanceJson"])
        provenance["legacy_export_abandoned"] = marker
        job.update(State="failed", Version=8, ProvenanceJson=json.dumps(provenance))
        for r in state["resources"]:
            r.update(ActiveJobID=None, OwnerID=None, Version=r["Version"] + 1)

    dal = SimpleNamespace(snapshot=lambda _: deepcopy(state), settle=Mock(side_effect=settle))
    from services.export_runtime_composition import RuntimeRegistration

    registration = SimpleNamespace(
        value=lambda: dict(
            account="account-a",
            storage_owner="disk",
            pools=[],
            legacy_configuration={"scan_data": config},
        )
    )
    registration.authorize_scope = lambda scope: RuntimeRegistration.authorize_scope(
        registration, scope
    )
    service = LegacyExportCloseout(
        dal=dal, execution=verifier.dal, store=verifier.store, registration=registration
    )
    return service, state, stream, request, events, docs


def contain(recovery):
    service, state, stream, _, _, _ = recovery
    original = deepcopy(state)
    containment_id = str(uuid4())
    seals = {stream["StreamID"]: dict(last_sequence=1, event_digest=(b"d" * 32).hex())}
    token = digest(dict(snapshot=original, seals=seals)).hex()
    audit = dict(
        kind="export_target_containment/1",
        containment_id=containment_id,
        before=original,
        seals=seals,
        token=token,
        targets=["file-a"],
    )
    saved = service.store.put(encode(audit))
    state["receipt"] = dict(
        ContainmentID=containment_id,
        SnapshotHash=token,
        ReceiptReference=saved.key,
        ReceiptHash=saved.sha256,
    )
    state["contained_targets"] = [dict(FileID="file-a", ContainmentID=containment_id)]
    stream.update(
        State="target_contained",
        Version=6,
        ClosureReference=saved.key,
        ClosureHash=bytes.fromhex(saved.sha256),
    )
    state["streams"] = [{k: v.hex() if isinstance(v, bytes) else v for k, v in stream.items()}]


@pytest.mark.parametrize("contained", [False, True])
def test_partial_success_can_be_abandoned_without_replay_and_survives_restart(recovery, contained):
    if contained:
        contain(recovery)
    service, state, *_ = recovery
    job = state["job"]["JobID"]
    before = deepcopy(state)
    evidence, token, done = service.inspect(job)
    assert not done and ACTION in evidence["actions"]
    action = dict(
        ActionID=str(uuid4()),
        ActionKind=ACTION,
        EvidenceHash=token,
        Reason="Next scan replaces output",
    )
    service.execute(job, ACTION, token, "recovery:" + action["ActionID"], action["Reason"])
    restarted = LegacyExportCloseout(
        dal=service.dal,
        execution=service.execution,
        store=service.store,
        registration=service.registration,
    )
    assert restarted.reconcile(job, action) == "verified"
    evidence, _, resolved = restarted.inspect(job)
    assert resolved and evidence["outcome"] == "abandoned"
    assert state["streams"] == before["streams"] and state["attempts"] == before["attempts"]
    assert state["contained_targets"] == before["contained_targets"]
    assert state["job"]["InputHash"] == before["job"]["InputHash"]
    assert service.dal.settle.call_count == 1
    with pytest.raises(SourceConflict):
        service.execute(job, ACTION, token, "recovery:" + action["ActionID"], action["Reason"])


@pytest.mark.parametrize(
    "damage",
    [
        "unknown",
        "missing_event",
        "missing_closure",
        "changed_payload",
        "live",
        "foreign_owner",
        "replacement",
        "changed_config",
        "changed_targets",
    ],
)
def test_missing_or_unsafe_evidence_never_authorizes_release(recovery, damage):
    service, state, stream, request, events, docs = recovery
    if damage == "unknown":
        events[-1]["State"] = "unknown"
    elif damage == "missing_event":
        events.pop()
    elif damage == "missing_closure":
        docs.pop(stream["ClosureReference"])
    elif damage == "changed_payload":
        docs[request["PayloadReference"]] = b"{}"
    elif damage == "live":
        stream["State"] = state["streams"][0]["State"] = "open"
    elif damage == "foreign_owner":
        state["resources"][0]["ActiveJobID"] = str(uuid4())
    elif damage == "replacement":
        state["replacements"] = [dict(ReplacementID=str(uuid4()))]
    elif damage == "changed_config":
        state["job"]["ProvenanceJson"] = "{}"
    elif damage == "changed_targets":
        state["membership"].append("destination:foreign")
    evidence, token, done = service.inspect(state["job"]["JobID"])
    assert not done and not evidence["actions"]
    with pytest.raises((SourceConflict, KeyError)):
        service.execute(
            state["job"]["JobID"], ACTION, token, "recovery:" + str(uuid4()), "obsolete"
        )
    service.dal.settle.assert_not_called()


def test_stale_confirmation_and_changed_original_closure_are_rejected(recovery):
    service, state, stream, *_ = recovery
    job = state["job"]["JobID"]
    _, token, _ = service.inspect(job)
    state["job"]["Version"] += 1
    with pytest.raises(SourceConflict):
        service.execute(job, ACTION, token, "recovery:" + str(uuid4()), "obsolete")
    contain(recovery)
    stream["Version"] += 1
    state["streams"][0]["Version"] += 1
    assert not service.inspect(job)[0]["actions"]
    service.dal.settle.assert_not_called()


def test_abandoned_history_survives_later_configuration_and_account_use(recovery):
    service, state, *_ = recovery
    job = state["job"]["JobID"]
    _, token, _ = service.inspect(job)
    service.execute(job, ACTION, token, "recovery:" + str(uuid4()), "obsolete export")
    changed = deepcopy(service.registration.value())
    changed["legacy_configuration"]["scan_data"]["destinations"] = ["later-config"]
    service.registration = SimpleNamespace(value=lambda: changed)
    state["foreign_streams"] = [dict(StreamID=str(uuid4()), State="open")]
    for resource in state["resources"]:
        resource.update(ActiveJobID=str(uuid4()), OwnerID=str(uuid4()))
    evidence, _, resolved = service.inspect(job)
    assert resolved and evidence["outcome"] == "abandoned" and not evidence["actions"]
    service.dal.settle.assert_called_once()


def test_active_foreign_stream_prevents_new_closeout(recovery):
    service, state, *_ = recovery
    state["foreign_streams"] = [dict(StreamID=str(uuid4()), State="open")]
    evidence, _, resolved = service.inspect(state["job"]["JobID"])
    assert not resolved and not evidence["actions"]


@pytest.fixture
def guided_closeout(recovery, monkeypatch):
    from threading import RLock

    pytest.importorskip("services.failed_export_recovery_authority")
    from scripts.run_export_authority import AuthorityBroker
    from services.export_proof_progress import ProofProgress
    from services.export_replacement_recovery_adapter import ReplacementRecoveryAdapter
    from services.export_runtime_composition import LocalAuthorityClient
    from services.recovery_release_policy import p0a_presentation
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import Store

    service, state, *_ = recovery
    contain(recovery)
    service.execution.connect = object()
    broker = object.__new__(AuthorityBroker)
    broker.proof_progress = ProofProgress(broker._dispatch)
    broker.boundary = SimpleNamespace(fingerprint="b" * 64, recheck=Mock())
    broker.authority = SimpleNamespace(
        _lock=RLock(), dal=service.execution, store=service.store, enrollment_plan=None
    )
    broker.replacements = SimpleNamespace(
        registrations=lambda: ([service.registration], service.registration)
    )
    monkeypatch.setattr(
        "services.failed_export_recovery_authority.FailedExportCloseoutDAL",
        lambda *_a, **_k: service.dal,
    )
    monkeypatch.setattr(
        "services.legacy_export_closeout_dal.LegacyExportCloseoutDAL", lambda *_a, **_k: service.dal
    )
    client = LocalAuthorityClient(broker)
    adapter = ReplacementRecoveryAdapter(
        SimpleNamespace(discovery=SimpleNamespace(job=lambda _: deepcopy(state))),
        runtime=SimpleNamespace(client=client),
        store=None,
    )
    store = Store()
    engine = RecoveryService(
        store,
        {"export_job": adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    evidence, token, resolved = adapter.inspect(state["job"]["JobID"])
    incident = store.observe(
        "export_job", state["job"]["JobID"], evidence, token, resolved=resolved
    )
    return engine, incident, store, service


def test_private_guided_confirmation_and_lost_reply(guided_closeout):
    from kvk.dal.new_source_import_dal import UncertainCommit
    from services.recovery_service import RecoveryActor
    from tests.test_guided_recovery import ACTOR, execute

    engine, incident, store, service = guided_closeout
    with pytest.raises(SourceConflict):
        execute(engine, incident, actor=RecoveryActor(99, 2, 3), action=ACTION)
    assert not store.actions
    store.lose_claim_ack = True
    with pytest.raises(UncertainCommit):
        execute(engine, incident, action=ACTION)
    service.dal.settle.assert_not_called()
    engine.review(ACTOR, incident["IncidentID"])
    assert engine.review(ACTOR, incident["IncidentID"])["State"] == "resolved"
    service.dal.settle.assert_called_once()
    assert store.actions[0]["State"] == "verified"
