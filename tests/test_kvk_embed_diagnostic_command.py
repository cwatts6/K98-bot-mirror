import types

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["allowed", "owner", "notify", "guild", "permissions", "defer"])
@pytest.mark.parametrize("mode", ["defaults", "run", "status"])
async def test_kvk_preview_real_pycord_invocation(monkeypatch, case, mode):
    from unittest.mock import AsyncMock, Mock

    import discord

    import bot_config
    from commands import stats_cmds as prekvk_cmds
    import decoraters
    from stats_alerts import kvk_diagnostics as diagnostics

    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(bot_config, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(decoraters, "usage_tracker", lambda: types.SimpleNamespace(log=AsyncMock()))
    monkeypatch.setattr(prekvk_cmds, "GUILD_ID", 10)
    groups = []
    bot = types.SimpleNamespace(
        add_application_command=groups.append, slash_command=lambda **kwargs: lambda fn: fn
    )
    prekvk_cmds.register_stats(bot)
    ops = next(group for group in groups if group.name == "kvk_admin")
    command = next(cmd for cmd in ops.subcommands if cmd.name == "test_embed")
    assert command.callback.__version__ == "v1.05"
    payload_options = {option["name"]: option for option in command.to_dict()["options"]}
    assert set(payload_options) == {"destination", "action", "session"}
    assert payload_options["destination"]["type"] == 7
    assert payload_options["destination"]["required"] is True
    assert payload_options["action"]["type"] == 3
    assert [choice["value"] for choice in payload_options["action"]["choices"]] == ["run", "status"]
    assert payload_options["session"]["type"] == 3
    assert payload_options["session"]["required"] is False
    user = types.SimpleNamespace(id=31 if case == "owner" else 30, display_name="Operator")
    guild = types.SimpleNamespace(id=11 if case == "guild" else 10, me=object())
    location = types.SimpleNamespace(id=41 if case == "notify" else 40, parent_id=None)
    response = types.SimpleNamespace(
        is_done=lambda: False, send_message=AsyncMock(), defer=AsyncMock()
    )
    interaction = types.SimpleNamespace(
        user=user,
        guild=guild,
        channel=location,
        response=response,
        followup=types.SimpleNamespace(send=AsyncMock()),
    )
    ctx = types.SimpleNamespace(
        user=user, guild=guild, channel=location, interaction=interaction, command=command, bot=bot
    )
    target = Mock(spec=discord.TextChannel)
    target.id = 20
    target.guild = types.SimpleNamespace(id=10)
    target.type = discord.ChannelType.text
    target.permissions_for.return_value = types.SimpleNamespace(
        view_channel=True,
        send_messages=case != "permissions",
        embed_links=True,
        read_message_history=True,
    )
    execute = AsyncMock(
        return_value=diagnostics.DiagnosticResult("status", "a" * 32, "observation")
    )
    monkeypatch.setattr(diagnostics.runner, "execute", execute)
    monkeypatch.setattr(prekvk_cmds, "safe_defer", AsyncMock(return_value=case != "defer"))
    guild._channels = {20: target}
    guild._threads = {}
    guild.get_channel_or_thread = lambda channel_id: guild._channels.get(channel_id)
    options = [{"name": "destination", "type": 7, "value": "20"}]
    if mode != "defaults":
        options += [
            {"name": "action", "type": 3, "value": mode},
            {"name": "session", "type": 3, "value": "a" * 32},
        ]
    interaction.data = {
        "options": options,
        "resolved": {"channels": {"20": {"id": "20", "type": 0, "name": "diagnostic"}}},
    }
    await command._invoke(ctx)
    assert execute.await_count == (1 if case == "allowed" else 0)
    replies = response.send_message.call_args_list + interaction.followup.send.call_args_list
    for reply in replies:
        assert reply.kwargs["ephemeral"] is True
        assert not any(token in str(reply.args) for token in ("@everyone", "@here", "<@"))
    if case == "allowed":
        assert execute.call_args.kwargs["channel_id"] == target.id
        assert execute.call_args.kwargs["action"] == ("run" if mode == "defaults" else mode)
        assert execute.call_args.kwargs["token"] == (None if mode == "defaults" else "a" * 32)
        assert replies[0].kwargs["allowed_mentions"].to_dict() == {"parse": []}
