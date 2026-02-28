from __future__ import annotations

import pytest

from ark.registration_messages import upsert_registration_message
from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState


class DummyMessage:
    def __init__(self, message_id: int, channel):
        self.id = message_id
        self.channel = channel
        self.deleted = False
        self.edits = []

    async def delete(self):
        self.deleted = True

    async def edit(self, *, embed=None, view=None):
        self.edits.append((embed, view))


class DummyChannel:
    def __init__(self, channel_id: int):
        self.id = channel_id
        self.sent = []
        self.messages = {}

    async def fetch_message(self, message_id: int):
        return self.messages[message_id]

    async def send(self, *, embed=None, view=None):
        msg = DummyMessage(message_id=1000 + len(self.sent), channel=self)
        self.sent.append((embed, view))
        self.messages[msg.id] = msg
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

    moved, changed = await upsert_registration_message(
        client=client,
        state=state,
        match_id=1,
        embed=object(),
        view=object(),
        target_channel_id=2,
    )

    assert moved is True
    assert changed is True
    assert channel_old.messages[10].deleted is True
    assert state.messages[1].registration.channel_id == 2


@pytest.mark.asyncio
async def test_upsert_registration_message_same_channel_edit():
    state = ArkJsonState()
    state.messages[2] = ArkMessageState(registration=ArkMessageRef(channel_id=5, message_id=55))

    channel = DummyChannel(5)
    channel.messages[55] = DummyMessage(55, channel=channel)

    client = DummyClient([channel])

    moved, changed = await upsert_registration_message(
        client=client,
        state=state,
        match_id=2,
        embed="embed",
        view="view",
        target_channel_id=5,
    )

    assert moved is False
    assert changed is False
    assert channel.messages[55].edits
