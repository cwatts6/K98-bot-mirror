"""Refused-stage recovery against disposable session-local SQL objects."""

import json
import os
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.producer_recovery_intent import current_intent, stats_inputs, stats_intent
from services.producer_refusal_dal import ProducerRefusalDAL
from services.producer_refusal_recovery import ProducerRefusalRecovery, unused
from services.recovery_service import RecoveryService
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import Store, execute

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def refused(request, monkeypatch):
    from tests import test_export_target_containment_sql as fixture

    monkeypatch.setattr(fixture, "TABLES", (*fixture.TABLES, "dbo.StatsImportExecution"))
    f = request.getfixturevalue("contained_job")
    legacy = LegacySnapshotDAL(f.connect)
    scope = dict(consumer="scan_data", outputs=["retained-output"])
    runtime = SimpleNamespace(
        dal=legacy,
        account="test-account",
        store=SimpleNamespace(storage_owner="disk"),
        configuration=json.dumps(dict(scan_data=scope)),
    )
    inputs = stats_inputs(
        "A",
        2,
        "stats_" + uuid4().hex + ".ready.csv",
        600,
        {"source_type": "excel", "source_filename": "scan.xlsx"},
    )
    with stats_intent(inputs) as intent:
        source = legacy.request(
            account=runtime.account,
            consumer="scan_data",
            kvk_no=None,
            request=dict(
                operation=intent["operation"], kind="scan_data", config=scope, producer=intent
            ),
            storage_owner="disk",
            actor="test",
            reason="Refused before execution",
        )
    legacy.withdraw_unstarted(source)
    return SimpleNamespace(
        f=f, runtime=runtime, dal=ProducerRefusalDAL(runtime), source=source, inputs=inputs
    )


def unblock(r):
    # Fixture-only removal of a synthetic blocker. Production recovery never does this.
    r.f.sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=NULL,OwnerID=NULL,BlockedReason=NULL,Version=Version+1 WHERE ResourceKey='account:test-account'"
    )


def setup(r, runner=None):
    imports = Mock()
    imports.inspect.return_value = (
        dict(outcome="prepared", explanation="Exact receipt needs review", actions={}),
        "f" * 64,
        False,
    )
    adapter = ProducerRefusalRecovery(r.dal, imports, runner or Mock())
    store = Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    evidence, token, resolved = adapter.inspect(r.source)
    row = store.observe(adapter.kind, r.source, evidence, token, resolved=resolved)
    return adapter, store, service, row


def test_refused_stage_is_discovered_with_exact_blocker_and_no_release(refused):
    r = refused
    adapter, _, _, _ = setup(r)
    assert adapter.pending_recovery() == [r.source]
    evidence, _, resolved = adapter.inspect(r.source)
    assert not resolved and evidence["actions"] == {}
    assert evidence["recovery_links"] == [
        dict(label="Review blocking export", kind="export_job", source_id=r.f.job)
    ]
    assert (
        r.f.sql.execute(
            "SELECT ActiveJobID FROM #ExportResource WHERE ResourceKey='account:test-account'"
        )
        .fetchval()
        .lower()
        == r.f.job
    )
    unblock(r)
    assert "resume_sql_stage" in adapter.inspect(r.source)[0]["actions"]


