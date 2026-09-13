from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from voting.discord_presentation import build_close_embed, build_vote_embed
from voting.models import VoteOption, VoteSnapshot
from voting.result_visibility import RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE
from voting.vote_modes import VOTE_MODE_MULTI_SELECT


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


def test_open_hidden_vote_embed_hides_public_totals_and_outcome():
    snapshot = replace(
        _closed_snapshot(total_votes=4),
        status="Open",
        closed_at_utc=None,
        closed_reason=None,
        closes_at_utc=datetime(2026, 7, 1, 13, 0, tzinfo=UTC),
        result_visibility=RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
    )

    embed = build_vote_embed(snapshot)
    fields = {field.name: field.value for field in embed.fields}

    assert "Total votes" not in fields
    assert fields["Results"] == "Hidden until close"
    assert fields["Result visibility"] == "Hidden until close"
    assert "Outcome" not in fields


def test_elapsed_hidden_vote_embed_waits_for_actual_close_before_reveal():
    snapshot = replace(
        _closed_snapshot(total_votes=4),
        status="Open",
        closed_at_utc=None,
        closed_reason=None,
        result_visibility=RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
    )

    embed = build_vote_embed(snapshot)
    fields = {field.name: field.value for field in embed.fields}

    assert fields["Results"] == "Hidden until close"
    assert "Total votes" not in fields
    assert "Outcome" not in fields


def test_closed_hidden_vote_embed_reveals_public_totals_and_outcome():
    snapshot = replace(
        _closed_snapshot(total_votes=4),
        result_visibility=RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
    )

    embed = build_vote_embed(snapshot)
    fields = {field.name: field.value for field in embed.fields}

    assert fields["Total votes"] == "4"
    assert fields["Outcome"].startswith("Winner:")


def test_multi_select_embed_uses_voter_and_selection_totals():
    snapshot = replace(
        _closed_snapshot(total_votes=2),
        vote_mode=VOTE_MODE_MULTI_SELECT,
        min_selections=1,
        max_selections=2,
        total_selections=3,
        options=(
            VoteOption(10, 42, "opt1", "18:00 UTC", 1, vote_count=1),
            VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=2),
        ),
    )

    embed = build_vote_embed(snapshot)
    fields = {field.name: field.value for field in embed.fields}

    assert fields["Total voters"] == "2"
    assert fields["Total selections"] == "3"
    assert fields["Vote mode"] == "Multi-select (1-2 selections)"
    assert fields["Outcome"].startswith("Top selection:")


def test_open_hidden_multi_select_embed_hides_selection_totals():
    snapshot = replace(
        _closed_snapshot(total_votes=2),
        status="Open",
        closed_at_utc=None,
        closed_reason=None,
        closes_at_utc=datetime(2026, 7, 1, 13, 0, tzinfo=UTC),
        result_visibility=RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
        vote_mode=VOTE_MODE_MULTI_SELECT,
        min_selections=1,
        max_selections=2,
        total_selections=3,
    )

    embed = build_vote_embed(snapshot)
    fields = {field.name: field.value for field in embed.fields}

    assert fields["Results"] == "Hidden until close"
    assert "Total voters" not in fields
    assert "Total selections" not in fields
    assert "Outcome" not in fields
