from __future__ import annotations

from datetime import UTC, datetime, timedelta

from voting.discord_presentation import build_close_embed, build_vote_embed
from voting.models import VoteOption, VoteSnapshot


def _closed_snapshot(*, total_votes: int) -> VoteSnapshot:
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
        options=(
            VoteOption(10, 42, "opt1", "18:00 UTC", 1, vote_count=1 if total_votes else 0),
            VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=max(0, total_votes - 1)),
        ),
    )


def test_close_embed_includes_winner_summary():
    embed = build_close_embed(_closed_snapshot(total_votes=4))

    assert embed.description is not None
    assert embed.description.startswith("Winner:")


def test_close_embed_includes_no_vote_summary():
    embed = build_close_embed(_closed_snapshot(total_votes=0))

    assert embed.description is not None
    assert embed.description.startswith("No votes were cast.")


def test_vote_embed_includes_outcome_for_elapsed_vote():
    snapshot = _closed_snapshot(total_votes=4)
    snapshot = VoteSnapshot(
        **{
            **snapshot.__dict__,
            "status": "Open",
            "closed_at_utc": None,
            "closed_reason": None,
        }
    )

    embed = build_vote_embed(snapshot)

    outcome_fields = [field for field in embed.fields if field.name == "Outcome"]
    assert outcome_fields
    assert outcome_fields[0].value.startswith("Winner:")
