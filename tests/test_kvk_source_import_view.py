from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from tests.test_kvk_source_admin import ACCESS
from ui.views.kvk_source_import_view import (
    KvkSourceImportView,
    SourceConfigurationModal,
    SourceMetadataModal,
    SourceRosterModal,
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
async def test_callback_defers_and_confirms_exact_receipt_version(monkeypatch):
    import ui.views.kvk_source_import_view as module

    view, service = make_view()
    inter = interaction()
    monkeypatch.setattr(module, "safe_defer", AsyncMock(return_value=True))
    await view.confirm_button.callback(inter)
    assert service.confirm.call_args.args[1:] == ("receipt", 2)
    assert inter.guild.fetch_member.await_count == 1
    assert all(item.disabled for item in view.children)


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
    assert len(meta.children) == len(config.children) == 5
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
