"""Intermediate captures follow durable pipeline/job linkage, never guessed delivery."""

from contextlib import nullcontext
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import pipeline_capture_handoff_dal as module
from services.import_recovery_service import ImportRecoveryAdapter
from tests.test_import_capture_recovery import fixture


def linked_capture(monkeypatch):
    service, preview, _ = fixture()
    prep = preview["preparation"]
    generation = service.generation(prep, preview["execution"])
    prep.update(
        GenerationJson=json.dumps(generation), State="captured", ConsumerKind="scan_data", Version=4
    )
    request = json.loads(prep["RequestJson"])
    request["request"]["producer"] = dict(operation=str(uuid4()), kind="stats_import")
    prep["RequestJson"] = json.dumps(request)
    preview["captured"] = True
    run, job, target = (str(uuid4()) for _ in range(3))
    registration = json.loads(service.runtime.configuration)
    row = dict(
        RunID=run,
        RegistrationJson=service.runtime.configuration,
        Stage="import",
        SourceVersion=4,
        ExportState="observed",
        EvidenceJson=json.dumps(dict(outcome="queued", preparation_id=target, job_id=job)),
        TargetID=target,
        ConfigurationOperation=str(uuid4()),
        TargetState="materialized",
        JobID=job,
        SpoolKey="retained",
        SpoolBytes=123,
        SpoolHash=b"h" * 32,
        TargetRequest=json.dumps(dict(request=dict(config=registration["scan_data"]))),
        JobState="uncertain",
        InputHash=b"h" * 32,
        JobSpoolKey="retained",
        JobSpoolBytes=123,
        DestinationSetHash=digest(tuple(sorted(registration["scan_data"]["destinations"]))),
    )
    cursor = Mock()
    service.runtime.account = "a"
    service.runtime.dal = SimpleNamespace(connect=Mock())
    service.runtime.verified_snapshot.side_effect = lambda identifier: (
        (dict(JobID=job), None, {}) if identifier == target else (prep, None, {})
    )
    monkeypatch.setattr(module, "transaction", lambda connect: nullcontext(cursor))
    monkeypatch.setattr(module, "rows", lambda cursor: [row])
    final = dict(
        PreparationID=target,
        RequestJson=json.dumps(
            dict(request=dict(producer=dict(operation=row["ConfigurationOperation"])))
        ),
    )
    pipeline = SimpleNamespace(configuration_result=Mock(return_value=final))
    monkeypatch.setattr(module, "PipelineReceiptDAL", lambda runtime: pipeline)
    service.pipeline_receipts = pipeline
    service.pipeline_handoff = module.PipelineCaptureHandoffDAL(service.runtime)
    return service, preview, row, cursor


@pytest.mark.parametrize("state", ["ready", "running", "uncertain", "failed", "confirmed"])
def test_existing_job_replaces_duplicate_queue_action_without_claiming_delivery(monkeypatch, state):
    service, preview, row, cursor = linked_capture(monkeypatch)
    row["JobState"] = state
    before = deepcopy(preview)
    evidence, token, handoff_resolved = ImportRecoveryAdapter(service.outcomes, service).inspect(
        "source"
    )
    assert evidence["actions"] == {}
    assert evidence["outcome"] == "pipeline_export_queued"
    assert "does not confirm spreadsheet delivery" in evidence["explanation"]
    assert evidence["recovery_links"][0]["source_id"] == row["JobID"]
    assert handoff_resolved and token == preview["token"]
    assert preview == before
    assert all(call.args[0].startswith("SELECT ") for call in cursor.execute.call_args_list)


@pytest.mark.parametrize(
    "field,value",
    [
        ("SourceVersion", 5),
        ("JobID", None),
        ("JobSpoolKey", "different"),
        ("JobSpoolBytes", 124),
        ("InputHash", b"x" * 32),
        ("DestinationSetHash", b"x" * 32),
        ("RegistrationJson", "{}"),
        ("TargetState", "captured"),
        ("JobState", None),
    ],
)
def test_changed_or_incomplete_lineage_cannot_claim_queue_handoff(monkeypatch, field, value):
    service, preview, row, _ = linked_capture(monkeypatch)
    row[field] = value
    with pytest.raises(SourceConflict):
        service.handoff_evidence(preview)


def test_pending_pipeline_keeps_capture_open_without_independent_queue_actions(monkeypatch):
    service, preview, row, _ = linked_capture(monkeypatch)
    row["ExportState"] = "running"
    evidence, _, resolved = service.handoff_evidence(preview)
    assert not resolved and not evidence["actions"]
    assert evidence["outcome"] == "pipeline_export_unconfirmed"


