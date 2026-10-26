import asyncio
from contextlib import nullcontext
import hashlib
import json
import threading
from unittest.mock import Mock

import pytest

from core import startup_diagnostics as startup
import player_stats_cache as cache
from services import player_stats_startup as subject
from services.legacy_export_snapshot_service import drain_thread


@pytest.fixture
def snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(startup, "_steps", {})
    path = tmp_path / "cache.json"
    monkeypatch.setattr(cache, "PLAYER_STATS_CACHE", str(path))
    output = {
        "1": {"GovernorID": "1", "GovernorName": "private name"},
        "_meta": {
            "count": 1,
            "source_row_count": 1,
            "source_kvk_no": 16,
            "source_last_refresh": "2026-10-21T06:00:00+00:00",
            "source_refresh_status": "refreshed",
            "cache_write_status": "written",
            "existing_json_preserved": False,
        },
    }
    path.write_text(json.dumps(output), encoding="utf-8")
    return path, output


@pytest.mark.asyncio
async def test_same_worker_finishes_after_deadline_with_verified_cache(snapshot, monkeypatch):
    path, output = snapshot
    entered, release = threading.Event(), threading.Event()
    calls = []

    def worker():
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return output

    # Exercise the real async cache entrypoint and its protected worker drain.
    import services.legacy_export_snapshot_service as legacy

    monkeypatch.setattr(legacy, "caller_runtime", lambda: nullcontext())
    monkeypatch.setattr(legacy, "_writer_runtime", lambda: object())
    monkeypatch.setattr(cache, "_build_and_persist_cache_sync", worker)
    task = asyncio.create_task(
        startup.run(
            cache.build_player_stats_cache(),
            0.001,
            "build_player_stats_cache",
            cancel_on_deadline=False,
            completion_check=subject.verify_completion,
        )
    )
    try:
        for _ in range(500):
            if entered.is_set() and startup.report()[0]["state"] == "deadline_elapsed_pending":
                break
            await asyncio.sleep(0.001)
        assert startup.report()[0]["state"] == "deadline_elapsed_pending"
        assert not task.done()
    finally:
        release.set()
    assert await task == output
    row = startup.report()[0]
    assert row["state"] == "completed_after_deadline"
    assert row["completion"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert row["completion"]["sql_execution_receipt"] is False
    assert "private name" not in str(row)
    assert calls == [1]


@pytest.mark.parametrize("status", ["refreshed", "skipped", "last_known_good"])
def test_readback_preserves_source_quality_without_sql(snapshot, monkeypatch, status):
    path, output = snapshot
    output["_meta"]["source_refresh_status"] = status
    path.write_text(json.dumps(output), encoding="utf-8")
    sql = Mock(side_effect=AssertionError("verification must not calculate"))
    monkeypatch.setattr(cache, "_execute_sp_with_retries", sql)
    assert subject._verify_completion(output)["source_refresh_status"] == status
    sql.assert_not_called()


@pytest.mark.parametrize("failure", ["failed", "missing", "changed", "invalid", "empty"])
@pytest.mark.asyncio
async def test_invalid_completion_is_failed_and_does_not_modify_saved_cache(snapshot, failure):
    path, output = snapshot
    if failure == "failed":
        output["_meta"].update(
            source_refresh_status="failed", cache_write_status="preserved_existing"
        )
    elif failure == "missing":
        path.unlink()
    elif failure == "changed":
        path.write_text('{"newer": true}', encoding="utf-8")
    elif failure == "invalid":
        path.write_text("{", encoding="utf-8")
    else:
        output = None
    before = path.read_bytes() if path.exists() else None

    async def work():
        return output

    assert (
        await startup.run(
            work(), 1, "cache", cancel_on_deadline=False, completion_check=subject.verify_completion
        )
        is None
    )
    assert startup.report()[0]["state"] == "failed"
    assert "completion" not in startup.report()[0]
    assert (path.read_bytes() if path.exists() else None) == before


@pytest.mark.asyncio
async def test_shutdown_during_pending_worker_drains_and_preserves_cancellation(snapshot):
    _, output = snapshot
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    calls = []

    def worker():
        calls.append(1)
        entered.set()
        assert release.wait(5)
        finished.set()
        return output

    task = asyncio.create_task(
        startup.run(drain_thread(worker), 0.001, "cache", cancel_on_deadline=False)
    )
    try:
        for _ in range(500):
            if entered.is_set() and startup.report()[0]["state"] == "deadline_elapsed_pending":
                break
            await asyncio.sleep(0.001)
        task.cancel()
        await asyncio.sleep(0.01)
        task.cancel()
        await asyncio.sleep(0.01)
        assert not task.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set()
    assert calls == [1]
    assert startup.report()[0]["state"] == "cancelled_outcome_unconfirmed"


@pytest.mark.asyncio
async def test_current_observation_does_not_reuse_previous_process_completion(
    snapshot, monkeypatch
):
    _, output = snapshot
    subject._verify_completion(output)
    monkeypatch.setattr(startup, "_steps", {})
    assert startup.report() == []
