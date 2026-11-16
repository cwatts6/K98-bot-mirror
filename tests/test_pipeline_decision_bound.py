"""Production-sized retained decisions, without importing or delivering anything."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, canonical, digest
from services.processing_pipeline_receipt_dal import pipeline_json
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_processing_pipeline_recovery_sql import pipeline as pipeline


@pytest.mark.parametrize("character", ["x", "\u00e9", "\U0001f680"])
def test_pipeline_bound_matches_serialized_sql_bytes(character):
    value = {"padding": character}
    remaining = 32768 // 2 - len(canonical(value))
    value["padding"] += "x" * remaining
    assert len(pipeline_json(value).encode("utf-16-le")) == 32768
    value["padding"] += "x"
    with pytest.raises(SourceConflict, match="32768-byte"):
        pipeline_json(value)


def test_pipeline_rejects_nonfinite_json():
    with pytest.raises(ValueError):
        pipeline_json({"invalid": float("nan")})


SQL = pytest.mark.skipif(os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local SQL opt-in")


def seed_large_history(r, *, stage="configuration", history_bytes=20010):
    registration = json.loads(r.runtime.configuration)
    registration["scan_data"]["synthetic_review_settings"] = ""
    registration["scan_data"]["synthetic_review_settings"] = "x" * (
        19298 // 2 - len(canonical(registration))
    )
    assert len(canonical(registration).encode("utf-16-le")) == 19298
    r.runtime.configuration = canonical(registration)
    r.owner.execute(
        r.rewrite("UPDATE dbo.ProcessingPipelineRun SET RegistrationJson=? WHERE RunID=?"),
        r.runtime.configuration,
        r.run_id,
    )
    history = [
        dict(
            action=str(uuid4()),
            token="a" * 64,
            reason="",
            choice="continue_stage",
            registration=registration,
            previous_operation=str(uuid4()),
            previous_state="not_started",
            previous_evidence=None,
        )
    ]
    history[0]["reason"] = "x" * (history_bytes // 2 - len(canonical(history)))
    assert len(canonical(history).encode("utf-16-le")) == history_bytes
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ProcessingPipelineStage SET State='unconfirmed',EvidenceJson=?,"
            "DecisionJson=? WHERE RunID=? AND Stage=?"
        ),
        canonical(dict(outcome="unconfirmed")),
        canonical(history),
        r.run_id,
        stage,
    )
    return history


@SQL
@pytest.mark.parametrize("recovery", ["scan_data"], indirect=True)
def test_full_prior_snapshot_then_disposition_preserves_receipts_and_reconciles(
    pipeline, monkeypatch
):
    from services.processing_pipeline_recovery import ProcessingPipelineRecovery

    r = pipeline
    history = seed_large_history(r)
    for stage in ("import", "player_cache", "name_cache", "maintenance"):
        operation = r.dal.start(r.run_id, stage)
        r.dal.observe(r.run_id, stage, operation, dict(outcome="fixture_verified"), verified=True)
    before = r.dal.snapshot(r.run_id)
    independent = r.owner.execute(r.rewrite("SELECT * FROM dbo.StatsImportExecution")).fetchall()

    def forbidden(*_):
        pytest.fail("Disposition must never dispatch a business stage")

    monkeypatch.setattr(r.adapter, "runner", forbidden)
    for selected in ("configuration", "target_cache", "export"):
        shown, token, complete = r.adapter.inspect(r.run_id)
        assert shown["selected_stage"] == selected and not complete
        action = str(uuid4())
        r.adapter.execute(r.run_id, "retain_stage", token, "recovery:" + action, "Keep unfinished")
        stage = r.dal.snapshot(r.run_id)["stages"][selected]
        entries = json.loads(stage["DecisionJson"])
        if selected == "configuration":
            assert entries[:-1] == history
            assert len(stage["DecisionJson"].encode("utf-16-le")) < 22000
        assert "registration" not in entries[-1]
        assert (
            entries[-1]["registration_sha256"] == digest(json.loads(r.runtime.configuration)).hex()
        )
        assert stage["State"] == "skipped"
        assert stage["OperationID"] == before["stages"][selected]["OperationID"]
        with pytest.raises(SourceConflict, match="already has an intent"):
            r.dal.start(r.run_id, selected, action_id=action)
        restarted = ProcessingPipelineRecovery(r.dal)
        assert (
            restarted.reconcile(
                r.run_id, dict(ActionID=action, EvidenceHash=token, ActionKind="retain_stage")
            )
            == "verified"
        )
    after = r.dal.snapshot(r.run_id)
    for stage in ("import", "player_cache", "name_cache", "maintenance"):
        assert after["stages"][stage] == before["stages"][stage]
    assert (
        r.owner.execute(r.rewrite("SELECT * FROM dbo.StatsImportExecution")).fetchall()
        == independent
    )
    assert after["run"] == before["run"]
    assert r.adapter.inspect(r.run_id)[2] is True


@SQL
@pytest.mark.parametrize("recovery", ["scan_data"], indirect=True)
def test_receipt_verification_uses_fingerprint_and_preserves_prior_history(pipeline):
    from tests.test_processing_pipeline_recovery_sql import link_import

    r = pipeline
    history = seed_large_history(r, stage="import")
    link_import(r)
    shown, token, complete = r.adapter.inspect(r.run_id)
    assert "verify_stage" in shown["actions"] and not complete
    r.adapter.execute(r.run_id, "verify_stage", token, "recovery:" + str(uuid4()), "Verify receipt")
    stage = r.dal.snapshot(r.run_id)["stages"]["import"]
    entries = json.loads(stage["DecisionJson"])
    assert entries[:-1] == history
    assert "registration" not in entries[-1]
    assert stage["State"] == "observed"


@SQL
@pytest.mark.parametrize("recovery", ["scan_data"], indirect=True)
@pytest.mark.parametrize("choice", ["retain_stage", "continue_stage"])
def test_exhausted_history_is_rejected_before_sql_update_without_truncation(pipeline, choice):
    r = pipeline
    seed_large_history(r, stage="name_cache", history_bytes=32768)
    for stage in ("import", "player_cache"):
        operation = r.dal.start(r.run_id, stage)
        r.dal.observe(r.run_id, stage, operation, dict(outcome="fixture_verified"), verified=True)
    _, token, _ = r.adapter.inspect(r.run_id)
    before = r.dal.snapshot(r.run_id)
    with pytest.raises(SourceConflict, match="32768-byte"):
        r.adapter.execute(r.run_id, choice, token, "recovery:" + str(uuid4()), "Keep evidence")
    assert r.dal.snapshot(r.run_id) == before
