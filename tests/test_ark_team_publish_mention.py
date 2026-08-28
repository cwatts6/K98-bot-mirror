from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

MATCH_ID = 1
CHANNEL_ID = 500
ACTOR_ID = 999


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_roster_row(
    governor_id: int,
    name: str,
    discord_user_id: int | None,
    status: str = "active",
) -> dict:
    return {
        "GovernorId": governor_id,
        "GovernorNameSnapshot": name,
        "DiscordUserId": discord_user_id,
        "Status": status,
    }


def _make_assignment(
    *,
    published_at_utc: str | None,
    team1_ids: list[int],
    team2_ids: list[int],
):
    from ark.team_state import ArkTeamAssignment

    a = ArkTeamAssignment(match_id=MATCH_ID)
    a.published_at_utc = published_at_utc
    a.team1_player_ids = list(team1_ids)
    a.team2_player_ids = list(team2_ids)
    a.roster_player_ids = list(team1_ids) + list(team2_ids)
    a.status = "draft"
    return a


def _make_match() -> dict:
    return {"MatchId": MATCH_ID, "Alliance": "K98", "ArkWeekendDate": "2026-03-28"}


def _make_embed_mock():
    return MagicMock(spec=discord.Embed)


def _make_channel():
    channel = MagicMock()
    channel.send = AsyncMock()
    channel.fetch_message = AsyncMock(side_effect=Exception("no existing message"))
    return channel


def _make_client(channel):
    client = MagicMock()
    client.get_channel.return_value = channel
    return client


# ---------------------------------------------------------------------------
# Test 1 — mention message sent on first publish
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mention_message_sent_on_first_publish() -> None:
    """On first publish the 4th channel.send contains <@ mention strings."""
    roster = [
        _make_roster_row(101, "Chrislos", 9001),
        _make_roster_row(102, "BlazieP", 9002),
        _make_roster_row(103, "PlayerA", 9003),
        _make_roster_row(104, "PlayerB", 9004),
    ]
    assignment = _make_assignment(
        published_at_utc=None,
        team1_ids=[101, 102],
        team2_ids=[103, 104],
    )

    channel = _make_channel()
    client = _make_client(channel)

    with (
        patch("ark.team_publish.get_match", new=AsyncMock(return_value=_make_match())),
        patch("ark.team_publish.get_roster", new=AsyncMock(return_value=roster)),
        patch("ark.team_publish.insert_audit_log", new=AsyncMock(return_value=1)),
        patch("ark.team_publish._header_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish._team_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish.ensure_aware_utc", side_effect=lambda x: x),
        # H-SQL: patch SQL flag — first publish returns True
        patch("ark.team_publish.mark_teams_first_published", new=AsyncMock(return_value=True)),
    ):
        from ark.team_publish import publish_ark_teams

        store = MagicMock()
        store.assignments = {MATCH_ID: assignment}
        store.save = MagicMock()

        result = await publish_ark_teams(
            client=client,
            match_id=MATCH_ID,
            target_channel_id=CHANNEL_ID,
            actor_discord_id=ACTOR_ID,
            store=store,
        )

    assert result is True

    all_calls = channel.send.call_args_list
    # 3 embed sends + at least 1 mention send
    assert len(all_calls) >= 4, f"Expected ≥4 channel.send calls, got {len(all_calls)}"

    # The mention message must contain at least one <@ token
    mention_calls = [c for c in all_calls if "content" in (c.kwargs or {})]
    assert mention_calls, "Expected at least one send with content= kwarg for mention message"
    mention_content = mention_calls[0].kwargs["content"]
    assert "<@" in mention_content, f"Expected <@ token in mention content: {mention_content!r}"


# ---------------------------------------------------------------------------
# Test 2 — mention message NOT sent on republish
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mention_message_not_sent_on_republish() -> None:
    """On a republish the mention message must not be sent again."""
    roster = [
        _make_roster_row(101, "Chrislos", 9001),
        _make_roster_row(102, "BlazieP", 9002),
    ]
    assignment = _make_assignment(
        published_at_utc="2026-03-01T12:00:00Z",  # already published
        team1_ids=[101],
        team2_ids=[102],
    )

    channel = _make_channel()
    client = _make_client(channel)

    with (
        patch("ark.team_publish.get_match", new=AsyncMock(return_value=_make_match())),
        patch("ark.team_publish.get_roster", new=AsyncMock(return_value=roster)),
        patch("ark.team_publish.insert_audit_log", new=AsyncMock(return_value=1)),
        patch("ark.team_publish._header_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish._team_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish.ensure_aware_utc", side_effect=lambda x: x),
        # H-SQL: SQL flag already set — returns False (not first publish)
        patch("ark.team_publish.mark_teams_first_published", new=AsyncMock(return_value=False)),
    ):
        from ark.team_publish import publish_ark_teams

        store = MagicMock()
        store.assignments = {MATCH_ID: assignment}
        store.save = MagicMock()

        result = await publish_ark_teams(
            client=client,
            match_id=MATCH_ID,
            target_channel_id=CHANNEL_ID,
            actor_discord_id=ACTOR_ID,
            store=store,
        )

    assert result is True

    all_calls = channel.send.call_args_list
    assert (
        len(all_calls) == 3
    ), f"Expected exactly 3 sends on republish (no mention), got {len(all_calls)}"


