from __future__ import annotations

from types import SimpleNamespace

from commands.command_inventory import flatten_application_commands


def _cmd(name: str, *, subcommands=None):
    return SimpleNamespace(name=name, subcommands=subcommands or [])


def test_flatten_application_commands_preserves_top_level_commands():
    ping = _cmd("ping")

    assert list(flatten_application_commands([ping])) == [("ping", ping)]


def test_flatten_application_commands_expands_group_subcommands():
    status = _cmd("status")
    logs = _cmd("logs")
    ops = _cmd("ops", subcommands=[status, logs])

    assert list(flatten_application_commands([ops])) == [
        ("ops status", status),
        ("ops logs", logs),
    ]


def test_flatten_application_commands_expands_nested_subcommand_groups():
    add = _cmd("add")
    ban = _cmd("ban", subcommands=[add])
    ark = _cmd("ark", subcommands=[ban])

    assert list(flatten_application_commands([ark])) == [("ark ban add", add)]
