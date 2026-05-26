from __future__ import annotations

from types import SimpleNamespace

from bot_helpers import get_command_signature


def test_get_command_signature_uses_grouped_inventory_name():
    def callback():
        return None

    callback.__version__ = "v9.01"
    command = SimpleNamespace(
        name="run_sql_proc",
        description="Manually run the SQL stored procedure",
        callback=callback,
    )

    assert get_command_signature(command, name="ops run_sql_proc") == {
        "name": "ops run_sql_proc",
        "description": "Manually run the SQL stored procedure",
        "version": "v9.01",
    }


def test_bot_startup_uses_flattened_command_inventory_for_signatures():
    source = open("bot_instance.py", encoding="utf-8").read()

    assert "from commands.command_inventory import flatten_application_commands" in source
    assert "signature_commands = list(flatten_application_commands(commands))" in source
    assert "get_command_signature(cmd, name=name)" in source
    assert "for name, cmd in signature_commands:" in source
