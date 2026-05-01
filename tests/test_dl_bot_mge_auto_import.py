from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class _FakeAttachment:
    def __init__(self, filename: str, payload: bytes):
        self.filename = filename
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class _FakeAuthor:
    def __init__(self, user_id: int, name: str = "tester"):
        self.id = user_id
        self.name = name
        self.bot = False

    def __str__(self) -> str:
        return self.name


class _FakeChannel:
    def __init__(self, channel_id: int, name: str = "mge-data"):
        self.id = channel_id
        self.name = name


class _FakeMessage:
    def __init__(self, channel_id: int, attachments):
        self.channel = _FakeChannel(channel_id)
        self.author = _FakeAuthor(123456789, "uploader")
        self.attachments = attachments
        self.content = ""
        self.guild = object()
        self.id = 111
        self.created_at = None


@pytest.mark.asyncio
async def test_mge_auto_import_success(monkeypatch):
    monkeypatch.setenv("WATCHDOG_RUN", "1")
    import DL_bot

    mge_channel_id = 999001
    monkeypatch.setattr(DL_bot, "MGE_DATA_CHANNEL_ID", mge_channel_id, raising=True)
    monkeypatch.setattr(DL_bot, "_get_notify_channel", AsyncMock(return_value=None), raising=True)

    sent = []

    async def _fake_send_embed(ch, title, fields, color, mention=None):
        sent.append((title, fields))

    async def _fake_offload(*args, **kwargs):
        return {
            "event_id": 42,
            "event_mode": "open",
            "rows": 3,
            "import_id": 77,
            "report": {"type": "open_top15"},
        }

    monkeypatch.setattr(DL_bot, "send_embed", _fake_send_embed, raising=True)
    monkeypatch.setattr(DL_bot, "_offload_callable", _fake_offload, raising=True)
    monkeypatch.setattr(
        DL_bot, "ensure_sql_headroom_or_notify", AsyncMock(return_value=True), raising=True
    )
    monkeypatch.setattr(
        type(DL_bot.bot),
        "user",
        property(lambda self: SimpleNamespace(id=987654321)),
        raising=True,
    )

    msg = _FakeMessage(
        mge_channel_id,
        [_FakeAttachment("mge_rankings_kd1198_20260311.xlsx", b"xlsx-bytes")],
    )

    await DL_bot.on_message(msg)
    assert sent
    assert sent[-1][0] == "MGE Results Import ✅"


@pytest.mark.asyncio
async def test_mge_auto_import_duplicate_rejected(monkeypatch):
    monkeypatch.setenv("WATCHDOG_RUN", "1")
    import DL_bot

    mge_channel_id = 999002
    monkeypatch.setattr(DL_bot, "MGE_DATA_CHANNEL_ID", mge_channel_id, raising=True)
    monkeypatch.setattr(DL_bot, "_get_notify_channel", AsyncMock(return_value=None), raising=True)

    sent = []

    async def _fake_send_embed(ch, title, fields, color, mention=None):
        sent.append((title, fields))

    async def _fake_offload(*args, **kwargs):
        raise ValueError(
            "Duplicate import rejected: this event already has a completed import (auto mode)."
        )

    monkeypatch.setattr(DL_bot, "send_embed", _fake_send_embed, raising=True)
    monkeypatch.setattr(DL_bot, "_offload_callable", _fake_offload, raising=True)
    monkeypatch.setattr(
        DL_bot, "ensure_sql_headroom_or_notify", AsyncMock(return_value=True), raising=True
    )
    monkeypatch.setattr(
        type(DL_bot.bot),
        "user",
        property(lambda self: SimpleNamespace(id=987654321)),
        raising=True,
    )

    msg = _FakeMessage(
        mge_channel_id,
        [_FakeAttachment("mge_rankings_kd1198_20260311.xlsx", b"xlsx-bytes")],
    )

    await DL_bot.on_message(msg)
    assert sent
    assert sent[-1][0] == "MGE Results Import ❌"
