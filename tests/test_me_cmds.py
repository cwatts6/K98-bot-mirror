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


def _register_me(monkeypatch):
    import commands.me_cmds as me_cmds

    created = {}

    def fake_group(*args, **kwargs):
        group = _FakeGroup(*args, **kwargs)
        created["group"] = group
        return group

    bot = SimpleNamespace(added=[])
    bot.add_application_command = lambda command: bot.added.append(command)
    monkeypatch.setattr(me_cmds.discord, "SlashCommandGroup", fake_group)

    me_cmds.register_me(bot)
    return me_cmds, created["group"], bot


def test_register_me_declares_player_self_service_group(monkeypatch) -> None:
    _module, group, bot = _register_me(monkeypatch)

    assert group.name == "me"
    assert set(group.commands) == {
        "dashboard",
        "accounts",
        "reminders",
        "preferences",
        "resources",
        "materials",
        "speedups",
        "stats",
    }
    assert bot.added == [group]


def test_me_commands_are_decorated_and_thin() -> None:
    import commands.me_cmds as me_cmds

    source = inspect.getsource(me_cmds.register_me)

    assert source.count("@versioned(") == 8
    assert source.count('@versioned("v1.03")') == 1
    assert source.count('@versioned("v1.02")') == 1
    assert source.count('@versioned("v1.01")') == 2
    assert source.count('@versioned("v1.00")') == 4
    assert source.count("@safe_command") == 8
    assert source.count("@track_usage()") == 8
    assert "set_user_config" not in source
    assert "remove_user" not in source
    assert "export_service" not in source
    assert "inventory_reporting_dal" not in source


@pytest.mark.asyncio
async def test_me_dashboard_hands_off_to_governor_dashboard_sender(monkeypatch) -> None:
    me_cmds, group, _bot = _register_me(monkeypatch)
    handler = _unwrap(group.commands["dashboard"])
    calls = []

    async def fake_sender(ctx):
        calls.append(ctx)

    monkeypatch.setattr(me_cmds, "send_governor_dashboard", fake_sender)
    ctx = SimpleNamespace()

    await handler(ctx)

    assert calls == [ctx]


@pytest.mark.asyncio
async def test_me_stats_hands_off_to_private_personal_stats_sender(monkeypatch) -> None:
    me_cmds, group, _bot = _register_me(monkeypatch)
    handler = _unwrap(group.commands["stats"])
    calls = []

    async def fake_sender(ctx):
        calls.append(ctx)

    monkeypatch.setattr(me_cmds, "send_personal_stats", fake_sender)
    ctx = SimpleNamespace()

    await handler(ctx)

    assert calls == [ctx]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("command_name", "expected_view"),
    (
        ("resources", "RESOURCES"),
        ("materials", "MATERIALS"),
        ("speedups", "SPEEDUPS"),
    ),
)
async def test_direct_inventory_commands_handoff_fixed_report_type(
    monkeypatch,
    command_name,
    expected_view,
) -> None:
    me_cmds, group, _bot = _register_me(monkeypatch)
    handler = _unwrap(group.commands[command_name])
    calls = []

    async def fake_sender(ctx, *, report_view):
        calls.append((ctx, report_view))

    monkeypatch.setattr(me_cmds, "send_player_inventory_report", fake_sender)
    ctx = SimpleNamespace()

    await handler(ctx)

    assert calls == [(ctx, getattr(me_cmds.InventoryReportView, expected_view))]


def test_me_command_module_has_no_sql_or_mutation_imports() -> None:
    import commands.me_cmds as me_cmds

    source = inspect.getsource(me_cmds)

    assert "SELECT " not in source.upper()
    assert "INSERT " not in source.upper()
    assert "UPDATE " not in source.upper()
    assert "DELETE " not in source.upper()
    assert "set_user_config" not in source
    assert "remove_user" not in source
    assert "PAGE_INVENTORY" not in source
