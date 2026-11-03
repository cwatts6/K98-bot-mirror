from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from ui.views.vote_admin_update_view import VoteAdminUpdateView, _VoteOptionIconModal
from voting.models import VoteOption, VoteSnapshot
from voting.option_emojis import normalize_option_emoji


def _snapshot(
    *, status: str = "Open", closes_delta: timedelta = timedelta(hours=1)
) -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=7,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="Vote",
        description=None,
        status=status,
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now + closes_delta,
        closed_at_utc=None,
        closed_by_discord_user_id=None,
        closed_reason=None,
        background_asset_key=None,
        total_votes=1,
        created_at_utc=now,
        updated_at_utc=now,
        options=(VoteOption(9, 7, "opt1", "A", 1, vote_count=1),),
    )


@pytest.mark.asyncio
async def test_update_view_guard_allows_owner_even_when_snapshot_is_elapsed(monkeypatch):
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.vote_admin_update_view.send_ephemeral", fake_send_ephemeral)
    view = VoteAdminUpdateView(
        _snapshot(closes_delta=timedelta(days=-1)),
        owner_user_id=123,
    )

    assert await view.guard(SimpleNamespace(user=SimpleNamespace(id=123))) is True
    assert sent == []


@pytest.mark.asyncio
async def test_update_view_guard_rejects_other_admin(monkeypatch):
    sent: list[str] = []

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        sent.append(content)

    monkeypatch.setattr("ui.views.vote_admin_update_view.send_ephemeral", fake_send_ephemeral)
    view = VoteAdminUpdateView(_snapshot(), owner_user_id=123)

    assert await view.guard(SimpleNamespace(user=SimpleNamespace(id=456))) is False
    assert sent == ["This update panel belongs to another admin."]


@pytest.mark.asyncio
async def test_option_icon_modal_updates_vote_and_refreshes_public_message(monkeypatch):
    captured: dict[str, object] = {}
    snapshot = _snapshot()
    updated = VoteSnapshot(
        **{
            **snapshot.__dict__,
            "options": (
                VoteOption(
                    9,
                    7,
                    "opt1",
                    "A",
                    1,
                    vote_count=1,
                    emoji=normalize_option_emoji("✅"),
                ),
            ),
        }
    )

    async def fake_update_vote_option_emoji(**kwargs):
        captured["update"] = kwargs
        return updated

    async def fake_refresh(_client, refreshed_snapshot):
        captured["refreshed"] = refreshed_snapshot

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral"] = content

    monkeypatch.setattr(
        "ui.views.vote_admin_update_view.update_vote_option_emoji",
        fake_update_vote_option_emoji,
    )
    monkeypatch.setattr("ui.views.vote_admin_update_view.send_ephemeral", fake_send_ephemeral)

    view = VoteAdminUpdateView(snapshot, owner_user_id=123, refresh_callback=fake_refresh)
    modal = _VoteOptionIconModal(view, option_id=9)
    modal.icon.value = "✅"

    await modal.callback(SimpleNamespace(user=SimpleNamespace(id=123), client=object()))

    assert captured["update"] == {
        "vote_post_id": 7,
        "option_id": 9,
        "emoji_value": "✅",
        "actor_discord_user_id": 123,
    }
    assert captured["refreshed"] is updated
    assert captured["ephemeral"] == "Option icon saved for ✅ A."
