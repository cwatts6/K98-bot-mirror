from __future__ import annotations

import logging

import discord
import pytest

from ark.registration_messages import (
    upsert_registration_message,
    upsert_registration_message_result,
)
from ark.state.ark_state import ArkJsonState
from core.discord_embed_limits import EmbedPayloadLimitError


class _Msg:
    def __init__(self, mid=1, cid=10):
        self.id = mid
        self.channel = type("C", (), {"id": cid})()

    async def edit(self, **kwargs):
        return None


class _Chan:
    id = 10

    async def fetch_message(self, _):
        return _Msg()

    async def send(self, **kwargs):
        self.last_kwargs = kwargs
        return _Msg()


class _Client:
    def get_channel(self, _):
        return _Chan()


@pytest.mark.asyncio
async def test_upsert_registration_no_everyone_by_default(monkeypatch):
    async def _get_match(_match_id):
        return None

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)

    state = ArkJsonState()
    client = _Client()
    moved, changed = await upsert_registration_message(
        client=client,
        state=state,
        match_id=1,
        embed=None,
        view=None,
        target_channel_id=10,
    )
    assert moved is True
    assert changed is True


@pytest.mark.asyncio
async def test_upsert_registration_with_announce_sets_everyone(monkeypatch):
    async def _get_match(_match_id):
        return None

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)

    state = ArkJsonState()
    channel = _Chan()

    class _Client2:
        def get_channel(self, _):
            return channel

    moved, changed = await upsert_registration_message(
        client=_Client2(),
        state=state,
        match_id=2,
        embed=None,
        view=None,
        target_channel_id=10,
        announce=True,
    )
    assert moved is True
    assert changed is True
    assert channel.last_kwargs["content"] == "@everyone"


@pytest.mark.asyncio
async def test_upsert_registration_validates_before_discord_delivery(monkeypatch):
    async def _get_match(_match_id):
        return None

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)
    invalid = discord.Embed(title="X" * 257)

    with pytest.raises(EmbedPayloadLimitError):
        await upsert_registration_message(
            client=_Client(),
            state=ArkJsonState(),
            match_id=3,
            embed=invalid,
            view=None,
            target_channel_id=10,
        )


@pytest.mark.asyncio
async def test_upsert_registration_reports_missing_destination(monkeypatch):
    async def _get_match(_match_id):
        return None

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)

    result = await upsert_registration_message_result(
        client=_Client(),
        state=ArkJsonState(),
        match_id=4,
        embed=None,
        view=None,
    )

    assert result.outcome == "failed"
    assert result.failure_reason == "missing_destination"
    assert result.state_changed is False


@pytest.mark.asyncio
async def test_upsert_registration_reports_unavailable_channel(monkeypatch):
    async def _get_match(_match_id):
        return None

    class _MissingChannelClient:
        def get_channel(self, _channel_id):
            return None

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)

    result = await upsert_registration_message_result(
        client=_MissingChannelClient(),
        state=ArkJsonState(),
        match_id=5,
        embed=None,
        view=None,
        target_channel_id=10,
    )

    assert result.outcome == "failed"
    assert result.failure_reason == "channel_unavailable"
    assert result.state_changed is False


@pytest.mark.asyncio
async def test_upsert_registration_logs_send_failure_and_preserves_exception(monkeypatch, caplog):
    async def _get_match(_match_id):
        return None

    class _FailingChannel:
        id = 10

        async def send(self, **_kwargs):
            raise RuntimeError("send failed")

    class _FailingClient:
        def get_channel(self, _channel_id):
            return _FailingChannel()

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)
    caplog.set_level(logging.ERROR, logger="ark.registration_messages")

    with pytest.raises(RuntimeError, match="send failed"):
        await upsert_registration_message_result(
            client=_FailingClient(),
            state=ArkJsonState(),
            match_id=6,
            embed=None,
            view=None,
            target_channel_id=10,
        )

    assert "delivery_outcome=failed" in caplog.text
    assert "failure_reason=send_failed" in caplog.text
