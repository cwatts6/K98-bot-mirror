"""Guided rollover admission preserves the original operation across replies/restarts."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_recovery_service import RolloverRecoveryAdapter
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryService
from tests.test_guided_recovery import ACTOR, Store, execute

ACTION = "continue_unstarted_rollover"


def fixture(state="closing"):
    snapshot = dict(
        operation=dict(
            State=state,
            Phase="draining" if state == "closing" else "ready",
            OwnerID=None,
            OldKVK=16,
            NewKVK=17,
            ProgressJson="{}",
        ),
        pool=dict(jobs=[], legacy_receipts=[]),
        resources=[],
    )
    discovery, pools, reconciler, rollover = Mock(), Mock(), Mock(), Mock()
    discovery.rollover.side_effect = lambda *_: deepcopy(snapshot)
    adapter = RolloverRecoveryAdapter(discovery, pools, reconciler, rollover=rollover)
    store = Store()
    service = RecoveryService(
        store,
        {adapter.kind: adapter},
        admin_id=1,
        guild_id=2,
        channel_id=3,
        presentation_policy=p0a_presentation,
    )
    evidence, token, resolved = adapter.inspect("operation")
    row = store.observe(adapter.kind, "operation", evidence, token, resolved=resolved)
    return service, adapter, store, row, snapshot


@pytest.mark.parametrize("state", ["closing", "ready"])
def test_confirmation_continues_original_operation_and_verifies_completion(state):
    service, adapter, store, row, snapshot = fixture(state)

    def complete(identifier):
        assert identifier == "operation"
        snapshot["operation"].update(State="completed", Phase="complete")

    adapter.rollover.advance.side_effect = complete
    assert execute(service, row, action=ACTION)["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"
    execute(service, row, action=ACTION)
    adapter.rollover.advance.assert_called_once_with("operation")
    adapter.pools.reconcile_complete.assert_not_called()


def test_lost_intent_reply_restarts_only_unowned_original_operation():
    service, adapter, store, row, snapshot = fixture()
    store.lose_claim_ack = True
    with pytest.raises(Exception, match="lost intent"):
        execute(service, row, action=ACTION)
    adapter.rollover.advance.assert_not_called()
    store.lose_claim_ack = False

    def complete(identifier):
        snapshot["operation"].update(State="completed", Phase="complete")

    adapter.rollover.advance.side_effect = complete
    restarted = RecoveryService(store, service.adapters, admin_id=1, guild_id=2, channel_id=3)
    assert restarted.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    restarted.review(ACTOR, row["IncidentID"])
    adapter.rollover.advance.assert_called_once_with("operation")
    assert store.actions[0]["State"] == "verified"


@pytest.mark.parametrize("state", ["running", "uncertain"])
def test_lost_provider_reply_hands_off_without_repeating_owned_phases(state):
    service, adapter, store, row, snapshot = fixture()

    def interrupted(identifier):
        snapshot["operation"].update(
            State=state,
            Phase="uncertain",
            OwnerID="original-owner",
            ProgressJson=json.dumps(dict(request=dict(phase="setup_pending"))),
        )
        raise TimeoutError("provider reply lost")

    adapter.rollover.advance.side_effect = interrupted
    current = execute(service, row, action=ACTION)
    assert current["State"] == "open"
    assert set(current["evidence"]["actions"]) == {"verify_rollover"}
    assert store.actions[0]["State"] == "verified"  # Admission only, not completion.
    service.review(ACTOR, row["IncidentID"])
    adapter.rollover.advance.assert_called_once()
    adapter.pools.reconcile_complete.assert_not_called()


def test_waiting_admission_remains_pending_and_continues_after_queue_clears():
    service, adapter, store, row, snapshot = fixture("ready")
    assert execute(service, row, action=ACTION)["pending_action"]
    assert len(store.actions) == 1
    snapshot["operation"].update(State="completed", Phase="complete")
    assert service.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert store.actions[0]["State"] == "verified"


def test_changed_evidence_requires_new_preview_before_admission():
    service, adapter, _, row, snapshot = fixture()
    snapshot["resources"].append(dict(Version=2))
    with pytest.raises(SourceConflict, match="changed"):
        execute(service, row, action=ACTION)
    adapter.rollover.advance.assert_not_called()


@pytest.mark.parametrize("state", ["running", "uncertain", "blocked"])
def test_owned_or_blocked_rollover_has_no_admission_action(state):
    _, adapter, _, _, snapshot = fixture(state)
    evidence, token, _ = adapter.inspect("operation")
    assert ACTION not in evidence["actions"]
    with pytest.raises(SourceConflict):
        adapter.execute("operation", ACTION, token, "recovery:action", "confirmed")
    adapter.rollover.advance.assert_not_called()


def test_old_season_blockers_have_bounded_guided_links_and_no_continue():
    _, adapter, _, _, snapshot = fixture()
    snapshot["pool"]["jobs"] = [dict(State="uncertain", JobID=str(i)) for i in range(10)]
    evidence, _, _ = adapter.inspect("operation")
    assert evidence["actions"] == {}
    assert [link["source_id"] for link in evidence["recovery_links"]] == ["0", "1", "2"]
    snapshot["pool"]["jobs"] = snapshot["pool"]["jobs"][3:]
    assert adapter.inspect("operation")[0]["recovery_links"][0]["source_id"] == "3"


def test_uncertain_historical_receipt_cannot_be_ignored():
    _, adapter, _, _, snapshot = fixture()
    snapshot["pool"]["legacy_receipts"] = [dict(DeliveryState="uncertain")]
    assert ACTION not in adapter.inspect("operation")[0]["actions"]


@pytest.mark.asyncio
async def test_admin_button_previews_destructive_rollover_and_requires_confirmation(monkeypatch):
    from ui.views import recovery_view as view

    _, _, _, row, _ = fixture()
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Continue waiting rollover"
    )
    await button.callback(interaction)
    message = interaction.followup.send.call_args.kwargs
    assert message["ephemeral"] is True
    assert isinstance(message["view"], view.RecoveryConfirmView)
    assert message["view"].action == ACTION
    assert "made private and cleared" in message["embed"].fields[0].value
    assert "16 to 17" in message["embed"].fields[0].value
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])


def test_original_configuration_summary_preserves_unknown_fault():
    _, adapter, _, _, snapshot = fixture()
    snapshot["operation"]["PlanJson"] = json.dumps(
        dict(snapshot=dict(pool=dict(RegistrationHash="a")))
    )
    snapshot["pool"]["pool"] = dict(RegistrationHash="a")
    summary = adapter.inspect("operation")[0]["failure_context"]["summary"]
    assert "16 to 17" in summary and "settings match" in summary
    assert "exception was not retained" in summary
    snapshot["pool"]["pool"]["RegistrationHash"] = "b"
    summary = adapter.inspect("operation")[0]["failure_context"]["summary"]
    assert "settings differ" in summary and "does not identify the fault" in summary


def test_reopened_completed_replacement_retains_verified_original_link():
    _, adapter, _, _, snapshot = fixture("completed")
    parent = str(uuid4())
    plan = dict(replacement_rollover=dict(operation_id=parent))
    snapshot["operation"].update(
        OperationID=str(uuid4()), PlanJson=json.dumps(plan), PlanHash=digest(plan).hex()
    )
    evidence, _, resolved = adapter.inspect("operation")
    assert resolved and evidence["recovery_links"] == [
        dict(label="Return to original rollover", kind="export_rollover", source_id=parent)
    ]
    snapshot["operation"]["PlanHash"] = "f" * 64
    with pytest.raises(SourceConflict, match="linkage cannot be verified"):
        adapter.inspect("operation")


@pytest.mark.asyncio
async def test_blocker_navigation_keeps_authorized_return_after_recheck(monkeypatch):
    from ui.views import recovery_view as view

    _, _, store, row, _ = fixture()
    row["evidence"]["recovery_links"] = [
        dict(label="Review blocker", kind="export_job", source_id="job")
    ]
    child = dict(
        row,
        IncidentID="child",
        SourceID="job",
        SourceKind="export_job",
        State="resolved",
        evidence=dict(row["evidence"], recovery_links=[], actions={}),
    )
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(side_effect=[child, child, row]))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    link = next(b for b in view.RecoveryIncidentView(row).children if b.label == "Review blocker")
    await link.callback(interaction)
    opened = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in opened.children if b.label == "Recheck").callback(interaction)
    reopened = interaction.followup.send.call_args.kwargs["view"]
    await next(b for b in reopened.children if b.label == "Return to rollover").callback(
        interaction
    )
    assert view.call.await_args_list[-1].args == ("review", ACTOR, row["IncidentID"])
    assert interaction.followup.send.call_args.kwargs["ephemeral"] is True
