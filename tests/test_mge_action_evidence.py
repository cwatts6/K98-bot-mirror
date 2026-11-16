"""O1: result wording requires post-settlement primary, secondary and audit evidence."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from mge import mge_action_response as responses
from mge.mge_action_result import (
    ActionDisposition as D,
    ActionEvidence,
    WriteEvidence,
    classify,
    qualified_action,
    record_write,
)
from mge.mge_refresh_work import RefreshCoordinator, registration_options


@pytest.mark.parametrize(
    "steps,success,expected",
    [
        ([], True, D.UNKNOWN),
        ([], False, D.NOT_ENTERED),
        ([WriteEvidence("primary", "unknown")], False, D.UNKNOWN),
        ([WriteEvidence("primary", "confirmed", 1)], True, D.COMPLETED),
        ([WriteEvidence("primary", "confirmed", 1)], False, D.PARTIAL),
        (
            [
                WriteEvidence("primary", "confirmed", 1),
                WriteEvidence("audit", "unknown", kind="audit"),
            ],
            True,
            D.PARTIAL,
        ),
        (
            [
                WriteEvidence("primary", "confirmed", 1),
                WriteEvidence("targets", "not_entered", kind="secondary"),
            ],
            True,
            D.PARTIAL,
        ),
        ([WriteEvidence("targets", "not_required", kind="secondary")], True, D.COMPLETED),
    ],
)
def test_evidence_classification(steps, success, expected):
    evidence = classify(steps, success=success)
    assert evidence.disposition == expected
    if expected in {D.PARTIAL, D.UNKNOWN}:
        assert "✅" not in evidence.message("Saved")
        assert evidence.message("Saved") != "Saved"


def test_confirmed_primary_then_exception_is_partial():
    @qualified_action
    def action():
        record_write("primary", "confirmed", count=1)
        raise OSError("private token")

    result = action()
    assert result.action.disposition == D.PARTIAL
    assert result.action.confirmed_count == 1
    assert "private" not in result.message


@pytest.mark.asyncio
@pytest.mark.parametrize("reply_fails", [False, True])
@pytest.mark.parametrize("disposition", [D.COMPLETED, D.PARTIAL, D.UNKNOWN, D.NOT_ENTERED])
async def test_reply_gate_releases_after_reply_even_when_transport_fails(
    monkeypatch, reply_fails, disposition
):
    coordinator = RefreshCoordinator()
    trace = []
    handles = []

    async def refresh():
        trace.append("refresh")
        return True

    def register(event_id):
        gate, readonly = registration_options(None, False)
        assert readonly == (disposition != D.COMPLETED)
        assert not gate.is_set()
        trace.append("register")
        handle = coordinator.request(event_id, refresh, gate=gate)
        handles.append(handle)
        return handle

    async def reply(interaction, text):
        assert "refresh" not in trace
        trace.append("reply")
        assert text.startswith("✅") == (disposition == D.COMPLETED)
        if reply_fails:
            raise OSError("response lost")
        return True

    monkeypatch.setattr(responses, "send_ephemeral", reply)
    result = SimpleNamespace(message="Saved.", action=ActionEvidence(disposition))
    if reply_fails:
        with pytest.raises(OSError):
            await responses.reply_with_refresh(
                object(), result, event_id=7, register_refresh=register
            )
    else:
        await responses.reply_with_refresh(object(), result, event_id=7, register_refresh=register)
    await coordinator.drain()
    assert trace == (
        ["reply"] if disposition == D.NOT_ENTERED else ["register", "reply", "refresh"]
    )
    assert coordinator.snapshot()["pending"] == 0


@pytest.mark.asyncio
async def test_registration_failure_does_not_claim_pending(monkeypatch):
    reply = AsyncMock(return_value=True)
    monkeypatch.setattr(responses, "send_ephemeral", reply)

    def refused(_):
        raise RuntimeError("closed")

    await responses.reply_with_refresh(
        object(),
        SimpleNamespace(message="Saved.", action=ActionEvidence(D.COMPLETED)),
        event_id=7,
        register_refresh=refused,
    )
    assert "could not be fully scheduled" in reply.await_args.args[1]
    assert "is pending" not in reply.await_args.args[1]


@pytest.mark.parametrize(
    "settlements,expected",
    [([1, 1], D.COMPLETED), ([1, 0], D.PARTIAL), ([1, None], D.PARTIAL), ([None], D.UNKNOWN)],
)
def test_real_waitlist_service_uses_settled_dal_primary_and_audit(
    monkeypatch, settlements, expected
):
    from mge import mge_roster_service as service
    from mge.dal import mge_roster_dal as dal

    monkeypatch.setattr(
        dal,
        "fetch_award_by_id",
        lambda _: dict(
            EventId=7,
            AwardId=1,
            GovernorId=101,
            AwardedRank=1,
            AwardStatus="awarded",
            InternalNotes="old",
        ),
    )
    returns = iter(settlements)
    monkeypatch.setattr(dal, "exec_with_cursor", lambda *a, **k: next(returns))
    result = service.move_to_waitlist(award_id=1, waitlist_order=1, actor_discord_id=1)
    assert result.action.disposition == expected
    assert result.action.confirmed_count == (0 if expected == D.UNKNOWN else 1)


@pytest.mark.asyncio
async def test_event_mismatch_is_refused_under_real_roster_owner(monkeypatch):
    from mge.dal import mge_roster_dal
    from mge.mge_roster_execution import run_roster_mutation

    monkeypatch.setattr(mge_roster_dal, "fetch_award_by_id", lambda _: dict(EventId=8, AwardId=1))

    def must_not_write(**kwargs):
        raise AssertionError("wrong event mutation entered")

    result = await run_roster_mutation(7, must_not_write, award_id=1)
    assert result.action.disposition == D.NOT_ENTERED


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", ["edit", "reset"])
@pytest.mark.parametrize("reply_fails", [False, True])
async def test_real_rules_callers_register_before_reply_and_release_on_transport_failure(
    monkeypatch, caller, reply_fails
):
    import asyncio

    from tests.test_mge_rules_edit_view import _DummyInteraction
    from ui.views import mge_rules_edit_view as views

    work = RefreshCoordinator()
    trace = []
    monkeypatch.setattr(views, "is_admin_or_leadership_interaction", lambda _: True)
    result = SimpleNamespace(
        success=True, message="Saved.", signup_channel_id=1, action=ActionEvidence(D.COMPLETED)
    )
    monkeypatch.setattr(views.mge_rules_service, "update_event_rules_text", lambda **kwargs: result)
    monkeypatch.setattr(
        views.mge_rules_service, "reset_event_rules_to_mode_default", lambda **kwargs: result
    )

    async def refresh():
        trace.append("refresh")
        return True

    def register(**kwargs):
        gate, readonly = registration_options(None, False)
        assert not readonly and not gate.is_set()
        trace.append("registered")
        return work.request(7, refresh, gate=gate)

    monkeypatch.setattr(views.mge_embed_manager, "request_signup_refresh", register)
    interaction = _DummyInteraction()

    async def send(content, **kwargs):
        trace.append("reply")
        assert "Board refresh is pending" in content and "refresh" not in trace
        await asyncio.sleep(0)
        if reply_fails:
            raise OSError("simulated reply failure")

    interaction.followup.send = send
    view = views.MgeRulesEditView(event_id=7)
    if caller == "edit":
        modal = views._RulesEditModal(view, "old")
        modal.rules_text.value = "new"
        await modal.callback(interaction)
    else:
        await view.reset_to_mode_default.callback(interaction)
    await work.drain()
    assert trace == ["registered", "reply", "refresh"]
    view.stop()


@pytest.mark.asyncio
async def test_unknown_signup_retains_private_reconciliation_reference(monkeypatch):
    from core.operation_outcome import MutationOutcome
    from mge.mge_signup_service import ServiceResult

    reply = AsyncMock(return_value=True)
    monkeypatch.setattr(responses, "send_ephemeral", reply)
    result = ServiceResult(
        False,
        "Unconfirmed",
        outcome=MutationOutcome.UNKNOWN,
        operation_id="fixture-recovery-reference",
    )
    await responses.reply_with_refresh(
        object(), result, event_id=7, refresh_public=False, refresh_leadership=False
    )
    text = reply.await_args.args[1]
    assert "fixture-recovery-reference" in text and "✅" not in text


@pytest.mark.parametrize("caller", ["edit", "reset"])
def test_uncertain_rules_write_preserves_refresh_destination(monkeypatch, caller):
    from mge import mge_rules_service as service

    monkeypatch.setattr(
        service.mge_rules_dal,
        "fetch_event_rules_context",
        lambda _: dict(RuleMode="fixed", RulesText="old", SignupEmbedChannelId=123),
    )
    monkeypatch.setattr(service.mge_rules_dal, "fetch_default_rules_text", lambda _: "default")
    monkeypatch.setattr(service.mge_rules_dal, "exec_with_cursor", lambda **_: None)
    result = (
        service.update_event_rules_text(event_id=7, new_rules_text="new", actor_discord_id=1)
        if caller == "edit"
        else service.reset_event_rules_to_mode_default(event_id=7, actor_discord_id=1)
    )
    assert result.signup_channel_id == 123
    assert result.action.disposition == D.UNKNOWN and result.action.read_only_refresh