@pytest.mark.asyncio
async def test_report_blocker_button_opens_guided_report_release(refused, monkeypatch):
    from unittest.mock import AsyncMock

    from services.player_report_recovery_dal import PlayerReportRecoveryDAL
    from services.player_report_recovery_service import (
        PlayerReportCaptureRecovery,
        PlayerReportRecoveryAdapter,
    )
    from tests.test_guided_recovery import ACTOR
    from ui.views import recovery_view as view

    r = refused
    unblock(r)
    # This case replaces the fixture's synthetic provider blocker with a report.
    r.f.sql.execute("DELETE #ExportExecutionStream")
    r.f.sql.commit()
    operation = str(uuid4())
    scope = json.loads(r.runtime.configuration)["scan_data"]
    report = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=dict(
            operation=operation,
            kind="scan_data",
            config=scope,
            producer=dict(kind="player_stats_report", operation=operation, atomic_checkpoint=1),
        ),
        storage_owner="disk",
        actor="test",
        reason="interrupted report",
    )
    r.runtime.dal.claim(
        report,
        account=r.runtime.account,
        storage_owner="disk",
        stage="preflight",
        resource_keys=("account:" + r.runtime.account,),
    )
    adapter, _, _, _ = setup(r)
    evidence, _, _ = adapter.inspect(r.source)
    assert evidence["recovery_links"] == [
        dict(label="Review blocking stage", kind="player_report", source_id=report)
    ]
    outcomes = PlayerReportRecoveryDAL(r.f.connect, account=r.runtime.account, storage_owner="disk")
    report_adapter = PlayerReportRecoveryAdapter(
        outcomes, PlayerReportCaptureRecovery(r.runtime, outcomes)
    )
    service = RecoveryService(
        Store(), {"player_report": report_adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    report_row = service.review_source(ACTOR, "player_report", report)
    assert "cancel_report" in report_row["evidence"]["actions"]
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=report_row))
    row = dict(report_row, evidence=evidence)
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Review blocking stage"
    )
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review_source", ACTOR, "player_report", report)
    assert interaction.followup.send.call_args.kwargs["ephemeral"]
    closed = execute(service, report_row, action="cancel_report")
    assert closed["State"] == "resolved"
    assert "resume_sql_stage" in adapter.inspect(r.source)[0]["actions"]


def test_lost_intent_reply_leaves_tombstone_and_late_callback_cannot_execute(refused):
    r = refused
    unblock(r)
    adapter, store, service, row = setup(r)
    store.lose_claim_ack = True
    from kvk.dal.new_source_import_dal import UncertainCommit

    with pytest.raises(UncertainCommit):
        execute(service, row, action="resume_sql_stage")
    restarted = RecoveryService(
        store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    refreshed = restarted.refresh(row["IncidentID"])
    assert store.actions[0]["State"] == "not_applied"
    child = r.dal.snapshot(r.source)["attempts"][0]
    assert unused(child)
    assert refreshed["evidence"]["actions"].keys() == {"resume_sql_stage"}
    with pytest.raises(SourceConflict, match="evidence changed"):
        adapter.execute(
            r.source,
            "resume_sql_stage",
            row["EvidenceHash"],
            "recovery:" + store.actions[0]["ActionID"],
            "late callback",
        )
    adapter.runner.assert_not_called()


@pytest.mark.parametrize("stage", ["pending", "preflight", "sql_pending", "writing", "uncertain"])
def test_restart_before_execution_fences_only_exact_child(refused, stage):
    r = refused
    unblock(r)
    adapter, store, _, row = setup(r)
    action_id, _ = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "resume_sql_stage",
        "discord:1",
        "confirmed",
    )
    with r.dal.serialized(r.source):
        child = r.dal.reserve(r.source, action_id)
        if stage != "pending":
            claim = r.runtime.dal.claim(
                child,
                account=r.runtime.account,
                storage_owner="disk",
                stage="preflight",
                resource_keys=("account:" + r.runtime.account,),
            )
            assert claim
            if stage != "preflight":
                claim = r.runtime.dal.transition(
                    claim, expected="preflight", state="sql_pending", release=True
                )
                if stage != "sql_pending":
                    claim = r.runtime.dal.claim(
                        child,
                        account=r.runtime.account,
                        storage_owner="disk",
                        stage="writing",
                        resource_keys=("sql_snapshot:legacy_outputs",),
                    )
                    assert claim
                    if stage == "uncertain":
                        r.runtime.dal.uncertain(claim)
    assert adapter.reconcile(r.source, store.actions[0]) == "not_applied"
    assert unused(r.dal.snapshot(r.source)["attempts"][0])
    if stage in {"writing", "uncertain"}:
        with pytest.raises(SourceConflict):
            r.runtime.dal.authorize(claim)
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID=?", child
        ).fetchval()
        == 0
    )
    adapter.runner.assert_not_called()


