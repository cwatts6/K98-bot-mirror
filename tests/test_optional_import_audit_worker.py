import asyncio
import json
import threading
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.download_log_service import DownloadLogWriter
from services.optional_import_audit_worker import ImportAuditWriter, PendingAudit


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_at", ["construction", "thread_start"])
async def test_adopted_start_failure_is_optional_and_never_falls_back(
    monkeypatch, caplog, failure_at
):
    from services import optional_import_audit_worker as service
    from services.honor_import_audit_service import HonorImportAuditContext, start_honor_audit_batch

    for name, value in {
        "QUALIFIED": True,
        "_writer": None,
        "_start_attempted": False,
        "_stopped": False,
        "_startup_error": None,
        "_unavailable_offers": 0,
    }.items():
        monkeypatch.setattr(service, name, value)
    starts = []

    def fail(*args, **kwargs):
        starts.append(1)
        raise RuntimeError("private-connection-text")

    if failure_at == "construction":
        monkeypatch.setattr(service, "ImportAuditWriter", fail)
    else:
        monkeypatch.setattr(threading.Thread, "start", fail)

    service.configure()
    service.configure()
    assert starts == [1]
    assert service._startup_error == "RuntimeError"
    assert "private-connection-text" not in caplog.text
    assert "RuntimeError" in caplog.text

    async def forbidden_fallback(*args, **kwargs):
        raise AssertionError("adopted unavailable audit must not use awaited SQL")

    handle = await start_honor_audit_batch(
        context=HonorImportAuditContext(source_filename="fixture.xlsx", is_test=False),
        xlsx_bytes=b"fixture",
        audit_runner=forbidden_fallback,
    )
    assert handle is None and service._unavailable_offers == 1
    service.shutdown()
    service.configure()
    assert starts == [1]


def test_failed_physical_thread_start_can_close_without_joining_unstarted_thread(monkeypatch):
    from services.optional_upload_transport import OptionalWriter

    worker = OptionalWriter(capacity=1, max_bytes=8, name="fixture-unstarted")

    def fail():
        raise RuntimeError("thread start unavailable")

    monkeypatch.setattr(worker._thread, "start", fail)
    with pytest.raises(RuntimeError):
        worker.start()
    assert not worker.offer(b"x")
    worker.close()
    assert not worker._started and not worker._thread.is_alive()
    assert worker.first_failure == "RuntimeError"


def test_gate_off_does_not_construct_optional_worker(monkeypatch):
    from services import optional_import_audit_worker as service

    monkeypatch.setattr(service, "QUALIFIED", False)
    monkeypatch.setattr(service, "_start_attempted", False)
    monkeypatch.setattr(service, "_stopped", False)

    def forbidden(*args, **kwargs):
        raise AssertionError("gate must remain closed")

    monkeypatch.setattr(service, "ImportAuditWriter", forbidden)
    service.configure()
    assert not service._start_attempted


def test_unconfirmed_connection_close_stops_writer_and_refuses_drain(monkeypatch):
    import pyodbc

    from stats.dal import import_audit_dal as audit_dal

    entered, release = threading.Event(), threading.Event()
    calls = []

    class Connection:
        autocommit = True

        def close(self):
            calls.append("close")
            raise OSError("connection close failed")

    connection = Connection()
    monkeypatch.setattr(pyodbc, "connect", lambda *a, **kw: connection)

    class ClosingDal(Dal):
        def start_import_audit_batch(self, **values):
            calls.append("start")
            with values["connection_factory"]():
                entered.set()
                assert release.wait(3)
                return SimpleNamespace(
                    import_audit_batch_id=7, correlation_id=values["correlation_id"]
                )

    worker = ImportAuditWriter(audit_dal.optional_upload_connection, dal=ClosingDal()).start()
    handle = worker.start_batch(import_kind="honor")
    try:
        assert entered.wait(2)
        worker.action(handle, "complete", {"rows_written": 4})
        release.set()
        wait_for(lambda: not worker._thread.is_alive())
        assert worker.dropped == 1
        assert worker.start_batch(import_kind="honor") is None
        with pytest.raises(audit_dal.AuditConnectionCleanupUnconfirmed) as error:
            worker.close()
        assert error.value.connection is connection
        assert worker.latest == "cleanup_unconfirmed"
        assert calls == ["start", "close"]
        with pytest.raises(audit_dal.AuditConnectionCleanupUnconfirmed):
            worker.close()
        assert calls == ["start", "close"]  # neither SQL nor close was retried
    finally:
        release.set()
        worker._thread.join(3)


def wait_for(predicate):
    deadline = time.monotonic() + 3
    while not predicate():
        assert time.monotonic() < deadline
        time.sleep(0.001)


class Dal:
    def __init__(self, start_error=None, mismatch=False):
        self.calls = []
        self.start_error = start_error
        self.mismatch = mismatch

    def start_import_audit_batch(self, **values):
        self.calls.append(("start", values))
        if self.start_error:
            raise self.start_error
        return SimpleNamespace(
            import_audit_batch_id=17,
            correlation_id=str(uuid4()) if self.mismatch else values["correlation_id"],
        )

    def record_import_audit_phase(self, **values):
        self.calls.append(("phase", values))

    def complete_import_audit_batch(self, **values):
        self.calls.append(("complete", values))

    def fail_import_audit_batch(self, **values):
        self.calls.append(("fail", values))


