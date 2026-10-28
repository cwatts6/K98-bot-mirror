from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.event_cache_service import RefreshResult, UpcomingEventCacheSnapshot


@pytest.mark.asyncio
@pytest.mark.parametrize("command_name", ["refresh", "refresh_kvk_overview"])
@pytest.mark.parametrize(
    "case", ["allowed", "wrong_admin", "wrong_channel", "pending", "failed", "memory_only"]
)
async def test_refresh_permissions_and_truthful_results(monkeypatch, command_name, case):
    from commands import events_cmds as commands
    import decoraters

    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(decoraters, "usage_tracker", lambda: SimpleNamespace(log=AsyncMock()))
    groups = []
    bot = SimpleNamespace(
        add_application_command=groups.append, slash_command=lambda **kw: lambda fn: fn
    )
    commands.register_events(bot)
    group = next(group for group in groups if group.name == "events")
    command = next(cmd for cmd in group.subcommands if cmd.name == command_name)
    stamp = datetime(2026, 10, 20, tzinfo=UTC)
    status = {"pending": "pending", "failed": "failed", "memory_only": "refreshed_memory_only"}.get(
        case, "refreshed"
    )
    result = RefreshResult(1, status, "succeeded", "replaced", "saved", 0, 1, stamp)
    refresh = AsyncMock(return_value=result)
    update = AsyncMock(return_value="not_in_kvk_no_message")
    monkeypatch.setattr(commands, "refresh_event_cache_result", refresh)
    monkeypatch.setattr(commands, "is_cache_stale", lambda: True)
    monkeypatch.setattr(
        commands,
        "get_upcoming_event_cache_snapshot",
        lambda: UpcomingEventCacheSnapshot(True, (), stamp, True),
    )
    monkeypatch.setattr(commands, "update_live_event_embeds", update)
    monkeypatch.setattr(commands, "post_or_update_daily_KVK_overview", update)
    defer = AsyncMock()
    monkeypatch.setattr(commands, "safe_defer", defer)
    user = SimpleNamespace(id=31 if case == "wrong_admin" else 30, display_name="Operator")
    channel = SimpleNamespace(id=41 if case == "wrong_channel" else 40, parent_id=None)
    response = SimpleNamespace(is_done=lambda: False, send_message=AsyncMock())
    interaction = SimpleNamespace(
        user=user,
        channel=channel,
        guild=SimpleNamespace(id=10),
        response=response,
        followup=SimpleNamespace(send=AsyncMock()),
        edit_original_response=AsyncMock(),
        data={"options": []},
    )
    ctx = SimpleNamespace(
        user=user,
        author=user,
        channel=channel,
        guild=interaction.guild,
        interaction=interaction,
        command=command,
    )
    await command.callback(ctx)
    if case.startswith("wrong_"):
        refresh.assert_not_awaited()
        update.assert_not_awaited()
        assert response.send_message.call_args.kwargs["ephemeral"]
    else:
        refresh.assert_awaited_once_with(observation_seconds=10.0)
        assert defer.call_args.kwargs["ephemeral"]
        text = interaction.edit_original_response.call_args.kwargs["content"]
        assert "2026-10-20" in text
        if case == "pending":
            update.assert_not_awaited()
            assert "still running" in text
        else:
            update.assert_awaited_once()
            if command_name == "refresh_kvk_overview":
                assert "Overview disposition: not_in_kvk_no_message" in text
                assert "Live visual acceptance is separate" in text
            else:
                assert "delivery is not independently verified" in text
        if case == "failed":
            assert "failed or was interrupted" in text
        if case == "memory_only":
            assert "saving the cache failed" in text
