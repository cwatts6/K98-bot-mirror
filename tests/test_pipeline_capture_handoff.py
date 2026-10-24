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


@pytest.mark.parametrize("action", ["queue", "abandon", "after_capture"])
def test_saved_old_capture_action_cannot_queue_or_abandon_pipeline_output(monkeypatch, action):
    service, preview, _, _ = linked_capture(monkeypatch)
    service.runtime.enqueue_snapshot = Mock()
    service.dal.conclude = Mock()
    args = dict(
        queue=("source", "proof"),
        abandon=("source", "proof", "actor", "reason"),
        after_capture=("source",),
    )
    with pytest.raises(SourceConflict, match="pipeline owns"):
        getattr(service, action)(*args[action])
    service.runtime.enqueue_snapshot.assert_not_called()
    service.dal.conclude.assert_not_called()


def test_unlinked_standalone_capture_retains_existing_guided_queue(monkeypatch):
    service, preview, _, _ = linked_capture(monkeypatch)
    monkeypatch.setattr(module, "rows", lambda cursor: [])
    assert service.handoff_evidence(preview) is None


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
