from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from kvk.models.source_receipt_state import receipt_actions
from tests.test_kvk_source_admin import ACCESS, ADMIN, NOW
from ui.views.kvk_source_import_view import (
    KvkSourceImportView,
    SourceConfigurationModal,
    SourceMetadataModal,
    SourcePairModal,
    SourceReviewView,
    SourceRosterModal,
    SourceUploadSeasonModal,
    SourceUploadStartView,
    send_receipt,
)


def interaction(*, owner=10, roles=(), guild=20, channel=30):
    user = SimpleNamespace(id=owner, bot=False)
    return SimpleNamespace(
        user=user,
        guild=SimpleNamespace(
            id=guild,
            fetch_member=AsyncMock(
                return_value=SimpleNamespace(id=owner, roles=[SimpleNamespace(id=r) for r in roles])
            ),
        ),
        channel=SimpleNamespace(id=channel),
        response=SimpleNamespace(
            is_done=lambda: False,
            send_message=AsyncMock(),
            send_modal=AsyncMock(),
            defer=AsyncMock(),
        ),
        followup=SimpleNamespace(send=AsyncMock()),
    )


def make_view(action="accept"):
    row = {
        "AttemptID": "receipt",
        "ActorID": "10",
        "Status": "validated",
        "payload": {
            "version": 2,
            "proposal": {"action": action, "candidate": {}, "expires": "2099-01-01T00:00:00+00:00"},
        },
    }
    service = SimpleNamespace(
        access=ACCESS,
        confirm=Mock(return_value=row),
        summary=lambda row: "accepted; not published",
        actions=lambda row, action="accept", **kw: receipt_actions(row, action, NOW, **kw),
        check_receipt_action=Mock(return_value=row),
    )
    return KvkSourceImportView(service, row, action=action), service


@pytest.mark.asyncio
async def test_resume_preserves_reviewed_source_revision_expectation():
    view, service = make_view("correct")
    view.row["payload"]["proposal"].update(
        expected_revision="revision", expected_revision_version=7
    )
    resumed = KvkSourceImportView(service, view.row, action="correct")
    assert (resumed.expected_revision, resumed.expected_revision_version) == ("revision", 7)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["owner", "guild", "channel", "timeout", "fetch_failure"])
async def test_callbacks_enforce_owner_guild_channel_expiry(case):
    view, service = make_view()
    inter = interaction(
        owner=11 if case == "owner" else 10,
        guild=99 if case == "guild" else 20,
        channel=99 if case == "channel" else 30,
    )
    if case == "timeout":
        view.expires_at = 0
    if case == "fetch_failure":
        inter.guild.fetch_member.side_effect = RuntimeError("member unavailable")
    assert await view.interaction_check(inter) is False
    await view.confirm_button.callback(inter)
    service.confirm.assert_not_called()
    assert inter.response.send_message.call_args.kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_callback_defers_and_confirms_exact_receipt_version():
    view, service = make_view()
    inter = interaction()
    await view.confirm_button.callback(inter)
    inter.response.defer.assert_awaited_once_with(ephemeral=True)
    assert service.confirm.call_args.args[1:] == ("receipt", 2)
    assert inter.guild.fetch_member.await_count == 1
    assert all(item.disabled for item in view.children)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["success", "expired", "other_owner", "wrong_channel"])
