from __future__ import annotations

import ast
from pathlib import Path

IN_SCOPE_KVK_ADMIN_COMMANDS = {
    "test_kvk_export",
    "kvk_export_all",
    "kvk_recompute",
    "kvk_list_scans",
    "kvk_window_preview",
}

FORBIDDEN_SQL_MARKERS = (
    "KVK.sp_KVK_Recompute_Windows",
    "FROM KVK.KVK_Scan",
    "FROM KVK.KVK_Windows",
    "FROM KVK.KVK_Player_Windowed",
    "SELECT MAX(ScanID)",
    "_conn()",
)


def _command_nodes() -> dict[str, ast.AsyncFunctionDef]:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name in IN_SCOPE_KVK_ADMIN_COMMANDS
    }


def test_kvk_admin_commands_delegate_to_service_layer() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")
    commands = _command_nodes()

    assert set(commands) == IN_SCOPE_KVK_ADMIN_COMMANDS

    for command_name, node in commands.items():
        segment = ast.get_source_segment(source, node) or ""
        assert "kvk_admin_service." in segment, f"{command_name} must call the KVK admin service"
        for marker in FORBIDDEN_SQL_MARKERS:
            assert marker not in segment, f"{command_name} must not contain direct admin SQL"


def test_stats_cmds_imports_kvk_admin_service_boundary() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")

    assert "from kvk.services import kvk_admin_service" in source
    assert "from kvk.dal.kvk_history_dal import resolve_current_kvk_no_from_cursor" not in source
