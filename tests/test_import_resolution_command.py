from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import discord
import pytest

from commands import import_resolution as command_module


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["allowed", "non_admin", "wrong_channel", "expired"])
async def test_resolution_checks_admin_channel_and_live_interaction(monkeypatch, case):
    import decoraters

    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
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
        channel=location,
        response=response,
        followup=SimpleNamespace(send=AsyncMock()),
        data={
            "options": [
                {"name": "preparation_id", "type": 3, "value": str(uuid4())},
                {"name": "action", "type": 3, "value": "resolve"},
                {"name": "confirmation", "type": 3, "value": "a" * 64},
                {"name": "reason", "type": 3, "value": "reviewed synthetic failure"},
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
    execute = Mock(return_value="No import replay; resolution recorded.")
    monkeypatch.setattr(command_module, "operate_import_resolution", execute)
    monkeypatch.setattr(command_module, "safe_defer", AsyncMock(return_value=case != "expired"))
    await command._invoke(ctx)
    assert execute.call_count == (1 if case == "allowed" else 0)
    if case == "allowed":
        assert execute.call_args.args[-1] == "discord:30"
        assert ctx.respond.call_args.kwargs["ephemeral"] is True
        assert ctx.respond.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}
