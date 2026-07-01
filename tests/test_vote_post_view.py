from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from ui.views.vote_post_view import VotePostView
from voting.models import VoteCastResult, VoteOption, VoteSnapshot


def _snapshot() -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=7,
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
        closes_at_utc=now + timedelta(hours=1),
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        background_asset_key=None,
        total_votes=1,
        created_at_utc=now,
        updated_at_utc=now,
        options=(VoteOption(9, 7, "opt1", "A", 1, vote_count=1),),
    )


class _Response:
    def __init__(self) -> None:
        self.done = False

    def is_done(self) -> bool:
        return self.done

    async def defer(self, *, ephemeral: bool) -> None:
        self.done = True
        self.ephemeral = ephemeral


@pytest.mark.asyncio
async def test_vote_button_edits_original_message_without_broad_mentions(monkeypatch):
    snapshot = _snapshot()
    view = VotePostView(snapshot)
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fake_cast_vote(**_kwargs):
        return VoteCastResult("recorded", 7, option_id=9, message="Vote recorded."), snapshot

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral_content"] = content

    async def fake_edit(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("ui.views.vote_post_view.vote_service.cast_vote", fake_cast_vote)
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456, edit=fake_edit),
    )

    await button.callback(interaction)

    allowed_mentions = captured["allowed_mentions"]
    assert allowed_mentions.everyone is False
    assert allowed_mentions.roles is False
    assert captured["ephemeral_content"] == "Vote recorded."
