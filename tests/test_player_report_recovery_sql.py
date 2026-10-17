"""Disposable SQL proves report atomicity, late execution exclusion and guided release."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.legacy_export_snapshot_dal import PreparationClaim
from services.player_report_recovery_service import PlayerReportRecoveryAdapter
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Temporary SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["player_report"], indirect=True),
]


def uncommitted(r):
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET State='writing',GenerationJson=NULL WHERE PreparationID=?"
        ),
        r.source,
    )
    r.owner.execute(
        r.rewrite("UPDATE dbo.ExportResource SET BlockedReason=NULL WHERE ActivePreparationID=?"),
        r.source,
    )
    preview = r.outcomes.inspect(r.source)
    prep = preview["preparation"]
    claim = PreparationClaim(
        r.source,
        "a",
        str(prep["OwnerID"]).lower(),
        prep["Fence"],
        prep["Version"],
        tuple((x["ResourceKey"], x["Version"]) for x in preview["resources"]),
    )
    return preview, claim


@pytest.mark.parametrize("commit", [True, False])
def test_output_and_checkpoint_share_the_actual_business_transaction(recovery, commit):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    _, claim = uncommitted(r)
    output = "##ReportAtomic_" + uuid4().hex
    r.owner.execute(f"CREATE TABLE {output} (Value int NOT NULL)")
    connection = r.outcomes.connect()
    try:
        cursor = connection.cursor()
        r.runtime.dal.begin_producer_transaction(claim, cursor)
        cursor.execute(f"INSERT {output} VALUES (7)")
        r.runtime.dal.transition(
            claim,
            expected="writing",
            state="committed",
            generation=generation,
            external_cursor=cursor,
        )
        (connection.commit if commit else connection.rollback)()
        cursor.close()
        preview = r.outcomes.inspect(r.source)
        assert preview["action"] == ("resume_capture" if commit else "cancel_report")
        assert r.owner.execute(f"SELECT COUNT(*) FROM {output}").fetchone()[0] == int(commit)
    finally:
        connection.close()


def test_lost_guard_does_not_release_live_business_transaction(recovery):
    from services.export_contention import CoordinationLockRefused

    r = recovery
    preview, claim = uncommitted(r)
    connection = r.outcomes.connect()
    try:
        cursor = connection.cursor()
        r.runtime.dal.begin_producer_transaction(claim, cursor)
        # Deliberately no independent guard session: actual cursor locks suffice.
        with pytest.raises(CoordinationLockRefused):
            r.outcomes.cancel(r.source, preview["token"], "admin", "close failed report")
        connection.rollback()
        cursor.close()
        assert r.outcomes.inspect(r.source)["token"] == preview["token"]
        r.outcomes.cancel(r.source, preview["token"], "admin", "close failed report")
        assert r.outcomes.inspect(r.source)["action"] == "cancelled"
    finally:
        connection.close()


def test_cancel_receipt_survives_restart_and_fences_late_producer(recovery):
    r = recovery
    preview, claim = uncommitted(r)
    action_id = str(uuid4())
    action = dict(
        ActionKind="cancel_report",
        EvidenceHash=preview["token"],
        ActionID=action_id,
        Reason="close failed report",
    )
    adapter = PlayerReportRecoveryAdapter(r.outcomes, r.service)
    adapter.execute(
        r.source, "cancel_report", preview["token"], "recovery:" + action_id, action["Reason"]
    )
    # Lose the caller acknowledgement and rebuild the adapter.
    restarted = PlayerReportRecoveryAdapter(r.outcomes, type(r.service)(r.runtime, r.outcomes))
    assert restarted.reconcile(r.source, action) == "verified"
    assert restarted.inspect(r.source)[2]
    assert not r.outcomes.inspect(r.source)["resources"]
    connection = r.outcomes.connect()
    try:
        with pytest.raises(SourceConflict):
            r.runtime.dal.begin_producer_transaction(claim, connection.cursor())
    finally:
        connection.rollback()
        connection.close()


def test_stale_confirmation_cannot_cancel_a_committed_report(recovery):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    preview, claim = uncommitted(r)
    r.runtime.dal.transition(claim, expected="writing", state="committed", generation=generation)
    with pytest.raises(SourceConflict):
        r.outcomes.cancel(r.source, preview["token"], "admin", "close")
    assert r.outcomes.inspect(r.source)["action"] == "resume_capture"


def test_autocommit_connection_cannot_enter_atomic_report_contract(recovery):
    r = recovery
    _, claim = uncommitted(r)
    connection = r.outcomes.connect()
    try:
        connection.autocommit = True
        with pytest.raises(SourceConflict, match="explicit producer transaction"):
            r.runtime.dal.begin_producer_transaction(claim, connection.cursor())
    finally:
        connection.close()


def test_report_discovered_without_misclassifying_as_stats_import(recovery):
    from services.stats_import_outcome_dal import StatsImportOutcomeDAL

    r = recovery
    uncommitted(r)
    assert r.source in r.outcomes.pending_recovery()
    imports = StatsImportOutcomeDAL(r.outcomes.connect, account="a", storage_owner="disk-a")
    assert r.source not in imports.pending_recovery()


@pytest.mark.parametrize("state", ["pending", "preflight", "sql_pending", "unavailable"])
def test_interrupted_admission_can_be_closed_with_exact_scope(recovery, state):
    r = recovery
    uncommitted(r)
    if state == "preflight":
        r.owner.execute(
            r.rewrite(
                "UPDATE dbo.ExportResource SET ResourceKey='account:a',ResourceKind='account' WHERE ActivePreparationID=?"
            ),
            r.source,
        )
    else:
        r.owner.execute(
            r.rewrite("DELETE dbo.ExportResource WHERE ActivePreparationID=?"), r.source
        )
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET State=?,OwnerID=CASE WHEN ?='pending' THEN NULL ELSE OwnerID END,Fence=CASE WHEN ?='pending' THEN 0 ELSE Fence END WHERE PreparationID=?"
        ),
        state,
        state,
        state,
        r.source,
    )
    preview = r.outcomes.inspect(r.source)
    assert preview["action"] == "cancel_report"
    r.outcomes.cancel(r.source, preview["token"], "admin", "close interrupted report")
    final = r.outcomes.inspect(r.source)
    assert final["action"] == "cancelled" and not final["resources"]
