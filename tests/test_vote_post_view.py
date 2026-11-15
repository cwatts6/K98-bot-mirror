from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from ui.views.vote_post_view import MultiSelectVotePanel, VotePostView
from voting.models import VoteCastResult, VoteOption, VoteSnapshot
from voting.option_emojis import normalize_option_emoji
from voting.vote_modes import VOTE_MODE_MULTI_SELECT


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


def _six_option_snapshot() -> VoteSnapshot:
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
        total_votes=0,
        created_at_utc=now,
        updated_at_utc=now,
        options=tuple(
            VoteOption(index, 7, f"opt{index}", f"Option {index}", index) for index in range(1, 7)
        ),
    )


def _multi_select_snapshot() -> VoteSnapshot:
    snapshot = _six_option_snapshot()
    return VoteSnapshot(
        **{
            **snapshot.__dict__,
            "closes_at_utc": datetime.now(UTC) + timedelta(hours=1),
            "vote_mode": VOTE_MODE_MULTI_SELECT,
            "min_selections": 1,
            "max_selections": 2,
            "total_votes": 0,
            "total_selections": 0,
        }
    )


@pytest.mark.asyncio
async def test_vote_post_view_applies_option_emoji_to_public_button() -> None:
    snapshot = _snapshot()
    option = VoteOption(9, 7, "opt1", "A", 1, vote_count=1, emoji=normalize_option_emoji("✅"))
    snapshot = VoteSnapshot(**{**snapshot.__dict__, "options": (option,)})

    view = VotePostView(snapshot)

    button = view.children[0]
    assert button.label == "A"
    assert str(button.emoji) == "✅"


@pytest.mark.asyncio
async def test_multi_select_panel_applies_option_emoji_to_select_options() -> None:
    snapshot = _multi_select_snapshot()
    options = (
        VoteOption(1, 7, "opt1", "Option 1", 1, emoji=normalize_option_emoji("✅")),
        *snapshot.options[1:],
    )
    snapshot = VoteSnapshot(**{**snapshot.__dict__, "options": options})

    panel = MultiSelectVotePanel(snapshot, owner_user_id=123)
    select = panel.children[0]

    assert str(select.options[0].emoji) == "✅"


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
    assert captured["attachments"] == []
    assert captured["files"]
    assert captured["ephemeral_content"] == "Vote recorded."


@pytest.mark.asyncio
async def test_vote_button_reports_cast_vote_failure(monkeypatch):
    snapshot = _snapshot()
    view = VotePostView(snapshot)
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fail_cast_vote(**_kwargs):
        raise RuntimeError("database unavailable")

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral_content"] = content

    monkeypatch.setattr("ui.views.vote_post_view.vote_service.cast_vote", fail_cast_vote)
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
    )

    await button.callback(interaction)

    assert captured["ephemeral_content"] == "Vote could not be recorded. Please try again."


@pytest.mark.asyncio
async def test_vote_button_does_not_edit_message_for_unchanged_vote(monkeypatch):
    snapshot = _snapshot()
    view = VotePostView(snapshot)
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fake_cast_vote(**_kwargs):
        return (
            VoteCastResult("unchanged", 7, option_id=9, message="Already recorded."),
            None,
        )

    async def fake_send_ephemeral(_interaction, content, **_kwargs):
        captured["ephemeral_content"] = content

    async def fail_edit(**_kwargs):
        raise AssertionError("unchanged votes should not edit the public message")

    monkeypatch.setattr("ui.views.vote_post_view.vote_service.cast_vote", fake_cast_vote)
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456, edit=fail_edit),
    )

    await button.callback(interaction)

    assert captured["ephemeral_content"] == "Already recorded."


@pytest.mark.asyncio
async def test_vote_post_view_lays_out_six_buttons_across_two_rows():
    view = VotePostView(_six_option_snapshot())

    rows = [child.row for child in view.children]
    assert rows == [0, 0, 0, 1, 1, 1]


