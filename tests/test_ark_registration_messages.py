from __future__ import annotations

import pytest

from ark.registration_messages import upsert_registration_message
from ark.state.ark_state import ArkJsonState


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
