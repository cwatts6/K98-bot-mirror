from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_recovery_service import (
    ExportRecoveryAdapter,
    RolloverRecoveryAdapter,
    job_token,
)


def job_fixture(*, consumer="new_source", state="failed", attempted=False):
    snapshot = dict(
        job=dict(
            JobID=str(uuid4()),
            AccountKey="account",
            ConsumerKind=consumer,
            State=state,
            Version=3,
            PoolEpoch=2 if consumer == "new_source" else None,
            ProvenanceJson="{}",
            Stalled=1,
            KVK_NO=1,
            SourceKey="snapshot_report_v1",
        ),
        attempts=[{}] if attempted else [],
        streams=[],
        resources=[],
        season=dict(SourceKey="snapshot_report_v1", SeasonState="open", SeasonVersion=1),
    )
    discovery, coordinator, reconciler = Mock(account="account"), Mock(), Mock()
    discovery.job.side_effect = lambda _: deepcopy(snapshot)
    discovery.registered_publication.side_effect = lambda *_: dict(
        job={k: v for k, v in snapshot["job"].items() if k != "Stalled"}, pool=dict(slots=[])
    )
    return ExportRecoveryAdapter(discovery, coordinator, reconciler), snapshot


def test_publication_observation_preserves_receipt_for_each_saved_action():
    adapter, snapshot = job_fixture(state="confirmed", attempted=True)
    history = [
        dict(actor="recovery:prior", proof=dict(proof_id=str(uuid4()), state="confirmed")),
        dict(actor="direct-operator", proof=dict(proof_id=str(uuid4()), state="confirmed")),
    ]
    snapshot["job"]["ProvenanceJson"] = json.dumps(dict(reconciliations=history))
    evidence, _, _ = adapter.inspect(snapshot["job"]["JobID"])
    assert evidence["publication_receipts"] == [
        dict(actor=entry["actor"], **entry["proof"]) for entry in history
    ]
    adapter.reconciler.probe.assert_not_called()


@pytest.mark.parametrize("consumer", ["new_source", "scan_data", "all_kvk"])
def test_guided_retry_only_for_proven_pre_attempt_failure(consumer):
    adapter, snapshot = job_fixture(consumer=consumer)
    evidence, token, resolved = adapter.inspect(snapshot["job"]["JobID"])
    assert not resolved and set(evidence["actions"]) == (
        {"retry_unstarted"} if consumer == "new_source" else {"retry_unstarted", "skip_unstarted"}
    )
    adapter.execute(
        snapshot["job"]["JobID"], "retry_unstarted", token, "recovery:action", "corrected"
    )
    adapter.coordinator.request_safe_retry.assert_called_once()
    adapter.reconciler.probe.assert_not_called()
    snapshot["attempts"] = [{}]
    assert adapter.inspect(snapshot["job"]["JobID"])[0]["actions"] == {}


def test_lost_retry_acknowledgement_reads_original_audit_without_duplicate_retry():
    adapter, snapshot = job_fixture()
    token = job_token(snapshot)
    snapshot["job"].update(
        Version=4,
        ProvenanceJson=json.dumps(
            dict(
                safe_retry_history=[dict(actor="recovery:action")], safe_retry=dict(requested=True)
            )
        ),
    )
    assert (
        adapter.reconcile(
            "source", dict(ActionKind="retry_unstarted", ActionID="action", EvidenceHash=token)
        )
        == "verified"
    )
    adapter.coordinator.request_safe_retry.assert_not_called()
    assert adapter.inspect("source")[2]


def test_unknown_provider_outcome_is_not_released_by_human_confirmation():
    adapter, snapshot = job_fixture(state="uncertain", attempted=True)
    token = job_token(snapshot)
    adapter.reconciler.probe.side_effect = SourceConflict("Unknown request outcome")
    with pytest.raises(SourceConflict):
        adapter.execute("source", "verify_publication", token, "recovery:action", "admin checked")
    adapter.coordinator.reconcile_operator.assert_not_called()
    assert not adapter.inspect("source")[2]


@pytest.mark.parametrize("error_type", ["PublicationCheckUnavailable", "TimeoutError", None])
def test_only_durable_initial_probe_refusal_can_close_without_applying(error_type):
    adapter, snapshot = job_fixture(state="uncertain", attempted=True)
    action = dict(
        ActionID="action",
        ActionKind="verify_publication",
        State="unknown",
        EvidenceHash=job_token(snapshot),
        Reason="Check original outcome",
        ResultJson=json.dumps({"error_type": error_type}),
    )
    adapter.reconciler.probe.side_effect = SourceConflict("Proof still unavailable")
    if error_type == "PublicationCheckUnavailable":
        assert adapter.reconcile("source", action) == "not_applied"
        adapter.reconciler.probe.assert_not_called()
    else:
        with pytest.raises(SourceConflict):
            adapter.reconcile("source", action)
    adapter.coordinator.reconcile_operator.assert_not_called()


