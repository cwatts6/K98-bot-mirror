from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from tests.test_kvk_source_admin import ACCESS, ADMIN
from ui.views.kvk_source_import_view import (
    KvkSourceImportView,
    SourceConfigurationModal,
    SourceMetadataModal,
    SourceRosterModal,
    SourceUploadSeasonModal,
    SourceUploadStartView,
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
        "payload": {"version": 2, "proposal": {"action": action, "candidate": {}}},
    }
    service = SimpleNamespace(
        access=ACCESS,
        confirm=Mock(return_value=row),
        summary=lambda row: "accepted; not published",
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
