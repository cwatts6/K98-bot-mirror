from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from voting import service
from voting.models import VoteCastResult, VoteCloseResult, VoteOption, VoteSnapshot


def test_build_create_request_validates_options_and_future_close():
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    req = service.build_create_request(
        guild_id=1,
        channel_id=2,
        created_by_discord_user_id=3,
        title="Best time?",
        description="Pick one",
        raw_options="18:00 | 19:00 | 20:00",
        close_time_utc=(now + timedelta(hours=2)).isoformat(),
        reminder_offsets="60, 30",
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        now_utc=now,
    )

    assert req.options == ("18:00", "19:00", "20:00")
    assert req.reminder_offsets_minutes == (60, 30)
    assert req.allow_vote_change is True


def test_build_create_request_rejects_duplicate_options():
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    with pytest.raises(service.VoteValidationError, match="unique"):
        service.build_create_request(
            guild_id=1,
            channel_id=2,
            created_by_discord_user_id=3,
            title="Best time?",
            description=None,
            raw_options="18:00 | 18:00",
            close_time_utc=(now + timedelta(hours=2)).isoformat(),
            reminder_offsets="60",
            allow_vote_change=True,
            launch_mention_everyone=False,
            reminder_mention_everyone=False,
            close_mention_everyone=False,
            now_utc=now,
        )


def test_build_create_request_rejects_past_close():
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    with pytest.raises(service.VoteValidationError, match="future"):
        service.build_create_request(
            guild_id=1,
            channel_id=2,
            created_by_discord_user_id=3,
            title="Best time?",
            description=None,
            raw_options="A | B",
            close_time_utc=(now - timedelta(minutes=1)).isoformat(),
            reminder_offsets="60",
            allow_vote_change=True,
            launch_mention_everyone=False,
            reminder_mention_everyone=False,
            close_mention_everyone=False,
            now_utc=now,
        )


def test_result_helpers_only_treat_state_changes_as_transitioning():
    assert VoteCastResult("recorded", 1).accepted is True
    assert VoteCastResult("changed", 1).accepted is True
    assert VoteCastResult("unchanged", 1).accepted is False
    assert VoteCloseResult("closed", 1).closed is True
    assert VoteCloseResult("already_closed", 1).closed is False


@pytest.mark.asyncio
async def test_update_vote_filters_past_due_reminder_offsets(monkeypatch):
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    captured = {}
    current = VoteSnapshot(
        vote_post_id=9,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Vote",
        description=None,
        status="Open",
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(minutes=10),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        background_asset_key=None,
        total_votes=0,
        created_at_utc=now,
        updated_at_utc=now,
        options=(VoteOption(1, 9, "opt1", "A", 1),),
    )

    async def fake_get_vote_snapshot(_vote_post_id):
        return current

    async def fake_update_vote_post(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(service.dal, "get_vote_snapshot", fake_get_vote_snapshot)
    monkeypatch.setattr(service.dal, "update_vote_post", fake_update_vote_post)

    await service.update_vote(
        vote_post_id=9,
        actor_discord_user_id=123,
        reminder_offsets="60,5",
        now_utc=now,
    )

    assert captured["reminder_offsets_minutes"] == (5,)
