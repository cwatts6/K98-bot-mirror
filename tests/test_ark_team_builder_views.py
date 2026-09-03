from __future__ import annotations

import pytest

from ui.views.team_builder_views import ArkTeamBuilderView


class _Response:
    def __init__(self):
        self.sent = []

    async def send_message(self, content, **kwargs):
        self.sent.append({"content": content, **kwargs})


class _Interaction:
    def __init__(self, user_id: int):
        self.user = type("User", (), {"id": user_id})()
        self.response = _Response()


@pytest.mark.asyncio
async def test_team_builder_preserves_requester_ownership_and_timeout():
    view = ArkTeamBuilderView(match_id=7, actor_discord_id=33)

    assert view.timeout == 300.0
    assert await view.interaction_check(_Interaction(33)) is True


@pytest.mark.asyncio
async def test_team_builder_rejects_other_user_ephemerally(monkeypatch):
    view = ArkTeamBuilderView(match_id=7, actor_discord_id=33)
    interaction = _Interaction(44)
    monkeypatch.setattr("ui.views.team_builder_views._is_admin_or_leadership", lambda _i: False)

    assert await view.interaction_check(interaction) is False
    assert interaction.response.sent == [
        {"content": "❌ You can't use this team builder.", "ephemeral": True}
    ]


@pytest.mark.asyncio
async def test_team_builder_preserves_admin_override(monkeypatch):
    view = ArkTeamBuilderView(match_id=7, actor_discord_id=33)
    monkeypatch.setattr("ui.views.team_builder_views._is_admin_or_leadership", lambda _i: True)

    assert await view.interaction_check(_Interaction(44)) is True


@pytest.mark.asyncio
async def test_team_builder_timeout_removes_only_its_webhook():
    view = ArkTeamBuilderView(match_id=7, actor_discord_id=33)
    other_key = (8, 44)
    ArkTeamBuilderView._active_webhooks[view._registry_key] = object()
    ArkTeamBuilderView._active_webhooks[other_key] = object()

    try:
        await view.on_timeout()
        assert view._registry_key not in ArkTeamBuilderView._active_webhooks
        assert other_key in ArkTeamBuilderView._active_webhooks
    finally:
        ArkTeamBuilderView._active_webhooks.pop(other_key, None)
