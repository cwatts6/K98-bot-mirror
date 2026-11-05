"""Composed ownership, bounded loss, and preservation of higher-priority evidence."""

import asyncio
import json
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services import (
    download_log_service as file,
    operation_diagnostics as diagnostics,
    optional_upload_lifecycle as lifecycle,
)
from services.optional_upload_observations import is_upload_row
from tests.test_optional_import_audit_worker import wait_for


def event(reference=None, stage="operation", state="failed"):
    from datetime import UTC, datetime

    return dict(
        reference=reference or str(uuid4()),
        stage=stage,
        state=state,
        observed_utc=datetime.now(UTC).isoformat(),
        schema="operation-boundary/2",
        event_id=str(uuid4()),
        sequence=1,
        role="parent",
        origin="code_owned",
        actor="system",
    )


def test_optional_storm_cannot_consume_general_queue_or_critical_reserve():
    sink = diagnostics.DiagnosticSink()
    identity = str(uuid4())
    first = event()
    sink.offer(first)
    for n in range(2000):
        sink.uploads.offer(identity, "failed", n, "sql")
    sink.uploads.offer(identity, "settled", 1999, "sql")
    assert list(sink.queue) == [first]
    assert sink.dropped == sink.critical_dropped == 0
    assert len(sink.uploads.slots) == 1
    assert sink.uploads.report()["coalesced"] == 2000
    observed = sink.uploads.take()
    assert observed[0]["diagnostic_loss"] == 0
    assert observed[-1]["diagnostic_loss"] == 1999
    assert len(json.dumps(observed).encode()) < 4096


def test_contended_optional_lane_does_not_wait_or_lose_business_evidence():
    sink = diagnostics.DiagnosticSink()
    with sink.uploads.lock:
        assert not sink.uploads.offer(str(uuid4()), "failed", 1, "sql")
        assert sink.offer(event())
    assert sink.uploads.report()["coverage"] == "partial"
    assert not sink.uploads.report()["counters_exact"]
    assert len(sink.queue) == 1


def test_optional_history_cannot_evict_business_even_if_business_completed(monkeypatch):
    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 4)
    sink = diagnostics.DiagnosticSink()
    business = [event(state="settled") for _ in range(4)]
    for item in business:
        sink._accept(item)
    sink._accept(event(stage="upload_audit", state="settled"))
    assert set(sink.records) == {item["reference"] for item in business}
    assert sink.uploads.report()["retention_omitted"] == 1


def test_business_evicts_optional_first_even_when_optional_failed(monkeypatch):
    monkeypatch.setattr(diagnostics, "MAX_OPERATIONS", 2)
    sink = diagnostics.DiagnosticSink()
    optional = event(stage="upload_audit")
    business, next_business = event(), event()
    for item in (optional, business, next_business):
        sink._accept(item)
    assert set(sink.records) == {business["reference"], next_business["reference"]}
    assert sink.uploads.report()["retention_omitted"] == 1


def test_bounded_mailbox_and_history_and_monotonic_loss():
    sink = diagnostics.DiagnosticSink()
    keys = [str(uuid4()) for _ in range(65)]
    for key in keys[:63]:
        assert sink.uploads.offer(key, "failed", 7, "sql")
    assert sink.uploads.offer(keys[63], "failed", 7, "file")
    assert not sink.uploads.offer(keys[-1], "failed", 1, "sql")
    for item in sink.uploads.take(64):
        sink._accept(item)
    assert len(sink.records) == 64
    sink._accept(event(keys[-1], stage="upload_audit"))
    assert len(sink.records) == 64
    later = event(keys[0], stage="upload_audit", state="settled")
    later["diagnostic_loss"] = 1
    sink._accept(later)
    assert sink.records[keys[0]]["transitions"][-1]["diagnostic_loss"] == 7


def test_final_flush_restoration_and_report_preserve_first_loss(tmp_path):
    sink = diagnostics.DiagnosticSink(tmp_path).start()
    identity = str(uuid4())
    for n in range(50):
        sink.uploads.offer(identity, "failed", n, "sql")
    sink.uploads.offer(identity, "settled", 49, "sql")
    sink.uploads.summary("sql", "drained", 3, None)
    sink.close()
    restored = diagnostics.DiagnosticSink(tmp_path).start()
    restored.close()
    report = restored.report()
    row = next(row for row in report["operations"] if row["reference"] == identity)
    assert row["first_failure"]["diagnostic_loss"] == 0
    assert row["latest"]["diagnostic_loss"] == 49
    assert report["upload_observations"]["prior"]["coalesced"] == 50
    assert report["upload_observations"]["workers"] == {}
    again = diagnostics.DiagnosticSink(tmp_path).start()
    again.close()
    assert again.report()["upload_observations"]["prior"]["coalesced"] == 50


