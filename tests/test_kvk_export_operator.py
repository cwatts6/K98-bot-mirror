"""Offline authority, confirmation and zero-provider operator boundaries."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.services.new_source_admin_service import SourceAccess, SourceActor
from kvk.services.source_export_operator_service import EXPORT_ACTIONS, SourceExportOperatorService


@pytest.fixture
def actor():
    return SourceActor(1, 2, 3, frozenset())


@pytest.fixture
def access():
    return SourceAccess(True, 2, 3, 1, frozenset({5}), frozenset({3}))


@pytest.fixture
def service(access):
    pools = Mock()
    pools.operation.side_effect = SourceConflict("not found")
    return SourceExportOperatorService(
        access_factory=lambda: access,
        pools=pools,
        coordinator=Mock(output_operations=True),
        rollover=Mock(),
        generation_loader=Mock(),
        reconciler=Mock(),
        now=lambda: 10,
    )


@pytest.mark.parametrize("action", sorted(EXPORT_ACTIONS))
def test_uploader_never_inherits_privileged_export_authority(access, action):
    with pytest.raises(PermissionError):
        access.authorize(SourceActor(9, 2, 3, frozenset({5})), action)


def test_config_is_rechecked_for_every_action(service, actor):
    service.access_factory = Mock(side_effect=PermissionError("disabled"))
    with pytest.raises(PermissionError):
        service.export(actor, 16)
    service.pools.export_context.assert_not_called()


def test_rollover_reconciliation_uses_exact_snapshot_and_no_mutation_adapter(service, actor):
    operation_id = str(uuid4())
    service.pools.operation.side_effect = None
    service.pools.operation.return_value = {"OperationID": operation_id}
    snapshot = {"operation": {"OperationID": operation_id, "State": "uncertain"}}
    service.pools.operation_snapshot.return_value = snapshot
    proof = {"state": "completed", "writer_terminated": True}
    service.reconciler.probe_rollover.return_value = proof
    service.pools.reconcile_complete.return_value = dict(
        OperationID=operation_id,
        State="completed",
        Phase="complete",
        OldKVK=16,
        NewKVK=17,
        OldEpoch=1,
        TargetEpoch=2,
    )
    assert service.reconcile(actor, operation_id)["State"] == "completed"
    service.pools.reconcile_complete.assert_called_once_with(snapshot, proof, actor="1")
    service.coordinator.reconcile_operator.assert_not_called()
    service.rollover.advance.assert_not_called()


def test_confirmed_repair_receipt_survives_restart_without_new_admission(service, actor):
    token = str(uuid4())
    service.coordinator.repair_receipt.return_value = dict(
        job_id="job", repair_id=token, state="ready", actor="1", guild="2", channel="3"
    )
    assert service.confirm(actor, token) == dict(job_id="job", repair_id=token, state="ready")
    service.coordinator.admit_repair.assert_not_called()
    service.coordinator.repair_receipt.return_value["channel"] = "4"
    with pytest.raises(PermissionError):
        service.confirm(actor, token)


def context(state="confirmed"):
    return dict(
        pool=dict(
            PoolID=str(uuid4()),
            ActiveKVK=16,
            Epoch=3,
            PoolState="active",
            OwnerID=None,
            IndexFileID="index-id",
        ),
        intent=dict(IntentID="intent", VectorHash="a" * 64),
        jobs=[dict(JobID="job", IntentID="intent", RepairID=None, State=state)],
        slots=[],
    )


def test_exact_confirmed_export_is_zero_provider_and_zero_materialization(service, actor):
    service.pools.export_context.return_value = context()
    result = service.export(actor, 16)
    assert result == dict(job_id="job", state="confirmed", no_op=True)
    service.generation_loader.assert_not_called()
    service.reconciler.probe.assert_not_called()
    service.coordinator.enqueue.assert_not_called()


@pytest.mark.parametrize("state", ["running", "uncertain", "failed", "ready"])
def test_existing_work_never_becomes_blind_retry(service, actor, state):
    service.pools.export_context.return_value = context(state)
    assert service.export(actor, 16)["state"] == state
    service.coordinator.enqueue.assert_not_called()


def test_pre_attempt_retry_keeps_job_identity_and_uses_audited_dal(service, actor):
    row = context("failed")
    row["attempts"] = []
    row["pool"]["AccountKey"] = "account-a"
    row["jobs"][0]["Version"] = 7
    service.pools.export_context.return_value = row
    assert service.export(actor, 16) == dict(job_id="job", state="queued", no_op=False)
    service.coordinator.request_safe_retry.assert_called_once_with(
        "job",
        "account-a",
        expected_version=7,
        expected_epoch=3,
        actor="1",
        reason="Operator requested retry of proven pre-attempt failure",
    )
    service.coordinator.enqueue.assert_not_called()
    service.generation_loader.assert_not_called()


def test_status_is_read_only_and_hides_unconfirmed_link(service, actor):
    service.pools.export_context.return_value = context("uncertain")
    assert service.status(actor, 16)["link"] is None
    service.coordinator.enqueue.assert_not_called()
    service.reconciler.probe.assert_not_called()
    service.generation_loader.assert_not_called()


def test_preview_pins_a_deep_copy_and_expires(service, actor):
    payload = {"files": ["file-a"]}
    preview = service._preview(actor, "rollover_confirm", payload)
    payload["files"].append("mutable")
    assert "mutable" not in preview.payload
    service.now = lambda: 310
    with pytest.raises(SourceConflict, match="expired"):
        service.confirm(actor, preview.token)
    service.rollover.confirm.assert_not_called()


def test_preview_owner_and_channel_cannot_be_substituted(service, actor):
    preview = service._preview(actor, "rollover_confirm", {})
    other = SourceActor(actor.user_id, actor.guild_id, 99, frozenset())
    with pytest.raises(PermissionError):
        service.confirm(other, preview.token)
    service.rollover.confirm.assert_not_called()


def test_restart_expires_unconfirmed_preview(service, actor):
    preview = service._preview(actor, "rollover_confirm", {})
    service._previews.clear()
    with pytest.raises(SourceConflict, match="restart"):
        service.confirm(actor, preview.token)


def test_restart_duplicate_confirm_reads_durable_outcome_without_work(service, actor):
    token = str(uuid4())
    service.pools.operation.side_effect = None
    service.pools.operation.return_value = dict(
        OperationID=token,
        ConfirmedBy="1",
        GuildID="2",
        ChannelID="3",
        State="uncertain",
        Phase="uncertain",
        OldKVK=16,
        NewKVK=17,
        OldEpoch=1,
        TargetEpoch=2,
    )
    result = service.confirm(actor, token)
    assert result["State"] == "uncertain"
    service.rollover.confirm.assert_not_called()
    service.reconciler.probe.assert_not_called()


def test_repair_cannot_be_inferred_from_uncertainty(service, actor):
    service.coordinator.operator_snapshot.return_value = dict(job=dict(State="uncertain"))
    service.reconciler.probe.return_value = {"state": "unknown"}
    with pytest.raises(SourceConflict, match="confirmed damage"):
        service.preview_rebuild(actor, str(uuid4()), reason="repair")
    assert service._previews == {}
