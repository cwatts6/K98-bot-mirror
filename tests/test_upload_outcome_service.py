import asyncio
from contextlib import contextmanager
import threading
from types import SimpleNamespace

import pytest

from services.upload_outcome_service import CommittedKvkResult, delivery_details
from stats_alerts.delivery_outcomes import DeliveryAttempt, DeliveryResult


def test_delivery_keeps_mixed_receipts_and_legacy_unknown():
    value = DeliveryResult(
        (
            DeliveryAttempt("a", outcome="sent", acknowledged=True),
            DeliveryAttempt("b", outcome="unknown"),
        ),
        "c",
        "route",
    )
    assert [a["outcome"] for a in delivery_details(value)["attempts"]] == ["sent", "unknown"]
    assert delivery_details(None) == {"delivery": "unverified", "attempts": []}


@pytest.mark.parametrize("count", [None, "bad", 7])
@pytest.mark.parametrize("operation", ["merge", "replace"])
def test_location_commit_survives_count_and_close_failure(monkeypatch, count, operation):
    import location_importer as importer

    events = []

    class Connection:
        def cursor(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, *args):
            pass

        def executemany(self, *args):
            pass

        def commit(self):
            events.append("commit")

        def rollback(self):
            events.append("rollback")

        def close(self):
            raise OSError("close unavailable")

    monkeypatch.setattr(importer, "_get_conn", Connection)
    monkeypatch.setattr(
        importer,
        "fetch_one_dict",
        lambda cur: {
            "StagingRows" if operation == "merge" else "ImportedRows": count,
            "TotalTracked": None,
        },
    )
    result = getattr(importer, "load_staging_and_" + operation)([(1,) * 10])
    assert result == (7 if count == 7 else None, None)
    assert result.cleanup == "unconfirmed" and events == ["commit"]


def test_kvk_capture_error_preserves_only_acknowledged_result(monkeypatch):
    from services import legacy_export_snapshot_service as service

    owner = SimpleNamespace(failed=False, closed=False)

    @contextmanager
    def scope(*args, **kwargs):
        yield owner
        raise OSError("capture or close failed")

    monkeypatch.setattr(service, "writer_scope", scope)
    result = CommittedKvkResult(success=True, kvk_no=16, scan_id=3, row_count=4)
    wrapped = service.admitted_writer("all_kvk", preserve_kvk_commit=True)(lambda: result)
    assert wrapped() is result
    assert result["capture_outcome"] == "unconfirmed"
    assert "export_preparation_id" not in result
    with pytest.raises(OSError):
        service.admitted_writer("all_kvk", preserve_kvk_commit=True)(lambda: dict(success=True))()


@pytest.mark.asyncio
async def test_finite_staged_reader_cancel_retains_lock_and_file_until_settled(tmp_path):
    from core.owned_work import drain_thread
    from services.fallback_upload_staging_service import stage_and_process_fallback_attachment

    entered = threading.Event()
    release = threading.Event()
    paths = []
    lock = asyncio.Lock()

    async def download(attachment, path, **kwargs):
        from pathlib import Path

        Path(path).write_bytes(b"unique content")
        paths.append(Path(path))
        return True

    def read(path):
        entered.set()
        assert release.wait(3)
        assert path.read_bytes() == b"unique content"

    async def process(name, path):
        await drain_thread(read, paths[0])

    task = asyncio.create_task(
        stage_and_process_fallback_attachment(
            SimpleNamespace(filename="stats.csv"),
            download_folder=tmp_path,
            processing_lock=lock,
            download_attachment=download,
            process_attachment=process,
        )
    )
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        await asyncio.sleep(0.02)
        assert not task.done() and lock.locked() and paths[0].exists()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not lock.locked() and not paths[0].exists()
    finally:
        release.set()


@pytest.mark.asyncio
async def test_weekly_source_count_cancellation_waits_for_parser(monkeypatch):
    from upload_routes import weekly_activity_route as route

    entered = threading.Event()
    release = threading.Event()

    def parse(content):
        entered.set()
        assert release.wait(3)
        return [content]

    monkeypatch.setattr(route, "parse_activity_excel", parse)
    task = asyncio.create_task(route.count_weekly_activity_source_rows(b"fixture"))
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        await asyncio.sleep(0.02)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        release.set()


@pytest.mark.asyncio
async def test_shutdown_closes_upload_admission_and_waits_for_physical_entry(monkeypatch):
    from core.owned_work import drain_thread
    from services import upload_lifecycle as life

    monkeypatch.setattr(life, "_closed", False)
    monkeypatch.setattr(life, "_tasks", set())
    entered = threading.Event()
    release = threading.Event()

    def work():
        entered.set()
        assert release.wait(3)

    @life.tracked_upload
    async def upload():
        await drain_thread(work)

    active = asyncio.create_task(upload())
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        closing = asyncio.create_task(life.drain())
        await asyncio.sleep(0.02)
        assert not closing.done() and not active.done()
        with pytest.raises(life.UploadAdmissionClosed):
            await upload()
        release.set()
        await closing
        assert active.cancelled() and not life._tasks
    finally:
        release.set()
