from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core import restart_operations


@pytest.mark.asyncio
async def test_write_restart_request_persists_flag_exit_code_and_audit(tmp_path):
    restart_flag_path = tmp_path / ".restart_flag.json"
    exit_code_file = tmp_path / ".exit_code"
    audit_calls = []

    async def append_csv_line(path, row):
        audit_calls.append((path, row))

    result = await restart_operations.write_restart_request(
        reason="slash_graceful_restart",
        user_id="123",
        append_csv_line=append_csv_line,
        restart_flag_path=str(restart_flag_path),
        exit_code_file=str(exit_code_file),
        exit_code=15,
        timestamp="2026-05-28T12:00:00+00:00",
    )

    assert result == {
        "timestamp": "2026-05-28T12:00:00+00:00",
        "reason": "slash_graceful_restart",
        "user_id": "123",
    }
    assert json.loads(restart_flag_path.read_text(encoding="utf-8")) == result
    assert exit_code_file.read_text(encoding="utf-8") == "15"
    assert audit_calls == [
        (
            "restart_log.csv",
            ["2026-05-28T12:00:00+00:00", "slash_graceful_restart", "123", "success", "", "", ""],
        )
    ]


@pytest.mark.asyncio
async def test_write_restart_request_keeps_marker_when_audit_fails(tmp_path, caplog):
    restart_flag_path = tmp_path / ".restart_flag.json"
    exit_code_file = tmp_path / ".exit_code"

    async def append_csv_line(_path, _row):
        raise OSError("locked")

    result = await restart_operations.write_restart_request(
        reason="slash_graceful_restart",
        user_id="123",
        append_csv_line=append_csv_line,
        restart_flag_path=str(restart_flag_path),
        exit_code_file=str(exit_code_file),
        exit_code=15,
        timestamp="2026-05-28T12:00:00+00:00",
    )

    assert json.loads(restart_flag_path.read_text(encoding="utf-8")) == result
    assert exit_code_file.read_text(encoding="utf-8") == "15"
    assert "Failed to append restart audit log" in caplog.text


@pytest.mark.asyncio
async def test_run_cooperative_restart_writes_markers_before_teardown_and_close(monkeypatch):
    calls = []

    async def fake_write_restart_request(**kwargs):
        calls.append(("write", kwargs["reason"], kwargs["user_id"]))
        return {"reason": kwargs["reason"], "user_id": kwargs["user_id"]}

    async def graceful_teardown():
        calls.append(("teardown",))

    async def close_bot():
        calls.append(("close",))

    def flush_logs():
        calls.append(("flush",))

    monkeypatch.setattr(restart_operations, "write_restart_request", fake_write_restart_request)

    await restart_operations.run_cooperative_restart(
        reason="slash_graceful_restart",
        user_id="123",
        append_csv_line=None,
        graceful_teardown=graceful_teardown,
        close_bot=close_bot,
        flush_logs=flush_logs,
        response_delay_seconds=0,
    )

    assert calls == [
        ("write", "slash_graceful_restart", "123"),
        ("teardown",),
        ("flush",),
        ("close",),
    ]


@pytest.mark.asyncio
async def test_run_cooperative_restart_close_timeout_does_not_hang(monkeypatch, caplog):
    calls = []

    async def fake_write_restart_request(**kwargs):
        calls.append(("write", kwargs["reason"], kwargs["user_id"]))
        return {"reason": kwargs["reason"], "user_id": kwargs["user_id"]}

    async def graceful_teardown():
        calls.append(("teardown",))

    async def close_bot():
        calls.append(("close",))
        await restart_operations.asyncio.sleep(1)

    monkeypatch.setattr(restart_operations, "write_restart_request", fake_write_restart_request)

    await restart_operations.run_cooperative_restart(
        reason="slash_graceful_restart",
        user_id="123",
        append_csv_line=None,
        graceful_teardown=graceful_teardown,
        close_bot=close_bot,
        response_delay_seconds=0,
        close_timeout_seconds=0.01,
    )

    assert calls == [
        ("write", "slash_graceful_restart", "123"),
        ("teardown",),
        ("close",),
    ]
    assert "bot.close() timed out" in caplog.text


def _async_function(tree: ast.AST, name: str) -> ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name
    )


def _command_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "command"
            ):
                continue
            for keyword in decorator.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    names.add(str(keyword.value.value))
    return names


def _calls_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == name
        for child in ast.walk(node)
    )


def test_ops_restart_surface_has_graceful_and_force_paths_only():
    tree = ast.parse(Path("commands/admin_cmds.py").read_text(encoding="utf-8"))
    names = _command_names(tree)

    assert "graceful_restart" in names
    assert "force_restart" in names
    assert "restart_bot" not in names

    graceful_restart = _async_function(tree, "graceful_restart")
    force_restart = _async_function(tree, "force_restart")
    assert _calls_name(graceful_restart, "run_cooperative_restart")
    assert _calls_name(force_restart, "write_restart_request")


def test_graceful_shutdown_has_configurable_15_second_fallback():
    src = Path("graceful_shutdown.py").read_text(encoding="utf-8")

    assert 'os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS")' in src
    assert "DEFAULT_COOPERATIVE_SHUTDOWN_TIMEOUT_SECONDS = 15.0" in src
    assert "cooperative_requested" in src
    assert "cooperative_timeout_kill" in src
