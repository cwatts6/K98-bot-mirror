from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ark.reminder_types import REMINDER_24H, REMINDER_REGISTRATION_CLOSE_1H

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_match(
    *,
    now: datetime,
    close_offset: timedelta,
    reg_channel_id: int | None = 111,
    reg_message_id: int | None = 222,
) -> dict:
    """Return a minimal match dict with SignupCloseUtc relative to *now*."""
    close_dt = now + close_offset
    return {
        "MatchId": 1,
        "Alliance": "k98A",
        "ArkWeekendDate": date(2026, 3, 28),
        "MatchDay": "Sat",
        "MatchTimeUtc": datetime(2026, 3, 28, 11, 0, tzinfo=UTC).time(),
        "SignupCloseUtc": close_dt,
        "RegistrationStartsAtUtc": datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
        "RegistrationChannelId": reg_channel_id,
        "RegistrationMessageId": reg_message_id,
        "ConfirmationChannelId": 333,
        "Status": "scheduled",
        "AnnouncementSent": True,
    }


def _make_alliance_row(reg_channel_id: int = 111) -> dict:
    return {
        "RegistrationChannelId": reg_channel_id,
        "ConfirmationChannelId": 333,
    }


def _make_scheduler_state() -> MagicMock:
    """Return a mock ArkSchedulerState with a real-ish reminder_state."""
    state = MagicMock()
    state.match_locks = MagicMock()
    # make match_locks[x] behave as an async context manager
    lock = MagicMock()
    lock.__aenter__ = AsyncMock(return_value=None)
    lock.__aexit__ = AsyncMock(return_value=False)
    state.match_locks.__getitem__ = MagicMock(return_value=lock)
    state.reminder_state = MagicMock()
    state.reminder_state.should_send_with_grace = MagicMock(return_value=True)
    state.reminder_state.mark_sent = MagicMock()
    state.reminder_state.save = MagicMock()
    return state


def _make_client(guild_id: int | None = 12345, reg_channel_id: int = 111) -> MagicMock:
    """Return a mock Discord client whose get_channel returns a channel with a guild."""
    client = MagicMock()
    channel = MagicMock()
    channel.send = AsyncMock()
    if guild_id is not None:
        channel.guild = MagicMock()
        channel.guild.id = guild_id
    else:
        channel.guild = None
    client.get_channel = MagicMock(return_value=channel)
    return client


# ---------------------------------------------------------------------------
# Test 1 — close_1h reminder fires when now is within window (T-45min)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_1h_reminder_fires_in_window() -> None:
    now = datetime(2026, 3, 28, 8, 15, 0, tzinfo=UTC)  # 45 min before close at 09:00
    match = _make_match(now=now, close_offset=timedelta(minutes=45))
    state = _make_scheduler_state()
    client = _make_client()

    with (
        patch("ark.ark_scheduler.get_match", new=AsyncMock(return_value=match)),
        patch("ark.ark_scheduler.get_alliance", new=AsyncMock(return_value=_make_alliance_row())),
        patch(
            "ark.ark_scheduler.get_config",
            new=AsyncMock(return_value={"PlayersCap": 15, "SubsCap": 5}),
        ),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler._utcnow", return_value=now),
    ):
        from ark.ark_scheduler import _run_match_reminder_dispatch

        await _run_match_reminder_dispatch(client=client, state=state, match=match)

    # should_send_with_grace must have been called with the close_1h key
    calls = state.reminder_state.should_send_with_grace.call_args_list
    keys_checked = [c.kwargs.get("key", c.args[0] if c.args else None) for c in calls]
    assert any(
        REMINDER_REGISTRATION_CLOSE_1H in str(k) for k in keys_checked
    ), f"Expected should_send_with_grace called with close_1h key; got keys: {keys_checked}"

    # channel.send must have been called with @everyone via allowed_mentions.everyone=True
    channel = client.get_channel.return_value
    assert channel.send.called, "Expected channel.send to be called for close_1h reminder"
    call_kwargs = channel.send.call_args.kwargs
    allowed = call_kwargs.get("allowed_mentions")
    assert allowed is not None, "Expected allowed_mentions to be set on channel.send"
    # discord.AllowedMentions does not implement __eq__, so compare the field directly
    assert (
        getattr(allowed, "everyone", False) is True
    ), f"Expected allowed_mentions.everyone=True; got: {allowed!r}"


# ---------------------------------------------------------------------------
# Test 2 — close_1h reminder does NOT fire when now is 2h before close
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_1h_reminder_does_not_fire_before_window() -> None:
    now = datetime(2026, 3, 28, 7, 0, 0, tzinfo=UTC)  # 2h before close at 09:00
    match = _make_match(now=now, close_offset=timedelta(hours=2))
    state = _make_scheduler_state()
    # close_1h_sched is in the future so the `now >= close_1h_sched` guard blocks it
    state.reminder_state.should_send_with_grace = MagicMock(return_value=False)
    client = _make_client()

    with (
        patch("ark.ark_scheduler.get_match", new=AsyncMock(return_value=match)),
        patch("ark.ark_scheduler.get_alliance", new=AsyncMock(return_value=_make_alliance_row())),
        patch("ark.ark_scheduler.get_config", new=AsyncMock(return_value={})),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler._utcnow", return_value=now),
    ):
        from ark.ark_scheduler import _run_match_reminder_dispatch

        await _run_match_reminder_dispatch(client=client, state=state, match=match)

    channel = client.get_channel.return_value
    assert not channel.send.called, "channel.send should NOT be called when 2h before close"


