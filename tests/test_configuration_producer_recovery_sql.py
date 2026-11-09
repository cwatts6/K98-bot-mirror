"""Atomic configuration outcomes and guided actions on disposable SQL tables."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.configuration_producer_recovery import ConfigurationProducerRecovery
from services.recovery_service import RecoveryService
from tests.test_guided_recovery import ACTOR, Store
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_player_report_recovery_sql import uncommitted

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Temporary SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_producer"], indirect=True),
]


def service(r):
    adapter = ConfigurationProducerRecovery(r.outcomes, r.service)
    return RecoveryService(Store(), {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)


def test_recovered_configuration_only_capture_never_queues_export(recovery):
    from kvk.dal.new_source_import_dal import digest

    r = recovery
    request = json.loads(r.outcomes.inspect(r.source)["preparation"]["RequestJson"])
    request["request"]["producer"]["export_disposition"] = "configuration_only_v1"
    r.owner.execute(
        r.rewrite(
            "UPDATE dbo.ExportPreparation SET RequestJson=?,RequestHash=? WHERE PreparationID=?"
        ),
        json.dumps(request),
        digest(request),
        r.source,
    )
    adapter = ConfigurationProducerRecovery(r.outcomes, r.service)
    evidence, token, _ = adapter.inspect(r.source)
    assert "resume_capture" in evidence["actions"]
    adapter.execute(r.source, "resume_capture", token, "recovery:" + str(uuid4()), "Capture only")
    preview = r.outcomes.inspect(r.source)
    assert preview["captured"] and not preview["preparation"]["JobID"]
    assert r.service.verify_queued(r.source)
    with pytest.raises(SourceConflict):
        r.service.queue(r.source, preview["token"])


@pytest.mark.parametrize("commit", [True, False])
def test_configuration_output_and_checkpoint_are_one_transaction(recovery, commit):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    _, claim = uncommitted(r)
    table = "##ConfigAtomic_" + uuid4().hex
    r.owner.execute(f"CREATE TABLE {table} (Value int NOT NULL)")
    conn = r.outcomes.connect()
    try:
        cursor = conn.cursor()
        r.runtime.dal.begin_producer_transaction(claim, cursor)
        cursor.execute(f"INSERT {table} VALUES (7)")
        r.runtime.dal.transition(
            claim,
            expected="writing",
            state="committed",
            generation=generation,
            external_cursor=cursor,
        )
        (conn.commit if commit else conn.rollback)()
        preview = r.outcomes.inspect(r.source)
        assert preview["action"] == ("resume_capture" if commit else "cancel_configuration")
        assert r.owner.execute(f"SELECT COUNT(*) FROM {table}").fetchval() == int(commit)
    finally:
        conn.close()


@pytest.mark.parametrize("committed", [True, False])
@pytest.mark.asyncio
async def test_alert_to_actual_confirmation_and_verified_repair(recovery, monkeypatch, committed):
    from ui.views import recovery_summary_view as summary_view, recovery_view as view

    r = recovery
    if not committed:
        _, claim = uncommitted(r)
    current = service(r)
    # Independent discovery finds the failed producer before another process fails.
    assert r.source in r.outcomes.pending_recovery()
    row = current.review_source(ACTOR, "configuration_producer", r.source)
    action = "resume_capture" if committed else "cancel_configuration"

    async def call(method, *args):
        return getattr(current, method)(*args)

    monkeypatch.setattr(view, "call", call)
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(summary_view, "call", call)
    monkeypatch.setattr(summary_view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(summary_view, "safe_defer", AsyncMock(return_value=True))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == row["evidence"]["actions"][action]["label"]
    )
    await button.callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    if isinstance(confirmation, summary_view.RecoverySummaryView):
        assert not current.store.actions
        await next(
            b for b in confirmation.children if b.label == "Continue to confirmation"
        ).callback(interaction)
        confirmation = interaction.followup.send.call_args.kwargs["view"]
    assert confirmation.action == action
    assert not current.store.actions
    confirm = next(b for b in confirmation.children if b.label.startswith("Confirm"))
    await confirm.callback(interaction)
    final = current.refresh(row["IncidentID"])
    assert final["State"] == "resolved"
    assert current.store.actions[0]["State"] == "verified"
    assert not r.outcomes.inspect(r.source)["resources"]
    if not committed:
        conn = r.outcomes.connect()
        try:
            with pytest.raises(SourceConflict):
                r.runtime.dal.begin_producer_transaction(claim, conn.cursor())
        finally:
            conn.rollback()
            conn.close()


def test_lost_close_reply_reconciles_after_restart(recovery):
    r = recovery
    preview, _ = uncommitted(r)
    action = dict(
        ActionKind="cancel_configuration",
        EvidenceHash=preview["token"],
        ActionID=str(uuid4()),
        Reason="Close verified rollback",
    )
    adapter = ConfigurationProducerRecovery(r.outcomes, r.service)
    adapter.execute(
        r.source,
        action["ActionKind"],
        action["EvidenceHash"],
        "recovery:" + action["ActionID"],
        action["Reason"],
    )
    restarted = ConfigurationProducerRecovery(r.outcomes, type(r.service)(r.runtime, r.outcomes))
    assert restarted.reconcile(r.source, action) == "verified"
    assert restarted.inspect(r.source)[2]


def test_stale_close_cannot_release_late_committed_result(recovery):
    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    preview, claim = uncommitted(r)
    r.runtime.dal.transition(claim, expected="writing", state="committed", generation=generation)
    with pytest.raises(SourceConflict):
        r.outcomes.cancel(r.source, preview["token"], "admin", "close")
    assert r.outcomes.inspect(r.source)["action"] == "resume_capture"


def test_config_is_not_misclassified_as_stats_import(recovery):
    from services.stats_import_outcome_dal import StatsImportOutcomeDAL

    r = recovery
    assert (
        r.source
        not in StatsImportOutcomeDAL(
            r.outcomes.connect, account="a", storage_owner="disk-a"
        ).pending_recovery()
    )


def test_active_business_transaction_prevents_release(recovery):
    from services.export_contention import CoordinationLockRefused

    r = recovery
    preview, claim = uncommitted(r)
    conn = r.outcomes.connect()
    try:
        r.runtime.dal.begin_producer_transaction(claim, conn.cursor())
        with pytest.raises(CoordinationLockRefused):
            r.outcomes.cancel(r.source, preview["token"], "admin", "close")
    finally:
        conn.rollback()
        conn.close()
