from __future__ import annotations

import ast
from pathlib import Path

from commands.stats_cmds import _split_discord_content

IN_SCOPE_KVK_ADMIN_COMMANDS = {
    "test_kvk_export",
    "refresh_stats_cache",
    "kvk_export_all",
    "kvk_recompute",
    "kvk_list_scans",
    "test_kvk_embed",
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


def test_player_stats_awaits_async_embed_builder() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")
    command = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "player_stats_command"
    )

    awaited_calls = [
        node.value.func.id
        for node in ast.walk(command)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    ]

    assert "build_embeds" in awaited_calls


def test_my_stats_contract_is_preserved_and_export_command_is_removed() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")

    assert 'name="my_stats_export"' not in source
    assert 'name="my_stats"' in source
    assert '@versioned("v1.14")' in source
    assert "@channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)" in source
    assert "get_account_summary_for_user" in source
    assert "get_stats_payload" in source
    assert "SliceButtons" in source


def test_split_discord_content_keeps_chunks_under_limit() -> None:
    content = "header\n" + "\n".join(f"row {idx:03d} " + ("x" * 80) for idx in range(60))

    chunks = _split_discord_content(content, max_chars=500)

    assert len(chunks) > 1
    assert all(len(chunk) <= 500 for chunk in chunks)
    assert "\n".join(chunks) == content


def test_kvk_list_scans_uses_discord_content_splitter() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")
    command = _command_nodes()["kvk_list_scans"]
    segment = ast.get_source_segment(source, command) or ""

    assert "_split_discord_content" in segment
    assert "for chunk in chunks" in segment


def test_kvk_export_all_reports_resolved_kvk_before_service_call() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")
    command = _command_nodes()["kvk_export_all"]
    segment = ast.get_source_segment(source, command) or ""

    assert "resolved_kvk_no = await asyncio.to_thread(kvk_admin_service.resolve_kvk_no" in segment
    assert "Exporting KVK `{resolved_kvk_no}`" in segment
    assert "kvk_no=resolved_kvk_no" in segment


def test_kvk_test_embed_passes_computed_kvk_state_to_sender() -> None:
    source = Path("commands/stats_cmds.py").read_text(encoding="utf-8")
    command = _command_nodes()["test_kvk_embed"]
    segment = ast.get_source_segment(source, command) or ""

    assert "is_kvk = context.is_kvk" in segment
    assert "send_stats_update_embed(ctx.bot, ts, is_kvk, is_test=True)" in segment
