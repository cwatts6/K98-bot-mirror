from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import ArkSchedulerState, _run_match_reminder_dispatch


class DummyChannel:
    def __init__(self):
        self.sent = []

    async def send(self, content: str):
        self.sent.append(content)
        return type("M", (), {"id": 1, "channel": type("C", (), {"id": 111})()})()


class DummyClient:
    guild_id = 1234

    def __init__(self):
        self.channels = {111: DummyChannel(), 222: DummyChannel()}

    def get_channel(self, cid):
        return self.channels.get(cid)

    def get_user(self, _uid):
        return None

    async def fetch_user(self, _uid):
        class _U:
            async def send(self, _content):
                return None

        return _U()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["Cancelled", "Completed"])
async def test_cancelled_completed_send_nothing(monkeypatch, tmp_path, status):
    now = datetime.now(UTC)

    match = {
        "MatchId": 50,
        "Alliance": "K98",
        "ArkWeekendDate": now.date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": (now + timedelta(hours=1)).time().replace(microsecond=0),
        "SignupCloseUtc": now + timedelta(minutes=30),
        "Status": status,
    }

    async def _get_match(_mid):
        return dict(match)

    async def _get_alliance(_alliance):
        return {"RegistrationChannelId": 111, "ConfirmationChannelId": 222}

    async def _get_roster(_mid):
        return [{"DiscordUserId": 999, "Status": "Active"}]

    async def _get_prefs(_uid):
        return {"OptOutAll": 0}

    class _State:
        def __init__(self):
            self.messages = {}

        async def load_async(self):
            return None

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_match", _get_match)
    monkeypatch.setattr("ark.ark_scheduler.get_alliance", _get_alliance)
    monkeypatch.setattr("ark.ark_scheduler.get_roster", _get_roster)
    monkeypatch.setattr("ark.ark_scheduler.get_reminder_prefs", _get_prefs)
    monkeypatch.setattr("ark.ark_scheduler.ArkJsonState", lambda: _State())

    state = ArkSchedulerState()
    state.reminder_state.path = tmp_path / "ark_reminder_state.json"

    client = DummyClient()
    await _run_match_reminder_dispatch(client=client, state=state, match=match)

    assert client.channels[111].sent == []
    assert client.channels[222].sent == []