async def test_upload_season_modal_uses_real_acknowledgement_before_staging(case):
    import discord

    row = {"AttemptID": "receipt", "ActorID": "10", "Status": "received", "payload": {"version": 1}}
    service = SimpleNamespace(
        access=ACCESS,
        stage_upload=Mock(return_value=row),
        summary=Mock(return_value="retained for review"),
        confirm=Mock(),
        actions=lambda row, action="accept", **kw: receipt_actions(row, action, NOW, **kw),
    )
    factory = Mock(return_value=service)
    attachment = SimpleNamespace(filename="baseline.xlsx", id=42, read=AsyncMock())
    view = SourceUploadStartView(ACCESS, ADMIN, [attachment], 99, factory, season=16)
    modal = SourceUploadSeasonModal(view)
    inter = interaction(
        owner=11 if case == "other_owner" else 10, channel=99 if case == "wrong_channel" else 30
    )
    acknowledged = False

    async def defer(*, ephemeral):
        nonlocal acknowledged
        assert ephemeral is True
        factory.assert_not_called()
        attachment.read.assert_not_awaited()
        if case == "expired":
            raise discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "expired")
        acknowledged = True

    async def read():
        assert acknowledged
        return b"synthetic workbook"

    inter.response.defer.side_effect = defer
    inter.response.is_done = lambda: acknowledged
    attachment.read.side_effect = read
    await modal.callback(inter)

    service.confirm.assert_not_called()  # Staging is never acceptance.
    if case == "success":
        inter.response.defer.assert_awaited_once_with(ephemeral=True)
        factory.assert_called_once_with()
        attachment.read.assert_awaited_once_with()
        service.stage_upload.assert_called_once_with(
            ADMIN,
            filename="baseline.xlsx",
            content=b"synthetic workbook",
            message_id=99,
            attachment_id=42,
            season="16",
        )
        assert inter.followup.send.await_count == 2
        assert all(call.kwargs["ephemeral"] for call in inter.followup.send.call_args_list)
        assert all(item.disabled for item in view.children)
    else:
        factory.assert_not_called()
        attachment.read.assert_not_awaited()
        service.stage_upload.assert_not_called()
        if case != "expired":
            inter.response.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_timeout_retains_receipt_and_never_mutates_service():
    view, service = make_view()
    await view.on_timeout()
    assert all(item.disabled for item in view.children)
    service.confirm.assert_not_called()
    assert view.receipt_id == "receipt"


@pytest.mark.asyncio
async def test_modal_limits_and_no_confirmation_before_preparation():
    view, service = make_view()
    meta, config = SourceMetadataModal(view), SourceConfigurationModal(view)
    assert len(meta.children) == 5
    assert len(config.children) == 3  # Imported map/weights are displayed, not retyped.
    assert all(item.max_length <= 4000 for item in (*meta.children, *config.children))
    view.row["Status"] = "received"
    fresh = KvkSourceImportView(service, view.row)
    assert fresh.confirm_button.disabled


@pytest.mark.asyncio
async def test_roster_mode_requires_its_own_review_and_survives_resume():
    view, service = make_view("configure")
    roster = KvkSourceImportView(service, view.row, action="configure", roster_correction=True)
    assert roster.confirm_button.disabled
    inter = interaction()
    await roster.prepare_button.callback(inter)
    assert isinstance(inter.response.send_modal.call_args.args[0], SourceRosterModal)
    view.row["payload"]["proposal"]["mode"] = "roster"
    resumed = KvkSourceImportView(service, view.row, action="configure")
    assert resumed.roster_correction
    assert not resumed.confirm_button.disabled


@pytest.mark.asyncio
async def test_setup_and_pair_modals_fit_discord_limits_and_preserve_update_id():
    from tests.test_kvk_source_admin import ADMIN
    from ui.views.kvk_source_import_view import (
        SourceChoiceModal,
        SourceConfigurationReviewModal,
        SourcePairModal,
    )

    service = SimpleNamespace(access=ACCESS)
    pair = SourcePairModal(service, ADMIN, 16, update_id="waiting-update")
    assert pair.update_id == "waiting-update"
    for modal in (
        SourceChoiceModal(service, ADMIN, 16),
        SourceConfigurationReviewModal(service, ADMIN, 16),
        pair,
    ):
        assert len(modal.children) <= 5
        assert all(len(item.label) <= 45 for item in modal.children)


