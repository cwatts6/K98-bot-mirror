from __future__ import annotations

import ast
from pathlib import Path


def test_admin_command_cache_handlers_use_canonical_cache_path():
    source = Path("commands/admin_cmds.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    in_scope = {"resync_commands", "validate_command_cache"}
    functions = {
        node.name: ast.get_source_segment(source, node) or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name in in_scope
    }

    assert set(functions) == in_scope

    combined = "\n".join(functions.values())
    assert "COMMAND_CACHE_FILE" in combined
    assert '"command_cache.json"' not in combined
    assert "command_cache_update(" in functions["resync_commands"]
    assert "build_command_cache_validation(" in functions["validate_command_cache"]
    assert "flatten_application_commands" not in combined


def test_phase3_ops_commands_are_grouped_with_existing_wrappers():
    source = Path("commands/admin_cmds.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    moved = {
        "summary_command": "summary",
        "weeksummary_command": "weeksummary",
        "history_command": "history",
        "failures_command": "failures",
        "test_embed_command": "test_embed",
        "usage_command": "usage",
        "usage_detail_command": "usage_detail",
    }

    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name in moved
    }

    assert set(functions) == set(moved)
    for function_name, command_name in moved.items():
        node = functions[function_name]
        decorators = node.decorator_list
        command_decorator = decorators[0]
        assert isinstance(command_decorator, ast.Call)
        assert isinstance(command_decorator.func, ast.Attribute)
        assert isinstance(command_decorator.func.value, ast.Name)
        assert command_decorator.func.value.id == "ops_group"
        assert command_decorator.func.attr == "command"
        assert any(
            keyword.arg == "name"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == command_name
            for keyword in command_decorator.keywords
        )
        decorator_names = {
            decorator.func.id
            for decorator in decorators
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
        } | {decorator.id for decorator in decorators if isinstance(decorator, ast.Name)}
        assert "safe_command" in decorator_names
        assert "track_usage" in decorator_names
