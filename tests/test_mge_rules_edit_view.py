from __future__ import annotations

import types

import pytest

from ui.views.mge_rules_edit_view import MgeRulesEditView


class _DummyClient:
    pass


class _DummyUser:
    def __init__(self, uid: int):
        self.id = uid


class _DummyResponse:
    def __init__(self):
        self.modal = None

    async def send_modal(self, modal):
        self.modal = modal


class _DummyInteraction:
    def __init__(self, user_id: int = 1):
        self.user = _DummyUser(user_id)
        self.client = _DummyClient()
        self.response = _DummyResponse()


@pytest.mark.asyncio
async def test_edit_button_opens_modal(monkeypatch):
    view = MgeRulesEditView(event_id=77)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )
    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.mge_rules_service.get_event_rules_context",
        lambda event_id: {"RulesText": "abc", "SignupEmbedChannelId": 999},
    )

    sent: list[str] = []

    async def _fake_send_ephemeral(interaction, message, **kwargs):
        sent.append(message)

    monkeypatch.setattr("ui.views.mge_rules_edit_view.send_ephemeral", _fake_send_ephemeral)

    interaction = _DummyInteraction()
    button = view.edit_rules_text

    await button.callback(interaction)
    assert interaction.response.modal is not None
    assert interaction.response.modal.rules_text.max_length == 1024
    assert sent == []


@pytest.mark.asyncio
async def test_reset_button_calls_service_and_reports(monkeypatch):
    view = MgeRulesEditView(event_id=55)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )

    async def _fake_refresh(bot):
        return True

    monkeypatch.setattr(view, "_refresh_signup_embed", _fake_refresh)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.mge_rules_service.reset_event_rules_to_mode_default",
        lambda event_id, actor_discord_id: types.SimpleNamespace(success=True, message="done"),
    )

    msgs: list[str] = []

    async def _fake_send_ephemeral(interaction, message, **kwargs):
        msgs.append(message)

    monkeypatch.setattr("ui.views.mge_rules_edit_view.send_ephemeral", _fake_send_ephemeral)

    interaction = _DummyInteraction(user_id=123)
    button = view.reset_to_mode_default

    await button.callback(interaction)
    assert any("✅" in m for m in msgs)


@pytest.mark.asyncio
async def test_edit_modal_submit_triggers_refresh(monkeypatch):
    view = MgeRulesEditView(event_id=88)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )
    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.mge_rules_service.get_event_rules_context",
        lambda event_id: {"RulesText": "old", "SignupEmbedChannelId": 444},
    )

    refresh_called = {"v": False}

    async def _fake_refresh(bot):
        refresh_called["v"] = True
        return True

    monkeypatch.setattr(view, "_refresh_signup_embed", _fake_refresh)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.mge_rules_service.update_event_rules_text",
        lambda event_id, new_rules_text, actor_discord_id: types.SimpleNamespace(
            success=True, message="updated"
        ),
    )

    msgs: list[str] = []

    async def _fake_send_ephemeral(interaction, message, **kwargs):
        msgs.append(message)

    monkeypatch.setattr("ui.views.mge_rules_edit_view.send_ephemeral", _fake_send_ephemeral)

    interaction = _DummyInteraction(user_id=42)

    # Open modal via button callback.
    await view.edit_rules_text.callback(interaction)
    modal = interaction.response.modal
    assert modal is not None

    # Submit modal with new rules text.
    modal.rules_text.value = "new rules body"

    modal_interaction = _DummyInteraction(user_id=42)
    await modal.callback(modal_interaction)

    assert refresh_called["v"] is True
    assert any("✅" in m for m in msgs)


@pytest.mark.asyncio
async def test_edit_modal_submit_reports_embed_limit_details(monkeypatch):
    view = MgeRulesEditView(event_id=90)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )
    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.mge_rules_service.get_event_rules_context",
        lambda event_id: {"RulesText": "old", "SignupEmbedChannelId": 444},
    )

    msgs: list[str] = []

    async def _fake_send_ephemeral(interaction, message, **kwargs):
        msgs.append(message)

    monkeypatch.setattr("ui.views.mge_rules_edit_view.send_ephemeral", _fake_send_ephemeral)

    interaction = _DummyInteraction(user_id=42)
    await view.edit_rules_text.callback(interaction)
    modal = interaction.response.modal
    assert modal is not None

    modal.rules_text.value = "x" * 1030
    await modal.callback(_DummyInteraction(user_id=42))

    assert any("actual: 1030" in m for m in msgs)
    assert any("allowed: 1024" in m for m in msgs)


@pytest.mark.asyncio
async def test_guard_blocks_non_leadership(monkeypatch):
    view = MgeRulesEditView(event_id=9)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.is_admin_or_leadership_interaction",
        lambda interaction: False,
    )

    msgs: list[str] = []

    async def _fake_send_ephemeral(interaction, message, **kwargs):
        msgs.append(message)

    monkeypatch.setattr("ui.views.mge_rules_edit_view.send_ephemeral", _fake_send_ephemeral)

    interaction = _DummyInteraction()
    allowed = await view._guard(interaction)
    assert allowed is False
    assert msgs and "Leadership/admin only" in msgs[0]


@pytest.mark.asyncio
async def test_edit_button_blocks_when_existing_rules_exceed_modal_limit(monkeypatch):
    view = MgeRulesEditView(event_id=123)

    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.is_admin_or_leadership_interaction",
        lambda interaction: True,
    )
    monkeypatch.setattr(
        "ui.views.mge_rules_edit_view.mge_rules_service.get_event_rules_context",
        lambda event_id: {"RulesText": "x" * 1025, "SignupEmbedChannelId": 999},
    )

    msgs: list[str] = []

    async def _fake_send_ephemeral(interaction, message, **kwargs):
        msgs.append(message)

    monkeypatch.setattr("ui.views.mge_rules_edit_view.send_ephemeral", _fake_send_ephemeral)

    interaction = _DummyInteraction()
    await view.edit_rules_text.callback(interaction)

    # Should block opening modal and show explicit warning.
    assert interaction.response.modal is None
    assert msgs
    assert "Current length: 1025" in msgs[0]
    assert "Allowed: 1024" in msgs[0]