@pytest.mark.asyncio
@pytest.mark.parametrize("where", ["construct", "start"])
async def test_file_startup_failure_is_once_only_without_awaited_fallback(
    monkeypatch, tmp_path, where
):
    for key, value in {
        "QUALIFIED": True,
        "_writer": None,
        "_start_attempted": False,
        "_stopped": False,
        "_startup_error": None,
        "_unavailable_offers": 0,
    }.items():
        monkeypatch.setattr(file, key, value)
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise OSError("PRIVATE_PATH")

    monkeypatch.setattr(
        file if where == "construct" else threading.Thread,
        "DownloadLogWriter" if where == "construct" else "start",
        fail,
    )
    file.configure(tmp_path / "unused.csv")
    file.configure(tmp_path / "unused.csv")
    assert not await file.record_download(tmp_path / "must-not-exist.csv", ["x"] * 5)
    assert not (tmp_path / "must-not-exist.csv").exists()
    assert calls == [1] and file._startup_error == "OSError"
    file.shutdown()
    file.configure(tmp_path / "unused.csv")
    assert calls == [1]


def test_file_close_refusal_retains_handle_and_no_replacement_or_retry(monkeypatch, tmp_path):
    calls = []
    entered, release = threading.Event(), threading.Event()

    class Stream:
        def write(self, payload):
            calls.append("write")
            entered.set()
            assert release.wait(3)
            raise ValueError("original-write-failure")

        def close(self):
            calls.append("close")
            raise OSError("private-path")

    stream = Stream()
    monkeypatch.setattr(type(tmp_path), "open", lambda *a, **kw: stream)
    writer = file.DownloadLogWriter(tmp_path / "fixture.csv").start()
    try:
        assert writer.offer_row(["x"] * 5)
        assert entered.wait(2)
        assert writer.offer_row(["discard"] * 5)
        release.set()
        wait_for(lambda: not writer._thread.is_alive())
        for _ in range(2):
            with pytest.raises(file.FileCleanupUnconfirmed) as error:
                writer.close()
            assert error.value.stream is stream
        assert calls == ["write", "close"]
        assert isinstance(error.value.__cause__, OSError)
        assert isinstance(error.value.__cause__.__context__, ValueError)
        assert not writer.offer_row(["late"] * 5)
    finally:
        release.set()
        writer._thread.join(3)


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_both_admissions_close_before_wait_and_other_owner_settles_on_failure(
    monkeypatch, cancel
):
    closed = []
    joined = []
    entered = threading.Event()
    release = threading.Event()

    def owner(name):
        def wait():
            assert closed == ["file", "sql"]
            entered.set()
            assert release.wait(3)
            joined.append(name)
            if name == "file":
                raise OSError("retained uncertainty")

        return SimpleNamespace(request_close=lambda: closed.append(name), wait_closed=wait)

    monkeypatch.setattr(lifecycle, "download_log_service", owner("file"))
    monkeypatch.setattr(lifecycle, "optional_import_audit_worker", owner("sql"))

    def sink_close():
        assert set(joined) == {"file", "sql"}
        joined.append("sink")

    monkeypatch.setattr(diagnostics, "shutdown", sink_close)
    task = asyncio.create_task(lifecycle.shutdown())
    await asyncio.to_thread(entered.wait, 2)
    if cancel:
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError if cancel else ExceptionGroup):
        await task
    assert joined[-1] == "sink"


def test_ordinary_report_prioritizes_business_over_optional():
    sink = diagnostics.DiagnosticSink()
    for _ in range(32):
        sink._accept(event(stage="upload_audit"))
    business = event()
    sink._accept(business)
    sink._publish()
    assert sink.report()["operations"][0]["reference"] == business["reference"]
    assert all(not is_upload_row(row) for row in sink.report()["operations"][:1])