def test_stale_preview_and_changed_registration_refuse_before_provider_reads():
    adapter, snapshot = job_fixture(state="uncertain", attempted=True)
    token = job_token(snapshot)
    snapshot["job"]["Version"] += 1
    with pytest.raises(SourceConflict):
        adapter.execute("source", "verify_publication", token, "recovery:action", "verify")
    adapter.reconciler.probe.assert_not_called()
    adapter.discovery.registered_publication.side_effect = SourceConflict("Registration changed")
    with pytest.raises(SourceConflict):
        adapter.execute(
            "source", "verify_publication", job_token(snapshot), "recovery:action", "verify"
        )
    adapter.reconciler.probe.assert_not_called()


def test_age_threshold_does_not_change_durable_action_identity():
    adapter, snapshot = job_fixture()
    token = job_token(snapshot)
    snapshot["job"]["Stalled"] = 0
    assert job_token(snapshot) == token
    snapshot["resources"] = [{"Version": 99}]
    assert job_token(snapshot) == token


@pytest.mark.parametrize("queued", [False, True])
def test_isolated_destination_reopens_incident_and_disables_ordinary_retry(queued):
    adapter, snapshot = job_fixture(consumer="scan_data")
    if queued:
        snapshot["job"]["ProvenanceJson"] = json.dumps(dict(safe_retry=dict(requested=True)))
    original_token = job_token(snapshot)
    snapshot["isolated_targets"] = [dict(FileID="old-file", ContainmentID=str(uuid4()))]
    evidence, token, resolved = adapter.inspect("source")
    assert not resolved and evidence["outcome"] == "replacement_required"
    assert "retry_unstarted" not in evidence["actions"]
    assert token != original_token
    with pytest.raises(SourceConflict, match="replacements"):
        adapter.execute("source", "retry_unstarted", token, "recovery:action", "retry")
    adapter.coordinator.request_safe_retry.assert_not_called()


def test_skip_reconciles_only_exact_receipt_and_stale_stream_fences_intent():
    adapter, snapshot = job_fixture(consumer="scan_data")
    action = dict(
        ActionID="action",
        ActionKind="skip_unstarted",
        EvidenceHash=job_token(snapshot),
        Reason="skip",
    )
    snapshot["streams"] = [dict(StreamID="new-stream")]
    assert adapter.reconcile("source", action) == "not_applied"
    adapter.coordinator.skip_unstarted.assert_not_called()
    snapshot["streams"] = []
    snapshot["job"].update(
        Version=4,
        ProvenanceJson=json.dumps(
            dict(export_skipped=dict(actor="recovery:action", reason="skip"))
        ),
    )
    assert adapter.reconcile("source", action) == "verified"
    snapshot["attempts"] = [{}]
    assert adapter.reconcile("source", action) is None
    assert not adapter.inspect("source")[2]


def test_skip_timeout_does_not_claim_success_or_resend_with_new_identity():
    adapter, snapshot = job_fixture(consumer="all_kvk")
    adapter.coordinator.skip_unstarted.side_effect = TimeoutError("commit acknowledgement lost")
    action = dict(
        ActionID="action",
        ActionKind="skip_unstarted",
        EvidenceHash=job_token(snapshot),
        Reason="skip",
    )
    with pytest.raises(TimeoutError):
        adapter.reconcile("source", action)
    assert adapter.coordinator.skip_unstarted.call_args.kwargs["actor"] == "recovery:action"
    assert not adapter.inspect("source")[2]


def test_failed_retry_reopens_incident_even_with_prior_successful_queue_action():
    adapter, snapshot = job_fixture()
    snapshot["job"]["ProvenanceJson"] = json.dumps(
        dict(safe_retry_history=[dict(actor="recovery:old")])
    )
    assert not adapter.inspect("source")[2]
    assert "retry_unstarted" in adapter.inspect("source")[0]["actions"]


def test_execution_stream_requires_reconciliation_even_without_attempt():
    adapter, snapshot = job_fixture(consumer="scan_data")
    snapshot["streams"] = [dict(StreamID=str(uuid4()), State="closed")]
    evidence, _, resolved = adapter.inspect("source")
    assert not resolved and not evidence["actions"]
    assert "execution must be reconciled first" in evidence["explanation"]


