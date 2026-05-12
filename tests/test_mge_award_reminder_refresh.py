from __future__ import annotations

from types import SimpleNamespace

import pytest

from mge import mge_publish_service


def _ctx(**overrides):
    base = {
        "EventId": 10,
        "EventName": "MGE Test",
        "VariantName": "Infantry",
        "RuleMode": "fixed",
        "Status": "published",
        "PublishVersion": 1,
        "AwardRemindersText": "old reminders",
        "AwardRemindersSentUtc": "2026-05-01T00:00:00",
        "AwardRemindersMessageId": 111,
        "AwardRemindersChannelId": 999,
        "AwardEmbedChannelId": 999,
    }
    base.update(overrides)
    return base


class _Message:
    def __init__(self, message_id: int = 111) -> None:
        self.id = message_id
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


class _Channel:
    id = 999

    def __init__(self, *, message: _Message | None = None, missing: bool = False) -> None:
        self.message = message or _Message()
        self.missing = missing
        self.sent = []

    async def fetch_message(self, message_id: int):
        if self.missing:
            raise mge_publish_service.discord.NotFound()
        return self.message

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        return _Message(222)


@pytest.mark.asyncio
async def test_refresh_updates_existing_reminder_message(monkeypatch):
    channel = _Channel()
    updates = []
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_default_award_reminders_text",
        lambda mode: "latest reminders",
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "update_event_award_reminders_text",
        lambda **kwargs: updates.append(kwargs) or True,
    )
    bot = SimpleNamespace(get_channel=lambda _cid: channel, fetch_channel=lambda _cid: channel)

    result = await mge_publish_service.refresh_award_reminders(
        bot=bot,
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.updated_existing is True
    assert channel.sent == []
    assert channel.message.edits
    assert updates[0]["reminders_text"] == "latest reminders"


@pytest.mark.asyncio
async def test_refresh_reposts_missing_message_and_persists_ids(monkeypatch):
    class _NotFound(Exception):
        pass

    channel = _Channel(missing=True)
    ids = {}
    monkeypatch.setattr(mge_publish_service.discord, "NotFound", _NotFound)
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_default_award_reminders_text",
        lambda mode: "latest reminders",
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "update_event_award_reminders_text",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "update_award_reminder_message_ids",
        lambda **kwargs: ids.update(kwargs) or True,
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "mark_award_reminders_sent",
        lambda **kwargs: True,
    )
    bot = SimpleNamespace(get_channel=lambda _cid: channel, fetch_channel=lambda _cid: channel)

    result = await mge_publish_service.refresh_award_reminders(
        bot=bot,
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.reposted_missing is True
    assert len(channel.sent) == 1
    assert ids["message_id"] == 222
    assert ids["channel_id"] == 999


@pytest.mark.asyncio
async def test_refresh_does_not_duplicate_when_message_exists(monkeypatch):
    channel = _Channel()
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(AwardRemindersText="latest reminders"),
    )
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_default_award_reminders_text",
        lambda mode: "latest reminders",
    )
    bot = SimpleNamespace(get_channel=lambda _cid: channel, fetch_channel=lambda _cid: channel)

    result = await mge_publish_service.refresh_award_reminders(
        bot=bot,
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.status == "updated"
    assert channel.sent == []


@pytest.mark.asyncio
async def test_refresh_refuses_when_awards_not_published(monkeypatch):
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(PublishVersion=0),
    )
    bot = SimpleNamespace(get_channel=lambda _cid: None, fetch_channel=lambda _cid: None)

    result = await mge_publish_service.refresh_award_reminders(
        bot=bot,
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is False
    assert result.skipped_no_awards is True
    assert result.status == "no_awards_published"


def test_refresh_award_reminders_command_uses_admin_decorator():
    import inspect

    from commands import mge_cmds

    source = inspect.getsource(mge_cmds.register_mge)
    assert 'name="mge_refresh_award_reminders"' in source
    assert "@is_admin_and_notify_channel(allow_leadership=True)" in source