@pytest.mark.asyncio
@pytest.mark.parametrize("deferred", [False, True])
@pytest.mark.parametrize("controls", [False, True])
@pytest.mark.parametrize("multipage", [False, True])
async def test_receipt_omits_absent_views_in_initial_and_followup_messages(
    deferred, controls, multipage
):
    import discord

    inter = interaction()
    done = deferred
    sent = []

    async def send(content, **kwargs):
        nonlocal done
        # Real Pycord's ephemeral webhook path dereferences explicit None.
        if "view" in kwargs:
            assert kwargs["view"] is not None
            assert kwargs["view"].timeout is not None
        assert kwargs["ephemeral"] is True
        assert kwargs["allowed_mentions"].to_dict()["parse"] == []
        sent.append((content, kwargs))
        done = True

    inter.response.is_done = lambda: done
    inter.response.send_message.side_effect = send
    inter.followup.send.side_effect = send
    view = discord.ui.View(timeout=300) if controls else None
    summary = "first line\n" + "x" * 1795 if multipage else "short receipt"
    service = SimpleNamespace(summary=lambda row: summary)
    assert await send_receipt(inter, service, {"AttemptID": "id"}, view)
    assert "\n".join(content for content, _ in sent) == summary
    assert len(sent) == (2 if multipage else 1)
    assert all("view" not in kwargs for _, kwargs in sent[:-1])
    assert ("view" in sent[-1][1]) is controls
    assert inter.response.send_message.await_count == (0 if deferred else 1)


@pytest.mark.asyncio
async def test_cancel_commit_survives_failed_delivery_and_controls_retire(caplog):
    from copy import deepcopy

    view, service = make_view()
    cancelled = deepcopy(view.row)
    cancelled["payload"].update(version=3, cancelled=True)
    cancelled["cancel_saved"] = True
    service.cancel = Mock(return_value=cancelled)
    inter = interaction()
    inter.response.is_done = lambda: inter.response.defer.await_count > 0
    inter.followup.send.side_effect = [RuntimeError("private SQL/password text"), None]
    await view.cancel_button.callback(inter)
    service.cancel.assert_called_once_with(ADMIN, "receipt", 2)
    assert all(item.disabled for item in view.children)
    fallback = inter.followup.send.call_args.args[0]
    assert "Action retained; receipt delivery failed" in fallback
    assert "action:resume receipt:receipt" in fallback
    assert "could not complete" not in fallback
    assert "private SQL/password text" not in caplog.text
    assert "version=3 saved=True" in caplog.text


@pytest.mark.asyncio
async def test_summary_failure_after_save_is_a_delivery_failure():
    inter = interaction()
    service = SimpleNamespace(summary=Mock(side_effect=RuntimeError("private")))
    assert not await send_receipt(inter, service, {"AttemptID": "id"}, saved=True)
    assert "Action retained" in inter.response.send_message.call_args.args[0]


@pytest.mark.asyncio
async def test_uncertain_commit_reports_inspection_not_failure_or_retry():
    from kvk.dal.new_source_import_dal import UncertainCommit

    view, service = make_view()
    service.cancel = Mock(side_effect=UncertainCommit("private"))
    inter = interaction()
    inter.response.is_done = lambda: inter.response.defer.await_count > 0
    await view.cancel_button.callback(inter)
    service.cancel.assert_called_once()
    message = inter.followup.send.call_args.args[0]
    assert "commit outcome is uncertain" in message
    assert "Do not repeat the mutation" in message
    assert "Action retained" not in message and "private" not in message


@pytest.mark.asyncio
async def test_delivery_preserves_cooperative_cancellation():
    import asyncio

    inter = interaction()
    inter.response.send_message.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await send_receipt(inter, SimpleNamespace(summary=lambda row: "receipt"), {})
    inter.followup.send.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["accepted", "cancelled", "expired"])
