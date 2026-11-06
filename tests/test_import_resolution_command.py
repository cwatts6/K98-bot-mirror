from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import discord
import pytest

from commands import import_resolution as command_module


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case", ["allowed", "non_admin", "wrong_channel", "wrong_guild", "expired"]
)
@pytest.mark.parametrize("action", ["status", "preview", "resolve"])
async def test_resolution_checks_admin_channel_and_live_interaction(monkeypatch, case, action):
    import bot_config
    import decoraters
    from services import recovery_runtime
    from ui.views import recovery_view

    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(bot_config, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(bot_config, "GUILD_ID", 10)
    monkeypatch.setattr(decoraters, "usage_tracker", lambda: SimpleNamespace(log=AsyncMock()))
    group = discord.SlashCommandGroup("ops", "Admin")
    command_module.attach_import_resolution(group)
    command = group.subcommands[0]
    user = SimpleNamespace(id=31 if case == "non_admin" else 30, display_name="Operator")
    location = SimpleNamespace(id=41 if case == "wrong_channel" else 40, parent_id=None)
    response = SimpleNamespace(is_done=lambda: False, send_message=AsyncMock(), defer=AsyncMock())
    interaction = SimpleNamespace(
        user=user,
        guild=SimpleNamespace(id=10),
        guild_id=11 if case == "wrong_guild" else 10,
        channel_id=location.id,
        channel=location,
        response=response,
        followup=SimpleNamespace(send=AsyncMock()),
        data={
            "options": [
                {"name": "preparation_id", "type": 3, "value": str(uuid4())},
                {"name": "action", "type": 3, "value": action},
                {"name": "confirmation", "type": 3, "value": "a" * 64},
                {"name": "reason", "type": 3, "value": "reviewed synthetic failure"},
                {"name": "accept_partial", "type": 5, "value": True},
            ]
        },
    )
    ctx = SimpleNamespace(
        user=user,
        author=user,
        guild=interaction.guild,
        channel=location,
        interaction=interaction,
        command=command,
        respond=AsyncMock(),
    )
    row = {"incident": "current"}
    review = Mock(return_value=row)
    monkeypatch.setattr(recovery_runtime, "call_recovery", review)
    monkeypatch.setattr(recovery_view, "incident_embed", Mock(return_value="current evidence"))
    monkeypatch.setattr(recovery_view, "RecoveryIncidentView", Mock(return_value="guided buttons"))
    monkeypatch.setattr(command_module, "safe_defer", AsyncMock(return_value=case != "expired"))
    await command._invoke(ctx)
    assert review.call_count == (1 if case == "allowed" else 0)
    if case == "allowed":
        assert review.call_args.args[0] == "review_source"
        assert review.call_args.args[1].user_id == 30
        assert review.call_args.args[2] == "stats_import"
        if action == "resolve":
            assert "old token has not applied a repair" in ctx.respond.call_args.kwargs["content"]
        assert ctx.respond.call_args.kwargs["view"] == "guided buttons"
        assert ctx.respond.call_args.kwargs["ephemeral"] is True
        assert ctx.respond.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}
