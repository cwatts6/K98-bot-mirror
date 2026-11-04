import asyncio
from copy import deepcopy
from datetime import UTC, datetime
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from core.board_lifecycle import BoardLifecycle, BoardWork
from mge import mge_finalisation as final
from mge.dal import mge_completion_dal


@pytest.fixture
def scene(monkeypatch):
    target = dict(
        EventId=1,
        BoardKind="signup",
        FinalisationId="generation-1",
        PublishVersion=2,
        ChannelId=10,
        MessageId=20,
        DeliveryState="pending",
        PayloadJson=None,
        Reason=None,
        Revision=1,
    )
    rows = {"signup": target}
    event = dict(
        EventId=1,
        Status="completed",
        PublishVersion=2,
        SignupEmbedChannelId=10,
        SignupEmbedMessageId=20,
    )
    payload = {"title": "Final board", "type": "rich"}
    message = SimpleNamespace(
        embeds=[discord.Embed.from_dict(payload)], components=[], edit=AsyncMock()
    )
    channel = SimpleNamespace(fetch_message=AsyncMock(return_value=message))
    bot = SimpleNamespace(get_channel=lambda _: channel, fetch_channel=AsyncMock())

    def targets(_):
        return deepcopy(list(rows.values()))

    def transition(snapshot, state, *, payload=None, reason=None, actor_id=None):
        current = rows[snapshot["BoardKind"]]
        if current["Revision"] != snapshot["Revision"] or current["DeliveryState"] in {
            "confirmed",
            "retired",
        }:
            return False
        current.update(DeliveryState=state, Revision=current["Revision"] + 1, Reason=reason)
        current["PayloadJson"] = current["PayloadJson"] or payload
        return True

    monkeypatch.setattr(final.dal, "targets", targets)
    monkeypatch.setattr(final.dal, "transition", transition)
    monkeypatch.setattr(final, "_prepare", AsyncMock(return_value=json.dumps(payload)))
    return SimpleNamespace(
        rows=rows,
        event=event,
        bot=bot,
        channel=channel,
        message=message,
        targets=targets,
        payload=payload,
    )


@pytest.mark.asyncio
async def test_final_delivery_restarts_do_zero_network_work(scene):
    assert await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.rows["signup"]["DeliveryState"] == "confirmed"
    for _ in range(3):
        assert await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.channel.fetch_message.await_count == scene.message.edit.await_count == 1


@pytest.mark.asyncio
async def test_crash_after_edit_before_ack_reconciles_without_replay(scene):
    scene.message.edit.side_effect = TimeoutError("ack lost")
    assert not await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.rows["signup"]["DeliveryState"] == "unknown"
    assert await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.message.edit.await_count == 1
    assert scene.rows["signup"]["DeliveryState"] == "confirmed"


@pytest.mark.asyncio
async def test_unknown_payload_mismatch_is_held_without_replay(scene):
    scene.rows["signup"].update(DeliveryState="unknown", PayloadJson=json.dumps(scene.payload))
    scene.message.embeds = [discord.Embed(title="old board")]
    assert not await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.rows["signup"]["DeliveryState"] == "held"
    scene.message.edit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("status,reason", [(404, "confirmed_missing"), (403, "inaccessible")])
async def test_deleted_and_inaccessible_are_distinct_and_never_replaced(scene, status, reason):
    response = SimpleNamespace(status=status, reason="fixture")
    error = discord.NotFound if status == 404 else discord.Forbidden
    scene.channel.fetch_message.side_effect = error(response, "fixture")
    assert not await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.rows["signup"]["Reason"] == reason
    scene.message.edit.assert_not_awaited()
    await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.channel.fetch_message.await_count == 1


@pytest.mark.asyncio
async def test_transient_fetch_failure_keeps_identity_and_retries_same_message(scene):
    scene.channel.fetch_message.side_effect = [TimeoutError(), scene.message]
    assert not await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert scene.rows["signup"]["DeliveryState"] == "failed"
    assert await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    assert [c.args for c in scene.channel.fetch_message.await_args_list] == [(20,), (20,)]


