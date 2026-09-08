from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from stats_alerts.diagnostic_sessions import SessionRepository
from ui.views import prekvk_dispatch_diagnostic_view as views


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["allowed", "owner", "guild", "channel", "stale", "error"])
async def test_callback_is_private_scoped_and_mention_neutral(tmp_path, monkeypatch, case):
    monkeypatch.setattr(views, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(views, "GUILD_ID", 10)
    session = SessionRepository(tmp_path / "diagnostics").open(10, 20, 30)
    session.store.message_state.update_prekvk_message(101)
    before = {str(p): p.read_bytes() for p in session.path.iterdir() if p.is_file()}
    view = views.PreKvkDispatchDiagnosticView([], session)
    response = SimpleNamespace(
        defer=AsyncMock(),
        is_done=lambda: case not in {"owner", "guild", "channel"},
        send_message=AsyncMock(),
    )
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=31 if case == "owner" else 30),
        guild_id=11 if case == "guild" else 10,
        channel_id=21 if case == "channel" else 20,
        message=SimpleNamespace(id=102 if case == "stale" else 101),
        channel=SimpleNamespace(
            permissions_for=lambda user: SimpleNamespace(view_channel=True, send_messages=True)
        ),
        response=response,
        followup=SimpleNamespace(send=AsyncMock()),
    )
    if case == "error":
        view.build_local_time_embed = AsyncMock(side_effect=ValueError("render"))
    await view.show_local_time(interaction)
    calls = response.send_message.call_args_list + interaction.followup.send.call_args_list
    assert len(calls) == 1
    assert calls[0].kwargs["ephemeral"] is True
    assert calls[0].kwargs["allowed_mentions"].to_dict() == {"parse": []}
    assert {str(p): p.read_bytes() for p in session.path.iterdir() if p.is_file()} == before
    assert view.children[0].custom_id == f"prekvk_diag_{session.token}_local_time"


@pytest.mark.asyncio
async def test_reopen_has_same_component_identity(tmp_path):
    repo = SessionRepository(tmp_path / "sessions")
    session = repo.open(10, 20, 30)
    before = views.PreKvkDispatchDiagnosticView([], session)
    after = views.PreKvkDispatchDiagnosticView([], repo.open(10, 20, 30, session.token))
    assert before.children[0].custom_id == after.children[0].custom_id


@pytest.mark.asyncio
@pytest.mark.parametrize("revoked", ["view_channel", "send_messages"])
async def test_revoked_destination_permission_denies_before_render(tmp_path, monkeypatch, revoked):
    monkeypatch.setattr(views, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(views, "GUILD_ID", 10)
    session = SessionRepository(tmp_path / "diagnostics").open(10, 20, 30)
    view = views.PreKvkDispatchDiagnosticView([], session)
    view.build_local_time_embed = AsyncMock()
    permissions = SimpleNamespace(view_channel=True, send_messages=True)
    setattr(permissions, revoked, False)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=30),
        guild_id=10,
        channel_id=20,
        channel=SimpleNamespace(permissions_for=lambda user: permissions),
        response=SimpleNamespace(is_done=lambda: False, send_message=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()),
    )
    await view.show_local_time(interaction)
    interaction.response.send_message.assert_awaited_once()
    call = interaction.response.send_message.call_args
    assert "no longer have access" in call.args[0]
    assert call.kwargs["ephemeral"] is True
    assert call.kwargs["allowed_mentions"].to_dict() == {"parse": []}
    assert "embed" not in call.kwargs
    view.build_local_time_embed.assert_not_awaited()
    interaction.followup.send.assert_not_awaited()
