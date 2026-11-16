from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from types import SimpleNamespace

import pytest

from voting.models import VoteOption, VoteSnapshot
from voting.scheduler import run_voting_scheduler_tick
from voting.survey_models import SurveyQuestion, SurveyQuestionOption, SurveySnapshot


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


def _survey_snapshot() -> SurveySnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return SurveySnapshot(
        survey_id=7,
        guild_id=1,
        channel_id=22,
        message_id=33,
        created_by_discord_user_id=44,
        title="Survey",
        description=None,
        status="Open",
        allow_response_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=True,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(minutes=30),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        total_responses=0,
        created_at_utc=now,
        updated_at_utc=now,
        questions=(
            SurveyQuestion(
                question_id=10,
                survey_id=7,
                question_key="q1",
                prompt="First?",
                question_type="SingleChoice",
                sort_order=1,
                min_selections=1,
                max_selections=1,
                options=(
                    SurveyQuestionOption(101, 10, "opt1", "A", 1),
                    SurveyQuestionOption(102, 10, "opt2", "B", 2),
                ),
            ),
        ),
    )


class _Channel:
    id = 22

    def __init__(self) -> None:
        self.sent = []

    async def send(self, **kwargs):
        self.sent.append(kwargs)
        return SimpleNamespace(id=900)


@pytest.fixture(autouse=True)
def _stub_empty_survey_scheduler(monkeypatch):
    async def list_due_closes(_now):
        return []

    async def claim_due_reminders(_now):
        return []

    monkeypatch.setattr("voting.scheduler.survey_dal.list_due_closes", list_due_closes)
    monkeypatch.setattr("voting.scheduler.survey_dal.claim_due_reminders", claim_due_reminders)


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

    assert summary == {"reminders": 1, "closes": 0, "survey_reminders": 0, "survey_closes": 0}
    assert channel.sent[0]["content"].startswith("@everyone")
    assert channel.sent[0]["allowed_mentions"].everyone is True
    assert (8, 900, now) in calls
    assert "ReminderSent" in calls


@pytest.mark.asyncio
async def test_scheduler_closes_due_votes_before_sending_reminders(monkeypatch):
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    calls = []

    async def list_due_closes(_now):
        calls.append("list_closes")
        return [5]

    async def close_due_vote(_bot, vote_post_id, _now):
        calls.append(("close", vote_post_id))

    async def claim_due_reminders(_now):
        calls.append("claim_reminders")
        return [{"ReminderID": 8, "VotePostID": 5}]

    async def send_reminder(_bot, reminder, _now):
        calls.append(("reminder", reminder["ReminderID"]))
        return True

    monkeypatch.setattr("voting.scheduler.dal.list_due_closes", list_due_closes)
    monkeypatch.setattr("voting.scheduler._close_due_vote", close_due_vote)
    monkeypatch.setattr("voting.scheduler.dal.claim_due_reminders", claim_due_reminders)
    monkeypatch.setattr("voting.scheduler._send_reminder", send_reminder)

    summary = await run_voting_scheduler_tick(SimpleNamespace(), now_utc=now)

    assert summary == {"reminders": 1, "closes": 1, "survey_reminders": 0, "survey_closes": 0}
    assert calls == [
        "list_closes",
        ("close", 5),
        "claim_reminders",
        ("reminder", 8),
    ]


@pytest.mark.asyncio
async def test_scheduler_does_not_count_or_success_audit_when_reminder_mark_fails(monkeypatch):
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    channel = _Channel()
    audits = []

    async def claim_due_reminders(_now):
        return [{"ReminderID": 8, "VotePostID": 5}]

    async def get_vote_snapshot(_vote_post_id):
        return _snapshot()

    async def mark_reminder_sent(_reminder_id, *, message_id, now_utc):
        return False

    async def list_due_closes(_now):
        return []

    async def insert_audit(**kwargs):
        audits.append(kwargs)

    monkeypatch.setattr("voting.scheduler.dal.claim_due_reminders", claim_due_reminders)
    monkeypatch.setattr("voting.scheduler.dal.get_vote_snapshot", get_vote_snapshot)
    monkeypatch.setattr("voting.scheduler.dal.mark_reminder_sent", mark_reminder_sent)
    monkeypatch.setattr("voting.scheduler.dal.list_due_closes", list_due_closes)
    monkeypatch.setattr("voting.scheduler.dal.insert_audit", insert_audit)

    bot = SimpleNamespace(get_channel=lambda _channel_id: channel)

    summary = await run_voting_scheduler_tick(bot, now_utc=now)

    assert summary == {"reminders": 0, "closes": 0, "survey_reminders": 0, "survey_closes": 0}
    assert len(channel.sent) == 1
    assert [audit["action_type"] for audit in audits] == ["ReminderMarkFailed"]
    assert audits[0]["details"] == {"reminder_id": 8, "message_id": 900}


@pytest.mark.asyncio
async def test_scheduler_logs_warning_when_survey_reminder_mark_fails(monkeypatch, caplog):
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    channel = _Channel()
    audits = []

    async def claim_vote_reminders(_now):
        return []

    async def list_due_closes(_now):
        return []

    async def claim_survey_reminders(_now):
        return [{"ReminderID": 9, "SurveyID": 7}]

    async def get_survey_snapshot(_survey_id):
        return _survey_snapshot()

    async def mark_reminder_sent(_reminder_id, *, message_id, now_utc):
        return False

    async def insert_audit(**kwargs):
        audits.append(kwargs)

    monkeypatch.setattr("voting.scheduler.dal.claim_due_reminders", claim_vote_reminders)
    monkeypatch.setattr("voting.scheduler.dal.list_due_closes", list_due_closes)
    monkeypatch.setattr("voting.scheduler.survey_dal.claim_due_reminders", claim_survey_reminders)
    monkeypatch.setattr("voting.scheduler.survey_dal.get_survey_snapshot", get_survey_snapshot)
    monkeypatch.setattr("voting.scheduler.survey_dal.mark_reminder_sent", mark_reminder_sent)
    monkeypatch.setattr("voting.scheduler.survey_dal.insert_audit", insert_audit)

    bot = SimpleNamespace(get_channel=lambda _channel_id: channel)

    with caplog.at_level(logging.WARNING, logger="voting.scheduler"):
        summary = await run_voting_scheduler_tick(bot, now_utc=now)

    assert summary == {"reminders": 0, "closes": 0, "survey_reminders": 0, "survey_closes": 0}
    assert len(channel.sent) == 1
    assert [audit["action_type"] for audit in audits] == ["ReminderMarkFailed"]
    assert audits[0]["details"] == {"reminder_id": 9, "message_id": 900}
    assert "survey_reminder_mark_failed survey_id=7 reminder_id=9 message_id=900" in caplog.text
