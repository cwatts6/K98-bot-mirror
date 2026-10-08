from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core import restart_operations


def test_restart_history_preserves_legacy_and_reads_runtime_independent_of_cwd(
    tmp_path, monkeypatch
):
    legacy = tmp_path / "source"
    logs = legacy / "logs"
    logs.mkdir(parents=True)
    old = legacy / "restart_log.csv"
    new = logs / "restart_log.csv"
    old.write_text("Timestamp,Reason\nold,legacy\n", encoding="utf-8")
    new.write_text("Timestamp,Reason\nnew,runtime\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr(restart_operations, "BASE_DIR", str(legacy))
    monkeypatch.setattr(restart_operations, "RESTART_LOG_FILE", str(new))
    assert restart_operations.read_restart_history(2) == [
        {"Timestamp": "old", "Reason": "legacy"},
        {"Timestamp": "new", "Reason": "runtime"},
    ]
    assert restart_operations.read_restart_history(1) == [{"Timestamp": "new", "Reason": "runtime"}]
    assert old.read_text() == "Timestamp,Reason\nold,legacy\n"


def test_restart_history_retains_first_headerless_watchdog_event(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime.csv"
    runtime.write_text(
        "2026-10-08T12:00:00+00:00,watchdog,SYSTEM,success\n"
        '2026-10-08T12:01:00+00:00,"slash,restart",123,success,,,\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(restart_operations, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(restart_operations, "RESTART_LOG_FILE", str(runtime))
    rows = restart_operations.read_restart_history(20)
    assert len(rows) == 2
    assert rows[0] == dict(
        Timestamp="2026-10-08T12:00:00+00:00", Reason="watchdog", UserId="SYSTEM", Status="success"
    )
    assert rows[1]["Reason"] == "slash,restart"
    assert rows[1]["WS Code"] == ""


def test_restart_history_empty_files_are_not_events(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime.csv"
    runtime.write_text("\n\n", encoding="utf-8")
    monkeypatch.setattr(restart_operations, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(restart_operations, "RESTART_LOG_FILE", str(runtime))
    assert restart_operations.read_restart_history() == []


@pytest.mark.parametrize(
    "headers",
    [
        "UserID,Status,WS_Code,WS_Description,WS_Timestamp",
        "UserId,Status,WS Code,WS Reason,WS Time",
        "user_id,Status,ws_code,ws_reason,ws_time",
    ],
)
def test_restart_history_normalizes_runtime_header_aliases(tmp_path, monkeypatch, headers):
    runtime = tmp_path / "runtime.csv"
    runtime.write_text(
        f"Timestamp,Reason,{headers}\n"
        "2026-10-08T12:00:00+00:00,manual,123,success,1006,connection lost,disconnect-time\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(restart_operations, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(restart_operations, "RESTART_LOG_FILE", str(runtime))
    [row] = restart_operations.read_restart_history()
    assert row["UserId"] == "123"
    assert row["WS Code"] == "1006"
    assert row["WS Reason"] == "connection lost"
    assert row["WS Time"] == "disconnect-time"


@pytest.mark.asyncio
async def test_restart_request_is_not_reported_as_completed(tmp_path, monkeypatch):
    import csv

    runtime = tmp_path / "runtime.csv"
    monkeypatch.setattr(restart_operations, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(restart_operations, "RESTART_LOG_FILE", str(runtime))

    async def append(path, row):
        with open(path, "a", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow(row)

    await restart_operations.write_restart_request(
        reason="slash_graceful_restart",
        user_id="123",
        append_csv_line=append,
        restart_flag_path=str(tmp_path / "request.json"),
        exit_code_file=str(tmp_path / "exit"),
    )
    # A failed replacement startup must leave only an honest pending request.
    assert [row["Status"] for row in restart_operations.read_restart_history()] == ["requested"]
    await append(runtime, ["later", "slash_graceful_restart", "123", "success", "", "", ""])
    assert [row["Status"] for row in restart_operations.read_restart_history()] == [
        "requested",
        "success",
    ]


@pytest.mark.asyncio
async def test_restart_audit_uses_runtime_path_outside_source_root(tmp_path, monkeypatch):
    target = tmp_path / "logs" / "restart_log.csv"
    monkeypatch.setattr(restart_operations, "RESTART_LOG_FILE", str(target))
    calls = []

    async def append(path, row):
        calls.append(path)

    await restart_operations.write_restart_request(
        reason="test",
        user_id="123",
        append_csv_line=append,
        restart_flag_path=str(tmp_path / "logs" / "restart.json"),
        exit_code_file=str(tmp_path / "logs" / "exit"),
    )
    assert calls == [str(target)]


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
            restart_operations.RESTART_LOG_FILE,
            ["2026-05-28T12:00:00+00:00", "slash_graceful_restart", "123", "requested", "", "", ""],
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
        force_exit=lambda _code: calls.append(("force_exit", _code)),
        response_delay_seconds=0,
        close_timeout_seconds=0.01,
    )

    assert calls == [
        ("write", "slash_graceful_restart", "123"),
        ("teardown",),
        ("close",),
        ("force_exit", 15),
    ]
    assert "bot.close() timed out" in caplog.text
    assert "Forcing process exit" in caplog.text


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
