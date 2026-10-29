from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from threading import Event

import pytest

from services.event_cache_service import (
    EventCacheService,
    UpcomingEventCacheSnapshot,
    refresh_message,
)


def make_service(*, fetch=None, persist=None):
    state = {"count": 0, "stamp": None, "generation": 0, "persistence": "unknown", "fetches": 0}

    async def default_fetch():
        state["fetches"] += 1
        return []

    async def default_persist(rows, stamp):
        pass

    def publish(rows, stamp, persistence):
        state.update(
            count=len(rows),
            stamp=stamp,
            persistence=persistence,
            generation=state["generation"] + 1,
        )

    def snapshot():
        return UpcomingEventCacheSnapshot(
            state["stamp"] is not None,
            tuple({} for _ in range(state["count"])),
            state["stamp"],
            False,
            generation=state["generation"],
            persistence=state["persistence"],
        )

    service = EventCacheService(
        snapshot=snapshot,
        fetch=fetch or default_fetch,
        normalize=lambda rows: rows,
        preserve=lambda rows: False,
        persist=persist or default_persist,
        publish=publish,
        clock=lambda: datetime.now(UTC),
    )
    return service, state


@pytest.mark.asyncio
async def test_empty_is_ready_and_report_is_read_only():
    service, state = make_service()
    result = await service.refresh()
    assert result.status == "refreshed"
    assert result.count == 0
    assert service.report()["availability"] == "loaded_empty"
    assert service.report() == service.report()
    assert state["fetches"] == 1


@pytest.mark.asyncio
async def test_observer_timeout_and_cancellation_share_original_owner():
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        entered.set()
        await release.wait()
        return []

    service, _ = make_service(fetch=fetch)
    observer = asyncio.create_task(service.refresh())
    await entered.wait()
    pending = await service.refresh(observation_seconds=0)
    assert pending.status == "pending" and pending.joined
    observer.cancel()
    with pytest.raises(asyncio.CancelledError):
        await observer
    joined = asyncio.create_task(service.refresh())
    await asyncio.sleep(0)
    release.set()
    result = await joined
    assert result.joined and result.status == "refreshed"
    assert calls == 1
    assert (await service.refresh()).attempt == 2


@pytest.mark.asyncio
async def test_failed_fetch_retains_snapshot_and_time():
    service, state = make_service()
    first = await service.refresh()

    async def fail():
        raise ValueError("private provider details")

    service.fetch = fail
    result = await service.refresh()
    assert result.status == "failed" and result.cache == "retained"
    assert result.last_refreshed == first.last_refreshed
    assert result.generation == first.generation
    assert "private provider" not in str(service.report())
    assert state["generation"] == 1


@pytest.mark.asyncio
async def test_failed_persistence_keeps_live_availability_distinct():
    async def fail(rows, stamp):
        raise PermissionError("private path")

    service, _ = make_service(persist=fail)
    result = await service.refresh()
    assert result.status == "refreshed_memory_only"
    assert result.fetch == "succeeded" and result.persistence == "failed"
    assert service.report()["availability"] == "loaded_empty"
    assert "saving" in refresh_message(result)


@pytest.mark.asyncio
async def test_empty_preservation_does_not_claim_replacement_or_advance_time():
    service, state = make_service()
    first = await service.refresh()
    service.preserve = lambda rows: True
    result = await service.refresh()
    assert result.status == "retained_by_policy"
    assert result.persistence == "not_attempted"
    assert result.last_refreshed == first.last_refreshed
    assert state["generation"] == 1


