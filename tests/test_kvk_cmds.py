from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest


class _FakeGroup:
    def __init__(self, name, description=None, guild_ids=None):
        self.name = name
        self.description = description
        self.guild_ids = guild_ids
        self.commands = {}

    def command(self, *, name, description=None, guild_ids=None):
        def decorator(fn):
            self.commands[name] = fn
            return fn

        return decorator


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _register_kvk(monkeypatch):
    import commands.kvk_cmds as kvk_cmds

    created = {}

    def fake_group(*args, **kwargs):
        group = _FakeGroup(*args, **kwargs)
        created["group"] = group
        return group

    bot = SimpleNamespace(added=[])
    bot.add_application_command = lambda command: bot.added.append(command)
    monkeypatch.setattr(kvk_cmds.discord, "SlashCommandGroup", fake_group)

    kvk_cmds.register_kvk(bot)
    return kvk_cmds, created["group"], bot


def test_register_kvk_declares_player_group(monkeypatch):
    _module, group, bot = _register_kvk(monkeypatch)

    assert group.name == "kvk"
    assert set(group.commands) == {"stats", "targets", "history", "rankings"}
    assert bot.added == [group]


def test_kvk_rankings_type_option_is_required():
    import commands.kvk_cmds as kvk_cmds

    source = inspect.getsource(kvk_cmds.register_kvk)

    assert 'name="type"' in source
    assert "required=True" in source
    assert 'choices=["kvk", "honor", "prekvk"]' in source


@pytest.mark.asyncio
async def test_kvk_rankings_routes_all_modes(monkeypatch):
    kvk_cmds, group, _bot = _register_kvk(monkeypatch)
    handler = _unwrap(group.commands["rankings"])
    ctx = SimpleNamespace(responded=[])

    calls = []

    async def fake_kvk(ctx_arg):
        calls.append(("kvk", ctx_arg))

    async def fake_honor(ctx_arg):
        calls.append(("honor", ctx_arg))

    async def fake_defer(ctx_arg, *, ephemeral=False):
        calls.append(("defer", ephemeral, ctx_arg))

    async def fake_prekvk_report(**kwargs):
        calls.append(("prekvk", kwargs))

    async def fake_channel_guarded(ctx_arg, channel_id, *, admin_override, callback):
        calls.append(("guard", channel_id, admin_override, callback.__name__))
        await callback(ctx_arg)

    async def fake_respond(message, *, ephemeral=False):
        ctx.responded.append((message, ephemeral))

    ctx.respond = fake_respond
    monkeypatch.setattr(kvk_cmds, "_send_kvk_rankings", fake_kvk)
    monkeypatch.setattr(kvk_cmds, "_send_honor_rankings", fake_honor)
    monkeypatch.setattr(kvk_cmds, "_run_channel_guarded", fake_channel_guarded)
    monkeypatch.setattr(kvk_cmds, "safe_defer", fake_defer)
    monkeypatch.setattr(kvk_cmds, "send_prekvk_report", fake_prekvk_report)
    monkeypatch.setattr(
        kvk_cmds.report_service,
        "parse_report_sort",
        lambda value: f"parsed:{value}",
    )

    await handler(ctx, "kvk")
    await handler(ctx, "honor")
    await handler(ctx, "prekvk")
    await handler(ctx, "bad")

    assert calls[0][0:3] == ("guard", kvk_cmds.KVK_PLAYER_STATS_CHANNEL_ID, True)
    assert calls[1] == ("kvk", ctx)
    assert calls[2][0:3] == ("guard", kvk_cmds.KVK_PLAYER_STATS_CHANNEL_ID, False)
    assert calls[3] == ("honor", ctx)
    assert calls[4] == ("defer", True, ctx)
    assert calls[5][0] == "prekvk"
    assert calls[5][1]["ctx"] is ctx
    assert calls[5][1]["sort_by"] == "parsed:Overall"
    assert calls[5][1]["limit"] == 10
    assert ctx.responded == [("Unknown ranking type.", True)]