@pytest.mark.parametrize("failure", [None, OSError("private SQL failure")])
def test_idle_sql_worker_publishes_settled_summary_without_another_upload(monkeypatch, failure):
    from services import operation_diagnostics

    summaries = []
    published = threading.Event()
    expected_state = "failed" if failure else "settled"

    def capture(kind, state, **details):
        summaries.append((kind, state, details))
        if state == expected_state:
            published.set()

    monkeypatch.setattr(operation_diagnostics, "upload_worker_summary", capture)
    monkeypatch.setattr(operation_diagnostics, "offer_upload_observation", lambda *a, **kw: None)
    dal = Dal(start_error=failure)
    worker = ImportAuditWriter(lambda: None, dal=dal).start()
    try:
        worker.start_batch(import_kind="honor")
        assert published.wait(3), "Idle worker did not publish its final physical outcome"
        kind, state, details = summaries[-1]
        assert kind == "sql" and state == expected_state
        assert details["failures"] == (1 if failure else 0)
        assert details["error_type"] == ("OSError" if failure else None)
        assert worker.settled == 1 and len(dal.calls) == 1
        assert worker._thread.is_alive() and not worker._closed
        assert "private SQL failure" not in repr(summaries)
    finally:
        worker.close()


@pytest.mark.parametrize(
    "failure,mismatch", [(RuntimeError("lost ack after insert"), False), (None, True)]
)
def test_no_binding_no_dependent_writes_or_retry(failure, mismatch):
    dal = Dal(failure, mismatch)
    worker = ImportAuditWriter(lambda: None, dal=dal).start()
    try:
        handle = worker.start_batch(import_kind="honor")
        assert isinstance(handle, PendingAudit)
        with pytest.raises(TypeError):
            int(handle)
        worker.action(handle, "phase", {"phase_name": "ingest", "phase_status": "completed"})
        worker.action(handle, "complete", {"rows_written": 2})
        wait_for(lambda: worker.settled == 3)
        assert [c[0] for c in dal.calls] == ["start"]
        assert worker.failures == 3
        assert not worker._contexts
    finally:
        worker.close()


def test_fifo_binding_and_intermediate_loss_preserves_terminal_business():
    dal = Dal()
    worker = ImportAuditWriter(lambda: None, dal=dal).start()
    try:
        first = worker.start_batch(import_kind="honor")
        second = worker.start_batch(import_kind="weekly_activity")
        assert not worker.action(first, "phase", {"details": b"file bytes forbidden"})
        worker.action(
            first,
            "phase",
            {"phase_name": "refresh", "phase_status": "failed", "set_batch_status": "failed"},
        )
        worker.action(first, "complete", {"rows_written": 7, "status": "completed"})
        worker.action(second, "complete", {"rows_written": 3})
        wait_for(lambda: worker.settled == 5)
        assert [c[0] for c in dal.calls] == ["start", "start", "phase", "complete", "complete"]
        assert dal.calls[2][1]["set_batch_status"] is None
        assert dal.calls[3][1]["status"] == "completed"
        assert dal.calls[3][1]["import_audit_batch_id"] == 17
        assert worker.dropped == 1
    finally:
        worker.close()


def test_close_drops_unentered_but_waits_for_physical_writer(tmp_path):
    entered = threading.Event()
    release = threading.Event()
    closed = threading.Event()
    worker = DownloadLogWriter(tmp_path / "download.csv")
    write = worker.write

    def held(payload):
        entered.set()
        assert release.wait(3)
        write(payload)

    worker.write = held
    worker.start()
    try:
        assert worker.offer_row(["a"] * 5)
        assert entered.wait(2)
        for _ in range(64):
            assert worker.offer_row(["b"] * 5)
        assert not worker.offer_row(["c"] * 5)
        closer = threading.Thread(target=lambda: (worker.close(), closed.set()))
        closer.start()
        assert not closed.wait(0.05)
        assert not worker.offer_row(["d"] * 5)
        assert worker.entered == 1
        release.set()
        closer.join(2)
        assert closed.is_set() and not worker._thread.is_alive()
        assert (tmp_path / "download.csv").read_text() == "a,a,a,a,a\n"
        assert worker.dropped >= 66 and worker.settled == 1
    finally:
        release.set()
        worker.close()


def test_offer_contention_and_payload_bounds_do_not_wait(tmp_path):
    worker = DownloadLogWriter(tmp_path / "download.csv").start()
    try:
        worker._lock.acquire()
        try:
            start = time.perf_counter()
            assert not worker.offer_row(["a"] * 5)
            assert time.perf_counter() - start < 0.1
        finally:
            worker._lock.release()
        assert not worker.offer_row(["x" * 2048] * 5)
        assert not worker.offer_row([object()] * 5)
        assert worker.dropped == 3
    finally:
        worker.close()


@pytest.mark.asyncio
async def test_real_domain_adapter_offers_no_bytes_and_never_uses_fallback(monkeypatch):
    from services import optional_import_audit_worker as transport
    from services.honor_import_audit_service import (
        HonorImportAuditContext,
        complete_honor_audit_batch,
        start_honor_audit_batch,
    )

    dal = Dal()
    worker = ImportAuditWriter(lambda: None, dal=dal).start()
    monkeypatch.setattr(transport, "_writer", worker)

    async def forbidden(*args, **kwargs):
        raise AssertionError("synchronous fallback forbidden")

    try:
        handle = await start_honor_audit_batch(
            context=HonorImportAuditContext(source_filename="sample.xlsx"),
            xlsx_bytes=b"private bytes",
            audit_runner=forbidden,
        )
        await complete_honor_audit_batch(handle, rows_written=3, audit_runner=forbidden)
        await asyncio.to_thread(wait_for, lambda: worker.settled == 2)
        assert [c[0] for c in dal.calls] == ["start", "complete"]
        assert "private bytes" not in repr(dal.calls)
        assert json.loads(dal.calls[0][1]["details_json"])["hash_availability"] == "unavailable"
    finally:
        worker.close()
