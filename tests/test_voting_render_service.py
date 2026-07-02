from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO

from PIL import Image

from voting.models import VoteOption, VoteSnapshot
from voting.result_visibility import RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE
from voting.render_service import HEIGHT, RED, WIDTH, _status, render_vote_card


def _snapshot(total_votes: int = 0) -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=42,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Best rally time?",
        description="Choose the time that works for you.",
        status="Open",
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + timedelta(hours=3),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        background_asset_key=None,
        total_votes=total_votes,
        created_at_utc=now,
        updated_at_utc=now,
        options=(
            VoteOption(10, 42, "opt1", "18:00 UTC", 1, vote_count=1 if total_votes else 0),
            VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=max(0, total_votes - 1)),
        ),
    )


def _six_option_snapshot() -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=43,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Best rally time?",
        description="Choose the time that works for you.",
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
        total_votes=12,
        created_at_utc=now,
        updated_at_utc=now,
        options=(
            VoteOption(10, 43, "opt1", "18:00 UTC", 1, vote_count=1),
            VoteOption(11, 43, "opt2", "19:00 UTC", 2, vote_count=2),
            VoteOption(12, 43, "opt3", "20:00 UTC", 3, vote_count=3),
            VoteOption(13, 43, "opt4", "21:00 UTC", 4, vote_count=4),
            VoteOption(14, 43, "opt5", "22:00 UTC", 5, vote_count=1),
            VoteOption(15, 43, "opt6", "23:00 UTC", 6, vote_count=1),
        ),
    )


def test_render_vote_card_outputs_png_with_expected_size():
    rendered = render_vote_card(
        _snapshot(total_votes=3), now_utc=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    )

    image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
    assert image.format == "PNG"
    assert image.size == (WIDTH, HEIGHT)
    assert rendered.filename == "vote_42.png"


def test_render_vote_card_handles_zero_vote_state():
    rendered = render_vote_card(
        _snapshot(total_votes=0), now_utc=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    )

    assert rendered.image_bytes.getbuffer().nbytes > 10_000


def test_render_vote_card_handles_hidden_open_results_without_outcome(monkeypatch):
    def fail_vote_outcome(_snapshot):
        raise AssertionError("open hidden vote should not compute a public outcome")

    monkeypatch.setattr("voting.render_service.vote_outcome", fail_vote_outcome)
    snapshot = _snapshot(total_votes=3)
    snapshot = VoteSnapshot(
        **{
            **snapshot.__dict__,
            "closes_at_utc": datetime(2026, 7, 1, 11, 59, tzinfo=UTC),
            "result_visibility": RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
        }
    )

    rendered = render_vote_card(snapshot, now_utc=datetime(2026, 7, 1, 12, 0, tzinfo=UTC))

    image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
    assert image.format == "PNG"
    assert image.size == (WIDTH, HEIGHT)


def test_render_vote_card_handles_six_closed_options_with_winner_state():
    rendered = render_vote_card(
        _six_option_snapshot(), now_utc=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    )

    image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
    assert image.format == "PNG"
    assert image.size == (WIDTH, HEIGHT)
    assert rendered.image_bytes.getbuffer().nbytes > 10_000


def test_status_treats_elapsed_open_vote_as_closed():
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    snapshot = replace(_snapshot(), closes_at_utc=now - timedelta(seconds=1))

    assert _status(snapshot, now) == ("Closed", RED)
