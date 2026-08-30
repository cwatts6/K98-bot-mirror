from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ui.views.mge_results_overwrite_confirm_view import MgeResultsOverwriteConfirmView


class _FakeMessage:
    def __init__(self):
        self.edit = AsyncMock()


class _FakeResponse:
    def __init__(self):
        self.send_message = AsyncMock()
        self.defer = AsyncMock()


class _FakeFollowup:
    def __init__(self):
        self.send = AsyncMock()


class _FakeUser:
    def __init__(self, uid: int):
        self.id = uid


class _FakeInteraction:
    def __init__(self, uid: int):
        self.user = _FakeUser(uid)
        self.response = _FakeResponse()
        self.followup = _FakeFollowup()
        self.message = _FakeMessage()


@pytest.mark.asyncio
async def test_confirm_overwrite_runs_import(monkeypatch):
    called = {"ok": False}

    def _fake_import(content, filename, event_id, actor_discord_id, force_overwrite):
        called["ok"] = True
        assert content == b"abc"
        assert filename == "mge_rankings_kd1198_20260311.xlsx"
        assert event_id == 123
        assert actor_discord_id == 999
        assert force_overwrite is True
        return {"event_id": 123, "event_mode": "controlled", "rows": 3, "import_id": 77}

    monkeypatch.setattr(
        "ui.views.mge_results_overwrite_confirm_view.import_results_manual",
        _fake_import,
    )

    view = MgeResultsOverwriteConfirmView(
        actor_discord_id=999,
        event_id=123,
        filename="mge_rankings_kd1198_20260311.xlsx",
        file_bytes=b"abc",
    )
    interaction = _FakeInteraction(uid=999)

    # call callback directly
    btn = next(
        b for b in view.children if getattr(b, "custom_id", "") == "mge_results_confirm_overwrite"
    )
    await btn.callback(interaction)

    assert called["ok"] is True
    interaction.response.defer.assert_awaited()
    interaction.followup.send.assert_awaited()


@pytest.mark.asyncio
async def test_cancel_overwrite_no_import(monkeypatch):
    # if import gets called, fail test
    def _should_not_call(*args, **kwargs):
        raise AssertionError("import_results_manual should not be called on cancel")

    monkeypatch.setattr(
        "ui.views.mge_results_overwrite_confirm_view.import_results_manual",
        _should_not_call,
    )

    view = MgeResultsOverwriteConfirmView(
        actor_discord_id=999,
        event_id=123,
        filename="mge_rankings_kd1198_20260311.xlsx",
        file_bytes=b"abc",
    )
    interaction = _FakeInteraction(uid=999)

    btn = next(
        b for b in view.children if getattr(b, "custom_id", "") == "mge_results_cancel_overwrite"
    )
    await btn.callback(interaction)

    interaction.response.send_message.assert_awaited()