async def test_resumed_receipt_controls_reflect_durable_state(state):
    from tests.test_kvk_source_receipt_state import receipt

    _, service = make_view()
    row = receipt(
        "accepted" if state == "accepted" else "validated", cancelled=state == "cancelled"
    )
    if state == "expired":
        row["payload"]["proposal"]["expires"] = NOW.isoformat()
    view = KvkSourceImportView(service, row)
    assert view.confirm_button.disabled
    assert view.prepare_button.disabled is (state != "expired")
    assert view.cancel_button.disabled is (state != "expired")
    assert view.pair_button.disabled is (state != "accepted")


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["pending", "completed", "cancelled", "expired"])
async def test_review_controls_are_terminal_or_expiry_aware(state):
    from datetime import timedelta

    row = {
        "ReviewState": "pending" if state == "expired" else state,
        "ExpiresUTC": NOW + timedelta(seconds=-1 if state == "expired" else 60),
    }
    view = SourceReviewView(SimpleNamespace(now=lambda: NOW), row)
    assert view.confirm.disabled is (state != "pending")
    assert view.cancel.disabled is (state not in ("pending", "expired"))


@pytest.mark.asyncio
async def test_stale_prepare_button_rechecks_service_before_opening_modal():
    from kvk.dal.new_source_import_dal import SourceConflict

    view, service = make_view()
    service.check_receipt_action.side_effect = SourceConflict("Receipt changed; resume.")
    inter = interaction()
    await view.prepare_button.callback(inter)
    inter.response.send_modal.assert_not_awaited()
    service.check_receipt_action.assert_called_once_with(ADMIN, "receipt", 2, "accept", "prepare")


@pytest.mark.asyncio
async def test_stale_receipt_origin_pair_modal_cannot_prepare_review():
    from kvk.dal.new_source_import_dal import SourceConflict

    origin, source_service = make_view()
    source_service.check_receipt_action.side_effect = SourceConflict("Receipt changed; resume.")
    review_service = SimpleNamespace(access=ACCESS, prepare_match=Mock())
    modal = SourcePairModal(review_service, ADMIN, 16, receipt_origin=origin)
    modal.scope.value = "16 | fight:pass4 | 6 | publish"
    modal.coverage.value = "2026-09-01T00:00Z | 2026-09-02T00:00Z | 2026-09-02T00:00Z"
    await modal.callback(interaction())
    review_service.prepare_match.assert_not_called()


@pytest.mark.asyncio
async def test_export_preview_delivery_failure_has_no_fake_receipt_identity():
    inter = interaction()
    inter.response.send_message.side_effect = [RuntimeError("send failed"), None]
    service = SimpleNamespace(summary=lambda row: "preview")
    assert not await send_receipt(inter, service, SimpleNamespace(token="preview"))
    message = inter.response.send_message.call_args.args[0]
    assert "Preview token:preview" in message
    assert "process-local" in message and "no export action was confirmed" in message
    assert "review:None" not in message and "action:resume" not in message
    assert "Action retained" not in message


@pytest.mark.asyncio
async def test_receipt_uses_real_pycord_webhook_without_network(monkeypatch):
    import discord
    from discord.webhook.async_ import async_context

    adapter = SimpleNamespace(execute_webhook=AsyncMock(return_value={}))
    webhook = discord.Webhook(
        {"id": "1", "type": discord.WebhookType.application.value, "token": "synthetic-test-token"},
        session=None,
        state=SimpleNamespace(allowed_mentions=None),
    )
    # Keep the library's complete webhook state; replace only the network response boundary.
    monkeypatch.setattr(discord.Webhook, "_create_message", lambda self, data: None)
    token = async_context.set(adapter)
    try:
        inter = interaction()
        inter.response.is_done = lambda: True
        inter.followup = webhook
        service = SimpleNamespace(summary=lambda row: "first\n" + "x" * 1798)
        assert await send_receipt(inter, service, {"AttemptID": "id"}, discord.ui.View(timeout=300))
        assert adapter.execute_webhook.await_count == 2
        payloads = [call.kwargs["payload"] for call in adapter.execute_webhook.call_args_list]
        assert "components" not in payloads[0]
        assert all(payload["flags"] & 64 for payload in payloads)
    finally:
        async_context.reset(token)