# ---------------------------------------------------------------------------
# Test 3 — name fallback for players without Discord ID
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mention_message_uses_name_fallback_for_no_discord() -> None:
    """Players without a DiscordUserId appear by name, not as <@ mentions."""
    roster = [
        _make_roster_row(101, "Chrislos", 9001),
        _make_roster_row(102, "NoLinkPlayer", None),  # no Discord ID
    ]
    assignment = _make_assignment(
        published_at_utc=None,
        team1_ids=[101],
        team2_ids=[102],
    )

    channel = _make_channel()
    client = _make_client(channel)

    with (
        patch("ark.team_publish.get_match", new=AsyncMock(return_value=_make_match())),
        patch("ark.team_publish.get_roster", new=AsyncMock(return_value=roster)),
        patch("ark.team_publish.insert_audit_log", new=AsyncMock(return_value=1)),
        patch("ark.team_publish._header_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish._team_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish.ensure_aware_utc", side_effect=lambda x: x),
        patch("ark.team_publish.mark_teams_first_published", new=AsyncMock(return_value=True)),
    ):
        from ark.team_publish import publish_ark_teams

        store = MagicMock()
        store.assignments = {MATCH_ID: assignment}
        store.save = MagicMock()

        result = await publish_ark_teams(
            client=client,
            match_id=MATCH_ID,
            target_channel_id=CHANNEL_ID,
            actor_discord_id=ACTOR_ID,
            store=store,
        )

    assert result is True

    all_calls = channel.send.call_args_list
    assert len(all_calls) >= 4

    mention_calls = [c for c in all_calls if "content" in (c.kwargs or {})]
    assert mention_calls
    combined = " ".join(c.kwargs["content"] for c in mention_calls)
    assert (
        "NoLinkPlayer" in combined
    ), f"Expected 'NoLinkPlayer' name fallback in mention content: {combined!r}"
    assert "<@9002>" not in combined, "No Discord ID player must not get a mention token"


# ---------------------------------------------------------------------------
# Test 4 — mention skipped when no players in roster map
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mention_message_skipped_when_no_players_in_map(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When roster is empty, only 3 sends occur and a warning is logged."""
    assignment = _make_assignment(
        published_at_utc=None,
        team1_ids=[101, 102],
        team2_ids=[103, 104],
    )

    channel = _make_channel()
    client = _make_client(channel)

    with (
        patch("ark.team_publish.get_match", new=AsyncMock(return_value=_make_match())),
        patch("ark.team_publish.get_roster", new=AsyncMock(return_value=[])),  # empty roster
        patch("ark.team_publish.insert_audit_log", new=AsyncMock(return_value=1)),
        patch("ark.team_publish._header_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish._team_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish.ensure_aware_utc", side_effect=lambda x: x),
        patch("ark.team_publish.mark_teams_first_published", new=AsyncMock(return_value=True)),
        caplog.at_level(logging.WARNING, logger="ark.team_publish"),
    ):
        from ark.team_publish import publish_ark_teams

        store = MagicMock()
        store.assignments = {MATCH_ID: assignment}
        store.save = MagicMock()

        result = await publish_ark_teams(
            client=client,
            match_id=MATCH_ID,
            target_channel_id=CHANNEL_ID,
            actor_discord_id=ACTOR_ID,
            store=store,
        )

    assert (
        result is True
    ), "publish_ark_teams must still return True when mention message is skipped"

    all_calls = channel.send.call_args_list
    assert (
        len(all_calls) == 3
    ), f"Expected exactly 3 sends when no players found; got {len(all_calls)}"

    assert any(
        "mention_message_skipped" in r.message for r in caplog.records
    ), f"Expected mention_message_skipped warning; log records: {[r.message for r in caplog.records]}"


# ---------------------------------------------------------------------------
# Test 5 — mention message chunked for large roster
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mention_message_chunked_for_large_roster() -> None:
    """With 100 players all having Discord IDs, chunking occurs and no message exceeds 2000 chars."""
    num_players = 100
    roster = [_make_roster_row(1000 + i, f"Player{i}", 900000 + i) for i in range(num_players)]

    team1_ids = [1000 + i for i in range(num_players // 2)]
    team2_ids = [1000 + i for i in range(num_players // 2, num_players)]

    assignment = _make_assignment(
        published_at_utc=None,
        team1_ids=team1_ids,
        team2_ids=team2_ids,
    )

    channel = _make_channel()
    client = _make_client(channel)

    with (
        patch("ark.team_publish.get_match", new=AsyncMock(return_value=_make_match())),
        patch("ark.team_publish.get_roster", new=AsyncMock(return_value=roster)),
        patch("ark.team_publish.insert_audit_log", new=AsyncMock(return_value=1)),
        patch("ark.team_publish._header_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish._team_embed", return_value=_make_embed_mock()),
        patch("ark.team_publish.ensure_aware_utc", side_effect=lambda x: x),
        patch("ark.team_publish.mark_teams_first_published", new=AsyncMock(return_value=True)),
        patch("ark.team_publish.MENTION_CHUNK_LIMIT", 200),
    ):
        from ark.team_publish import publish_ark_teams

        store = MagicMock()
        store.assignments = {MATCH_ID: assignment}
        store.save = MagicMock()

        result = await publish_ark_teams(
            client=client,
            match_id=MATCH_ID,
            target_channel_id=CHANNEL_ID,
            actor_discord_id=ACTOR_ID,
            store=store,
        )

    assert result is True

    all_calls = channel.send.call_args_list
    assert len(all_calls) > 4, (
        f"Expected more than 4 channel.send calls for 100 players with chunk limit=200; "
        f"got {len(all_calls)}"
    )

    # No individual message content should exceed Discord's 2000-char limit
    for c in all_calls:
        content = (c.kwargs or {}).get("content")
        if content:
            assert (
                len(content) <= 2000
            ), f"Message exceeds 2000 chars ({len(content)}): {content[:100]!r}…"