@pytest.mark.parametrize("state", ["planned", "closing", "closed", None])
def test_season_lifecycle_withholds_retry_and_changes_reviewed_evidence(state):
    adapter, snapshot = job_fixture()
    token = job_token(snapshot)
    if state is None:
        snapshot["season"] = None
    else:
        snapshot["season"]["SeasonState"] = state
        snapshot["season"]["SeasonVersion"] += 1
    evidence, current, resolved = adapter.inspect("source")
    assert current != token and not resolved
    assert "retry_unstarted" not in evidence["actions"]
    assert "season is not open" in evidence["explanation"]
    assert (
        adapter.reconcile(
            "source", dict(ActionID="action", ActionKind="retry_unstarted", EvidenceHash=token)
        )
        == "not_applied"
    )
    adapter.coordinator.request_safe_retry.assert_not_called()


def test_confirmed_export_description_does_not_claim_fresh_provider_check():
    adapter, _ = job_fixture(state="confirmed", attempted=True)
    evidence, _, resolved = adapter.inspect("source")
    assert resolved and "confirmed delivery" in evidence["explanation"]
    assert "not a fresh check" in evidence["explanation"]


def test_guided_retirement_checks_again_after_clear_before_release():
    adapter, snapshot = job_fixture(state="uncertain", attempted=True)
    before = dict(job=deepcopy(snapshot["job"]), pool=dict(slots=[dict(State="retired")]))
    before["job"].pop("Stalled")
    after = dict(job=deepcopy(before["job"]), pool=dict(slots=[dict(State="free")]))
    after["job"]["Version"] += 1
    adapter.discovery.registered_publication.side_effect = [before, after]
    adapter.retirement = Mock()
    adapter.reconciler.probe.side_effect = [dict(kind="retirement"), dict(kind="publication")]
    adapter.execute("source", "verify_publication", job_token(snapshot), "recovery:action", "ok")
    adapter.retirement.resume.assert_called_once_with(
        before, dict(kind="retirement"), actor="recovery:action"
    )
    adapter.coordinator.reconcile_operator.assert_called_once_with(
        after, dict(kind="publication"), actor="recovery:action"
    )


def test_pending_retirement_resumes_only_same_action_and_never_replays_unknown_clear():
    adapter, snapshot = job_fixture(state="uncertain", attempted=True)
    original_token = job_token(snapshot)
    snapshot["job"].update(
        Version=7,
        ProvenanceJson=json.dumps(dict(retirement_recovery=dict(actor="recovery:action"))),
    )
    adapter.reconciler.probe.side_effect = SourceConflict("Unknown retirement clear")
    adapter.retirement = Mock()
    action = dict(
        ActionID="action", ActionKind="verify_publication", EvidenceHash=original_token, Reason="ok"
    )
    with pytest.raises(SourceConflict):
        adapter.reconcile("source", action)
    adapter.retirement.resume.assert_not_called()
    adapter.coordinator.reconcile_operator.assert_not_called()
    action["ActionID"] = "other"
    assert adapter.reconcile("source", action) == "not_applied"


@pytest.mark.parametrize(
    "outcome,state,kind",
    [
        ("damaged", "confirmed", "rebuild_damaged"),
        ("absent", "failed", "retry_absent"),
    ],
)
def test_recovery_export_uses_durable_repair_id_and_reads_receipt_after_ack_loss(
    outcome, state, kind
):
    adapter, snapshot = job_fixture(state=state, attempted=True)
    job_id = snapshot["job"]["JobID"]
    action_id = str(uuid4())
    snapshot["job"]["ProvenanceJson"] = json.dumps(
        dict(reconciliations=[dict(proof=dict(state=outcome))])
    )
    adapter.discovery.repairs.return_value = []
    adapter.rebuild_plan = Mock(
        return_value=dict(
            snapshot=dict(job={k: v for k, v in snapshot["job"].items() if k != "Stalled"}),
            actor="admin",
            proof=dict(state=outcome),
        )
    )
    evidence, token, resolved = adapter.inspect(job_id)
    assert not resolved and set(evidence["actions"]) == {kind}
    adapter.coordinator.admit_repair.side_effect = TimeoutError("commit acknowledgement lost")
    with pytest.raises(TimeoutError):
        adapter.execute(job_id, kind, token, "recovery:" + action_id, "recover export")
    repair_id, plan = adapter.coordinator.admit_repair.call_args.args
    assert repair_id == action_id and plan["actor"] == "recovery:" + action_id
    repair = dict(
        JobID=str(uuid4()),
        ProvenanceJson=json.dumps(dict(repair=plan)),
        State="ready",
        CreatedUTC="2026-10-19T21:00:00",
    )
    adapter.coordinator.repair_receipt.return_value = dict(
        job_id=repair["JobID"], actor=plan["actor"]
    )
    adapter.discovery.job.side_effect = lambda key: (
        dict(job=repair) if key == repair["JobID"] else deepcopy(snapshot)
    )
    action = dict(
        ActionID=action_id,
        ActionKind=kind,
        EvidenceHash=token,
        Reason="replace damage",
    )
    assert adapter.reconcile(job_id, action) == "verified"
    adapter.coordinator.admit_repair.assert_called_once()
    adapter.discovery.repairs.return_value = [repair]
    assert not adapter.inspect(job_id)[2]
    assert adapter.inspect(job_id)[0]["recovery_links"][0]["source_id"] == repair["JobID"]
    repair["State"] = "confirmed"
    assert adapter.inspect(job_id)[2]
    repair["ProvenanceJson"] = json.dumps(
        dict(repair=plan, reconciliations=[dict(proof=dict(state="damaged"))])
    )
    assert not adapter.inspect(job_id)[2]
    adapter.coordinator.repair_receipt.return_value["actor"] = "other"
    with pytest.raises(SourceConflict, match="belong"):
        adapter.reconcile(job_id, action)


