from __future__ import annotations

import ast
from pathlib import Path


EXPECTED_ARK_SUBCOMMANDS = {
    "ark_create_match": "create_match",
    "ark_force_announce": "force_announce",
    "ark_amend_match": "amend_match",
    "ark_cancel_match": "cancel_match",
    "ark_reminder_prefs": "reminder_prefs",
    "ark_set_preference": "set_preference",
    "ark_clear_preference": "clear_preference",
    "ark_ban_add": "ban_add",
    "ark_ban_revoke": "ban_revoke",
    "ark_ban_list": "ban_list",
    "ark_set_result": "set_result",
    "ark_report_players": "report_players",
    "ark_generate_draft": "generate_draft",
    "create_ark_team": "create_team",
}

ADMIN_OR_LEADERSHIP_COMMANDS = {
    "ark_create_match",
    "ark_force_announce",
    "ark_amend_match",
    "ark_cancel_match",
    "ark_set_preference",
    "ark_clear_preference",
    "ark_ban_add",
    "ark_ban_revoke",
    "ark_ban_list",
    "ark_set_result",
    "ark_generate_draft",
    "create_ark_team",
}


def _decorator_names(node: ast.AsyncFunctionDef) -> set[str]:
    names = set()
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            names.add(decorator.func.id)
        elif isinstance(decorator, ast.Name):
            names.add(decorator.id)
    return names


def test_all_phase4_ark_commands_are_grouped_with_expected_wrappers():
    source = Path("commands/ark_cmds.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name in EXPECTED_ARK_SUBCOMMANDS
    }

    assert set(functions) == set(EXPECTED_ARK_SUBCOMMANDS)
    assert "discord.SlashCommandGroup" in source
    assert "bot.add_application_command(ark_group)" in source

    for function_name, subcommand_name in EXPECTED_ARK_SUBCOMMANDS.items():
        node = functions[function_name]
        command_decorator = node.decorator_list[0]
        assert isinstance(command_decorator, ast.Call)
        assert isinstance(command_decorator.func, ast.Attribute)
        assert isinstance(command_decorator.func.value, ast.Name)
        assert command_decorator.func.value.id == "ark_group"
        assert command_decorator.func.attr == "command"
        assert any(
            keyword.arg == "name"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == subcommand_name
            for keyword in command_decorator.keywords
        )

        decorators = _decorator_names(node)
        assert "safe_command" in decorators
        assert "track_usage" in decorators
        if function_name in ADMIN_OR_LEADERSHIP_COMMANDS:
            assert "is_admin_or_leadership_only" in decorators
            assert "channel_only" in decorators
        else:
            assert "is_admin_or_leadership_only" not in decorators
            assert "channel_only" not in decorators


def test_phase4_removed_flat_ark_registration_names():
    source = Path("commands/ark_cmds.py").read_text(encoding="utf-8")

    stale_names = [
        'name="ark_create_match"',
        'name="ark_force_announce"',
        'name="ark_amend_match"',
        'name="ark_cancel_match"',
        'name="ark_reminder_prefs"',
        'name="ark_set_preference"',
        'name="ark_clear_preference"',
        'name="ark_ban_add"',
        'name="ark_ban_revoke"',
        'name="ark_ban_list"',
        'name="ark_set_result"',
        'name="ark_report_players"',
        'name="ark_generate_draft"',
        'name="create_ark_team"',
    ]
    for stale_name in stale_names:
        assert stale_name not in source