@pytest.mark.asyncio
async def test_cancel_does_not_mutate_when_acknowledgement_fails():
    view, service = make_view()
    service.cancel = Mock()
    inter = interaction()
    inter.response.defer.side_effect = RuntimeError("expired")
    await view.cancel_button.callback(inter)
    service.cancel.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("family", ["receipt", "review"])
@pytest.mark.parametrize("changed", [False, True])
async def test_cancel_delivery_reports_actual_write_for_both_view_families(family, changed):
    from datetime import timedelta

    if family == "receipt":
        view, service = make_view()
        row = dict(view.row, cancel_saved=changed)
        callback = view.cancel_button.callback
    else:
        row = dict(
            ReviewID="review",
            ActorID="10",
            GuildID="20",
            ChannelID="30",
            ReviewState="pending",
            Version=1,
            ExpiresUTC=NOW + timedelta(minutes=5),
        )
        service = SimpleNamespace(access=ACCESS, now=lambda: NOW, summary=lambda row: "receipt")
        view = SourceReviewView(service, row)
        row = dict(row, ReviewState="cancelled", Version=2, cancel_saved=changed)
        callback = view.cancel.callback
    service.cancel = Mock(return_value=row)
    inter = interaction()
    inter.response.is_done = lambda: inter.response.defer.await_count > 0
    inter.followup.send.side_effect = [RuntimeError("private failure"), None]
    await callback(inter)
    service.cancel.assert_called_once()
    message = inter.followup.send.call_args.args[0]
    assert ("Action retained" in message) is changed
    assert "receipt delivery failed" in message.lower()
    assert "private failure" not in message
    assert all(item.disabled for item in view.children)


@pytest.mark.asyncio
@pytest.mark.parametrize("family", ["player", "aggregate"])
@pytest.mark.parametrize("later", ["cancelled", "completed", "legacy_cancelled"])
async def test_pair_modal_prefills_one_retained_acceptance_not_later_proposal(
    monkeypatch, family, later
):
    from tests.test_kvk_source_receipt_state import DurableReceipt, receipt

    original = receipt("accepted")
    outcome = dict(state="accepted", scan_id=6)
    outcome["observation_revision_id" if family == "player" else "aggregate_revision_id"] = (
        "accepted-revision"
    )
    original["payload"]["outcome"] = outcome
    original["payload"]["proposal"]["candidate"] = dict(
        period_key="fight:accepted",
        coverage_start_utc="2026-09-01T00:00:00Z",
        coverage_end_utc="2026-09-02T00:00:00Z",
        as_of_utc="2026-09-02T01:00:00Z",
    )
    if family == "aggregate":
        original.update(ObservationRevisionID=None, AggregateRevisionID="accepted-revision")
    store = DurableReceipt(monkeypatch, original)
    store.prepare("correct")
    store.row["payload"]["proposal"]["candidate"] = dict(
        period_key="fight:unaccepted",
        coverage_start_utc="bad",
        coverage_end_utc="bad",
        as_of_utc="bad",
    )
    if later == "cancelled":
        row = store.cancel(3)
    else:
        row = store.row
        row["payload"]["proposal"]["action"] = "configure"
        row["payload"]["outcome"] = dict(
            state="configuration requested", observation_revision_id="accepted-revision"
        )
        if later == "legacy_cancelled":
            row["payload"]["cancelled"] = True
            row["payload"]["history"].append(
                dict(action="cancel", version=3, outcome=dict(row["payload"]["outcome"]))
            )
    modal = SourcePairModal(SimpleNamespace(access=ACCESS), ADMIN, 16, receipt=row)
    assert modal.scope.value == "16 | fight:accepted | 6 | publish"
    assert modal.aggregate.value == ("accepted-revision" if family == "aggregate" else "")
    assert (
        modal.coverage.value == "2026-09-01T00:00:00Z | 2026-09-02T00:00:00Z | 2026-09-02T01:00:00Z"
    )
