from __future__ import annotations

import pytest

from ui.views.ark_reminder_prefs_view import ArkReminderPrefsView


class DummyResponse:
    def __init__(self) -> None:
        self.sent = []
        self.edits = []

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral, **kwargs})

    async def edit_message(self, content=None, view=None, **kwargs):
        self.edits.append({"content": content, "view": view, **kwargs})


class DummyUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class DummyInteraction:
    def __init__(self, user_id: int):
        self.user = DummyUser(user_id)
        self.response = DummyResponse()


@pytest.mark.asyncio
async def test_view_rejects_other_user():
    view = ArkReminderPrefsView(author_id=100)
    interaction = DummyInteraction(user_id=200)

    ok = await view._guard(interaction)
    assert ok is False
    assert interaction.response.sent
    assert "not for you" in interaction.response.sent[0]["content"].lower()


@pytest.mark.asyncio
async def test_toggle_updates_pref(monkeypatch):
    view = ArkReminderPrefsView(author_id=100)
    interaction = DummyInteraction(user_id=100)

    async def _get(_uid):
        return {
            "OptOutAll": 0,
            "OptOut24h": 0,
            "OptOut4h": 0,
            "OptOut1h": 0,
            "OptOutStart": 0,
            "OptOutCheckIn12h": 0,
        }

    captured = {}

    async def _upsert(uid, **kwargs):
        captured["uid"] = uid
        captured["kwargs"] = kwargs
        return True

    monkeypatch.setattr("ui.views.ark_reminder_prefs_view.get_reminder_prefs", _get)
    monkeypatch.setattr("ui.views.ark_reminder_prefs_view.upsert_reminder_prefs", _upsert)

    await view._toggle(interaction, "OptOut24h")

    assert captured["uid"] == 100
    assert captured["kwargs"]["opt_out_24h"] == 1
    assert interaction.response.edits
