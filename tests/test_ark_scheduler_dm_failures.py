from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import ArkSchedulerState, _dispatch_dm_reminders_for_match


class DummyClient:
    def get_user(self, _uid):
        return None

    async def fetch_user(self, user_id: int):
        class _User:
            id = user_id

            async def send(self, _content):
                raise RuntimeError("DM blocked")

        return _User()


@pytest.mark.asyncio
async def test_dispatch_dm_records_failures(monkeypatch, tmp_path):
    now = datetime.now(UTC)
    match = {
        "MatchId": 10,
        "Alliance": "K98",
        "ArkWeekendDate": now.date(),
        "MatchDay": "Sat",
        "MatchTimeUtc": now.time().replace(microsecond=0),
        "SignupCloseUtc": now + timedelta(hours=1),
        "Status": "Locked",
    }

    async def _get_roster(_mid):
        return [
            {"DiscordUserId": 9001, "Status": "Active"},
            {"DiscordUserId": 9002, "Status": "Active"},
        ]

    async def _get_prefs(_uid):
        return {"OptOutAll": 0}

    monkeypatch.setattr("ark.ark_scheduler.get_roster", _get_roster)
    monkeypatch.setattr("ark.ark_scheduler.get_reminder_prefs", _get_prefs)

    state = ArkSchedulerState()
    state.reminder_state.path = tmp_path / "ark_reminder_state.json"

    counters = await _dispatch_dm_reminders_for_match(
        client=DummyClient(),
        state=state,
        match=match,
        reminder_type="24h",
        scheduled_for=now,
    )

    assert counters["attempted"] == 2
    assert counters["failed"] == 2
