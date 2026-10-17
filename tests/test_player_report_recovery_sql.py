"""Disposable SQL proves report atomicity, late execution exclusion and guided release."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.legacy_export_snapshot_dal import PreparationClaim
from services.player_report_recovery_service import PlayerReportRecoveryAdapter
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_recovery_sql import store as store

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
            "UPDATE dbo.ExportPreparation SET State=?,OwnerID=CASE WHEN ?='pending' THEN NULL ELSE OwnerID END,Fence=CASE WHEN ?='pending' THEN 0 ELSE Fence END,Version=1 WHERE PreparationID=?"
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


@pytest.mark.asyncio
async def test_initial_report_queue_guided_confirmation_and_restart_verification(recovery):
    from services.queue_admission_recovery import QueueAdmissionRecovery
    from services.queue_admission_recovery_dal import QueueAdmissionDAL
    from services.recovery_release_policy import p0a_presentation
    from services.recovery_service import RecoveryActor, RecoveryService
    from tests.test_guided_recovery import ACTOR, Store, execute
    from ui.views.recovery_view import RecoveryIncidentView

    r = recovery
    uncommitted(r)
    r.owner.execute(r.rewrite("DELETE dbo.ExportResource WHERE ActivePreparationID=?"), r.source)
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET State='pending',OwnerID=NULL,Fence=0,Version=1 WHERE PreparationID=?"
        ),
        r.source,
    )
    r.runtime.account = r.outcomes.account
    queue = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime))
    evidence, _, resolved = queue.inspect(r.source)
    assert not resolved and not evidence["actions"]
    link = evidence["recovery_links"][0]
    assert (link["kind"], link["source_id"]) == ("player_report", r.source)
    store = Store()
    adapter = PlayerReportRecoveryAdapter(r.outcomes, r.service)
    service = RecoveryService(
        store,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    row = service.review_source(ACTOR, link["kind"], link["source_id"])
    assert "release_notice" not in row
    assert "Close failed report & release" in [b.label for b in RecoveryIncidentView(row).children]
    for actor in (RecoveryActor(9, 2, 3), RecoveryActor(1, 9, 3), RecoveryActor(1, 2, 9)):
        with pytest.raises(SourceConflict, match="configured admin"):
            execute(service, row, actor=actor, action="cancel_report")
    assert store.actions == []
    # An acknowledgement lost after durable approval must retain the same action.
    store.lose_claim_ack = True
    with pytest.raises(Exception, match="lost intent commit"):
        execute(service, row, action="cancel_report")
    store.lose_claim_ack = False
    restarted = RecoveryService(
        store,
        {adapter.kind: PlayerReportRecoveryAdapter(r.outcomes, r.service)},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    assert restarted.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert len(store.actions) == 1 and store.actions[0]["State"] == "verified"
    # A second independent read verifies the durable domain receipt.
    assert restarted.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert len(store.actions) == 1 and store.actions[0]["State"] == "verified"
    final = r.outcomes.inspect(r.source)["preparation"]
    assert final["State"] == "unavailable" and final["Fence"] == 1 and final["Version"] == 2
    assert r.source not in queue.pending_recovery()
    # Terminal metadata alone cannot resolve the queue; a fresh runtime must
    # verify the owning report's durable closure before hiding its handoff.
    assert not queue.inspect(r.source)[2]
    restarted_queue = QueueAdmissionRecovery(QueueAdmissionDAL(r.runtime), restarted.adapters)
    queue_evidence, _, queue_resolved = restarted_queue.inspect(r.source)
    assert queue_resolved and queue_evidence["outcome"] == "domain_recovery_verified"


@pytest.mark.parametrize("lose_cancel_reply", [False, True])
def test_monitor_finishes_lost_approval_receipt_before_report_disappears(
    recovery, store, monkeypatch, lose_cancel_reply
):
    from contextlib import contextmanager

    from services import recovery_runtime as runtime
    from services.recovery_service import RecoveryService
    from tests.test_guided_recovery import ACTOR, execute

    r = recovery
    uncommitted(r)
    adapter = PlayerReportRecoveryAdapter(r.outcomes, r.service)
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, r.source)
    original_claim = store.claim

    def lose_approval(*args, **kwargs):
        original_claim(*args, **kwargs)
        raise TimeoutError("Approval committed; acknowledgement lost")

    monkeypatch.setattr(store, "claim", lose_approval)
    with pytest.raises(TimeoutError, match="Approval committed"):
        execute(service, row, action="cancel_report")
    assert r.outcomes.inspect(r.source)["action"] == "cancel_report"
    original_cancel = r.outcomes.cancel
    cancellations = []

    def cancel(*args):
        cancellations.append(1)
        original_cancel(*args)
        if lose_cancel_reply:
            raise TimeoutError("Cancellation committed; acknowledgement lost")

    monkeypatch.setattr(r.outcomes, "cancel", cancel)

    @contextmanager
    def scoped_service():
        # Reconstruct the service and adapter; durable SQL owns the intent.
        fresh = PlayerReportRecoveryAdapter(r.outcomes, r.service)
        yield RecoveryService(store, {fresh.kind: fresh}, admin_id=1, guild_id=2, channel_id=3)

    monkeypatch.setattr(runtime, "recovery_service", scoped_service)
    monkeypatch.setattr(runtime, "_retry_admission", lambda: True)
    monkeypatch.setattr(runtime, "_cursors", {})
    monkeypatch.setattr(runtime, "_incident_cursor", None)
    monkeypatch.setattr(runtime, "_priority_incident_cursor", None)
    failures = runtime.observe_recovery()
    if lose_cancel_reply:
        assert failures and store.get(row["IncidentID"])["State"] == "open"
        assert store.pending_actions(row["IncidentID"])
        # Empty end pages reset their cursors; the following pass verifies the
        # saved marker without another cancellation.
        for _ in range(2):
            failures = runtime.observe_recovery()
        assert failures == []
    else:
        assert failures == []
    assert store.get(row["IncidentID"])["State"] == "resolved"
    assert not store.pending_actions(row["IncidentID"])
    from services.recovery_backlog_dal import RecoveryBacklogDAL

    assert RecoveryBacklogDAL(store).summary()["actions"] == [
        {"State": "verified", "ActionKind": "cancel_report", "Total": 1}
    ]
    assert r.source not in adapter.pending_recovery()
    assert runtime.observe_recovery() == []
    assert cancellations == [1]
