"""Interrupted original admissions close with exact evidence before continuation."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.stats_import_outcome_dal import StatsImportOutcomeDAL
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import execute
from tests.test_producer_refusal_sql import refused as refused, setup, unblock

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


def unstarted(r, stage):
    unblock(r)
    request = json.loads(r.runtime.dal.read(r.source)["RequestJson"])["request"]
    request["operation"] = request["producer"]["operation"] = str(uuid4())
    r.source = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=request,
        storage_owner="disk",
        actor="test",
        reason="Interrupted original admission",
    )
    claim = None
    if stage != "pending":
        claim = r.runtime.dal.claim(
            r.source,
            account=r.runtime.account,
            storage_owner="disk",
            stage="preflight",
            resource_keys=("account:" + r.runtime.account,),
        )
        if stage != "preflight":
            claim = r.runtime.dal.transition(
                claim, expected="preflight", state="sql_pending", release=True
            )
            if stage != "sql_pending":
                claim = r.runtime.dal.claim(
                    r.source,
                    account=r.runtime.account,
                    storage_owner="disk",
                    stage="writing",
                    resource_keys=("sql_snapshot:legacy_outputs",),
                )
                if stage == "uncertain":
                    r.runtime.dal.uncertain(claim)
    return claim


@pytest.mark.parametrize("stage", ["pending", "preflight", "sql_pending", "writing", "uncertain"])
def test_interrupted_original_requires_close_then_separate_resume_confirmation(refused, stage):
    r = refused
    claim = unstarted(r, stage)
    adapter, store, service, row = setup(r)
    assert row["evidence"]["actions"].keys() == {"close_unstarted_admission"}
    result = execute(service, row, action="close_unstarted_admission")
    assert result["State"] == "open"
    assert store.actions[0]["State"] == "verified"
    assert result["evidence"]["actions"].keys() == {"resume_sql_stage"}
    adapter.runner.assert_not_called()
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID=?", r.source
        ).fetchval()
        == 0
    )
    if claim:
        with pytest.raises(SourceConflict):
            r.runtime.dal.authorize(claim)
    # A new confirmation is required and the runner receives only saved inputs.
    execute(service, result, action="resume_sql_stage")
    adapter.runner.assert_called_once_with(r.inputs)


def test_lost_close_reply_reconciles_original_marker(refused, monkeypatch):
    r = refused
    unstarted(r, "writing")
    _, store, service, row = setup(r)
    close = r.dal.close_admission

    def lose_reply(*args):
        close(*args)
        raise TimeoutError("Original closure committed; reply lost")

    monkeypatch.setattr(r.dal, "close_admission", lose_reply)
    result = execute(service, row, action="close_unstarted_admission")
    assert store.actions[0]["State"] == "verified"
    assert result["evidence"]["actions"].keys() == {"resume_sql_stage"}
    assert service.refresh(row["IncidentID"])["pending_action"] is None


def test_registration_race_routes_to_exact_receipt_and_never_releases(refused):
    r = refused
    claim = unstarted(r, "writing")
    adapter, store, service, row = setup(r)
    action_id, _ = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "close_unstarted_admission",
        "discord:1",
        "confirmed",
    )
    StatsImportOutcomeDAL(r.f.connect, account=r.runtime.account, storage_owner="disk").prepare(
        claim, r.inputs["completed_filename"]
    )
    result = service.refresh(row["IncidentID"])
    assert store.actions[0]["State"] == "not_applied"
    assert result["evidence"]["actions"] == {}
    assert result["evidence"]["recovery_links"] == [
        dict(label="Review original SQL stage", kind="stats_import", source_id=r.source)
    ]
    assert r.runtime.dal.read(r.source)["State"] == "writing"
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID=?", r.source
        ).fetchval()
        == 1
    )
    with pytest.raises(SourceConflict):
        adapter.execute(
            r.source,
            "close_unstarted_admission",
            row["EvidenceHash"],
            "recovery:" + action_id,
            "late callback",
        )
    adapter.runner.assert_not_called()


def test_changed_original_ownership_refuses_old_confirmation(refused):
    r = refused
    unstarted(r, "preflight")
    _, _, service, row = setup(r)
    r.f.sql.execute(
        "UPDATE #ExportResource SET OwnerID=? WHERE ActivePreparationID=?", str(uuid4()), r.source
    )
    with pytest.raises(SourceConflict, match="ownership"):
        execute(service, row, action="close_unstarted_admission")
    assert r.runtime.dal.read(r.source)["State"] == "preflight"


def test_proactive_discovery_uses_age_only_for_alerting_not_release(refused):
    r = refused
    unstarted(r, "sql_pending")
    assert r.source not in r.dal.pending()
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET CreatedUTC=DATEADD(minute,-10,SYSUTCDATETIME()),UpdatedUTC=DATEADD(minute,-3,SYSUTCDATETIME()) WHERE PreparationID=?",
        r.source,
    )
    r.f.sql.commit()
    assert r.source in r.dal.pending()
    assert r.runtime.dal.read(r.source)["State"] == "sql_pending"


def test_lost_close_intent_is_safe_to_finish_after_restart(refused):
    from kvk.dal.new_source_import_dal import UncertainCommit

    r = refused
    unstarted(r, "preflight")
    adapter, store, service, row = setup(r)
    store.lose_claim_ack = True
    with pytest.raises(UncertainCommit):
        execute(service, row, action="close_unstarted_admission")
    service.refresh(row["IncidentID"])
    result = service.refresh(row["IncidentID"])
    assert store.actions[0]["State"] == "verified"
    assert result["evidence"]["actions"].keys() == {"resume_sql_stage"}
    adapter.runner.assert_not_called()


def test_child_cannot_be_adopted_as_an_independent_original(refused):
    r = refused
    with r.dal.serialized(r.source):
        action = str(uuid4())
        child = r.dal.reserve(r.source, action)
        r.dal.close_unused(r.source, action)
    with pytest.raises(SourceConflict, match="Exact withdrawn"):
        r.dal.snapshot(child)


def test_live_original_producer_guard_prevents_cancellation(refused):
    import pyodbc

    r = refused
    unstarted(r, "writing")
    adapter, store, service, row = setup(r)
    other = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    try:
        assert (
            other.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r"
            ).fetchval()
            >= 0
        )
        with pytest.raises(SourceConflict, match="still running"):
            execute(service, row, action="close_unstarted_admission")
        assert r.runtime.dal.read(r.source)["State"] == "writing"
        assert store.actions[0]["State"] == "unknown"
        adapter.runner.assert_not_called()
    finally:
        other.execute(
            "EXEC sys.sp_releaseapplock @Resource=N'k98-legacy-output-snapshot',@LockOwner='Session'"
        )
        other.close()
    service.refresh(row["IncidentID"])
    assert service.refresh(row["IncidentID"])["pending_action"] is None
