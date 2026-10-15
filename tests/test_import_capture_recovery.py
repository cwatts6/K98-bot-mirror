"""Completion evidence is distinct from permission to discard or replay an import."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.import_capture_recovery_service import ImportCaptureRecovery
from services.import_recovery_service import ImportRecoveryAdapter
from tests.test_stats_import_outcomes import evidence


def fixture():
    prep, execution, resources = evidence("completed")
    scope = dict(consumer="scan_data", destinations=["registered"])
    prep["RequestJson"] = json.dumps(
        dict(
            consumer="scan_data",
            storage_owner="disk-a",
            request=dict(kind="scan_data", config=scope),
        )
    )
    execution.update(
        CompletedFileName="stats_" + "a" * 32 + ".ready.csv", ScanOrder=4, LastRunCounter=7
    )
    runtime = SimpleNamespace(
        configuration=json.dumps(dict(scan_data=scope)),
        store=SimpleNamespace(storage_owner="disk-a"),
    )
    outcomes = Mock()
    service = ImportCaptureRecovery(runtime, outcomes)
    preview = dict(
        preparation=prep,
        execution=execution,
        action="resume_capture",
        captured=False,
        token="proof",
    )
    outcomes.inspect.return_value = preview
    return service, preview, resources


@pytest.mark.parametrize("change", ["registration", "producer", "commit", "completion", "capture"])
def test_changed_generation_cannot_be_replaced(change):
    service, preview, _ = fixture()
    prep, execution = preview["preparation"], preview["execution"]
    generation = service.generation(prep, execution)
    key = {
        "registration": "registration_sha256",
        "producer": "producer",
        "commit": "commit_identity",
        "completion": "completion",
        "capture": "capture",
    }[change]
    generation[key] = "different"
    prep["GenerationJson"] = json.dumps(generation)
    with pytest.raises(SourceConflict):
        service.generation(prep, execution)


def test_missing_checkpoint_requires_original_registered_configuration():
    service, preview, _ = fixture()
    service.runtime.configuration = json.dumps(
        dict(scan_data=dict(consumer="scan_data", destinations=["other"]))
    )
    with pytest.raises(SourceConflict, match="registration"):
        service.generation(preview["preparation"], preview["execution"])


def test_guided_capture_action_describes_verification_and_queueing():
    service, preview, _ = fixture()
    adapter = ImportRecoveryAdapter(service.outcomes, service)
    display, _, resolved = adapter.inspect("source")
    assert not resolved
    assert set(display["actions"]) == {"resume_capture"}
    assert "import is not rerun" in display["actions"]["resume_capture"]["effect"]


def test_capture_without_queue_receipt_does_not_resolve_incident():
    service, preview, _ = fixture()
    preview.update(captured=True, action="hold")
    preview["preparation"]["GenerationJson"] = json.dumps(
        dict(capture_recovery=dict(token="proof", actor="recovery:action"))
    )
    adapter = ImportRecoveryAdapter(service.outcomes, service)
    assert adapter.inspect("source")[2] is False
    preview["preparation"]["JobID"] = "queue-receipt"
    assert adapter.inspect("source")[2] is True


def test_changed_evidence_cannot_start_an_old_capture_intent():
    service, preview, _ = fixture()
    service.run = Mock()
    preview["token"] = "changed"
    action = dict(ActionKind="resume_capture", EvidenceHash="original", ActionID="action")
    assert (
        ImportRecoveryAdapter(service.outcomes, service).reconcile("source", action)
        == "not_applied"
    )
    service.run.assert_not_called()


def test_mismatched_registration_still_produces_a_durable_incident():
    service, preview, _ = fixture()
    preview["preparation"]["RequestJson"] = "{}"
    display, _, resolved = ImportRecoveryAdapter(service.outcomes, service).inspect("source")
    assert not resolved
    assert display["actions"] == {}
    assert "does not match" in display["explanation"]
