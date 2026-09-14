import types

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["allowed", "owner", "notify", "guild", "permissions", "defer"])
@pytest.mark.parametrize("selected", [None, 15])
@pytest.mark.parametrize("mode", ["defaults", "run", "status"])
async def test_kvk_preview_real_pycord_invocation(monkeypatch, case, mode, selected):
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
    assert command.callback.__version__ == "v1.06"
    payload_options = {option["name"]: option for option in command.to_dict()["options"]}
    assert set(payload_options) == {"destination", "action", "session", "kvk_no"}
    assert payload_options["destination"]["type"] == 7
    assert payload_options["destination"]["required"] is True
    assert payload_options["action"]["type"] == 3
    assert [choice["value"] for choice in payload_options["action"]["choices"]] == ["run", "status"]
    assert payload_options["session"]["type"] == 3
    assert payload_options["session"]["required"] is False
    assert payload_options["kvk_no"]["type"] == 4
    assert payload_options["kvk_no"]["required"] is False
    assert payload_options["kvk_no"]["min_value"] == 1
    assert payload_options["kvk_no"]["max_value"] == 2147483647
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
    if selected is not None:
        options.append({"name": "kvk_no", "type": 4, "value": selected})
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
        assert execute.call_args.kwargs["kvk_no"] == selected
        assert execute.call_args.kwargs["channel_id"] == target.id
        assert execute.call_args.kwargs["action"] == ("run" if mode == "defaults" else mode)
        assert execute.call_args.kwargs["token"] == (None if mode == "defaults" else "a" * 32)
        assert replies[0].kwargs["allowed_mentions"].to_dict() == {"parse": []}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name", ["recompute", "list_scans", "window_preview", "test_export", "export_all"]
)
@pytest.mark.parametrize("permitted", [True, False])
async def test_grouped_admin_dispatch_uses_fresh_permissions(monkeypatch, name, permitted):
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock, Mock

    import bot_config
    from commands import stats_cmds
    import decoraters
    from kvk.dal.new_source_import_dal import SourceConflict
    from kvk.services import kvk_admin_service as service

    monkeypatch.setattr(bot_config, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(bot_config, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(decoraters, "usage_tracker", lambda: types.SimpleNamespace(log=AsyncMock()))
    monkeypatch.setattr(stats_cmds, "GUILD_ID", 10)
    groups = []
    bot = types.SimpleNamespace(
        add_application_command=groups.append, slash_command=lambda **kw: lambda fn: fn, loop=None
    )
    stats_cmds.register_stats(bot)
    group = next(g for g in groups if g.name == "kvk_admin")
    assert len(group.subcommands) <= 25
    command = next(c for c in group.subcommands if c.name == name)
    user = types.SimpleNamespace(id=30)
    guild = types.SimpleNamespace(id=10, fetch_member=AsyncMock(return_value=user))
    channel = types.SimpleNamespace(
        id=40,
        parent_id=None,
        permissions_for=lambda _: types.SimpleNamespace(view_channel=True, send_messages=permitted),
    )
    response = types.SimpleNamespace(
        is_done=lambda: False, defer=AsyncMock(), send_message=AsyncMock()
    )
    followup = types.SimpleNamespace(send=AsyncMock())
    interaction = types.SimpleNamespace(
        user=user,
        guild=guild,
        channel=channel,
        response=response,
        followup=followup,
        edit_original_response=AsyncMock(),
        data={"options": []},
    )
    ctx = types.SimpleNamespace(
        user=user,
        guild=guild,
        channel=channel,
        interaction=interaction,
        followup=followup,
        command=command,
        bot=bot,
    )
    monkeypatch.setattr(stats_cmds, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(service, "resolve_kvk_no", lambda _: 16)
    monkeypatch.setattr(service, "require_admin_result_current", Mock())
    methods = {
        "recompute": ("recompute_kvk_windows", service.KvkRecomputeResult(16, 0, True, ())),
        "list_scans": (
            "list_recent_scans",
            service.KvkRecentScansResult(16, 20, [], "snapshot_report_v1"),
        ),
        "window_preview": (
            "load_window_preview",
            service.KvkWindowPreviewResult(16, [], [], datetime.now(UTC), "snapshot_report_v1"),
        ),
        "test_export": ("run_export_test", None),
        "export_all": ("run_export_all", None),
    }
    method, result = methods[name]
    execute = Mock(return_value=result)
    if name in {"test_export", "export_all"}:
        execute.side_effect = SourceConflict("Export admission unavailable; no export started.")
    monkeypatch.setattr(service, method, execute)
    await command._invoke(ctx)
    assert execute.call_count == int(permitted)
    assert guild.fetch_member.await_count >= 1