@pytest.mark.parametrize("disposition", ["pipeline_export_v1", "configuration_only_v1", None])
def test_handoff_reuses_verified_configuration_successor(monkeypatch, disposition):
    service, preview, row, _ = linked_capture(monkeypatch)
    final = service.pipeline_receipts.configuration_result.return_value
    final["RequestJson"] = json.dumps(
        dict(request=dict(producer=dict(operation=str(uuid4()), export_disposition=disposition)))
    )
    if disposition == "pipeline_export_v1":
        evidence, _, resolved = service.handoff_evidence(preview)
        assert resolved and evidence["recovery_links"][0]["source_id"] == row["JobID"]
    else:
        with pytest.raises(SourceConflict, match="configuration-only"):
            service.handoff_evidence(preview)
    service.pipeline_receipts.configuration_result.assert_called_once_with(
        row["ConfigurationOperation"]
    )


@pytest.mark.parametrize("result", [None, "foreign", "unverified"])
def test_unverified_configuration_successor_cannot_link_existing_job(monkeypatch, result):
    service, preview, _, _ = linked_capture(monkeypatch)
    resolver = service.pipeline_receipts.configuration_result
    if result == "unverified":
        resolver.side_effect = SourceConflict("Continuation request differs")
    else:
        resolver.return_value = None if result is None else dict(PreparationID=str(uuid4()))
    with pytest.raises(SourceConflict):
        service.handoff_evidence(preview)


@pytest.mark.parametrize("action", ["queue", "abandon"])
def test_saved_old_capture_action_cannot_queue_or_abandon_pipeline_output(monkeypatch, action):
    service, preview, _, _ = linked_capture(monkeypatch)
    service.runtime.enqueue_snapshot = Mock()
    service.dal.conclude = Mock()
    args = dict(
        queue=("source", "proof"),
        abandon=("source", "proof", "actor", "reason"),
    )
    with pytest.raises(SourceConflict, match="pipeline owns"):
        getattr(service, action)(*args[action])
    service.runtime.enqueue_snapshot.assert_not_called()
    service.dal.conclude.assert_not_called()


def test_unlinked_standalone_capture_retains_existing_guided_queue(monkeypatch):
    service, preview, _, _ = linked_capture(monkeypatch)
    monkeypatch.setattr(module, "rows", lambda cursor: [])
    assert service.handoff_evidence(preview) is None


@pytest.mark.parametrize("kind", ["queue_capture", "resume_capture"])
@pytest.mark.parametrize("invalid_lineage", [False, True])
def test_durable_action_reconciliation_preserves_pipeline_capture(
    monkeypatch, kind, invalid_lineage
):
    service, preview, row, _ = linked_capture(monkeypatch)
    before = deepcopy(preview)
    service.dal.conclude = Mock()
    service.runtime.enqueue_snapshot = Mock()
    if invalid_lineage:
        row["SourceVersion"] += 1
    action = dict(ActionKind=kind, ActionID=str(uuid4()), EvidenceHash=preview["token"])
    if invalid_lineage:
        with pytest.raises(SourceConflict):
            service.reconcile_capture("source", action)
    else:
        assert service.reconcile_capture("source", action) == "not_applied"
    service.dal.conclude.assert_not_called()
    service.runtime.enqueue_snapshot.assert_not_called()
    assert preview == before


def test_pipeline_capture_completion_does_not_enqueue_intermediate_snapshot(monkeypatch):
    service, preview, _, _ = linked_capture(monkeypatch)
    service.runtime.enqueue_snapshot = Mock()
    assert service.after_capture(preview["preparation"]["PreparationID"]) is None
    service.runtime.enqueue_snapshot.assert_not_called()


@pytest.mark.parametrize("captured", [False, True])
def test_pipeline_capture_only_resume_reconciles_to_verified_without_queue(monkeypatch, captured):
    service, preview, _, _ = linked_capture(monkeypatch)
    preview["captured"] = captured
    action = dict(ActionKind="resume_capture", ActionID=str(uuid4()), EvidenceHash=preview["token"])
    actor = "recovery:" + action["ActionID"]
    generation = json.loads(preview["preparation"]["GenerationJson"])
    generation["capture_recovery"] = dict(token=preview["token"], actor=actor)
    preview["preparation"]["GenerationJson"] = json.dumps(generation)
    service.runtime.enqueue_snapshot = Mock()
    service.dal.conclude = Mock()

    def capture_only(source_id, token, actor):
        preview["captured"] = True
        return service.after_capture(source_id)

    service.run = Mock(side_effect=capture_only)
    assert service.reconcile_capture("source", action) == "verified"
    service.run.assert_called_once_with("source", preview["token"], actor)
    service.runtime.enqueue_snapshot.assert_not_called()
    service.dal.conclude.assert_not_called()


def test_runtime_wires_all_three_pipeline_producers():
    import ast
    from pathlib import Path

    tree = ast.parse((Path(__file__).parents[1] / "services/recovery_runtime.py").read_text())
    loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Tuple)
    ]
    assert any(
        [getattr(item, "id", None) for item in node.iter.elts]
        == ["adapter", "report_adapter", "config_adapter"]
        and "pipeline_handoff" in ast.unparse(node)
        for node in loops
    )
