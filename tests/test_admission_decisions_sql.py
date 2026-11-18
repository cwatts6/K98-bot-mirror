"""Guided registration decisions, queue ownership and unbounded refusal history."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.producer_recovery_intent import current_intent
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, execute
from tests.test_producer_refusal_sql import refused as refused, setup, unblock

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Temporary SQL opt-in required"
)


def registration(r, name):
    r.runtime.configuration = json.dumps(
        dict(scan_data=dict(consumer="scan_data", outputs=["changed"], destinations=[name]))
    )


@pytest.mark.asyncio
async def test_changed_registration_dispatch_keeps_exact_inputs_and_receipt(refused, monkeypatch):
    from services.stats_import_outcome_dal import StatsImportOutcomeDAL
    from ui.views import (
        recovery_review_view as pages,
        recovery_summary_view as summaries,
        recovery_view as view,
    )

    r = refused
    unblock(r)
    original = r.runtime.dal.read(r.source)["RequestJson"]
    registration(r, "current-sheet")
    calls = []

    def runner(inputs):
        calls.append(inputs)
        intent = current_intent()
        scope = json.loads(r.runtime.configuration)["scan_data"]
        child = r.runtime.dal.request(
            account=r.runtime.account,
            consumer="scan_data",
            kvk_no=None,
            request=dict(
                operation=intent["operation"], kind="scan_data", config=scope, producer=intent
            ),
            storage_owner="disk",
            actor="test",
            reason="same confirmed continuation",
        )
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
        raise TimeoutError("Lost reply after registration")

    adapter, store, service, row = setup(r, runner)
    assert set(row["evidence"]["actions"]) == {"resume_current_registration", "cancel_saved_stage"}

    async def call(method, *args):
        return getattr(service, method)(*args)

    for module in (view, pages, summaries):
        monkeypatch.setattr(module, "actor_for", lambda _: ACTOR)
        monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
        monkeypatch.setattr(module, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in view.RecoveryIncidentView(row).children
        if b.label == "Continue with current destinations"
    )
    await button.callback(interaction)
    details = interaction.followup.send.call_args.kwargs["view"]
    assert isinstance(details, summaries.RecoverySummaryView)
    assert not calls and not store.actions
    await details.confirm.callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    assert isinstance(confirmation, view.RecoveryConfirmView) and not calls
    await confirmation.confirm.callback(interaction)
    result = interaction.followup.send.call_args.kwargs["view"].row
    assert calls == [r.inputs]
    assert store.actions[0]["State"] == "verified" and result["State"] == "open"
    assert result["evidence"]["recovery_links"][0]["kind"] == "stats_import"
    assert r.runtime.dal.read(r.source)["RequestJson"] == original
    state = r.dal.snapshot(r.source)
    assert state["attempt_count"] == 1
    child = json.loads(state["attempts"][0]["RequestJson"])["request"]
    assert child["config"]["destinations"] == ["current-sheet"]
    assert child["producer"]["inputs"] == r.inputs
    # Another registration change cannot create another reservation for this action.
    registration(r, "later-sheet")
    assert adapter.reconcile(r.source, store.actions[0]) == "verified"
    assert r.dal.snapshot(r.source)["attempt_count"] == 1 and calls == [r.inputs]


def test_registration_change_after_preview_requires_new_confirmation(refused):
    r = refused
    unblock(r)
    registration(r, "first-sheet")
    adapter, _, service, row = setup(r)
    registration(r, "second-sheet")
    with pytest.raises(SourceConflict):
        execute(service, row, action="resume_current_registration")
    adapter.runner.assert_not_called()
    assert r.dal.snapshot(r.source)["attempt_count"] == 0


def test_lost_new_registration_intent_is_closed_without_dispatch(refused):
    r = refused
    unblock(r)
    registration(r, "first-sheet")
    adapter, store, service, row = setup(r)
    store.lose_claim_ack = True
    with pytest.raises(UncertainCommit):
        execute(service, row, action="resume_current_registration")
    registration(r, "second-sheet")
    service.refresh(row["IncidentID"])
    assert store.actions[0]["State"] == "not_applied"
    assert r.dal.snapshot(r.source)["attempt_count"] == 1
    registration(r, "third-sheet")
    assert adapter.reconcile(r.source, store.actions[0]) == "not_applied"
    assert r.dal.snapshot(r.source)["attempt_count"] == 1
    adapter.runner.assert_not_called()


def test_healthy_queued_preparation_is_shown_before_any_resource_claim(refused):
    r = refused
    unblock(r)
    r.f.sql.commit()
    request = json.loads(r.runtime.dal.read(r.source)["RequestJson"])["request"]
    operation = str(uuid4())
    request["operation"] = request["producer"]["operation"] = operation
    queued = r.runtime.dal.request(
        account=r.runtime.account,
        consumer="scan_data",
        kvk_no=None,
        request=request,
        storage_owner="disk",
        actor="test",
        reason="healthy queued work",
    )
    adapter, _, _, _ = setup(r)
    evidence, _, resolved = adapter.inspect(r.source)
    assert not resolved and evidence["outcome"] == "waiting_in_queue"
    assert set(evidence["actions"]) == {"cancel_saved_stage"}
    assert evidence["recovery_links"] == [
        dict(label="Review blocking stage", kind="producer_refusal", source_id=queued)
    ]
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE ActivePreparationID=?", queued
        ).fetchval()
        == 0
    )
    r.runtime.dal.withdraw_unstarted(queued)
    assert "resume_sql_stage" in adapter.inspect(r.source)[0]["actions"]


def test_more_than_one_hundred_refusals_remain_recoverable_and_bounded(refused):
    r = refused
    unblock(r)
    first_action, first_child = None, None
    with r.dal.serialized(r.source):
        for _ in range(105):
            action = str(uuid4())
            child = r.dal.reserve(r.source, action)
            first_action, first_child = (first_action or action), (first_child or child)
            r.runtime.dal.withdraw_unstarted(child)
        state = r.dal.snapshot(r.source)
        assert state["attempt_count"] == 105 and len(state["attempts"]) == 1
        assert len(state["attempt_history_sha256"]) == 64
        assert r.dal.reserve(r.source, first_action) == first_child
        assert r.dal.close_unused(r.source, first_action)
    adapter, _, _, _ = setup(r)
    assert "resume_sql_stage" in adapter.inspect(r.source)[0]["actions"]
    assert r.dal.snapshot(r.source)["attempt_count"] == 105
