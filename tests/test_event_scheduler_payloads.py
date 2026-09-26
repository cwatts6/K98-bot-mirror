from datetime import UTC, datetime, timedelta

import pytest

from core.discord_embed_limits import (
    MAX_DESCRIPTION_CHARACTERS,
    MAX_TITLE_CHARACTERS,
    validate_embed_payload,
)
import event_scheduler as mod


def _event(**overrides):
    event = {
        "name": "Altar Fight",
        "type": "altars",
        "start_time": datetime.now(UTC) + timedelta(hours=1),
    }
    event.update(overrides)
    return event


def test_public_reminder_embed_compacts_pathological_event_name(monkeypatch):
    monkeypatch.setattr(mod.random, "choice", lambda values: values[0])
    event = _event(name="N" * 1000)

    embed = mod.build_public_reminder_embed(
        event,
        timedelta(hours=1),
        starts_now=False,
        add_public_quote=True,
    )

    assert len(embed.title) == MAX_TITLE_CHARACTERS
    assert embed.title.endswith("…")
    assert "Starts <t:" in embed.description
    assert not validate_embed_payload(embed)


def test_legacy_dm_embed_bounds_personalized_pathological_segments():
    embed = mod.build_user_reminder_embed(
        event=_event(name="N" * 1000),
        discord_name="D" * 5000,
        main_governor="G" * 5000,
        quote="Q" * 9000,
    )

    assert len(embed.title) == MAX_TITLE_CHARACTERS
    assert len(embed.description) <= MAX_DESCRIPTION_CHARACTERS
    assert "Starts <t:" in embed.description
    assert not validate_embed_payload(embed)


@pytest.mark.asyncio
async def test_public_reminder_route_keeps_everyone_mention_and_valid_view(monkeypatch):
    now = datetime.now(UTC)
    event = _event(start_time=now)

    class Message:
        id = 123

    class Channel:
        def __init__(self):
            self.payload = None

        async def send(self, **kwargs):
            self.payload = kwargs
            return Message()

    class Bot:
        def __init__(self, channel):
            self.channel = channel

        def get_channel(self, _channel_id):
            return self.channel

    channel = Channel()
    monkeypatch.setattr(mod, "utcnow", lambda: now)
    monkeypatch.setattr(mod, "save_active_reminders", lambda: None)
    monkeypatch.setattr(mod.random, "choice", lambda values: values[0])
    mod.active_reminders.clear()

    await mod.send_reminder_at(Bot(channel), 42, event, timedelta(0))

    assert channel.payload["content"] == "@everyone"
    assert channel.payload["view"].complete_event_packing is True
    assert not validate_embed_payload(channel.payload["embed"])
