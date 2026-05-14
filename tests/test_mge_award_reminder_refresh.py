from __future__ import annotations

import pytest

from mge import mge_publish_service


class _MessageRef:
    def __init__(self, message_id: int, channel_id: int) -> None:
        self.message_id = int(message_id)
        self.channel_id = int(channel_id)


class _IoResult:
    def __init__(self, status: str, message_ref: _MessageRef | None = None) -> None:
        self.status = status
        self.message_ref = message_ref


class _RefreshAdapter:
    default_award_channel_id = 999

    def __init__(self, channel: _Channel | None) -> None:
        self.channel = channel

    async def send_awards_embed(self, **kwargs):
        return _IoResult("sent", _MessageRef(1, 999))

    async def send_republish_change_log(self, **kwargs):
        return _IoResult("sent")

    async def send_award_reminders_embed(self, *, channel_id: int, **kwargs):
        if self.channel is None:
            return _IoResult("channel_unavailable")
        msg = await self.channel.send(
            content="@everyone", embed=object(), allowed_mentions=object()
        )
        return _IoResult("sent", _MessageRef(msg.id, self.channel.id))

    async def update_award_reminders_embed(self, *, channel_id: int, message_id: int, **kwargs):
        if self.channel is None:
            return _IoResult("channel_unavailable")
        try:
            message = await self.channel.fetch_message(message_id)
        except Exception:
            return _IoResult("not_found")
        await message.edit(content="@everyone", embed=object(), allowed_mentions=object())
        return _IoResult("updated", _MessageRef(message_id, self.channel.id))

    async def delete_message(self, **kwargs):
        return _IoResult("deleted")

    async def refresh_boards(self, **kwargs):
        return {"public": True, "leadership": True, "awards": True}

    async def send_award_mail(self, **kwargs):
        return type("_MailResult", (), {"sent": False, "status": "skipped_no_recipient"})()


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
            raise LookupError("missing")
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

    result = await mge_publish_service.refresh_award_reminders(
        adapter=_RefreshAdapter(channel),
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.updated_existing is True
    assert channel.sent == []
    assert channel.message.edits
    assert updates == []


@pytest.mark.asyncio
async def test_refresh_reposts_missing_message_and_persists_ids(monkeypatch):
    channel = _Channel(missing=True)
    ids = {}
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
    result = await mge_publish_service.refresh_award_reminders(
        adapter=_RefreshAdapter(channel),
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.reposted_missing is True
    assert len(channel.sent) == 1
    assert ids["message_id"] == 222
    assert ids["channel_id"] == 999


@pytest.mark.asyncio
async def test_refresh_persists_default_text_only_after_successful_discord_update(monkeypatch):
    channel = _Channel()
    updates = []
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(AwardRemindersText=None),
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

    result = await mge_publish_service.refresh_award_reminders(
        adapter=_RefreshAdapter(channel),
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.updated_existing is True
    assert len(updates) == 1
    assert updates[0]["reminders_text"] == "latest reminders"


@pytest.mark.asyncio
async def test_refresh_does_not_persist_default_text_when_discord_update_fails(monkeypatch):
    channel = None
    updates = []
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(AwardRemindersText=None),
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
    result = await mge_publish_service.refresh_award_reminders(
        adapter=_RefreshAdapter(channel),
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is False
    assert result.status == "channel_unavailable"
    assert updates == []


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

    result = await mge_publish_service.refresh_award_reminders(
        adapter=_RefreshAdapter(channel),
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is True
    assert result.status == "updated"
    assert channel.sent == []


@pytest.mark.asyncio
async def test_refresh_refuses_when_awards_not_published(monkeypatch):
    channel = None
    monkeypatch.setattr(
        mge_publish_service.mge_publish_dal,
        "fetch_event_publish_context",
        lambda event_id: _ctx(PublishVersion=0),
    )
    result = await mge_publish_service.refresh_award_reminders(
        adapter=_RefreshAdapter(channel),
        event_id=10,
        actor_discord_id=1,
    )

    assert result.success is False
    assert result.skipped_no_awards is True
    assert result.status == "no_awards_published"


def test_refresh_award_reminders_command_uses_admin_decorator(monkeypatch):
    from commands import mge_cmds

    captured = {"allow_leadership": None}

    class _RecordedCommand:
        def __init__(self, callback, *, name=None, **kwargs):
            self.callback = callback
            self.name = name
            self.kwargs = kwargs

    class _RecordedRegistrar:
        def __init__(self):
            self.commands = []

        def slash_command(self, *args, **kwargs):
            def decorator(func):
                self.commands.append(
                    _RecordedCommand(
                        func,
                        name=kwargs.get("name"),
                        **{k: v for k, v in kwargs.items() if k != "name"},
                    )
                )
                return func

            return decorator

    class _RecordedBot:
        def __init__(self):
            self.tree = _RecordedRegistrar()

        def slash_command(self, *args, **kwargs):
            return self.tree.slash_command(*args, **kwargs)

    def _fake_is_admin_and_notify_channel(*, allow_leadership=False):
        captured["allow_leadership"] = allow_leadership

        def decorator(func):
            func._admin_check_applied = True
            return func

        return decorator

    monkeypatch.setattr(
        mge_cmds,
        "is_admin_and_notify_channel",
        _fake_is_admin_and_notify_channel,
    )

    bot = _RecordedBot()
    mge_cmds.register_mge(bot)

    refresh_commands = [
        command for command in bot.tree.commands if command.name == "mge_refresh_award_reminders"
    ]

    assert captured["allow_leadership"] is True
    assert refresh_commands
    assert any(
        getattr(command.callback, "_admin_check_applied", False) for command in refresh_commands
    )