@pytest.mark.asyncio
async def test_identity_conflict_holds_before_network(scene):
    scene.event["SignupEmbedMessageId"] = 21
    assert not await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    scene.channel.fetch_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_retirement_uses_preview_version_and_keeps_message(scene):
    from mge import mge_embed_manager as manager
    from mge.mge_refresh_work import RefreshCoordinator

    manager._refreshes = RefreshCoordinator()
    preview = await final.retirement_preview(1)
    scene.rows["signup"]["Revision"] += 1
    assert await final.retire_targets(scene.bot, 1, preview, 123) == {"signup": False}
    assert await final.retire_targets(scene.bot, 1, await final.retirement_preview(1), 123) == {
        "signup": True
    }
    assert not await final.deliver_target(scene.bot, scene.event, scene.targets(1)[0])
    scene.channel.fetch_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("actor_id,source", [(123, "admin_view"), (None, "scheduler")])
async def test_completion_keeps_origin_in_audit_log(scene, monkeypatch, caplog, actor_id, source):
    from mge import mge_embed_manager as manager
    from mge.dal import mge_event_dal
    from mge.mge_refresh_work import RefreshCoordinator

    monkeypatch.setattr(manager, "_refreshes", RefreshCoordinator())
    monkeypatch.setattr(mge_event_dal, "fetch_event_for_embed", lambda *a, **k: scene.event)
    monkeypatch.setattr(
        mge_completion_dal, "fetch_event_completion_context", lambda _: {"Status": "published"}
    )
    monkeypatch.setattr(mge_completion_dal, "mark_event_completed", lambda **kwargs: True)
    with caplog.at_level("INFO", logger="mge.mge_completion_service"):
        result = await final.finalise_event(scene.bot, 1, actor_id=actor_id, complete=True)
    record = next(record for record in caplog.records if record.message == "mge_event_complete")
    assert record.source == source
    assert record.actor_discord_id == actor_id
    assert result["domain_completed"]


@pytest.mark.asyncio
async def test_finalisation_waits_for_inflight_refresh_and_drains_cancellation(scene, monkeypatch):
    from mge import mge_embed_manager as manager
    from mge.dal import mge_event_dal
    from mge.mge_board_ownership import presentation_owner
    from mge.mge_refresh_work import RefreshCoordinator

    monkeypatch.setattr(manager, "_refreshes", RefreshCoordinator())
    monkeypatch.setattr(mge_event_dal, "fetch_event_for_embed", lambda *a, **k: scene.event)
    entered, release = asyncio.Event(), asyncio.Event()

    async def edit(**kwargs):
        entered.set()
        await release.wait()

    scene.message.edit.side_effect = edit
    async with presentation_owner(scene.bot, 1):
        task = asyncio.create_task(final.finalise_event(scene.bot, 1))
        await asyncio.sleep(0)
        scene.channel.fetch_message.assert_not_awaited()
    await entered.wait()
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert scene.rows["signup"]["DeliveryState"] == "confirmed"
    await final.finalise_event(scene.bot, 1)
    assert scene.message.edit.await_count == 1


@pytest.mark.asyncio
async def test_partial_targets_keep_success_and_continue(scene, monkeypatch):
    from mge import mge_embed_manager as manager
    from mge.dal import mge_event_dal
    from mge.mge_refresh_work import RefreshCoordinator

    monkeypatch.setattr(manager, "_refreshes", RefreshCoordinator())
    monkeypatch.setattr(mge_event_dal, "fetch_event_for_embed", lambda *a, **k: scene.event)
    scene.event.update(LeadershipEmbedChannelId=10, LeadershipEmbedMessageId=21)
    scene.rows["leadership"] = dict(scene.rows["signup"], BoardKind="leadership", MessageId=21)
    scene.channel.fetch_message.side_effect = [scene.message, TimeoutError(), scene.message]
    result = await final.finalise_event(scene.bot, 1)
    assert result["states"] == {"signup": "confirmed", "leadership": "failed"}
    result = await final.finalise_event(scene.bot, 1)
    assert set(result["states"].values()) == {"confirmed"}
    assert [c.args for c in scene.channel.fetch_message.await_args_list] == [(20,), (21,), (21,)]


