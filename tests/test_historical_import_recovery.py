"""Unknown outcomes remain unknown and conflicting history never gains a repair."""

from copy import deepcopy
import hashlib
import json
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import digest
from services.historical_import_recovery_service import ACTION, HistoricalImportRecovery
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    OutputSection,
    configuration_digest,
    output_digest,
)
from services.recovery_release_policy import p0a_presentation
from tests.test_import_capture_recovery import fixture


@pytest.fixture
def history():
    capture, preview, _ = fixture()
    prep = preview["preparation"]
    generation = capture.generation(prep, preview["execution"])
    scope = json.loads(capture.runtime.configuration)["scan_data"]
    sections = (OutputSection("stats", ("value",), ((7,),)),)
    generation.update(
        capture="complete",
        config_sha256=configuration_digest(scope),
        output_sha256=output_digest(sections),
    )
    snapshot = LegacySnapshot.capture(
        consumer="scan_data",
        preparation_id=prep["PreparationID"],
        generation=generation,
        config=scope,
        provenance=dict(owner=prep["OwnerID"], fence=prep["Fence"]),
        sections=sections,
    )
    prep.update(
        State="captured",
        RequestHash=digest(json.loads(prep["RequestJson"])),
        GenerationJson=json.dumps(generation),
        SpoolKey="capture",
        SpoolHash=hashlib.sha256(snapshot.payload).digest(),
        SpoolBytes=len(snapshot.payload),
        CreatedUTC="2026-10-18",
    )
    state = dict(preparation=prep, execution=None, resources=[], streams=[], token="a" * 64)
    service = HistoricalImportRecovery(capture.outcomes, capture.runtime)
    service.dal.inspect = Mock(return_value=state)
    capture.runtime.store.read = Mock(return_value=snapshot.payload)
    return service, state


@pytest.mark.parametrize(
    "conflict",
    ["execution", "resources", "streams", "job", "generation", "typed", "malformed", "spool"],
)
def test_conflicting_history_has_specific_blocker_and_no_retire(history, conflict):
    service, state = history
    prep = state["preparation"]
    if conflict in {"execution", "resources", "streams"}:
        state[conflict] = [{"present": True}]
    elif conflict == "job":
        prep["JobID"] = str(uuid4())
    elif conflict == "generation":
        document = json.loads(prep["GenerationJson"])
        document["producer"]["completed_filename"] = "stats_" + "b" * 32 + ".ready.csv"
        prep["GenerationJson"] = json.dumps(document)
    elif conflict == "typed":
        document = json.loads(prep["RequestJson"])
        document["request"]["producer"] = dict(kind="configuration_import")
        prep["RequestJson"] = json.dumps(document)
    elif conflict == "malformed":
        prep["GenerationJson"] = "[]"
    else:
        service.runtime.store.read.side_effect = FileNotFoundError(
            "private path must not be exposed"
        )
    evidence, _, resolved = service.inspect("source")
    assert not resolved and not evidence["actions"]
    assert evidence["failure_context"]["verification_blocker"]
    assert "private path" not in json.dumps(evidence)
    assert evidence["outcome"] == "unproven"


def test_retirement_is_enabled_and_unknown_is_not_certified(history):
    service, state = history
    evidence, token, resolved = service.inspect("source")
    assert not resolved and evidence["outcome"] == "unproven"
    assert evidence["failure_context"]["original_fault"] == "not_recorded"
    assert set(
        p0a_presentation(dict(SourceKind="stats_import", State="open", evidence=evidence))[
            "evidence"
        ]["actions"]
    ) == {ACTION}
    details = service.review_details("source", ACTION, token)
    assert any(d.get("file_id") == "registered" for d in details)
    assert "stats_" in json.dumps(details)
    assert state["preparation"]["State"] == "captured"


def test_only_exact_saved_disposition_verifies(history):
    service, state = history
    action = dict(
        ActionKind=ACTION,
        EvidenceHash=state["token"],
        ActionID=str(uuid4()),
        Reason="No longer needed",
    )
    generation = json.loads(state["preparation"]["GenerationJson"])
    generation["historical_disposition"] = dict(
        token=action["EvidenceHash"],
        actor="recovery:" + action["ActionID"],
        reason=action["Reason"],
        sql_outcome="unproven",
    )
    state["preparation"].update(State="unavailable", GenerationJson=json.dumps(generation))
    assert service.reconcile("source", action) == "verified"
    evidence, _, resolved = service.inspect("source")
    assert resolved and evidence["outcome"] == "unproven" and not evidence["actions"]
    assert evidence["failure_context"]["current_blocker"] is None
    other = deepcopy(action)
    other["ActionID"] = str(uuid4())
    assert service.reconcile("source", other) == "not_applied"


def test_new_activity_cannot_replay_old_disposition(history):
    service, state = history
    state.update(token="b" * 64, streams=[dict(State="open")])
    service.execute = Mock()
    assert (
        service.reconcile(
            "source",
            dict(
                ActionKind=ACTION,
                EvidenceHash="a" * 64,
                ActionID=str(uuid4()),
                Reason="No longer needed",
            ),
        )
        == "not_applied"
    )
    service.execute.assert_not_called()


def test_changed_current_settings_invalidate_review(history):
    service, _ = history
    _, token, _ = service.inspect("source")
    service.runtime.configuration = json.dumps(
        dict(scan_data=dict(consumer="scan_data", destinations=["new_destination"]))
    )
    with pytest.raises(ValueError, match="changed"):
        service.review_details("source", ACTION, token)


def test_applied_decision_with_missing_bytes_remains_pending(history):
    service, state = history
    action = dict(
        ActionKind=ACTION,
        EvidenceHash=state["token"],
        ActionID=str(uuid4()),
        Reason="No longer needed",
    )
    generation = json.loads(state["preparation"]["GenerationJson"])
    generation["historical_disposition"] = dict(
        token=action["EvidenceHash"],
        actor="recovery:" + action["ActionID"],
        reason=action["Reason"],
        sql_outcome="unproven",
    )
    state["preparation"].update(State="unavailable", GenerationJson=json.dumps(generation))
    service.runtime.store.read.side_effect = FileNotFoundError("private")
    assert service.reconcile("source", action) is None
    assert service.inspect("source")[2] is False


def test_changed_original_request_cannot_become_historical(history):
    service, state = history
    request = json.loads(state["preparation"]["RequestJson"])
    request["request"]["producer"] = dict(kind="stats_import")
    state["preparation"]["RequestHash"] = digest(request)
    # A removed producer leaves the original typed-request hash behind.
    evidence, _, resolved = service.inspect("source")
    assert not resolved and not evidence["actions"]
    assert "original hash" in evidence["failure_context"]["verification_blocker"]
