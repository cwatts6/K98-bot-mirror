"""Health-purpose, retry and service regression tests; no provider calls."""

import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_contention import CoordinationLockRefused
from services.queue_admission_recovery_dal import QueueAdmissionDAL
from tests.test_legacy_export_snapshot import producer_runtime


def state():
    request = dict(
        consumer="config",
        kvk_no=None,
        request=dict(read_configuration=str(uuid4())),
        storage_owner="disk",
    )
    return dict(
        preparation=dict(
            PreparationID=str(uuid4()),
            AccountKey="test-account",
            StorageOwner="disk",
            ConsumerKind="config",
            KVK_NO=None,
            Actor="system:health_probe:v1",
            RequestJson=json.dumps(request),
            RequestHash=digest(request).hex(),
            State="pending",
            Version=1,
            Fence=0,
            OwnerID=None,
            GenerationJson=None,
            SpoolKey=None,
            SpoolBytes=None,
            SpoolHash=None,
            JobID=None,
        ),
        counts=dict(
            ExportPreparationResource=0,
            ExportResource=0,
            ExportExecutionStream=0,
            StatsImportExecution=0,
        ),
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("Actor", "system:configuration"),
        ("ConsumerKind", "scan_data"),
        ("KVK_NO", 1),
        ("RequestHash", "0" * 64),
    ],
)
def test_only_explicit_exact_health_identity(key, value):
    saved = state()
    assert QueueAdmissionDAL.health_probe(saved)
    saved["preparation"][key] = value
    assert not QueueAdmissionDAL.health_probe(saved)


@pytest.mark.parametrize("field", ["producer", "configuration_import", "other"])
def test_no_business_intent_can_opt_into_health_cleanup(field):
    saved = state()
    document = json.loads(saved["preparation"]["RequestJson"])
    document["request"][field] = {"kind": "configuration_import"}
    saved["preparation"].update(
        RequestJson=json.dumps(document), RequestHash=digest(document).hex()
    )
    assert not QueueAdmissionDAL.health_probe(saved)


@pytest.mark.parametrize(
    "field",
    [
        "ExportPreparationResource",
        "ExportResource",
        "ExportExecutionStream",
        "StatsImportExecution",
    ],
)
def test_any_execution_or_ownership_history_blocks_cleanup(field):
    saved = state()
    saved["counts"][field] = 1
    assert not QueueAdmissionDAL.eligible(saved)


def test_health_retry_has_time_after_first_refusal(monkeypatch):
    from tests.test_export_contention import clock, refusal

    now = clock(monkeypatch)
    connection = Mock(autocommit=False)
    dal = QueueAdmissionDAL(
        SimpleNamespace(
            dal=SimpleNamespace(connect=lambda: connection),
            account="test-account",
            store=SimpleNamespace(storage_owner="disk"),
        )
    )
    saved = state()

    def snapshot(*args):
        if snapshot.calls == 0:
            snapshot.calls += 1
            now[0] += 1.8
            raise refusal(-1)
        return saved

    snapshot.calls = 0
    monkeypatch.setattr(dal, "_snapshot", snapshot)
    write = Mock()
    monkeypatch.setattr(dal, "_withdraw", write)
    dal.withdraw_health_probe(saved["preparation"]["PreparationID"])
    connection.rollback.assert_called_once()
    assert connection.close.call_count == 2
    write.assert_called_once()


def test_health_refusal_cleanup_exhaustion_is_deferred(tmp_path, monkeypatch):
    from services.legacy_export_snapshot_service import ConfigurationAdmissionDeferred

    runtime, dal = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-a"]}}
    )
    dal.claim.return_value = None
    error = CoordinationLockRefused(
        result=-1, session=1, transaction_state=1, transaction_count=1, resource_hash="a" * 64
    )
    error.transaction_released = True
    cleanup = Mock(side_effect=error)
    monkeypatch.setattr(QueueAdmissionDAL, "withdraw_health_probe", cleanup)
    with pytest.raises(ConfigurationAdmissionDeferred, match="cleanup"):
        with runtime.configuration_requests(health_probe=True):
            pytest.fail("No provider entry after refusal")
    assert dal.request.call_args.kwargs["actor"] == "system:health_probe:v1"
    cleanup.assert_called_once_with(dal.request.return_value)
    dal.withdraw_unstarted.assert_not_called()
    dal.uncertain.assert_not_called()


def test_health_claim_success_never_cancels_or_replays(tmp_path, monkeypatch):
    runtime, dal = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-a"]}}
    )
    cleanup = Mock()
    monkeypatch.setattr(QueueAdmissionDAL, "withdraw_health_probe", cleanup)
    entered = []
    with runtime.configuration_requests(health_probe=True):
        entered.append(True)
    assert entered == [True]
    dal.claim.assert_called_once()
    dal.transition.assert_called_once()
    cleanup.assert_not_called()


@pytest.mark.parametrize("options", [dict(publication_intent=True), dict(wait_for_admission=True)])
def test_health_cannot_publish_or_wait(tmp_path, options):
    runtime, dal = producer_runtime(tmp_path)
    with pytest.raises(ValueError):
        with runtime.configuration_requests(health_probe=True, **options):
            pytest.fail("invalid purpose")
    dal.request.assert_not_called()


def test_recovery_can_win_before_health_claim_without_false_failure(tmp_path, monkeypatch):
    from services.legacy_export_snapshot_service import ConfigurationAdmissionDeferred

    runtime, dal = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-a"]}}
    )
    dal.claim.side_effect = SourceConflict("ticket fenced")
    monkeypatch.setattr(QueueAdmissionDAL, "snapshot", Mock(return_value={}))
    monkeypatch.setattr(QueueAdmissionDAL, "health_withdrawn", Mock(return_value=True))
    with pytest.raises(ConfigurationAdmissionDeferred, match="safely withdrawn"):
        with runtime.configuration_requests(health_probe=True):
            pytest.fail("late caller must never enter")
    dal.uncertain.assert_not_called()
