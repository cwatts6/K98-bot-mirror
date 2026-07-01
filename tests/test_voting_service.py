from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from voting import service


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