def test_resume_uses_exact_inputs_and_registered_receipt_never_replays(refused):
    r = refused
    unblock(r)
    calls = []

    def runner(inputs):
        from services.stats_import_outcome_dal import StatsImportOutcomeDAL

        calls.append(inputs)
        intent = current_intent()
        child = r.dal.reserve(r.source, intent["operation"])
        claim = r.runtime.dal.claim(
            child,
            account=r.runtime.account,
            storage_owner="disk",
            stage="preflight",
            resource_keys=("account:" + r.runtime.account,),
        )
        r.runtime.dal.transition(claim, expected="preflight", state="sql_pending", release=True)
        claim = r.runtime.dal.claim(
            child,
            account=r.runtime.account,
            storage_owner="disk",
            stage="writing",
            resource_keys=("sql_snapshot:legacy_outputs",),
        )
        StatsImportOutcomeDAL(r.f.connect, account=r.runtime.account, storage_owner="disk").prepare(
            claim, inputs["completed_filename"]
        )
        raise TimeoutError("lost reply after registration")

    adapter, store, service, row = setup(r, runner)
    result = execute(service, row, action="resume_sql_stage")
    assert calls == [r.inputs]
    assert result["State"] == "open"
    assert result["evidence"]["actions"] == {}
    assert result["evidence"]["recovery_links"][0]["kind"] == "stats_import"
    assert store.actions[0]["State"] == "verified"
    service.refresh(row["IncidentID"])
    assert calls == [r.inputs]
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID IS NOT NULL"
        ).fetchval()
        == 1
    )
    adapter.imports.inspect.return_value = (
        dict(outcome="completed", explanation="Captured and queued", actions={}),
        "e" * 64,
        True,
    )
    assert service.refresh(row["IncidentID"])["State"] == "resolved"


def test_changed_registration_and_wrong_actor_cannot_resume(refused):
    r = refused
    unblock(r)
    adapter, _, service, row = setup(r)
    from services.recovery_service import RecoveryActor

    with pytest.raises(SourceConflict, match="configured admin"):
        execute(service, row, RecoveryActor(9, 2, 3), action="resume_sql_stage")
    r.runtime.configuration = json.dumps(
        dict(scan_data=dict(consumer="scan_data", outputs=["changed"]))
    )
    assert set(adapter.inspect(r.source)[0]["actions"]) == {"resume_current_registration"}
    with pytest.raises(SourceConflict, match=r"evidence changed|not permitted"):
        execute(service, row, action="resume_sql_stage")
    adapter.runner.assert_not_called()


def test_mutated_request_fails_closed_without_writes(refused):
    r = refused
    r.f.sql.execute(
        "UPDATE #ExportPreparation SET RequestJson=JSON_MODIFY(RequestJson,'$.request.producer.inputs.seed',9) WHERE PreparationID=?",
        r.source,
    )
    with pytest.raises(SourceConflict, match="Exact withdrawn"):
        r.dal.snapshot(r.source)


def test_release_requires_live_dispatcher_exclusion(refused):
    with pytest.raises(SourceConflict, match="dispatcher exclusion"):
        refused.dal.close_unused(refused.source, str(uuid4()))


def test_discovery_wraps_after_last_seen_id(refused):
    assert refused.dal.pending(refused.source) == [refused.source]


@pytest.mark.parametrize("guard", ["dispatcher", "producer"])
def test_live_external_guard_prevents_recovery_without_changing_attempt(refused, guard):
    import pyodbc

    from services.stats_import_outcome_dal import ImportExecutionActive

    r = refused
    unblock(r)
    adapter, store, _, row = setup(r)
    action_id, _ = store.claim(
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "resume_sql_stage",
        "discord:1",
        "confirmed",
    )
    with r.dal.serialized(r.source):
        child = r.dal.reserve(r.source, action_id)
    other = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\K98DEV;DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    resource = (
        "k98-producer-recovery:" + r.source
        if guard == "dispatcher"
        else "k98-legacy-output-snapshot"
    )
    try:
        assert (
            other.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r",
                resource,
            ).fetchval()
            >= 0
        )
        with pytest.raises(ImportExecutionActive if guard == "dispatcher" else SourceConflict):
            adapter.reconcile(r.source, store.actions[0])
        assert r.runtime.dal.read(child)["State"] == "pending"
        adapter.runner.assert_not_called()
    finally:
        other.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", resource)
        other.close()


def test_context_is_retained_in_drained_worker_thread():
    import asyncio

    inputs = stats_inputs("A", None, "stats_" + uuid4().hex + ".ready.csv", 600, {})
    action, source = str(uuid4()), str(uuid4())

    async def offload():
        return await asyncio.to_thread(current_intent)

    with stats_intent(inputs, action_id=action, parent=source):
        assert asyncio.run(offload()) == dict(
            kind="stats_import", inputs=inputs, operation=action, parent=source
        )
    assert current_intent() is None
