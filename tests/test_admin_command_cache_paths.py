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
    assert "atomic_json_write(COMMAND_CACHE_FILE" in functions["resync_commands"]
