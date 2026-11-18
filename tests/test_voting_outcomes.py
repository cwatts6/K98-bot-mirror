from __future__ import annotations

from datetime import UTC, datetime, timedelta

from voting.models import VoteOption, VoteSnapshot
from voting.outcomes import vote_outcome


def _snapshot(options: tuple[VoteOption, ...], *, total_votes: int) -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=42,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Best rally time?",
        description=None,
        status="Closed",
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now - timedelta(minutes=1),
        closed_at_utc=now,
        closed_by_discord_user_id=None,
        closed_reason="deadline",
        background_asset_key=None,
        total_votes=total_votes,
        created_at_utc=now,
        updated_at_utc=now,
        options=options,
    )


def test_vote_outcome_reports_clear_winner():
    outcome = vote_outcome(
        _snapshot(
            (
                VoteOption(10, 42, "opt1", "18:00 UTC", 1, vote_count=1),
                VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=3),
            ),
            total_votes=4,
        )
    )

    assert outcome.kind == "winner"
    assert outcome.winning_option_ids == (11,)
    assert outcome.summary.startswith("Winner: 19:00 UTC")


def test_vote_outcome_reports_tie():
    outcome = vote_outcome(
        _snapshot(
            (
                VoteOption(10, 42, "opt1", "18:00 UTC", 1, vote_count=2),
                VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=2),
            ),
            total_votes=4,
        )
    )

    assert outcome.kind == "tie"
    assert outcome.winning_option_ids == (10, 11)
    assert outcome.summary.startswith("Tie:")


def test_vote_outcome_reports_no_votes():
    outcome = vote_outcome(
        _snapshot(
            (
                VoteOption(10, 42, "opt1", "18:00 UTC", 1, vote_count=0),
                VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=0),
            ),
            total_votes=0,
        )
    )

    assert outcome.kind == "no_votes"
    assert outcome.summary == "No votes were cast."
