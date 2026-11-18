"""Offline evidence capture: no SQL, provider, process start or real credentials."""

import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from services import export_authority_diagnostics as diagnostics


@pytest.fixture(autouse=True)
def isolated_logger():
    logger = diagnostics.logger
    old, level = list(logger.handlers), logger.level
    logger.handlers = [logging.NullHandler()]
    yield
    for handler in logger.handlers:
        if handler not in old:
            handler.close()
    logger.handlers, logger.level = old, level


def configure(root):
    return diagnostics.configure_authority_diagnostics(root, inspect_path=lambda p, **_: Path(p))


def records(root):
    return [
        json.loads(line) for line in (root / "authority-diagnostics.jsonl").read_text().splitlines()
    ]


def test_capture_survives_absent_console_and_canonical_launcher_import(
    tmp_path, monkeypatch, capsys
):
    import runpy

    launcher = runpy.run_path(str(Path(__file__).parents[1] / "scripts/run_export_authority.py"))
    monkeypatch.setattr(diagnostics.sys, "stderr", None)
    assert configure(tmp_path)
    launcher["report_dispatch_failure"](
        {"action": "close", "stream_id": str(uuid4())}, ValueError("SECRET")
    )
    captured = records(tmp_path)
    assert [r["stage"] for r in captured] == [
        "AUTHORITY_CAPTURE_READY",
        "AUTHORITY_DISPATCH_FAILED",
    ]
    assert "SECRET" not in json.dumps(captured)
    console = capsys.readouterr()
    assert console.out == console.err == ""


def test_failure_step_preserves_exact_error_and_does_not_retry(tmp_path):
    assert configure(tmp_path)
    failure = type("ProgrammingError", (Exception,), {"__module__": "pyodbc"})(
        "42000", "secret=password; Export admission busy. (51700)"
    )
    request = SimpleNamespace(request_id=str(uuid4()), stream_id=str(uuid4()))
    calls = []
    with pytest.raises(type(failure)) as raised:
        with diagnostics.authority_request_step("request_dispatch", request):
            calls.append("once")
            raise failure
    assert raised.value is failure and calls == ["once"]
    row = records(tmp_path)[-1]
    assert row["checkpoint"] == "request_dispatch"
    assert row["reason_code"] == "account_busy" and row["sql_numbers"] == [51700]
    assert row["request_id"] == request.request_id
    assert "secret" not in json.dumps(row).lower()
    assert row["frames"] and all(set(f) == {"file", "function", "line"} for f in row["frames"])


def test_log_failures_never_replace_outcome(monkeypatch):
    monkeypatch.setattr(diagnostics.logger, "info", Mock(side_effect=OSError("private")))
    monkeypatch.setattr(diagnostics.sys, "stderr", Mock(write=Mock(side_effect=OSError("private"))))
    failure = RuntimeError("original")
    with pytest.raises(RuntimeError) as raised:
        with diagnostics.authority_request_step(
            "request_guard", SimpleNamespace(request_id=None, stream_id=None)
        ):
            raise failure
    assert raised.value is failure


def test_rotation_is_bounded_and_reconfiguration_is_idempotent(tmp_path):
    assert configure(tmp_path) and configure(tmp_path)
    handlers = [h for h in diagnostics.logger.handlers if hasattr(h, "baseFilename")]
    assert len(handlers) == 1
    handlers[0].maxBytes = 1024
    for _ in range(20):
        diagnostics.report_authority_event("AUTHORITY_SERVING")
    paths = list(tmp_path.glob("authority-diagnostics.jsonl*"))
    assert len(paths) == 3
    assert all(p.stat().st_size < 2048 for p in paths)


def test_untrusted_directory_never_gets_fallback_log(tmp_path):
    def refuse(*_, **__):
        raise ValueError("not protected")

    assert not diagnostics.configure_authority_diagnostics(tmp_path, inspect_path=refuse)
    assert list(tmp_path.iterdir()) == []


def test_hardlinked_diagnostic_destination_is_refused(tmp_path):
    original = tmp_path / "original"
    original.write_text("retain")
    os.link(original, tmp_path / "authority-diagnostics.jsonl")
    assert not configure(tmp_path)
    assert original.read_text() == "retain"


def test_long_cyclic_exception_chain_and_private_payload_are_bounded():
    first = ValueError("private SQL password")
    last = first
    for _ in range(20):
        next_error = RuntimeError("private data")
        last.__cause__ = next_error
        last = next_error
    last.__cause__ = first
    row = diagnostics.diagnostic_record(
        "AUTHORITY_DISPATCH_FAILED",
        error=first,
        message={
            "action": ["private"],
            "request": {"request_id": "private"},
            "scope": "private",
        },
    )
    assert len(row["exception_types"]) == 8
    assert len(json.dumps(row)) < 2048 and "private" not in json.dumps(row)


def test_private_logger_does_not_propagate_to_bot_logs(tmp_path, caplog):
    assert configure(tmp_path)
    with caplog.at_level(logging.INFO):
        diagnostics.report_authority_event("AUTHORITY_SERVING")
    assert "AUTHORITY_SERVING" not in caplog.text
    assert records(tmp_path)[-1]["stage"] == "AUTHORITY_SERVING"


@pytest.mark.parametrize("loaded", [False, True])
def test_prebootstrap_failure_never_imports_or_replaces_original(monkeypatch, loaded):
    from scripts import run_export_authority as launcher

    failure = launcher.AuthorityStartupError("original source refusal")
    monkeypatch.setattr(launcher, "_main", Mock(side_effect=failure))
    if loaded:
        monkeypatch.setattr(diagnostics, "report_authority_event", Mock(side_effect=OSError()))
    else:
        monkeypatch.delitem(launcher.sys.modules, "services.export_authority_diagnostics")
    with pytest.raises(launcher.AuthorityStartupError) as result:
        launcher.main([])
    assert result.value is failure
    if not loaded:
        assert "services.export_authority_diagnostics" not in launcher.sys.modules
