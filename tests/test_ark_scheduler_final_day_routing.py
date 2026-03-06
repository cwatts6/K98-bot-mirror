from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import ArkSchedulerState, _run_match_reminder_dispatch


class DummyMsg:
    def __init__(self, channel_id: int):
        self.id = 999
        self.channel = type("C", (), {"id": channel_id})()


class DummyChannel:
    def __init__(self, channel_id: int):
        self.id = channel_id
        self.sent = []

    async def send(self, content: str):
        self.sent.append(content)
        return DummyMsg(self.id)


class DummyClient:
    guild_id = 1234

    def __init__(self):
        self.channels = {111: DummyChannel(111), 222: DummyChannel(222)}

    def get_channel(self, cid: int):
        return self.channels.get(cid)

    def get_user(self, _uid):
        return None

    async def fetch_user(self, _uid):
        class _U:
            async def send(self, _content):
                return None

        return _U()


@pytest.mark.asyncio
async def test_final_day_goes_to_registration_channel(monkeypatch, tmp_path):
    now = datetime.now(UTC).replace(hour=12, minute=5, second=0, microsecond=0)
    close_dt = now.replace(hour=23, minute=0, second=0, microsecond=0)

    match = {
        "MatchId": 21,
        "Alliance": "K98",
        "ArkWeekendDate": now.date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": (now + timedelta(hours=20)).time().replace(microsecond=0),
        "SignupCloseUtc": close_dt,
        "Status": "Scheduled",
    }

    async def _get_match(_mid):
        return dict(match)

    async def _get_alliance(_alliance):
        return {"RegistrationChannelId": 111, "ConfirmationChannelId": 222}

    async def _get_roster(_mid):
        return []

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

    reg_msgs = " ".join(client.channels[111].sent).lower()
    conf_msgs = " ".join(client.channels[222].sent).lower()

    assert "final-day" in reg_msgs or "final day" in reg_msgs
    assert "final-day" not in conf_msgs