def test_observation_failure_cannot_escape_optional_file_admission(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise RuntimeError("diagnostic emission failed")

    monkeypatch.setattr(diagnostics, "offer_upload_observation", fail)
    writer = file.DownloadLogWriter(tmp_path / "fixture.csv").start()
    try:
        assert writer.offer_row(["one"] * 5)
        wait_for(lambda: writer.settled == 1)
        assert writer.observation_unavailable
        assert writer.failures == 0
        assert (tmp_path / "fixture.csv").read_text().splitlines() == ["one,one,one,one,one"]
    finally:
        writer.close()


@pytest.mark.parametrize("run_result", ["return", "error", "system_exit"])
def test_process_exit_drains_workers_before_releasing_singleton(monkeypatch, tmp_path, run_result):
    import ast
    import os
    from pathlib import Path
    import sys

    # Execute the real process-exit block with inert Discord and process markers.
    root = Path(__file__).resolve().parents[1]
    main = ast.parse((root / "DL_bot.py").read_text(encoding="utf-8")).body[-1]
    assert isinstance(main, ast.If)
    code = compile(ast.Module(body=[main], type_ignores=[]), "DL_bot.py", "exec")
    entered, release = threading.Event(), threading.Event()
    released, errors = [], []
    writer = file.DownloadLogWriter(tmp_path / "fixture.csv")
    original_write = writer.write

    def blocked_write(payload):
        entered.set()
        assert release.wait(5)
        original_write(payload)

    writer.write = blocked_write
    writer.start()
    monkeypatch.setattr(file, "_writer", writer)
    monkeypatch.setattr(lifecycle.optional_import_audit_worker, "_writer", None)
    monkeypatch.setattr(diagnostics, "shutdown", lambda: None)
    assert writer.offer_row(["once"] * 5)
    assert entered.wait(2)
    pid = tmp_path / "pid"
    pid.write_text(str(os.getpid()))

    def run(_):
        if run_result == "error":
            raise RuntimeError("inert bot.run failure")
        if run_result == "system_exit":
            raise SystemExit(0)

    env = dict(
        __name__="__main__",
        bot=SimpleNamespace(run=run),
        TOKEN="inert",
        logger=SimpleNamespace(info=lambda *a: None, exception=lambda *a: None),
        flush_logs=lambda: None,
        sys=sys,
        os=os,
        asyncio=asyncio,
        EXIT_CODE_FILE=tmp_path / "exit",
        BOT_PID_FILE=pid,
        BOT_LOCK_PATH="inert",
        release_singleton_lock=lambda _: released.append(True),
    )

    def execute():
        try:
            exec(code, env)
        except BaseException as exc:
            errors.append(exc)

    runner = threading.Thread(target=execute)
    runner.start()
    try:
        wait_for(lambda: writer._closed)
        assert runner.is_alive()
        assert pid.exists() and not released
        assert not writer.offer_row(["late"] * 5)
    finally:
        release.set()
        runner.join(5)
        writer.close()
    assert not runner.is_alive() and not writer._thread.is_alive()
    assert not pid.exists() and released == [True]
    assert writer.entered == writer.settled == 1
    assert len(errors) == (run_result != "return")
    assert all(isinstance(exc, SystemExit) for exc in errors)


def test_process_exit_refuses_singleton_release_when_drain_unconfirmed(monkeypatch, tmp_path):
    import ast
    import os
    from pathlib import Path

    main = ast.parse(
        (Path(__file__).resolve().parents[1] / "DL_bot.py").read_text(encoding="utf-8")
    ).body[-1]
    code = compile(ast.Module(body=[main], type_ignores=[]), "DL_bot.py", "exec")
    owners = []

    def refuse():
        raise OSError("retained close uncertainty")

    monkeypatch.setattr(
        lifecycle,
        "download_log_service",
        SimpleNamespace(request_close=lambda: owners.append("file"), wait_closed=refuse),
    )
    monkeypatch.setattr(
        lifecycle,
        "optional_import_audit_worker",
        SimpleNamespace(
            request_close=lambda: owners.append("sql"), wait_closed=lambda: owners.append("joined")
        ),
    )
    monkeypatch.setattr(diagnostics, "shutdown", lambda: None)
    pid = tmp_path / "pid"
    pid.write_text(str(os.getpid()))
    released = []
    with pytest.raises(ExceptionGroup):
        exec(
            code,
            dict(
                __name__="__main__",
                bot=SimpleNamespace(run=lambda _: None),
                TOKEN="inert",
                asyncio=asyncio,
                os=os,
                BOT_PID_FILE=pid,
                BOT_LOCK_PATH="inert",
                release_singleton_lock=lambda _: released.append(True),
            ),
        )
    assert owners == ["file", "sql", "joined"]
    assert pid.exists() and not released