# ---------------------------------------------------------------------------
# Test 3 — close_1h reminder does NOT fire after close_dt has passed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_1h_reminder_does_not_fire_after_close() -> None:
    # close_dt is 10 min in the past — now > close_dt, so the outer guard blocks the entire block
    now = datetime(2026, 3, 28, 9, 10, 0, tzinfo=UTC)
    match = _make_match(now=now, close_offset=timedelta(minutes=-10))
    state = _make_scheduler_state()
    client = _make_client()

    with (
        patch("ark.ark_scheduler.get_match", new=AsyncMock(return_value=match)),
        patch("ark.ark_scheduler.get_alliance", new=AsyncMock(return_value=_make_alliance_row())),
        patch("ark.ark_scheduler.get_config", new=AsyncMock(return_value={})),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler._utcnow", return_value=now),
    ):
        from ark.ark_scheduler import _run_match_reminder_dispatch

        await _run_match_reminder_dispatch(client=client, state=state, match=match)

    channel = client.get_channel.return_value
    assert not channel.send.called, "channel.send should NOT be called after close_dt has passed"


# ---------------------------------------------------------------------------
# Test 4 — close_1h includes jump link when RegistrationChannelId + MessageId are set
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_1h_includes_jump_link_when_ref_available() -> None:
    now = datetime(2026, 3, 28, 8, 15, 0, tzinfo=UTC)
    match = _make_match(
        now=now,
        close_offset=timedelta(minutes=45),
        reg_channel_id=111,
        reg_message_id=222,
    )
    state = _make_scheduler_state()
    client = _make_client(guild_id=12345, reg_channel_id=111)

    with (
        patch("ark.ark_scheduler.get_match", new=AsyncMock(return_value=match)),
        patch("ark.ark_scheduler.get_alliance", new=AsyncMock(return_value=_make_alliance_row())),
        patch("ark.ark_scheduler.get_config", new=AsyncMock(return_value={})),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler._utcnow", return_value=now),
    ):
        from ark.ark_scheduler import _run_match_reminder_dispatch

        await _run_match_reminder_dispatch(client=client, state=state, match=match)

    channel = client.get_channel.return_value
    assert channel.send.called, "Expected channel.send to be called"
    content = channel.send.call_args.kwargs.get("content", "")
    assert (
        "https://discord.com/channels/12345/111/222" in content
    ), f"Expected jump URL in content; got: {content!r}"


# ---------------------------------------------------------------------------
# Test 5 — close_1h omits jump link when RegistrationMessageId is None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_1h_omits_link_when_no_ref() -> None:
    now = datetime(2026, 3, 28, 8, 15, 0, tzinfo=UTC)
    match = _make_match(
        now=now,
        close_offset=timedelta(minutes=45),
        reg_channel_id=111,
        reg_message_id=None,
    )
    state = _make_scheduler_state()
    client = _make_client(guild_id=12345, reg_channel_id=111)

    with (
        patch("ark.ark_scheduler.get_match", new=AsyncMock(return_value=match)),
        patch("ark.ark_scheduler.get_alliance", new=AsyncMock(return_value=_make_alliance_row())),
        patch("ark.ark_scheduler.get_config", new=AsyncMock(return_value={})),
        patch("ark.ark_scheduler.get_roster", new=AsyncMock(return_value=[])),
        patch("ark.ark_scheduler._utcnow", return_value=now),
    ):
        from ark.ark_scheduler import _run_match_reminder_dispatch

        await _run_match_reminder_dispatch(client=client, state=state, match=match)

    channel = client.get_channel.return_value
    assert channel.send.called, "Expected channel.send to be called"
    content = channel.send.call_args.kwargs.get("content", "")
    assert (
        "https://discord.com/channels/" not in content
    ), f"Expected NO jump URL when RegistrationMessageId is None; got: {content!r}"


# ---------------------------------------------------------------------------
# Test 6 — REMINDER_24H does not appear in the windows dispatch list
# ---------------------------------------------------------------------------


def test_24h_window_not_in_dispatch() -> None:
    """Confirm REMINDER_24H is not present in the windows list inside _run_match_reminder_dispatch."""
    import ast
    import inspect

    from ark.ark_scheduler import _run_match_reminder_dispatch

    source = inspect.getsource(_run_match_reminder_dispatch)
    tree = ast.parse(source)

    # Walk all string constants in the AST — REMINDER_24H resolves to "24h"
    string_literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value)

    assert REMINDER_24H not in string_literals, (
        f"REMINDER_24H value {REMINDER_24H!r} found as a literal in _run_match_reminder_dispatch "
        f"— it must not appear in the windows list"
    )

    # Also confirm the constant itself isn't referenced by name in the windows assignment
    # (belt-and-suspenders: check no Name node references REMINDER_24H by identifier)
    name_refs: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name_refs.append(node.id)

    assert (
        "REMINDER_24H" not in name_refs
    ), "REMINDER_24H identifier found in _run_match_reminder_dispatch — it must be removed from windows"
