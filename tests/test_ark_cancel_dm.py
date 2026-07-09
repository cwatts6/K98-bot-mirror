from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ark.reminders import cancel_match_reminders, dispatch_cancel_dms


def _make_match() -> dict:
    return {
        "MatchId": 42,
        "Alliance": "k98A",
        "Status": "scheduled",
    }


def _make_row(
    *,
    discord_user_id: int | None,
    status: str = "Active",
    governor_name: str = "PlayerOne",
) -> dict:
    return {
        "DiscordUserId": discord_user_id,
        "Status": status,
        "GovernorNameSnapshot": governor_name,
    }


def _make_client_for_users(users_by_id: dict[int, MagicMock]) -> MagicMock:
    """Build a fake client where get_user returns None (forces fetch_user path)."""
    client = MagicMock()
    # get_user returns None so the code falls through to fetch_user (CR9)
    client.get_user.return_value = None
    client.fetch_user = AsyncMock(side_effect=lambda user_id: users_by_id[user_id])
    return client


@pytest.mark.asyncio
async def test_cancel_dm_sent_to_active_players() -> None:
    roster = [
        _make_row(discord_user_id=1001, governor_name="Alpha"),
        _make_row(discord_user_id=1002, governor_name="Bravo"),
    ]

    user1 = MagicMock()
    user1.send = AsyncMock()
    user2 = MagicMock()
    user2.send = AsyncMock()
    client = _make_client_for_users({1001: user1, 1002: user2})

    reminder_state = MagicMock()
    reminder_state.was_sent.return_value = False
    reminder_state.mark_sent = MagicMock()
    reminder_state.save = MagicMock()
    reminder_state.reminders = {}

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        counters = await dispatch_cancel_dms(
            client=client,
            match_id=42,
            match=_make_match(),
            roster=roster,
        )

    assert counters == {"attempted": 2, "sent": 2, "skipped_dedupe": 0, "failed": 0}
    assert user1.send.await_count == 1
    assert user2.send.await_count == 1

    embed1 = user1.send.await_args.kwargs["embed"]
    embed2 = user2.send.await_args.kwargs["embed"]
    assert "Cancelled" in embed1.title
    assert "Cancelled" in embed2.title


@pytest.mark.asyncio
async def test_cancel_dm_skips_inactive_players() -> None:
    roster = [
        _make_row(discord_user_id=1001, status="Active", governor_name="Alpha"),
        _make_row(discord_user_id=1002, status="Inactive", governor_name="Bravo"),
    ]

    user1 = MagicMock()
    user1.send = AsyncMock()
    client = _make_client_for_users({1001: user1})

    reminder_state = MagicMock()
    reminder_state.was_sent.return_value = False
    reminder_state.mark_sent = MagicMock()
    reminder_state.save = MagicMock()
    reminder_state.reminders = {}

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        counters = await dispatch_cancel_dms(
            client=client,
            match_id=42,
            match=_make_match(),
            roster=roster,
        )

    assert counters == {"attempted": 1, "sent": 1, "skipped_dedupe": 0, "failed": 0}
    assert user1.send.await_count == 1


@pytest.mark.asyncio
async def test_cancel_dm_skips_players_without_discord_id() -> None:
    roster = [
        _make_row(discord_user_id=None, governor_name="NoLink"),
    ]

    client = MagicMock()
    client.get_user.return_value = None

    reminder_state = MagicMock()
    reminder_state.was_sent.return_value = False
    reminder_state.mark_sent = MagicMock()
    reminder_state.save = MagicMock()
    reminder_state.reminders = {}

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        counters = await dispatch_cancel_dms(
            client=client,
            match_id=42,
            match=_make_match(),
            roster=roster,
        )

    assert counters == {"attempted": 0, "sent": 0, "skipped_dedupe": 0, "failed": 0}
    assert not client.fetch_user.called


@pytest.mark.asyncio
async def test_cancel_dm_deduplication() -> None:
    roster = [
        _make_row(discord_user_id=1001, governor_name="Alpha"),
        _make_row(discord_user_id=1002, governor_name="Bravo"),
    ]

    user2 = MagicMock()
    user2.send = AsyncMock()
    client = _make_client_for_users({1002: user2})

    reminder_state = MagicMock()
    reminder_state.was_sent.side_effect = lambda key: key == "42|1001|cancelled"
    reminder_state.mark_sent = MagicMock()
    reminder_state.save = MagicMock()
    reminder_state.reminders = {"42|1001|cancelled": "2026-03-26T00:00:00Z"}

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        counters = await dispatch_cancel_dms(
            client=client,
            match_id=42,
            match=_make_match(),
            roster=roster,
        )

    assert counters == {"attempted": 1, "sent": 1, "skipped_dedupe": 1, "failed": 0}
    assert user2.send.await_count == 1


@pytest.mark.asyncio
async def test_cancel_dm_forbidden_is_marked_sent() -> None:
    roster = [
        _make_row(discord_user_id=1001, governor_name="Alpha"),
    ]

    import discord as _discord

    user1 = MagicMock()
    # Simulate discord.Forbidden — needs to be an actual subclass for isinstance checks,
    # but since we're patching discord.Forbidden in reminders.py we use the real one.
    user1.send = AsyncMock(side_effect=_discord.Forbidden(MagicMock(), "DMs disabled"))
    client = _make_client_for_users({1001: user1})

    reminder_state = MagicMock()
    reminder_state.was_sent.return_value = False
    reminder_state.mark_sent = MagicMock()
    reminder_state.save = MagicMock()
    reminder_state.reminders = {}

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        counters = await dispatch_cancel_dms(
            client=client,
            match_id=42,
            match=_make_match(),
            roster=roster,
        )

    assert counters == {"attempted": 1, "sent": 0, "skipped_dedupe": 0, "failed": 1}
    reminder_state.mark_sent.assert_called_once_with("42|1001|cancelled")


@pytest.mark.asyncio
async def test_cancel_dm_unexpected_exception_not_marked_sent() -> None:
    roster = [
        _make_row(discord_user_id=1001, governor_name="Alpha"),
    ]

    user1 = MagicMock()
    user1.send = AsyncMock(side_effect=Exception("boom"))
    client = _make_client_for_users({1001: user1})

    reminder_state = MagicMock()
    reminder_state.was_sent.return_value = False
    reminder_state.mark_sent = MagicMock()
    reminder_state.save = MagicMock()
    reminder_state.reminders = {}

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        counters = await dispatch_cancel_dms(
            client=client,
            match_id=42,
            match=_make_match(),
            roster=roster,
        )

    assert counters == {"attempted": 1, "sent": 0, "skipped_dedupe": 0, "failed": 1}
    reminder_state.mark_sent.assert_not_called()


def test_cancel_match_reminders_uses_reminder_state() -> None:
    reminder_state = MagicMock()
    reminder_state.reminders = {
        "42|1001|24h": "2026-03-26T00:00:00Z",
        "42|1002|cancelled": "2026-03-26T00:00:00Z",
        "99|1001|24h": "2026-03-26T00:00:00Z",
    }
    reminder_state.save = MagicMock()

    with patch("ark.reminders.ArkReminderState.load", return_value=reminder_state):
        changed = cancel_match_reminders(42)

    assert changed is True
    assert "42|1001|24h" not in reminder_state.reminders
    assert "42|1002|cancelled" in reminder_state.reminders  # CR1: cancelled keys are preserved
    assert "99|1001|24h" in reminder_state.reminders
    reminder_state.save.assert_called_once()
    assert inspect.iscoroutinefunction(cancel_match_reminders) is False
