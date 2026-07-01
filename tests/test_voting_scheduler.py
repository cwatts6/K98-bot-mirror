from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from voting.models import VoteOption, VoteSnapshot
from voting.scheduler import run_voting_scheduler_tick


def _snapshot() -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=5,
        guild_id=1,
        channel_id=22,
        message_id=33,
        created_by_discord_user_id=44,
        title="Vote",
        description=None,
        status="Open",
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=True,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(minutes=30),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        background_asset_key=None,
        total_votes=0,
        created_at_utc=now,
        updated_at_utc=now,
        options=(VoteOption(1, 5, "opt1", "A", 1), VoteOption(2, 5, "opt2", "B", 2)),
    )


class _Channel:
    id = 22

    def __init__(self) -> None:
        self.sent = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        return SimpleNamespace(id=900)


@pytest.mark.asyncio
async def test_scheduler_sends_claimed_reminder_once_with_configured_mentions(monkeypatch):
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    channel = _Channel()
    calls = []

    async def claim_due_reminders(_now):
        calls.append("claim")
        return [{"ReminderID": 8, "VotePostID": 5}]

    async def get_vote_snapshot(_vote_post_id):
        return _snapshot()

    async def mark_reminder_sent(reminder_id, *, message_id, now_utc):
        calls.append((reminder_id, message_id, now_utc))
        return True

    async def list_due_closes(_now):
        return []

    async def insert_audit(**kwargs):
        calls.append(kwargs["action_type"])

    monkeypatch.setattr("voting.scheduler.dal.claim_due_reminders", claim_due_reminders)
    monkeypatch.setattr("voting.scheduler.dal.get_vote_snapshot", get_vote_snapshot)
    monkeypatch.setattr("voting.scheduler.dal.mark_reminder_sent", mark_reminder_sent)
    monkeypatch.setattr("voting.scheduler.dal.list_due_closes", list_due_closes)
    monkeypatch.setattr("voting.scheduler.dal.insert_audit", insert_audit)

    bot = SimpleNamespace(get_channel=lambda _channel_id: channel)

    summary = await run_voting_scheduler_tick(bot, now_utc=now)

    assert summary == {"reminders": 1, "closes": 0}
    assert channel.sent[0]["content"].startswith("@everyone")
    assert channel.sent[0]["allowed_mentions"].everyone is True
    assert (8, 900, now) in calls
    assert "ReminderSent" in calls