@pytest.mark.asyncio
async def test_final_payload_has_finished_wording_and_utc_timestamp(monkeypatch):
    from mge import mge_embed_manager as manager

    stamp = datetime(2026, 10, 29, 10)
    event = dict(
        EventId=1,
        Status="completed",
        RuleMode="fixed",
        EventMode="controlled",
        PublishVersion=2,
        UpdatedUtc=stamp,
        UpdatedUtcToken="2026-10-29T10:00:00",
        StartUtc=stamp,
        EndUtc=stamp,
        SignupCloseUtc=stamp,
        EventName="MGE",
        VariantName="Infantry",
        SignupEmbedChannelId=10,
        SignupEmbedMessageId=20,
        LeadershipEmbedChannelId=None,
        LeadershipEmbedMessageId=None,
        AwardEmbedChannelId=None,
        AwardEmbedMessageId=None,
    )
    monkeypatch.setattr(manager, "public_names", lambda *a, **k: [])
    payload = json.loads(await final._prepare(event, "signup"))
    assert payload["description"] == "This MGE event has been completed."
    assert datetime.fromisoformat(payload["timestamp"]) == stamp.replace(tzinfo=UTC)


@pytest.mark.asyncio
async def test_retirement_confirmation_rejects_other_actor(monkeypatch):
    from tests.test_mge_admin_completion_view import _FakeInteraction
    from ui.views import mge_admin_completion_view as views

    monkeypatch.setattr(views, "is_admin_interaction", lambda _: True)
    monkeypatch.setattr(views, "send_ephemeral", AsyncMock())
    mutation = AsyncMock()
    monkeypatch.setattr(final, "retire_targets", mutation)
    view = views._RetireFinalBoards(1, [], 123)
    await view.confirm.callback(_FakeInteraction(456))
    mutation.assert_not_awaited()


@pytest.mark.asyncio
async def test_ordinary_completed_board_refresh_does_no_network(scene, monkeypatch):
    from mge import mge_embed_manager as manager
    from mge.mge_refresh_work import RefreshCoordinator

    monkeypatch.setattr(manager, "_refreshes", RefreshCoordinator())
    monkeypatch.setattr(manager, "fetch_event_for_embed", lambda *a, **k: scene.event)
    monkeypatch.setattr(manager, "validate_event", lambda *a, **k: None)
    assert not await manager.sync_event_signup_embed(
        bot=scene.bot, event_id=1, signup_channel_id=10
    )
    assert not await manager.sync_event_leadership_embed(bot=scene.bot, event_id=1, channel_id=10)
    scene.channel.fetch_message.assert_not_awaited()


def test_domain_boundary_and_calendar_continuity():
    assert BoardLifecycle(False, "pending").work() == BoardWork.REFRESH
    assert BoardLifecycle(True, "pending").work() == BoardWork.FINAL_EDIT
    assert BoardLifecycle(True, "unknown").work() == BoardWork.RECONCILE
    # Rolling calendar is never final just because its previous events ended.
    assert BoardLifecycle(False, "active").work() == BoardWork.REFRESH
    # Ark awaiting a late result stops roster refresh without finalising results.
    assert BoardLifecycle(False, "pending", refresh_allowed=False).work() == BoardWork.NONE


@pytest.mark.asyncio
async def test_ark_late_result_real_dal_contract(monkeypatch):
    from ark.dal import ark_dal

    stored = dict(MatchId=7, Status="Completed", Result=None)
    assert (
        BoardLifecycle(bool(stored["Result"]), "pending", refresh_allowed=False).work()
        == BoardWork.NONE
    )

    async def write(sql, params):
        assert "Status = 'Completed'" in sql
        stored.update(Result=params[0], Status="Completed")
        return {"MatchId": 7}

    monkeypatch.setattr(ark_dal, "run_one_async", write)
    assert await ark_dal.set_match_result(
        match_id=7, result="Win", notes=None, actor_discord_id=123
    )
    assert (
        BoardLifecycle(bool(stored["Result"]), "pending", refresh_allowed=False).work()
        == BoardWork.FINAL_EDIT
    )


def test_completion_captures_targets_in_same_transaction(monkeypatch):
    statements = []
    cur = SimpleNamespace(rowcount=1, execute=lambda sql, *args: statements.append(sql))
    monkeypatch.setattr(mge_completion_dal, "exec_with_cursor", lambda fn: fn(cur))
    assert mge_completion_dal.mark_event_completed(1, 123, datetime.now(UTC))
    assert len(statements) == 2
    assert "Status = 'completed'" in statements[0]
    assert "NEWID()" in statements[1] and "MGE_BoardFinalisation" in statements[1]