@pytest.mark.asyncio
async def test_shutdown_drains_real_worker_even_after_repeated_cancellation():
    from services.legacy_export_snapshot_service import drain_thread

    entered, release = Event(), Event()

    def worker():
        entered.set()
        assert release.wait(5)
        return []

    service, state = make_service(fetch=lambda: drain_thread(worker))
    observer = asyncio.create_task(service.refresh())
    await asyncio.to_thread(entered.wait, 2)
    stop = asyncio.create_task(service.shutdown())
    await asyncio.sleep(0)
    stop.cancel()
    await asyncio.sleep(0)
    assert not stop.done()
    assert (await service.refresh()).status == "closed"
    release.set()
    await stop
    with pytest.raises(asyncio.CancelledError):
        await observer
    assert state["generation"] == 0


@pytest.mark.asyncio
async def test_shutdown_during_save_does_not_publish_late_snapshot():
    from services.legacy_export_snapshot_service import drain_thread

    entered, release = Event(), Event()

    def worker():
        entered.set()
        assert release.wait(5)

    async def persist(rows, stamp):
        await drain_thread(worker)

    service, state = make_service(persist=persist)
    observer = asyncio.create_task(service.refresh())
    await asyncio.to_thread(entered.wait, 2)
    stop = asyncio.create_task(service.shutdown())
    await asyncio.sleep(0)
    assert not stop.done()
    release.set()
    await stop
    with pytest.raises(asyncio.CancelledError):
        await observer
    assert state["generation"] == 0


def test_disk_invalid_candidate_preserves_memory_and_bytes(monkeypatch, tmp_path):
    import event_cache as cache

    path = tmp_path / "cache.json"
    path.write_text('{"last_refreshed":"bad","events":[]}', encoding="utf-8")
    monkeypatch.setattr(cache, "CACHE_FILE_PATH", str(path))
    stamp = datetime.now(UTC)
    monkeypatch.setattr(cache, "last_refreshed", stamp)
    monkeypatch.setattr(cache, "event_cache", [])
    original = path.read_bytes()
    cache.load_event_cache()
    assert cache.last_refreshed == stamp
    assert path.read_bytes() == original


@pytest.mark.asyncio
async def test_real_loader_deadline_drains_before_another_fetch(monkeypatch):
    import event_cache as cache
    import event_data_loader as loader

    entered, release = Event(), Event()
    calls = []

    def fetch(range_a1, **kwargs):
        calls.append(range_a1)
        if range_a1 == loader.RANGES["ruins"]:
            entered.set()
            assert release.wait(5)
        return []

    monkeypatch.setattr(loader, "_fetch_values", fetch)
    monkeypatch.setattr(cache, "GSHEETS_CALL_TIMEOUT", 0.01)
    monkeypatch.setattr(cache, "EVENT_CACHE_MIN_REFRESH_TIMEOUT", 0.02)
    service, _state = make_service(fetch=cache._fetch)
    try:
        assert (await service.refresh(observation_seconds=0.03)).status == "pending"
        assert entered.is_set()
        second = await service.refresh(observation_seconds=0.01)
        assert second.status == "pending" and second.joined
        assert len(calls) == 4
        release.set()
        final = await service.refresh()
        assert final.status == "failed" and final.attempt == 1
        assert len(calls) == 4
    finally:
        release.set()
        await service.shutdown()


def test_disk_valid_empty_and_failed_replace(monkeypatch, tmp_path):
    import event_cache as cache
    import file_utils

    path = tmp_path / "cache.json"
    path.write_text('{"last_refreshed":"2026-01-01T00:00:00+00:00","events":[]}', encoding="utf-8")
    monkeypatch.setattr(cache, "CACHE_FILE_PATH", str(path))
    monkeypatch.setattr(cache, "event_cache", [])
    monkeypatch.setattr(cache, "last_refreshed", None)
    cache.load_event_cache()
    assert cache.get_upcoming_event_cache_snapshot().ok
    original = path.read_bytes()

    def fail(*args, **kwargs):
        raise PermissionError()

    monkeypatch.setattr(file_utils, "atomic_write_json", fail)
    with pytest.raises(PermissionError):
        cache.save_event_cache([], datetime.now(UTC))
    assert path.read_bytes() == original
