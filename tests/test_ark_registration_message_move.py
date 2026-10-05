from __future__ import annotations

import pytest

from ark.registration_messages import (
    upsert_registration_message,
    upsert_registration_message_result,
)
from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState


class DummyMessage:
    def __init__(self, message_id: int, channel):
        self.id = message_id
        self.channel = channel
        self.deleted = False
        self.edits = []
        self.raise_not_found = False

    async def delete(self):
        self.deleted = True

    async def edit(self, *, embed=None, view=None, content=None, allowed_mentions=None):
        if self.raise_not_found:
            raise self.raise_not_found
        self.edits.append((embed, view))


class DummyChannel:
    def __init__(self, channel_id):
        self.id = channel_id
        self.messages = {}
        self.sent = []

    async def fetch_message(self, message_id):
        return self.messages[message_id]

    async def send(self, embed=None, view=None, content=None, allowed_mentions=None, **kwargs):
        mid = max(self.messages.keys(), default=100) + 1
        msg = DummyMessage(mid, channel=self)
        self.messages[mid] = msg
        self.sent.append(
            {
                "content": content,
                "embed": embed,
                "view": view,
                "allowed_mentions": allowed_mentions,
                **kwargs,
            }
        )
        return msg


class DummyClient:
    def __init__(self, channels):
        self.channels = {c.id: c for c in channels}

    def get_channel(self, channel_id: int):
        return self.channels.get(channel_id)


@pytest.mark.asyncio
async def test_upsert_registration_message_moves_channel():
    state = ArkJsonState()
    state.messages[1] = ArkMessageState(registration=ArkMessageRef(channel_id=1, message_id=10))

    channel_old = DummyChannel(1)
    channel_new = DummyChannel(2)

    channel_old.messages[10] = DummyMessage(10, channel=channel_old)

    client = DummyClient([channel_old, channel_new])

    result = await upsert_registration_message_result(
        client=client,
        state=state,
        match_id=1,
        embed=object(),
        view=object(),
        target_channel_id=2,
    )

    assert result.outcome == "moved"
    assert result.succeeded is True
    assert result.state_changed is True
    assert channel_old.messages[10].deleted is True
    assert state.messages[1].registration.channel_id == 2


@pytest.mark.asyncio
async def test_upsert_registration_message_same_channel_edit():
    state = ArkJsonState()
    state.messages[2] = ArkMessageState(registration=ArkMessageRef(channel_id=5, message_id=55))

    channel = DummyChannel(5)
    channel.messages[55] = DummyMessage(55, channel=channel)

    client = DummyClient([channel])

    result = await upsert_registration_message_result(
        client=client,
        state=state,
        match_id=2,
        embed="embed",
        view="view",
        target_channel_id=5,
    )

    assert result.outcome == "edited"
    assert result.state_changed is False
    assert channel.messages[55].edits


@pytest.mark.asyncio
async def test_upsert_registration_message_force_repost_same_channel():
    state = ArkJsonState()
    state.messages[3] = ArkMessageState(registration=ArkMessageRef(channel_id=7, message_id=77))

    channel = DummyChannel(7)
    channel.messages[77] = DummyMessage(77, channel=channel)
    client = DummyClient([channel])

    result = await upsert_registration_message_result(
        client=client,
        state=state,
        match_id=3,
        embed="embed",
        view="view",
        target_channel_id=7,
        force_repost=True,
    )

    assert result.outcome == "reposted"
    assert result.state_changed is True
    assert channel.messages[77].deleted is True
    assert state.messages[3].registration.message_id != 77


@pytest.mark.asyncio
async def test_upsert_registration_message_recreates_when_missing():
    class _NotFound(Exception):
        pass

    state = ArkJsonState()
    state.messages[4] = ArkMessageState(registration=ArkMessageRef(channel_id=9, message_id=99))

    channel = DummyChannel(9)
    missing = DummyMessage(99, channel=channel)
    missing.raise_not_found = _NotFound()
    channel.messages[99] = missing
    client = DummyClient([channel])

    import ark.registration_messages as reg_messages

    original_not_found = reg_messages.discord.NotFound
    reg_messages.discord.NotFound = _NotFound
    try:
        result = await upsert_registration_message_result(
            client=client,
            state=state,
            match_id=4,
            embed="embed",
            view="view",
            target_channel_id=9,
        )
    finally:
        reg_messages.discord.NotFound = original_not_found

    assert result.outcome == "recreated"
    assert result.state_changed is True
    assert state.messages[4].registration.message_id != 99


@pytest.mark.asyncio
async def test_upsert_registration_message_same_channel_edit_with_string_ids():
    state = ArkJsonState()
    state.messages[20] = ArkMessageState(
        registration=ArkMessageRef(channel_id="5", message_id="55")
    )

    channel = DummyChannel(5)
    channel.messages[55] = DummyMessage(55, channel=channel)

    client = DummyClient([channel])

    result = await upsert_registration_message_result(
        client=client,
        state=state,
        match_id=20,
        embed="embed",
        view="view",
        target_channel_id=5,
    )

    assert result.outcome == "edited"
    assert result.state_changed is False
    assert channel.messages[55].edits


@pytest.mark.asyncio
async def test_upsert_registration_message_preserves_legacy_tuple(monkeypatch):
    async def _get_match(_match_id):
        return None

    monkeypatch.setattr("ark.registration_messages.get_match", _get_match)
    state = ArkJsonState()
    channel = DummyChannel(5)
    client = DummyClient([channel])

    moved, changed = await upsert_registration_message(
        client=client,
        state=state,
        match_id=30,
        embed="embed",
        view="view",
        target_channel_id=5,
    )

    assert (moved, changed) == (True, True)


@pytest.mark.asyncio
async def test_upsert_registration_message_reports_edit_failure():
    state = ArkJsonState()
    state.messages[31] = ArkMessageState(registration=ArkMessageRef(channel_id=5, message_id=55))
    channel = DummyChannel(5)
    message = DummyMessage(55, channel=channel)
    message.raise_not_found = RuntimeError("edit failed")
    channel.messages[55] = message

    result = await upsert_registration_message_result(
        client=DummyClient([channel]),
        state=state,
        match_id=31,
        embed="embed",
        view="view",
        target_channel_id=5,
    )

    assert result.outcome == "failed"
    assert result.failure_reason == "edit_failed"
    assert result.succeeded is False
