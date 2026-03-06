from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from event_calendar import service as svc_mod
from event_calendar.service import CalendarService


@pytest.mark.asyncio
async def test_calendar_service_refresh_success(monkeypatch):
    class _R:
        ok = True
        status = "success"
        rows_read_recurring = 1
        rows_read_oneoff = 2
        rows_read_overrides = 3
        rows_upserted_recurring = 1
        rows_upserted_oneoff = 0
        rows_upserted_overrides = 2
        instances_generated = 0
        error_message = None

    monkeypatch.setattr(svc_mod, "sync_sheets_to_sql", lambda _sid: _R())

    s = svc_mod.CalendarService()
    out = await s.refresh(actor_user_id=1, sheet_id="abc")
    assert out["ok"] is True
    assert out["status"] == "success"

    st = await s.get_status()
    assert st["sync"]["status"] == "success"
    assert st["sync"]["last_result"]["rows_read_oneoff"] == 2


@pytest.mark.asyncio
async def test_calendar_service_refresh_missing_sheet_id():
    s = svc_mod.CalendarService()
    out = await s.refresh(actor_user_id=1, sheet_id=None)
    assert out["ok"] is False
    assert out["status"] == "failed_service"


@pytest.mark.asyncio
async def test_refresh_uses_to_thread(monkeypatch):
    svc = CalendarService()

    called = {"to_thread": 0, "sync_fn": 0}

    class FakeSyncResult:
        ok = True
        status = "success"
        rows_read_recurring = 1
        rows_read_oneoff = 2
        rows_read_overrides = 3
        rows_upserted_recurring = 1
        rows_upserted_oneoff = 1
        rows_upserted_overrides = 1
        instances_generated = 0
        error_message = None

    def fake_sync(sheet_id: str):
        called["sync_fn"] += 1
        assert sheet_id == "sheet123"
        return FakeSyncResult()

    async def fake_to_thread(fn, *args, **kwargs):
        called["to_thread"] += 1
        assert fn is fake_sync
        return fn(*args, **kwargs)

    monkeypatch.setattr("event_calendar.service.sync_sheets_to_sql", fake_sync)
    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: None)

    out = await svc.refresh(actor_user_id=42, sheet_id="sheet123")
    assert out["ok"] is True
    assert called["to_thread"] == 1
    assert called["sync_fn"] == 1


@pytest.mark.asyncio
async def test_refresh_failure_emits_telemetry(monkeypatch):
    svc = CalendarService()
    events = []

    async def fake_to_thread(fn, *args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: events.append(e))

    out = await svc.refresh(actor_user_id=99, sheet_id="x")
    assert out["ok"] is False
    assert out["status"] == "failed_service"
    assert any(e.get("event") == "calendar_refresh" and e.get("ok") is False for e in events)


@pytest.mark.asyncio
async def test_generate_uses_to_thread_and_updates_status(monkeypatch):
    svc = CalendarService()

    class FakeGenResult:
        ok = True
        status = "success"
        instances_generated = 10
        instances_written = 10
        cancelled_count = 1
        modified_count = 2
        error_message = None

    async def fake_to_thread(fn, *args, **kwargs):
        return FakeGenResult()

    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: None)

    out = await svc.generate(actor_user_id=1, horizon_days=365)
    assert out["ok"] is True
    status = await svc.get_status()
    assert status["generate"]["status"] == "success"
    assert status["generate"]["last_result"]["instances_generated"] == 10


@pytest.mark.asyncio
async def test_publish_uses_to_thread_and_updates_status(monkeypatch):
    svc = CalendarService()

    class FakePubResult:
        ok = True
        status = "success"
        events_written = 7
        cache_path = "cache/event_calendar.json"
        error_message = None

    async def fake_to_thread(fn, *args, **kwargs):
        return FakePubResult()

    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: None)

    out = await svc.publish_cache(actor_user_id=1, horizon_days=365, force_empty=False)
    assert out["ok"] is True
    status = await svc.get_status()
    assert status["publish"]["status"] == "success"
    assert status["publish"]["last_result"]["events_written"] == 7


@pytest.mark.asyncio
async def test_refresh_full_stops_on_sync_failure(monkeypatch):
    svc = CalendarService()
    svc.refresh = AsyncMock(return_value={"ok": False, "status": "failed_service"})
    svc.generate = AsyncMock()
    svc.publish_cache = AsyncMock()

    out = await svc.refresh_full(actor_user_id=1, sheet_id="abc")
    assert out["ok"] is False
    assert out["stage"] == "sync"
    svc.generate.assert_not_called()
    svc.publish_cache.assert_not_called()


@pytest.mark.asyncio
async def test_status_includes_calendar_health(monkeypatch, tmp_path):
    from event_calendar import service as svc_local

    cache = tmp_path / "event_calendar_cache.json"
    cache.write_text('{"events":[]}', encoding="utf-8")
    monkeypatch.setattr(svc_local, "EVENT_CALENDAR_CACHE_FILE_PATH", str(cache))

    s = svc_local.CalendarService()
    st = await s.get_status()
    assert "calendar_health" in st
    assert "current_degraded_mode" in st["calendar_health"]


@pytest.mark.asyncio
async def test_calendar_health_degraded_on_stale_cache(monkeypatch, tmp_path):
    from datetime import UTC, datetime, timedelta

    from event_calendar import service as svc_local

    cache = tmp_path / "event_calendar_cache.json"
    cache.write_text('{"events":[]}', encoding="utf-8")
    old = datetime.now(UTC) - timedelta(minutes=300)
    ts = old.timestamp()
    import os

    os.utime(cache, (ts, ts))

    monkeypatch.setattr(svc_local, "EVENT_CALENDAR_CACHE_FILE_PATH", str(cache))
    monkeypatch.setattr(svc_local, "EVENT_CALENDAR_STALE_WARN_MINUTES", 60)
    monkeypatch.setattr(svc_local, "EVENT_CALENDAR_STALE_DEGRADED_MINUTES", 240)

    s = svc_local.CalendarService()
    st = await s.get_status()
    assert st["calendar_health"]["current_degraded_mode"] is True