def test_damage_plan_changed_during_verification_does_not_queue_repair():
    adapter, snapshot = job_fixture(state="confirmed", attempted=True)
    plan = dict(snapshot=dict(job=dict(snapshot["job"], Version=99)))
    adapter.rebuild_plan = Mock(return_value=plan)
    from services.export_recovery_service import PublicationCheckUnavailable

    with pytest.raises(PublicationCheckUnavailable, match="no export was admitted") as error:
        adapter.execute(
            "source", "rebuild_damaged", job_token(snapshot), "recovery:" + str(uuid4()), "ok"
        )
    assert isinstance(error.value.__cause__, SourceConflict)
    assert "changed" in str(error.value.__cause__)
    adapter.coordinator.admit_repair.assert_not_called()


def test_rollover_confirmation_requires_exact_proof_and_reads_its_audit_after_ack_loss():
    snapshot = dict(
        operation=dict(
            State="uncertain",
            Phase="uncertain",
            OldKVK=1,
            NewKVK=2,
            ProgressJson=json.dumps(dict(request=dict(phase="setup_pending"))),
            PlanJson="{}",
            PlanHash=digest({}).hex(),
        ),
        resources=[],
    )
    discovery, pools, reconciler = Mock(), Mock(), Mock()
    discovery.rollover.side_effect = lambda *_: deepcopy(snapshot)
    adapter = RolloverRecoveryAdapter(discovery, pools, reconciler)
    evidence, token, resolved = adapter.inspect("source")
    assert not resolved and "verify_rollover" in evidence["actions"]
    reconciler.probe_rollover.side_effect = SourceConflict("Unknown clear")
    with pytest.raises(SourceConflict):
        adapter.execute("source", "verify_rollover", token, "recovery:action", "verify")
    pools.reconcile_complete.assert_not_called()
    snapshot["operation"].update(
        State="completed",
        ProgressJson=json.dumps(dict(reconciliation=dict(actor="recovery:action"))),
    )
    assert (
        adapter.reconcile(
            "source", dict(ActionKind="verify_rollover", ActionID="action", EvidenceHash=token)
        )
        == "verified"
    )


def test_runtime_keeps_export_incidents_in_the_recovery_centre(monkeypatch):
    from contextlib import contextmanager

    from services import legacy_export_snapshot_service, recovery_runtime

    export = SimpleNamespace(kind="export_job")
    rollover = SimpleNamespace(kind="export_rollover")
    runtime = SimpleNamespace(
        account="account",
        store=SimpleNamespace(storage_owner="disk"),
        dal=SimpleNamespace(connect=Mock()),
        recovery_client=None,
        recovery_adapters=(export, rollover),
    )

    @contextmanager
    def caller():
        yield runtime

    monkeypatch.setattr(legacy_export_snapshot_service, "caller_runtime", caller)
    with recovery_runtime.recovery_service() as service:
        assert service.adapters["export_job"] is export
        assert service.adapters["export_rollover"] is rollover


@pytest.mark.parametrize("kind", ["retry_absent", "rebuild_damaged"])
@pytest.mark.parametrize("refusal", [True, False])
def test_repair_preparation_refusal_is_not_an_unknown_admission(kind, refusal):
    adapter, snapshot = job_fixture(state="confirmed", attempted=True)
    adapter.coordinator.repair_receipt.return_value = None
    adapter.execute = Mock()
    action = dict(
        ActionID=str(uuid4()),
        ActionKind=kind,
        EvidenceHash=job_token(snapshot),
        Reason="Retained output needed",
        State="unknown",
        ResultJson=json.dumps(
            {"error_type": "PublicationCheckUnavailable" if refusal else "UncertainCommit"}
        ),
    )
    outcome = adapter.reconcile(snapshot["job"]["JobID"], action)
    if refusal:
        assert outcome == "not_applied"
        adapter.execute.assert_not_called()
    else:
        assert outcome is None
        adapter.execute.assert_called_once()