@pytest.mark.asyncio
async def test_multi_select_vote_post_view_uses_single_persistent_opener():
    view = VotePostView(_multi_select_snapshot())

    assert len(view.children) == 1
    button = view.children[0]
    assert button.label == "Choose options"
    assert button.custom_id == "vote_multi:7"


@pytest.mark.asyncio
async def test_multi_select_opener_sends_private_selection_panel(monkeypatch):
    snapshot = _multi_select_snapshot()
    view = VotePostView(snapshot)
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fake_get_vote_snapshot(_vote_post_id):
        return snapshot

    async def fake_get_multi_select_selection_ids(**kwargs):
        assert kwargs == {"vote_post_id": 7, "discord_user_id": 123}
        return (1, 3)

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.vote_post_view.vote_service.get_vote_snapshot", fake_get_vote_snapshot
    )
    monkeypatch.setattr(
        "ui.views.vote_post_view.vote_service.get_multi_select_selection_ids",
        fake_get_multi_select_selection_ids,
    )
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
    )

    await button.callback(interaction)

    assert "Choose 1-2 options" in str(captured["content"])
    assert isinstance(captured["view"], MultiSelectVotePanel)
    panel = captured["view"]
    select = panel.children[0]
    assert select.min_values == 1
    assert select.max_values == 2
    defaults = {option.value for option in select.options if option.default}
    assert defaults == {"1", "3"}


@pytest.mark.asyncio
async def test_multi_select_opener_still_opens_when_existing_selection_load_fails(monkeypatch):
    snapshot = _multi_select_snapshot()
    view = VotePostView(snapshot)
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fake_get_vote_snapshot(_vote_post_id):
        return snapshot

    async def fail_get_multi_select_selection_ids(**_kwargs):
        raise RuntimeError("database unavailable")

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.vote_post_view.vote_service.get_vote_snapshot", fake_get_vote_snapshot
    )
    monkeypatch.setattr(
        "ui.views.vote_post_view.vote_service.get_multi_select_selection_ids",
        fail_get_multi_select_selection_ids,
    )
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
    )

    await button.callback(interaction)

    assert isinstance(captured["view"], MultiSelectVotePanel)
    select = captured["view"].children[0]
    assert [option.value for option in select.options if option.default] == []


@pytest.mark.asyncio
async def test_multi_select_opener_reports_snapshot_load_failure(monkeypatch):
    view = VotePostView(_multi_select_snapshot())
    button = view.children[0]
    captured: dict[str, object] = {}

    async def fail_get_vote_snapshot(_vote_post_id):
        raise RuntimeError("database unavailable")

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.vote_post_view.vote_service.get_vote_snapshot", fail_get_vote_snapshot
    )
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
    )

    await button.callback(interaction)

    assert captured["content"] == "Vote could not be loaded. Please try again."


@pytest.mark.asyncio
async def test_multi_select_panel_rejects_invalid_payload_before_cast(monkeypatch):
    snapshot = _multi_select_snapshot()
    panel = MultiSelectVotePanel(snapshot, owner_user_id=123)
    select = panel.children[0]
    select._interaction = SimpleNamespace(data={})
    select._selected_values = ["not-an-option-id"]
    captured: dict[str, object] = {}

    async def fail_cast_multi_select_vote(**_kwargs):
        raise AssertionError("invalid payload should not reach service cast")

    async def fake_send_ephemeral(_interaction, content, **kwargs):
        captured["content"] = content
        captured.update(kwargs)

    monkeypatch.setattr(
        "ui.views.vote_post_view.vote_service.cast_multi_select_vote",
        fail_cast_multi_select_vote,
    )
    monkeypatch.setattr("ui.views.vote_post_view.send_ephemeral", fake_send_ephemeral)

    interaction = SimpleNamespace(
        response=_Response(),
        user=SimpleNamespace(id=123),
        message=SimpleNamespace(id=456),
    )

    await select.callback(interaction)

    assert captured["content"] == "One or more selected options are not valid."
