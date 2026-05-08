from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import ArkSchedulerState, _run_match_reminder_dispatch
from ark.reminder_types import REMINDER_DAILY

UTC = UTC


class DummyMsg:
    def __init__(self, channel_id: int, message_id: int):
        self.channel = type("Ch", (), {"id": channel_id})()
        self.id = message_id


class DummyChannel:
    def __init__(self, channel_id: int):
        self.id = channel_id
        self.sent = []

    async def send(self, content=None, embed=None, **kwargs):
        self.sent.append({"content": content, "embed": embed, **kwargs})


class DummyClient:
    def __init__(self):
        self.guild_id = 1234
        self.channels = {111: DummyChannel(111), 222: DummyChannel(222)}

    def get_channel(self, channel_id: int):
        return self.channels.get(channel_id)

    def get_user(self, _uid):
        return None

    async def fetch_user(self, user_id: int):
        class _U:
            id = user_id

            async def send(self, _content):
                return None

        return _U()


@pytest.mark.asyncio
async def test_daily_visibility_refresh_reposts_registration(monkeypatch, tmp_path):
    now = datetime.now(UTC).replace(hour=20, minute=5, second=0, microsecond=0)
    match_dt = now + timedelta(days=1)

    base_match = {
        "MatchId": 1,
        "Alliance": "K98",
        "ArkWeekendDate": match_dt.date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": match_dt.time().replace(microsecond=0),
        "SignupCloseUtc": now + timedelta(hours=10),
        "Status": "Scheduled",
    }

    async def _get_match(_mid):
        return dict(base_match)

    async def _get_alliance(_alliance):
        return {"RegistrationChannelId": 111, "ConfirmationChannelId": 222}

    async def _get_roster(_mid):
        return []

    async def _get_prefs(_uid):
        return None

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15}

    class _State:
        def __init__(self):
            self.messages = {}

        async def load_async(self):
            return None

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_match", _get_match)
    monkeypatch.setattr("ark.ark_scheduler.get_alliance", _get_alliance)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.get_roster", _get_roster)
    monkeypatch.setattr("ark.ark_scheduler.get_reminder_prefs", _get_prefs)
    monkeypatch.setattr("ark.ark_scheduler.ArkJsonState", lambda: _State())

    calls = {}

    class _Controller:
        def __init__(self, *, match_id: int, config: dict):
            calls["init"] = {"match_id": match_id, "config": config}

        async def ensure_registration_message(self, **kwargs):
            calls["kwargs"] = kwargs
            return type("Ref", (), {"channel_id": 111, "message_id": 987})()

    monkeypatch.setattr("ark.ark_scheduler.ArkRegistrationController", _Controller)

    scheduler_state = ArkSchedulerState()
    scheduler_state.reminder_state.path = tmp_path / "ark_reminder_state.json"

    client = DummyClient()
    await _run_match_reminder_dispatch(client=client, state=scheduler_state, match=base_match)

    assert calls["kwargs"]["force_repost"] is True
    assert calls["kwargs"]["announce"] is False
    assert not client.channels[111].sent


@pytest.mark.asyncio
async def test_daily_visibility_refresh_dedupes(monkeypatch, tmp_path):
    now = datetime.now(UTC).replace(hour=20, minute=3, second=0, microsecond=0)
    match_dt = now + timedelta(days=1)

    base_match = {
        "MatchId": 3,
        "Alliance": "K98",
        "ArkWeekendDate": match_dt.date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": match_dt.time().replace(microsecond=0),
        "SignupCloseUtc": now + timedelta(hours=10),
        "Status": "Scheduled",
    }

    async def _get_match(_mid):
        return dict(base_match)

    async def _get_alliance(_alliance):
        return {"RegistrationChannelId": 111, "ConfirmationChannelId": 222}

    async def _get_roster(_mid):
        return []

    async def _get_prefs(_uid):
        return None

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15}

    class _State:
        def __init__(self):
            self.messages = {}

        async def load_async(self):
            return None

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_match", _get_match)
    monkeypatch.setattr("ark.ark_scheduler.get_alliance", _get_alliance)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.get_roster", _get_roster)
    monkeypatch.setattr("ark.ark_scheduler.get_reminder_prefs", _get_prefs)
    monkeypatch.setattr("ark.ark_scheduler.ArkJsonState", lambda: _State())

    calls = {"count": 0}

    class _Controller:
        def __init__(self, *, match_id: int, config: dict):
            self.match_id = match_id

        async def ensure_registration_message(self, **kwargs):
            calls["count"] += 1
            return type("Ref", (), {"channel_id": 111, "message_id": 1110 + calls["count"]})()

    monkeypatch.setattr("ark.ark_scheduler.ArkRegistrationController", _Controller)

    scheduler_state = ArkSchedulerState()
    scheduler_state.reminder_state.path = tmp_path / "ark_reminder_state.json"

    client = DummyClient()
    await _run_match_reminder_dispatch(client=client, state=scheduler_state, match=base_match)
    first_count = calls["count"]

    await _run_match_reminder_dispatch(client=client, state=scheduler_state, match=base_match)
    second_count = calls["count"]

    assert first_count >= 1
    assert second_count == first_count
    assert any(REMINDER_DAILY in k for k in scheduler_state.reminder_state.reminders.keys())
