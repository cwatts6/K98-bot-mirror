"""Replacement qualification through the deployed action boundary, not bare adapters.

Temporary SQL and simulated provider/pipe transport retain the existing fixture
boundaries. Every reconstructed recovery service uses the production policy.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests.test_export_replacement_rpc_sql import (
    contained_job as contained_job,
    guided as guided,
    guided_completion,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    rpc as rpc,
    store as store,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR


@pytest.fixture
def isolation_entry(monkeypatch, request, store):
    from services.export_replacement_dal import ExportReplacementDAL
    from services.export_replacement_service import ExportReplacementService
    from services.export_replacement_workflow import ReplacementWorkflow
    from tests import test_export_target_containment_sql as fixture

    monkeypatch.setattr(fixture, "TABLES", (*fixture.TABLES, "dbo.ExportReplacementPlan"))
    containment, sql_fixture, _ = request.getfixturevalue("recovery")
    proposals = ExportReplacementService(
        dal=ExportReplacementDAL(sql_fixture.connect),
        containment=containment,
        registration=containment.registration,
        store=containment.store,
    )
    # These later stages are not reached until a replacement proposal exists.
    workflow = ReplacementWorkflow(
        proposals=proposals,
        verification=None,
        activation=None,
        plan_factory=None,
        continuation=None,
    )
    service = RecoveryService(store, {"export_job": workflow}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, "export_job", sql_fixture.job)
    return SimpleNamespace(recovery=service, f=sql_fixture, row=row)


@pytest.fixture(autouse=True)
def production_action_policy(monkeypatch):
    original = RecoveryService.__init__

    def initialize(self, *args, **kwargs):
        kwargs["presentation_policy"] = p0a_presentation
        original(self, *args, **kwargs)

    monkeypatch.setattr(RecoveryService, "__init__", initialize)


def test_released_form_restart_activation_queue_and_independent_delivery(rpc):
    guided_completion(rpc)
    assert rpc.recovery.review(ACTOR, rpc.row["IncidentID"])["State"] == "resolved"


def test_released_failed_read_has_guided_discard_and_fresh_verification(guided):
    from tests.test_export_replacement_guided_sql import (
        test_failed_file_check_offers_discard_then_fresh_check,
    )

    test_failed_file_check_offers_discard_then_fresh_check(guided)


def test_released_original_read_settlement_uses_saved_journal_without_provider_replay(
    rpc, monkeypatch
):
    from services.export_replacement_verification_service import ReplacementVerificationService
    from tests.test_export_replacement_guided_sql import apply

    r = rpc
    finish = ReplacementVerificationService.finish
    with monkeypatch.context() as injected:
        injected.setattr(ReplacementVerificationService, "finish", lambda *_: None)
        row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "checking_replacements"
    assert "finish_replacement_check" in row["evidence"]["actions"]
    assert ReplacementVerificationService.finish is finish
    sent = len(r.runtime.sent)
    row = apply(r, "finish_replacement_check")
    assert row["evidence"]["outcome"] == "activation_required"
    assert len(r.runtime.sent) == sent
    assert not row["pending_action"]


@pytest.mark.asyncio
@pytest.mark.parametrize("stale", [False, True])
async def test_released_isolation_confirmation_preserves_unknown_write_and_next_form(
    isolation_entry, monkeypatch, stale
):
    from ui.views import recovery_view as view

    r = isolation_entry
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        current = RecoveryService(
            r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
        )
        return getattr(current, method)(*args)

    monkeypatch.setattr(view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    label = r.row["evidence"]["actions"]["isolate_targets"]["label"]
    button = next(b for b in view.RecoveryIncidentView(r.row).children if b.label == label)
    await button.callback(interaction)
    confirmation = interaction.followup.send.call_args.kwargs["view"]
    assert isinstance(confirmation, view.RecoveryConfirmView)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 0
    if stale:
        r.f.sql.execute("UPDATE #ExportExecutionStream SET Version=Version+1")
        r.f.sql.commit()
    await confirmation.children[0].callback(interaction)
    assert interaction.followup.send.call_args.kwargs["ephemeral"] is True
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == (
        0 if stale else 1
    )
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    if not stale:
        row = r.recovery.review(ACTOR, r.row["IncidentID"])
        assert row["State"] == "open" and "choose_replacements" in row["evidence"]["actions"]
        assert r.recovery.input_page(ACTOR, row["IncidentID"], "choose_replacements")["fields"]
        await confirmation.children[0].callback(interaction)
        assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 1


@pytest.mark.asyncio
async def test_released_buttons_require_confirmation_and_verify_delivery(rpc, monkeypatch):
    from tests.test_export_replacement_end_to_end import prepare_publication
    from ui.views import recovery_view as view

    r = rpc
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        # Reopen the service on every callback, as after a lost view or restart.
        current = RecoveryService(
            r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
        )
        return getattr(current, method)(*args)

    monkeypatch.setattr(view, "call", call)
    confirmations = []
    for action in ("verify_replacements", "activate_replacements", "publish_replacement"):
        row = r.recovery.review(ACTOR, r.row["IncidentID"])
        assert "release_notice" not in row
        label = row["evidence"]["actions"][action]["label"]
        interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
        button = next(b for b in view.RecoveryIncidentView(row).children if b.label == label)
        await button.callback(interaction)
        preview = interaction.followup.send.call_args.kwargs
        assert preview["ephemeral"] is True
        assert isinstance(preview["view"], view.RecoveryConfirmView)
        assert {f.name for f in preview["embed"].fields} >= {
            "Check before confirming",
            "What the bot will do",
            "Verification",
        }
        # Opening a confirmation must not execute the action.
        unchanged = r.recovery.review(ACTOR, r.row["IncidentID"])
        assert unchanged["EvidenceHash"] == row["EvidenceHash"]
        confirmations.append((preview["view"], interaction))
        await preview["view"].children[0].callback(interaction)
        result = interaction.followup.send.call_args.kwargs
        assert result["ephemeral"] is True
        assert isinstance(result["view"], view.RecoveryIncidentView)
        assert result["view"].row["State"] == "open"

    r.activated = r.workflow._state(r.f.job)["activation"]
    r.delivery = r.workflow.continuation
    prepare_publication(r)
    r.publish()
    settled = r.recovery.review(ACTOR, r.row["IncidentID"])
    assert settled["State"] == "resolved"
    assert settled["evidence"]["outcome"] == "replacement_delivered"
    for confirmation, interaction in confirmations:
        await confirmation.children[0].callback(interaction)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    r.http.request.assert_not_called()
