"""Guided all-KVK recovery uses atomic completion evidence and never replays SQL."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.all_kvk_capture_recovery_dal import AllKvkCaptureRecoveryDAL
from services.all_kvk_capture_recovery_service import (
    AllKvkCaptureRecovery,
    AllKvkCaptureRecoveryAdapter,
)
from services.legacy_export_snapshot_service import configuration_digest
from tests.test_import_capture_recovery import fixture as stats_fixture


def fixture():
    original, preview, resources = stats_fixture()
    prep = preview["preparation"]
    scope = dict(consumer="all_kvk", kvk_no=7, destinations=["registered"])
    prep.update(
        ConsumerKind="all_kvk",
        KVK_NO=7,
        State="committed",
        RequestJson=json.dumps(
            dict(
                consumer="all_kvk",
                kvk_no=7,
                storage_owner="disk-a",
                request=dict(kind="all_kvk", config=scope),
            )
        ),
        GenerationJson=json.dumps(
            dict(
                completion="committed",
                commit_identity=prep["PreparationID"],
                capture="pending",
                registration_sha256=configuration_digest(scope),
                producer=dict(procedure="KVK recompute", kvk_no=7),
            )
        ),
    )
    preview.update(execution=None, explanation=None)
    runtime = SimpleNamespace(
        configuration=json.dumps(dict(all_kvk=scope)),
        store=original.runtime.store,
        enqueue_snapshot=Mock(),
        verified_snapshot=Mock(return_value=(prep, None, {})),
    )
    service = AllKvkCaptureRecovery(runtime, original.outcomes)
    return service, preview, resources


@pytest.mark.parametrize("procedure", ["KVK recompute", "KVK ingest and recompute"])
def test_both_atomic_producer_checkpoints_offer_guided_capture(procedure):
    service, preview, _ = fixture()
    prep = preview["preparation"]
    generation = json.loads(prep["GenerationJson"])
    if procedure == "KVK ingest and recompute":
        generation["producer"] = dict(
            procedure=procedure,
            kvk_no=7,
            scan_id=4,
            file_sha256="a" * 64,
        )
    prep["GenerationJson"] = json.dumps(generation)
    adapter = AllKvkCaptureRecoveryAdapter(service.outcomes, service)
    evidence, _, resolved = adapter.inspect(prep["PreparationID"])
    assert not resolved
    assert set(evidence["actions"]) == {"resume_capture", "abandon_capture"}
    assert "not rerun" in evidence["actions"]["resume_capture"]["effect"]
    service.runtime.enqueue_snapshot.assert_not_called()


@pytest.mark.parametrize(
    "key,value",
    [
        ("completion", "unknown"),
        ("commit_identity", "foreign"),
        ("registration_sha256", "changed"),
        ("producer", {}),
        ("capture", "unknown"),
    ],
)
def test_invalid_checkpoint_is_preserved_and_never_offers_capture(key, value):
    service, preview, _ = fixture()
    prep = preview["preparation"]
    generation = json.loads(prep["GenerationJson"])
    generation[key] = value
    prep["GenerationJson"] = json.dumps(generation)
    evidence, _, resolved = AllKvkCaptureRecoveryAdapter(service.outcomes, service).inspect("id")
    assert not resolved and not evidence["actions"]
    service.runtime.enqueue_snapshot.assert_not_called()


@pytest.mark.parametrize(
    "change", ["account", "storage", "consumer", "owner", "fence", "job", "operation", "resource"]
)
def test_foreign_scope_or_changed_owner_cannot_be_adopted(change):
    _, preview, resources = fixture()
    prep = preview["preparation"]
    dal = AllKvkCaptureRecoveryDAL(Mock(), account="a", storage_owner="disk-a")
    if change in {"account", "storage", "consumer"}:
        prep[
            {"account": "AccountKey", "storage": "StorageOwner", "consumer": "ConsumerKind"}[change]
        ] = "other"
        with pytest.raises(SourceConflict):
            dal._scope(prep)
    else:
        resources[0][
            {
                "owner": "OwnerID",
                "fence": "Fence",
                "job": "ActiveJobID",
                "operation": "ActiveOutputOperationID",
                "resource": "ResourceKey",
            }[change]
        ] = (
            999 if change == "fence" else "11111111-1111-1111-1111-111111111111"
        )
        with pytest.raises(SourceConflict):
            dal.action(prep, None, resources)


def test_captured_queue_gap_requires_confirmation_and_inspection_is_read_only():
    service, preview, _ = fixture()
    preview.update(action="queue_capture", captured=True, explanation=None)
    adapter = AllKvkCaptureRecoveryAdapter(service.outcomes, service)
    evidence, token, resolved = adapter.inspect("source")
    assert not resolved and set(evidence["actions"]) == {"queue_capture", "abandon_capture"}
    service.runtime.enqueue_snapshot.assert_not_called()
    adapter.execute("source", "queue_capture", token, "admin", "continue")
    service.runtime.enqueue_snapshot.assert_called_once_with("source")


def test_already_queued_inspection_only_verifies_retained_bytes():
    service, preview, _ = fixture()
    preview.update(action="resolved", captured=True, explanation=None)
    preview["preparation"].update(State="materialized", JobID="job")
    assert AllKvkCaptureRecoveryAdapter(service.outcomes, service).inspect("source")[2]
    service.runtime.verified_snapshot.assert_called_once_with("source")
    service.runtime.enqueue_snapshot.assert_not_called()


def test_stale_queue_confirmation_cannot_enqueue():
    service, preview, _ = fixture()
    preview.update(action="queue_capture", captured=True, explanation=None)
    with pytest.raises(SourceConflict, match="changed"):
        service.queue("source", "stale")
    service.runtime.enqueue_snapshot.assert_not_called()


def test_changed_pending_queue_intent_is_retired_without_dispatch():
    service, preview, _ = fixture()
    preview.update(action="queue_capture", captured=True, explanation=None)
    action = dict(ActionKind="queue_capture", EvidenceHash="stale", ActionID="id")
    assert (
        AllKvkCaptureRecoveryAdapter(service.outcomes, service).reconcile("source", action)
        == "not_applied"
    )
    service.runtime.enqueue_snapshot.assert_not_called()
