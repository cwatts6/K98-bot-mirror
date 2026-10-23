"""Complete private journals distinguish failed reads from dispatched writes."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from test_export_reconciliation_service import closed_stream_fixture

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.failed_export_closeout import ACTION, FailedExportCloseout
from services.legacy_export_snapshot_service import configuration_digest


@pytest.mark.parametrize("terminal", ["succeeded", "unknown", "dispatch_intent", "prepared"])
def test_closed_mutation_stream_with_only_read_requests_proves_no_writes(terminal):
    verifier, stream, request, events, _ = closed_stream_fixture(purpose="probe")
    stream["Purpose"] = "mutation"
    if terminal == "unknown":
        events[-1]["State"] = terminal
    else:
        del events[[e["State"] for e in events].index(terminal) + 1 :]
    proof = verifier.verify(
        stream["StreamID"],
        account="account-a",
        registration_hash=b"r" * 32,
        require_observation=False,
        allow_failed_reads=True,
        require_no_writes=True,
    )
    assert proof.dispatched_mutations == 0
    if terminal != "succeeded":
        with pytest.raises(SourceConflict):
            verifier.verify(
                stream["StreamID"],
                account="account-a",
                registration_hash=b"r" * 32,
                require_observation=False,
            )


@pytest.mark.parametrize("terminal", ["succeeded", "unknown", "dispatch_intent", "prepared"])
def test_dispatched_or_unfinished_mutation_cannot_be_closed(terminal):
    verifier, stream, _, events, _ = closed_stream_fixture()
    if terminal == "unknown":
        events[-1]["State"] = terminal
    else:
        del events[[e["State"] for e in events].index(terminal) + 1 :]
    with pytest.raises(SourceConflict):
        verifier.verify(
            stream["StreamID"],
            account="account-a",
            registration_hash=b"r" * 32,
            require_observation=False,
            allow_failed_reads=True,
            require_no_writes=True,
        )


@pytest.fixture
def workflow():
    verifier, stream, _, events, docs = closed_stream_fixture(purpose="probe")
    stream["Purpose"] = "mutation"
    events[-1]["State"] = "unknown"
    job_id, owner, session = (str(uuid4()) for _ in range(3))
    config = dict(consumer="scan_data", destinations=["file-a"])
    registration_hash = configuration_digest(config)
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
        ScopeJson=json.dumps(
            dict(
                resources=[
                    dict(key="account:account-a", version=3),
                    dict(key="destination:file-a", version=3),
                ]
            )
        ),
    )
    wire = {k: v.hex() if isinstance(v, bytes) else v for k, v in stream.items()}
    state = dict(
        job=dict(
            JobID=job_id,
            AccountKey="account-a",
            ConsumerKind="scan_data",
            State="failed",
            OwnerID=owner,
            Fence=2,
            Version=7,
            CreatedUTC="2026-10-01T00:00:00",
            UpdatedUTC="2026-10-01T00:01:00",
            InputHash=digest("input").hex(),
            DestinationSetHash=digest(["file-a"]).hex(),
            ProvenanceJson=json.dumps(dict(registration_sha256=registration_hash)),
        ),
        membership=["account:account-a", "destination:file-a"],
        held=[],
        attempts=[],
        streams=[wire],
        sessions=[dict(SessionID=session, AuthorityPrincipal="authority")],
        principal="authority",
    )

    def put(raw):
        key = str(uuid4())
        docs[key] = raw
        return SimpleNamespace(key=key, sha256=hashlib.sha256(raw).hexdigest())

    verifier.store.put = put

    def retire(expected, marker):
        assert state == expected
        job = state["job"]
        provenance = json.loads(job["ProvenanceJson"])
        provenance["failed_export_retired"] = marker
        job.update(ProvenanceJson=json.dumps(provenance), Version=job["Version"] + 1)

    dal = SimpleNamespace(
        account="account-a", snapshot=lambda _: deepcopy(state), retire=Mock(side_effect=retire)
    )
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
    service = FailedExportCloseout(
        dal=dal, execution=verifier.dal, store=verifier.store, registrations=[registration]
    )
    return service, state, docs, events


def test_changed_identity_between_preview_and_verification_cannot_be_approved(workflow):
    service, state, _, _ = workflow
    old = deepcopy(state)
    state["job"]["InputHash"] = digest("different input").hex()
    state["job"]["CreatedUTC"] = "2026-10-02T00:00:00"
    service.dal.snapshot = Mock(side_effect=[old, deepcopy(state), deepcopy(state)])
    evidence, token, resolved = service.inspect(state["job"]["JobID"])
    assert not evidence["actions"] and not resolved
    assert token == digest(old).hex()
    assert evidence["failure_context"]["input_sha256"] == old["job"]["InputHash"]
    service.dal.snapshot = lambda _: deepcopy(state)
    with pytest.raises(SourceConflict, match="evidence changed"):
        service.execute(
            state["job"]["JobID"], ACTION, token, "recovery:" + str(uuid4()), "obsolete"
        )
    service.dal.retire.assert_not_called()


def test_retirement_reads_back_after_lost_acknowledgement_and_restart(workflow):
    service, state, _, _ = workflow
    job_id = state["job"]["JobID"]
    evidence, token, resolved = service.inspect(job_id)
    assert not resolved and ACTION in evidence["actions"]
    assert evidence["failure_context"]["original_fault"] == "not_recorded"
    action = dict(ActionID=str(uuid4()), ActionKind=ACTION, EvidenceHash=token, Reason="obsolete")
    service.execute(job_id, ACTION, token, "recovery:" + action["ActionID"], action["Reason"])
    restarted = FailedExportCloseout(
        dal=service.dal,
        execution=service.execution,
        store=service.store,
        registrations=service.registrations,
    )
    assert restarted.reconcile(job_id, action) == "verified"
    assert restarted.inspect(job_id)[2]
    assert service.dal.retire.call_count == 1
    assert state["job"]["State"] == "failed" and not state["held"]
    with pytest.raises(SourceConflict):
        restarted.execute(job_id, ACTION, token, "recovery:" + action["ActionID"], action["Reason"])


@pytest.mark.parametrize("change", ["held", "attempt", "config", "membership", "journal", "owner"])
def test_changed_or_unverifiable_evidence_does_not_offer_retirement(workflow, change):
    service, state, docs, _ = workflow
    if change == "held":
        state["held"] = [dict(ResourceKey="account:account-a")]
    if change == "attempt":
        state["attempts"] = [dict(AttemptID=str(uuid4()))]
    if change == "config":
        state["job"]["ProvenanceJson"] = "{}"
    if change == "membership":
        state["membership"].append("destination:other")
    if change == "journal":
        docs.clear()
    if change == "owner":
        state["streams"][0]["OwnerID"] = str(uuid4())
    evidence, _, resolved = service.inspect(state["job"]["JobID"])
    assert not evidence["actions"] and not resolved
    service.dal.retire.assert_not_called()


@pytest.fixture
def guided(workflow, monkeypatch):
    from threading import RLock

    from scripts.run_export_authority import AuthorityBroker
    from services.export_proof_progress import ProofProgress
    from services.export_replacement_recovery_adapter import ReplacementRecoveryAdapter
    from services.export_runtime_composition import LocalAuthorityClient
    from services.recovery_release_policy import p0a_presentation
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import Store

    service, state, _, _ = workflow
    service.execution.connect = object()
    broker = object.__new__(AuthorityBroker)
    broker.proof_progress = ProofProgress(broker._dispatch)
    broker.boundary = SimpleNamespace(fingerprint="b" * 64, recheck=Mock())
    broker.authority = SimpleNamespace(
        _lock=RLock(), dal=service.execution, store=service.store, enrollment_plan=None
    )
    broker.replacements = SimpleNamespace(
        registrations=lambda: (service.registrations, service.registrations[-1])
    )
    monkeypatch.setattr(
        "services.failed_export_recovery_authority.FailedExportCloseoutDAL",
        lambda *_a, **_kw: service.dal,
    )
    monkeypatch.setattr(
        "services.legacy_export_closeout_dal.LegacyExportCloseoutDAL",
        lambda *_a, **_kw: SimpleNamespace(receipt_exists=lambda _job: False),
    )
    client = LocalAuthorityClient(broker)
    base = SimpleNamespace(discovery=SimpleNamespace(job=lambda _: deepcopy(state)))
    adapter = ReplacementRecoveryAdapter(base, runtime=SimpleNamespace(client=client), store=None)
    store = Store()
    recovery = RecoveryService(
        store,
        {"export_job": adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    evidence, token, resolved = adapter.inspect(state["job"]["JobID"])
    row = store.observe("export_job", state["job"]["JobID"], evidence, token, resolved=resolved)
    return recovery, row, store, broker


def test_guided_client_authority_approval_and_report_verify(guided):
    from services.recovery_report import incident_report
    from services.recovery_service import RecoveryActor
    from tests.test_guided_recovery import ACTOR, execute

    recovery, row, store, broker = guided
    with pytest.raises(SourceConflict):
        execute(recovery, row, actor=RecoveryActor(99, 2, 3), action=ACTION)
    assert not store.actions
    result = execute(recovery, row, action=ACTION)
    if result["State"] != "resolved":
        result = recovery.review(ACTOR, row["IncidentID"])
    assert result["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"
    report = incident_report(recovery, result)
    assert "retired" in json.dumps(report)
    assert "not_recorded" in json.dumps(report)
    assert "original_registration_sha256" in json.dumps(report)
    assert "original_job" not in json.dumps(report)
    broker.boundary.recheck.assert_called()


def test_lost_intent_ack_reconciles_once_through_authority(guided, workflow):
    from kvk.dal.new_source_import_dal import UncertainCommit
    from tests.test_guided_recovery import ACTOR, execute

    recovery, row, store, _ = guided
    store.lose_claim_ack = True
    with pytest.raises(UncertainCommit):
        execute(recovery, row, action=ACTION)
    assert workflow[0].dal.retire.call_count == 0
    recovery.review(ACTOR, row["IncidentID"])
    assert recovery.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert workflow[0].dal.retire.call_count == 1


@pytest.mark.parametrize("damage", ["deployment", "extra", "operation", "payload"])
def test_authority_rejects_forged_closeout_message(guided, damage):
    _, row, _, broker = guided
    message = dict(
        version=1,
        action="failed_export_recovery",
        job_id=row["SourceID"],
        operation="inspect",
        deployment_hash=broker.boundary.fingerprint,
    )
    if damage == "deployment":
        message["deployment_hash"] = "c" * 64
    if damage == "extra":
        message["registration"] = {}
    if damage == "operation":
        message["operation"] = "fields"
    if damage == "payload":
        message["payload"] = {"skip": True}
    with pytest.raises((SourceConflict, ValueError)):
        broker.dispatch(message)
