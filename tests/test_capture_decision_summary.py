"""Short decisions retain original identity and the existing evidence boundary."""

from datetime import datetime
import json
from unittest.mock import Mock

import pytest

from services.capture_recovery_context import capture_context, capture_summary
from services.import_recovery_service import ImportRecoveryAdapter
from services.recovery_service import SourceConflict
from tests.test_import_capture_recovery import fixture


def setup():
    recovery, preview, _ = fixture()
    prep = preview["preparation"]
    prep["CreatedUTC"] = datetime(2026, 10, 18, 14, 30)
    generation = recovery.generation(prep, preview["execution"])
    generation["producer"] = {"procedure": "dbo.UPDATE_ALL2", "phases": []}
    prep["GenerationJson"] = json.dumps(generation)
    adapter = Mock(capture_recovery=recovery, dal=recovery.outcomes)
    adapter.inspect.return_value = (
        {
            "actions": {
                "queue_capture": {"check": "Queue this output?", "effect": "Verify and queue once."}
            }
        },
        "proof",
        False,
    )
    return recovery, preview, adapter


def test_summary_identifies_work_and_distinguishes_capture_from_failure():
    recovery, preview, adapter = setup()
    fields = capture_summary(adapter, "source", "queue_capture", "proof")
    text = "\n".join(f["text"] for f in fields)
    assert len(fields) == 5
    assert "2026-10-18 14:30:00" in text and "dbo.UPDATE_ALL2" in text
    assert preview["execution"]["CompletedFileName"] in text
    assert "settings match" in text and "does not establish" in text
    assert "If you cannot identify" in text
    assert all(len(f["text"]) < 1024 for f in fields)
    adapter.execute.assert_not_called()


@pytest.mark.parametrize("change", ["token", "resolved", "action", "inspection"])
def test_summary_rejects_stale_or_unavailable_decisions(change):
    _, preview, adapter = setup()
    if change == "token":
        preview["token"] = "changed"
    else:
        evidence, token, resolved = adapter.inspect.return_value
        if change == "resolved":
            resolved = True
        if change == "action":
            evidence["actions"] = {}
        if change == "inspection":
            token = "changed"
        adapter.inspect.return_value = evidence, token, resolved
    with pytest.raises(SourceConflict):
        capture_summary(adapter, "source", "queue_capture", "proof")


def test_context_exposes_only_bounded_recorded_identity_and_configuration_fingerprints():
    recovery, preview, _ = setup()
    prep = preview["preparation"]
    recovery.runtime.configuration = json.dumps(
        {"scan_data": {"consumer": "scan_data", "destinations": ["new-target", "second-target"]}}
    )
    context = capture_context(prep, preview["execution"], recovery)
    assert not context["registration_matches"]
    assert context["original_destination_count"] == 1 and context["current_destination_count"] == 2
    assert len(context["original_configuration_sha256"]) == 64
    assert context["original_configuration_sha256"] != context["current_configuration_sha256"]
    assert "new-target" not in json.dumps(context)
    prep["GenerationJson"] = json.dumps({"producer": {"procedure": "secret=do-not-display"}})
    preview["execution"]["CompletedFileName"] = "C:/private/original.csv"
    context = capture_context(prep, preview["execution"], recovery)
    assert context["input_file"] is None and context["producer_procedure"] is None
    assert "do-not-display" not in json.dumps(context)


def test_adapter_routes_capture_summary_without_historical_retirement():
    recovery, preview, _ = fixture()
    adapter = ImportRecoveryAdapter(recovery.outcomes, recovery)
    fields = adapter.review_summary("source", "resume_capture", preview["token"])
    assert len(fields) == 5
    evidence, _, _ = adapter.inspect("source")
    assert evidence["actions"]["resume_capture"]["review_summary"] is True
