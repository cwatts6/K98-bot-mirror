from __future__ import annotations

import ast
import datetime
from pathlib import Path

if not hasattr(datetime, "UTC"):
    datetime.UTC = datetime.UTC


def test_ark_preference_commands_are_grouped_with_existing_wrappers():
    source = Path("commands/ark_cmds.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    moved = {
        "ark_set_preference": "set_preference",
        "ark_clear_preference": "clear_preference",
    }

    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name in moved
    }

    assert set(functions) == set(moved)
    for function_name, command_name in moved.items():
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
            and keyword.value.value == command_name
            for keyword in command_decorator.keywords
        )
        decorator_names = {
            decorator.func.id
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
        } | {decorator.id for decorator in node.decorator_list if isinstance(decorator, ast.Name)}
        assert "safe_command" in decorator_names
        assert "is_admin_or_leadership_only" in decorator_names
        assert "channel_only" in decorator_names
        assert "track_usage" in decorator_names
