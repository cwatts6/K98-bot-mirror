"""Guided RPC actions retain authority decisions and exact base-operation tokens."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_recovery_service import job_token
from services.export_replacement_recovery_adapter import ReplacementRecoveryAdapter
from services.export_runtime_composition import RuntimeLifetime


@pytest.fixture
def adapter():
    snapshot = dict(
        job=dict(
            JobID="job",
            ConsumerKind="new_source",
            State="uncertain",
            ProvenanceJson="{}",
            Version=1,
        ),
        attempts=[],
        streams=[dict(StreamID="stream")],
        resources=[],
        season=dict(SourceKey="snapshot_report_v1", SeasonState="open", SeasonVersion=1),
    )
    base = Mock()
    base.discovery.job.side_effect = lambda _: deepcopy(snapshot)
    base.inspect.return_value = (
        dict(actions=dict(verify_publication=dict(label="Verify"))),
        "base-token",
        False,
    )
    runtime = RuntimeLifetime(object())
    runtime.registration = SimpleNamespace(value=lambda: {"legacy_configuration": {}})
    runtime.client = Mock()
    runtime.client.replacement_recovery.side_effect = lambda *_args, **_kw: dict(
        evidence=dict(actions=dict(isolate_targets=dict(label="Retire"))),
        token="authority-token",
        resolved=False,
    )
    runtime.refresh_replacement_registration = Mock()
    result = ReplacementRecoveryAdapter(base, runtime=runtime, store=object())
    return SimpleNamespace(adapter=result, base=base, runtime=runtime, snapshot=snapshot)


@pytest.mark.parametrize("marker", [{"reference": "receipt", "sha256": "a" * 64}, None])
@pytest.mark.parametrize("verified", [True, False])
def test_retired_export_cannot_reenter_replacement_after_destination_isolation(
    adapter, marker, verified
):
    import json

    r = adapter
    r.snapshot["job"].update(
        State="failed",
        ConsumerKind="scan_data",
        ProvenanceJson=json.dumps({"failed_export_retired": marker}),
    )
    r.snapshot["isolated_targets"] = [dict(FileID="old-file")]
    expected = dict(actions={}, outcome="retired" if verified else "failed")
    r.runtime.client.failed_export_recovery.return_value = dict(
        evidence=expected, token="receipt-token", resolved=verified
    )
    assert r.adapter.inspect("job") == (expected, "receipt-token", verified)
    r.runtime.client.failed_export_recovery.assert_called_once_with("job", "inspect")
    r.runtime.client.replacement_recovery.assert_not_called()
    r.base.inspect.assert_not_called()


def test_original_publication_verification_remains_guided_before_isolation(adapter):
    r = adapter
    evidence, token, _ = r.adapter.inspect("job")
    assert set(evidence["actions"]) == {"verify_publication", "isolate_targets"}
    original = job_token(r.snapshot)
    r.adapter.execute("job", "verify_publication", token, "actor", "reason")
    r.base.execute.assert_called_once_with("job", "verify_publication", original, "actor", "reason")


@pytest.mark.parametrize(
    "outcome,done,expected",
    [
        ("replacement_delivered", True, True),
        ("replacement_delivered", False, False),
        ("retired", True, False),
    ],
)
@pytest.mark.parametrize("parent_claims_delivery", [False, True])
def test_original_repair_waits_for_verified_successor_delivery(
    adapter, outcome, done, expected, parent_claims_delivery
):
    import json

    r = adapter
    parent = deepcopy(r.snapshot)
    parent["job"].update(State="failed", JobID="parent")
    parent["streams"] = []
    child = deepcopy(r.snapshot)
    child["job"].update(
        JobID="child",
        ProvenanceJson=json.dumps({"repair": {"snapshot": {"job": {"JobID": "parent"}}}}),
    )
    r.base.discovery.job.side_effect = lambda job: deepcopy(parent if job == "parent" else child)
    r.base.discovery.repairs.return_value = [child["job"]]
    r.base.inspect.side_effect = lambda job: (
        dict(
            actions={},
            outcome="failed",
            recovery_links=(
                [dict(label="Review repair export", kind="export_job", source_id="child")]
                if job == "parent"
                else []
            ),
        ),
        "a" * 64,
        parent_claims_delivery if job == "parent" else False,
    )
    r.runtime.client.replacement_recovery.side_effect = lambda *_args, **_kw: dict(
        evidence=dict(actions={}, outcome=outcome), token="b" * 64, resolved=done
    )
    evidence, _, resolved = r.adapter.inspect("parent")
    assert resolved is expected
    assert (evidence["outcome"] == "repair_delivered") is expected
    child_evidence, _, _ = r.adapter.inspect("child")
    assert child_evidence["recovery_links"][0]["label"] == "Return to original export"


@pytest.mark.parametrize("changed_part", ["job", "season"])
def test_base_action_does_not_adopt_state_changed_during_authority_review(adapter, changed_part):
    r = adapter
    original = job_token(r.snapshot)

    def changed(_):
        if changed_part == "job":
            r.snapshot["job"]["Version"] += 1
        else:
            r.snapshot["season"].update(SeasonState="closing", SeasonVersion=2)
        return dict(actions=dict(verify_publication={})), "authority-token", False

    r.adapter.inspect = changed

    def consume(_job, _action, token, *_):
        if token != job_token(r.snapshot):
            raise SourceConflict("Stale original job")

    r.base.execute.side_effect = consume
    with pytest.raises(SourceConflict, match="Stale"):
        r.adapter.execute("job", "verify_publication", "authority-token", "actor", "reason")
    assert r.base.execute.call_args.args[2] == original


@pytest.mark.parametrize("fault", ["token", "isolated"])
def test_stale_or_isolated_publication_cannot_use_old_settlement(adapter, fault):
    r = adapter
    if fault == "isolated":
        r.snapshot["isolated_targets"] = [dict(FileID="old-file")]
    with pytest.raises(SourceConflict):
        r.adapter.execute(
            "job",
            "verify_publication",
            "stale" if fault == "token" else "authority-token",
            "actor",
            "reason",
        )
    r.base.execute.assert_not_called()


def test_activation_runs_inside_owned_admin_call_then_refreshes_registration(adapter):
    r = adapter
    with r.runtime.owned():
        r.adapter.execute("job", "activate_replacements", "authority-token", "actor", "reason")
        assert len(r.runtime._calls) == 1
    r.runtime.client.replacement_recovery.assert_called_once_with(
        "job",
        "execute",
        step="activate_replacements",
        token="authority-token",
        actor="actor",
        reason="reason",
        payload=None,
    )
    r.runtime.refresh_replacement_registration.assert_called_once()
    assert not r.runtime._calls and not r.runtime._reconfiguration_calls


def test_failed_activation_preserves_call_and_does_not_install_unverified_registry(adapter):
    r = adapter
    r.runtime.client.replacement_recovery.side_effect = SourceConflict("Activation unverified")
    with r.runtime.owned():
        with pytest.raises(SourceConflict, match="unverified"):
            r.adapter.execute("job", "activate_replacements", "authority-token", "actor", "reason")
        assert len(r.runtime._calls) == 1
    r.runtime.refresh_replacement_registration.assert_not_called()


def test_queue_uses_only_authority_context_and_reconfigures_before_spool_access(
    adapter, monkeypatch
):
    r = adapter
    activation = dict(activation_id="sealed")
    r.runtime.client.replacement_recovery.return_value = activation
    r.runtime.client.replacement_recovery.side_effect = None
    delivery = Mock()

    def queue(*args, **kwargs):
        assert not r.runtime._calls and r.runtime._reconfiguration_calls
        r.runtime.refresh_replacement_registration.assert_called_once()
        assert args == ("job", activation, "publish_replacement")

    delivery.execute.side_effect = queue
    monkeypatch.setattr(r.adapter, "_delivery", lambda: delivery)
    wake = Mock()
    monkeypatch.setattr("services.export_coordination_service.wake_exports", wake)
    with r.runtime.owned():
        r.adapter.execute("job", "publish_replacement", "authority-token", "actor", "reason")
    r.runtime.client.replacement_recovery.assert_called_once_with(
        "job", "context", token="authority-token"
    )
    wake.assert_called_once()


def test_changed_queue_decision_reconciles_receipt_without_replaying_publish(adapter, monkeypatch):
    r = adapter
    r.runtime.client.replacement_recovery.side_effect = [dict(token="changed"), "verified"]
    execute = Mock()
    monkeypatch.setattr(r.adapter, "execute", execute)
    action = dict(
        ActionID="action",
        ActionKind="publish_replacement",
        EvidenceHash="original",
        Reason="Confirmed",
        InputJson=None,
        Diagnostic="private diagnostic",
    )
    assert r.adapter.reconcile("job", action) == "verified"
    execute.assert_not_called()
    assert (
        "Diagnostic"
        not in r.runtime.client.replacement_recovery.call_args.kwargs["recovery_action"]
    )
