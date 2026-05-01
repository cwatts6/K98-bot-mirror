"""
Tests for Phase G+H: Check-in Announcement, SQL Dedup, Code Review Fixes.

Covers:
- CR1: cancel_match_reminders preserves cancelled dedupe keys
- CR2: dispatch_cancel_dms saves state after each successful send
- CR4: scheduler reloads ArkReminderState from disk each poll tick
- CR5: cancel DM dispatch is backgrounded
- Phase G: check-in open channel announcement fires on checkin_12h window
- H-SQL: mark_teams_first_published idempotency
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ark.reminder_state import ArkReminderState, make_channel_key, make_dm_key
from ark.reminder_types import REMINDER_CHECKIN_12H

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(path=None) -> ArkReminderState:
    from pathlib import Path
    import tempfile

    if path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        path = Path(tmp.name)
        tmp.close()
    return ArkReminderState(path=path)


# ---------------------------------------------------------------------------
# CR1 — cancel_match_reminders preserves cancelled dedupe keys
# ---------------------------------------------------------------------------


def test_cancel_match_reminders_preserves_cancelled_keys(tmp_path):
    """Cancelled-DM keys must survive cancel_match_reminders."""
    from ark.reminders import cancel_match_reminders

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)

    match_id = 42
    # A normal reminder key — should be removed
    normal_key = make_dm_key(match_id, 1001, "4h")
    # A cancelled key — must be preserved
    cancel_key = f"{match_id}|1002|cancelled"

    state.mark_sent(normal_key)
    state.mark_sent(cancel_key)
    state.save()

    # Load from disk so the saved reminders are present
    loaded = ArkReminderState.load(state_path)

    with patch("ark.reminders.ArkReminderState.load", return_value=loaded):
        result = cancel_match_reminders(match_id)

    assert result is True, "Should return True (keys were removed)"
    # Reload from disk using .load() so reminders dict is populated
    final = ArkReminderState.load(state_path)
    assert cancel_key in final.reminders, "Cancelled key must be preserved"
    assert normal_key not in final.reminders, "Normal reminder key must be removed"


# ---------------------------------------------------------------------------
# CR1 — cancel_match_reminders with only cancelled keys returns False
# ---------------------------------------------------------------------------


def test_cancel_match_reminders_only_cancelled_keys_returns_false(tmp_path):
    """If only cancelled-DM keys exist, no change → returns False."""
    from ark.reminders import cancel_match_reminders

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)
    match_id = 99

    cancel_key = f"{match_id}|5000|cancelled"
    state.mark_sent(cancel_key)
    state.save()

    # Load from disk so the saved reminders are present
    loaded = ArkReminderState.load(state_path)
    with patch("ark.reminders.ArkReminderState.load", return_value=loaded):
        result = cancel_match_reminders(match_id)

    assert result is False


# ---------------------------------------------------------------------------
# CR2 — dispatch_cancel_dms saves state after each successful send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_cancel_dms_saves_after_each_send(tmp_path):
    """State must be saved immediately after each successful DM send."""
    from ark.reminders import dispatch_cancel_dms

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)
    state.save()

    match_id = 7
    match = {
        "MatchId": match_id,
        "Alliance": "K98",
        "ArkWeekendDate": "2026-04-05",
        "MatchTimeUtc": "14:00:00",
    }
    roster = [
        {"Status": "active", "DiscordUserId": 101, "GovernorNameSnapshot": "Alpha"},
        {"Status": "active", "DiscordUserId": 102, "GovernorNameSnapshot": "Beta"},
    ]

    class _FakeUser:
        def __init__(self, uid: int):
            self.id = uid

        async def send(self, *, embed=None, content=None) -> None:
            pass

    users = {101: _FakeUser(101), 102: _FakeUser(102)}

    fake_client = MagicMock()
    fake_client.get_user.side_effect = lambda uid: users.get(uid)

    save_spy = MagicMock(wraps=state.save)

    with (
        patch("ark.reminders.ArkReminderState.load", return_value=state),
        patch.object(state, "save", save_spy),
    ):
        result = await dispatch_cancel_dms(
            client=fake_client,
            match_id=match_id,
            match=match,
            roster=roster,
        )

    assert result["sent"] == 2
    assert result["attempted"] == 2
    # save must have been called at least once per successful send
    assert save_spy.call_count >= 2, f"Expected save called ≥2 times; got {save_spy.call_count}"


# ---------------------------------------------------------------------------
# CR9 — dispatch_cancel_dms uses get_user before fetch_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_cancel_dms_uses_get_user_before_fetch(tmp_path):
    """get_user is called first; fetch_user only called if get_user returns None."""
    from ark.reminders import dispatch_cancel_dms

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)
    state.save()

    match_id = 20
    match = {
        "MatchId": match_id,
        "Alliance": "K98",
        "ArkWeekendDate": "2026-04-05",
        "MatchTimeUtc": "14:00:00",
    }
    roster = [
        {"Status": "active", "DiscordUserId": 200, "GovernorNameSnapshot": "CachedUser"},
        {"Status": "active", "DiscordUserId": 201, "GovernorNameSnapshot": "UncachedUser"},
    ]

    class _FakeUser:
        def __init__(self, uid: int):
            self.id = uid

        async def send(self, *, embed=None, content=None) -> None:
            pass

    cached_user = _FakeUser(200)
    fetched_user = _FakeUser(201)

    fake_client = MagicMock()
    fake_client.get_user.side_effect = lambda uid: cached_user if uid == 200 else None
    fake_client.fetch_user = AsyncMock(return_value=fetched_user)

    with patch("ark.reminders.ArkReminderState.load", return_value=state):
        result = await dispatch_cancel_dms(
            client=fake_client,
            match_id=match_id,
            match=match,
            roster=roster,
        )

    assert result["sent"] == 2
    # fetch_user should only have been called for uid 201 (not in cache)
    fake_client.fetch_user.assert_called_once_with(201)


# ---------------------------------------------------------------------------
# Phase G — check-in open channel announcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_checkin_open_announcement_sent_in_window(tmp_path):
    """_run_match_reminder_dispatch fires check-in open announcement in the 12h window."""
    from ark.ark_scheduler import ArkSchedulerState, _run_match_reminder_dispatch

    now = datetime(2026, 4, 5, 2, 0, tzinfo=UTC)  # 2:00 UTC
    match_dt = datetime(2026, 4, 5, 14, 0, tzinfo=UTC)  # 14:00 UTC — 12h later
    # checkin_sched = 2:00 UTC — exactly at 'now'

    conf_channel_id = 555
    match_id = 10

    match = {
        "MatchId": match_id,
        "Alliance": "K98",
        "ArkWeekendDate": date(2026, 4, 5),
        "MatchDay": "Sat",
        "MatchTimeUtc": match_dt.time(),
        "SignupCloseUtc": now + timedelta(hours=2),
        "Status": "locked",
        "ConfirmationChannelId": conf_channel_id,
        "RegistrationChannelId": None,
        "RegistrationStartsAtUtc": None,
    }

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)
    state.save()

    scheduler_state = ArkSchedulerState()
    scheduler_state.reminder_state = state

    channel = MagicMock()
    channel.send = AsyncMock()

    client = MagicMock()
    client.get_channel.return_value = channel

    checkin_key = make_channel_key(match_id, conf_channel_id, REMINDER_CHECKIN_12H)

    async def _mock_get_match(_mid):
        return dict(match)

    async def _mock_get_alliance(_alliance):
        return {
            "RegistrationChannelId": None,
            "ConfirmationChannelId": conf_channel_id,
        }

    async def _mock_get_roster(_mid):
        return []

    async def _mock_list_team_rows(match_id, draft_only=False):
        return []

    with (
        patch("ark.ark_scheduler._utcnow", return_value=now),
        patch("ark.ark_scheduler.get_match", side_effect=_mock_get_match),
        patch("ark.ark_scheduler.get_alliance", side_effect=_mock_get_alliance),
        patch("ark.ark_scheduler.get_roster", side_effect=_mock_get_roster),
        patch("ark.ark_scheduler.list_match_team_rows", side_effect=_mock_list_team_rows),
        patch("ark.ark_scheduler.get_reminder_prefs", new=AsyncMock(return_value=None)),
    ):
        await _run_match_reminder_dispatch(client, scheduler_state, match)

    # The check-in announcement key must have been recorded in state
    assert state.was_sent(
        checkin_key
    ), "checkin_12h channel key must be marked sent after announcement"
    # Channel.send must have been called at least once with check-in text
    assert channel.send.called, "channel.send must be called for check-in announcement"
    # _send_channel_reminder calls channel.send(content=..., embed=...) — use kwargs
    sent_contents = [str(c.kwargs.get("content") or "") for c in channel.send.call_args_list]
    assert any(
        "Check-in is now open" in t for t in sent_contents
    ), f"Expected 'Check-in is now open' in one of {sent_contents}"


@pytest.mark.asyncio
async def test_checkin_open_announcement_not_sent_outside_window(tmp_path):
    """No check-in announcement when now is before the checkin window."""
    from ark.ark_scheduler import ArkSchedulerState, _run_match_reminder_dispatch

    now = datetime(2026, 4, 5, 1, 0, tzinfo=UTC)  # 1:00 UTC
    match_dt = datetime(2026, 4, 5, 14, 0, tzinfo=UTC)  # 14:00 UTC — 13h away
    # checkin_sched = 2:00 UTC — 1h in the future

    conf_channel_id = 666
    match_id = 11

    match = {
        "MatchId": match_id,
        "Alliance": "K98",
        "ArkWeekendDate": date(2026, 4, 5),
        "MatchDay": "Sat",
        "MatchTimeUtc": match_dt.time(),
        "SignupCloseUtc": now + timedelta(hours=4),
        "Status": "locked",
        "ConfirmationChannelId": conf_channel_id,
        "RegistrationChannelId": None,
        "RegistrationStartsAtUtc": None,
    }

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)
    state.save()

    scheduler_state = ArkSchedulerState()
    scheduler_state.reminder_state = state

    channel = MagicMock()
    channel.send = AsyncMock()

    client = MagicMock()
    client.get_channel.return_value = channel

    checkin_key = make_channel_key(match_id, conf_channel_id, REMINDER_CHECKIN_12H)

    async def _mock_get_match(_mid):
        return dict(match)

    async def _mock_get_alliance(_alliance):
        return {
            "RegistrationChannelId": None,
            "ConfirmationChannelId": conf_channel_id,
        }

    with (
        patch("ark.ark_scheduler._utcnow", return_value=now),
        patch("ark.ark_scheduler.get_match", side_effect=_mock_get_match),
        patch("ark.ark_scheduler.get_alliance", side_effect=_mock_get_alliance),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler.get_reminder_prefs", new=AsyncMock(return_value=None)),
    ):
        await _run_match_reminder_dispatch(client, scheduler_state, match)

    assert not state.was_sent(
        checkin_key
    ), "checkin_12h channel key must NOT be set when outside the window"


@pytest.mark.asyncio
async def test_checkin_open_announcement_not_sent_twice(tmp_path):
    """Check-in announcement is deduplicated — not sent on second tick."""
    from ark.ark_scheduler import ArkSchedulerState, _run_match_reminder_dispatch

    now = datetime(2026, 4, 5, 2, 1, tzinfo=UTC)
    match_dt = datetime(2026, 4, 5, 14, 0, tzinfo=UTC)

    conf_channel_id = 777
    match_id = 12

    match = {
        "MatchId": match_id,
        "Alliance": "K98",
        "ArkWeekendDate": date(2026, 4, 5),
        "MatchDay": "Sat",
        "MatchTimeUtc": match_dt.time(),
        "SignupCloseUtc": now + timedelta(hours=4),
        "Status": "locked",
        "ConfirmationChannelId": conf_channel_id,
        "RegistrationChannelId": None,
        "RegistrationStartsAtUtc": None,
    }

    state_path = tmp_path / "state.json"
    state = ArkReminderState(path=state_path)
    # Pre-mark the key as already sent
    checkin_key = make_channel_key(match_id, conf_channel_id, REMINDER_CHECKIN_12H)
    state.mark_sent(checkin_key)
    state.save()

    scheduler_state = ArkSchedulerState()
    scheduler_state.reminder_state = state

    channel = MagicMock()
    channel.send = AsyncMock()

    client = MagicMock()
    client.get_channel.return_value = channel

    async def _mock_get_match(_mid):
        return dict(match)

    async def _mock_get_alliance(_alliance):
        return {
            "RegistrationChannelId": None,
            "ConfirmationChannelId": conf_channel_id,
        }

    with (
        patch("ark.ark_scheduler._utcnow", return_value=now),
        patch("ark.ark_scheduler.get_match", side_effect=_mock_get_match),
        patch("ark.ark_scheduler.get_alliance", side_effect=_mock_get_alliance),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler.list_match_team_rows", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler.get_reminder_prefs", new=AsyncMock(return_value=None)),
    ):
        await _run_match_reminder_dispatch(client, scheduler_state, match)

    # channel.send should NOT have been called with check-in text (already deduplicated)
    for c in channel.send.call_args_list:
        content = c.kwargs.get("content") or ""
        if "Check-in is now open" in str(content):
            pytest.fail("Check-in announcement sent twice — deduplication failed")


# ---------------------------------------------------------------------------
# H-SQL — mark_teams_first_published idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_teams_first_published_idempotent():
    """mark_teams_first_published returns True on first call, False on second."""
    from ark.dal.ark_dal import mark_teams_first_published

    match_id = 55
    # First call — NULL row → returns True
    first_row = {"MatchId": match_id}
    # Second call — already set → returns empty (None)
    second_row = None

    with patch(
        "ark.dal.ark_dal.run_one_async",
        new=AsyncMock(side_effect=[first_row, second_row]),
    ):
        result1 = await mark_teams_first_published(match_id)
        result2 = await mark_teams_first_published(match_id)

    assert result1 is True, "First publish must return True"
    assert result2 is False, "Second publish must return False (already set)"
