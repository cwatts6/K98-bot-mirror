from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from event_calendar import service as svc_mod
from event_calendar.service import CalendarService, _classify_error


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

    from event_calendar import service as svc_local

    async def fake_to_thread(fn, *args, **kwargs):
        if fn is svc_local.generate_calendar_instances:
            return FakeGenResult()
        return fn(*args, **kwargs)

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
        type_index_path = "cache/event_type_index.json"
        error_message = None

    from event_calendar import service as svc_local

    async def fake_to_thread(fn, *args, **kwargs):
        if fn is svc_local.publish_event_calendar_cache:
            return FakePubResult()
        return fn(*args, **kwargs)

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


@pytest.mark.asyncio
async def test_calendar_health_uses_to_thread(monkeypatch, tmp_path):
    from event_calendar import service as svc_local

    cache = tmp_path / "event_calendar_cache.json"
    cache.write_text('{"events":[]}', encoding="utf-8")
    monkeypatch.setattr(svc_local, "EVENT_CALENDAR_CACHE_FILE_PATH", str(cache))

    called = {"to_thread": 0}

    async def fake_to_thread(fn, *args, **kwargs):
        called["to_thread"] += 1
        assert fn is svc_local._load_cache_state
        return fn(*args, **kwargs)

    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)

    s = svc_local.CalendarService()
    st = await s.get_status()
    assert "calendar_health" in st
    assert called["to_thread"] == 1


@pytest.mark.asyncio
async def test_get_status_defaults_not_started(monkeypatch):
    svc = svc_mod.CalendarService()

    async def _fake_health():
        return {
            "cache_age_minutes": None,
            "cache_event_count": None,
            "cache_horizon_days": None,
            "cache_stale_warning": False,
            "next_upcoming_event_utc": None,
            "last_successful_pipeline_utc": "not_started",
            "current_degraded_mode": False,
        }

    monkeypatch.setattr(svc, "_calendar_health", _fake_health)

    st = await svc.get_status()

    assert st["sync"]["status"] == "not_started"
    assert st["sync"]["last_refresh_utc"] == "not_started"
    assert st["generate"]["status"] == "not_started"
    assert st["generate"]["last_generate_utc"] == "not_started"
    assert st["publish"]["status"] == "not_started"
    assert st["publish"]["last_publish_utc"] == "not_started"
    assert st["pipeline"]["status"] == "not_started"
    assert st["pipeline"]["last_run_utc"] == "not_started"
    assert st["pipeline"]["pipeline_run_id"] == "not_started"
    assert st["latest_error"] == {}
    assert st["calendar_health"]["last_successful_pipeline_utc"] == "not_started"


@pytest.mark.asyncio
async def test_calendar_health_reads_cache_count_and_horizon(tmp_path, monkeypatch):
    cache_file = tmp_path / "event_calendar_cache.json"
    cache_file.write_text(
        """
{
  "meta": {"horizon_days": 365},
  "events": [
    {"start_utc": "2099-01-01T00:00:00+00:00"},
    {"start_utc": "2099-01-02T00:00:00+00:00"}
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(svc_mod, "EVENT_CALENDAR_CACHE_FILE_PATH", str(cache_file))

    svc = svc_mod.CalendarService()
    health = await svc._calendar_health()

    assert health["cache_event_count"] == 2
    assert health["cache_horizon_days"] == 365
    assert health["cache_stale_warning"] in (True, False)
    assert "last_successful_pipeline_utc" in health


@pytest.mark.asyncio
async def test_refresh_pipeline_success_sets_pipeline_run_id_and_clears_latest_error(monkeypatch):
    svc = svc_mod.CalendarService()
    svc._latest_error = {
        "stage": "sync",
        "error_type": "Example",
        "message": "old",
        "at_utc": "2000-01-01T00:00:00+00:00",
    }

    async def _fake_refresh(*, actor_user_id=None, sheet_id=None):
        return {"ok": True, "status": "success", "details": "ok"}

    async def _fake_generate(*, actor_user_id=None, horizon_days=365):
        return {
            "ok": True,
            "status": "success",
            "instances_generated": 12,
            "details": "ok",
        }

    async def _fake_publish(*, actor_user_id=None, horizon_days=365, force_empty=False):
        return {
            "ok": True,
            "status": "success",
            "events_written": 11,
            "details": "ok",
        }

    monkeypatch.setattr(svc, "refresh", _fake_refresh)
    monkeypatch.setattr(svc, "generate", _fake_generate)
    monkeypatch.setattr(svc, "publish_cache", _fake_publish)

    out = await svc.refresh_pipeline(actor_user_id=1, sheet_id="sheet123")

    assert out["ok"] is True
    assert out["stage"] == "done"
    assert out["pipeline_run_id"]
    assert out["events_generated"] == 12
    assert out["events_written"] == 11

    st = await svc.get_status()
    assert st["pipeline"]["status"] == "success"
    assert st["pipeline"]["pipeline_run_id"] == out["pipeline_run_id"]
    assert st["latest_error"] == {}


@pytest.mark.asyncio
async def test_result_based_retry_retries_retryable_status(monkeypatch):
    svc = svc_mod.CalendarService()
    calls = {"n": 0}

    async def _stage_call():
        calls["n"] += 1
        if calls["n"] == 1:
            return {"ok": False, "status": "failed_service", "details": "temporary"}
        return {"ok": True, "status": "success", "details": "ok"}

    original_sleep = asyncio.sleep

    async def _fake_sleep(_s):
        await original_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)

    result, dur, attempts = await svc._run_stage_with_policy(
        pipeline_run_id="run1",
        actor_source="test",
        stage_name="sync",
        policy=svc_mod._StagePolicy(timeout_seconds=3, retries=2),
        stage_call=_stage_call,
        allow_timeout_retry=False,
    )

    assert result["ok"] is True
    assert attempts == 2
    assert calls["n"] == 2
    assert isinstance(dur, int)


@pytest.mark.asyncio
async def test_result_based_retry_does_not_retry_non_retryable_status():
    svc = svc_mod.CalendarService()
    calls = {"n": 0}

    async def _stage_call():
        calls["n"] += 1
        return {"ok": False, "status": "validation_failed", "details": "bad input"}

    result, _dur, attempts = await svc._run_stage_with_policy(
        pipeline_run_id="run2",
        actor_source="test",
        stage_name="generate",
        policy=svc_mod._StagePolicy(timeout_seconds=3, retries=3),
        stage_call=_stage_call,
        allow_timeout_retry=False,
    )

    assert result["ok"] is False
    assert attempts == 1
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_timeout_does_not_retry_when_timeout_retry_disabled():
    svc = svc_mod.CalendarService()
    calls = {"n": 0}

    async def _stage_call():
        calls["n"] += 1
        raise TimeoutError("simulated timeout")

    with pytest.raises(asyncio.TimeoutError):
        await svc._run_stage_with_policy(
            pipeline_run_id="run3",
            actor_source="test",
            stage_name="publish",
            policy=svc_mod._StagePolicy(timeout_seconds=1, retries=3),
            stage_call=_stage_call,
            allow_timeout_retry=False,
        )

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_refresh_pipeline_failure_sets_latest_error(monkeypatch):
    svc = svc_mod.CalendarService()

    async def _fake_refresh(*, actor_user_id=None, sheet_id=None):
        return {"ok": True, "status": "success", "details": "ok"}

    async def _fake_generate(*, actor_user_id=None, horizon_days=365):
        return {"ok": False, "status": "failed_service", "details": "gen broke"}

    async def _fake_publish(*, actor_user_id=None, horizon_days=365, force_empty=False):
        return {"ok": True, "status": "success", "events_written": 1, "details": "ok"}

    monkeypatch.setattr(svc, "refresh", _fake_refresh)
    monkeypatch.setattr(svc, "generate", _fake_generate)
    monkeypatch.setattr(svc, "publish_cache", _fake_publish)

    out = await svc.refresh_pipeline(actor_user_id=1, sheet_id="sheet123")

    assert out["ok"] is False
    assert out["stage"] == "generate"

    st = await svc.get_status()
    assert st["pipeline"]["status"] == "failed_generate"
    assert st["latest_error"]["stage"] == "generate"
    assert "gen broke" in st["latest_error"]["message"]


@pytest.mark.asyncio
async def test_classify_error_timeout_tuple_fix():
    assert svc_mod._classify_error(TimeoutError("x")) == "timeout"
    assert svc_mod._classify_error(TimeoutError("x")) == "timeout"
    assert svc_mod._classify_error(RuntimeError("x")) == "exception"


@pytest.mark.asyncio
async def test_stage_telemetry_non_ok_not_labeled_success(monkeypatch):
    svc = svc_mod.CalendarService()
    emitted: list[dict] = []

    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: emitted.append(e))

    async def _stage_call():
        return {"ok": False, "status": "validation_failed", "details": "bad"}

    result, _dur, attempts = await svc._run_stage_with_policy(
        pipeline_run_id="run-telemetry",
        actor_source="test",
        stage_name="sync",
        policy=svc_mod._StagePolicy(timeout_seconds=5, retries=0),
        stage_call=_stage_call,
        allow_timeout_retry=False,
    )

    assert attempts == 1
    assert result["ok"] is False

    events = [e.get("event") for e in emitted]
    assert "calendar_pipeline_stage_completed_not_ok" in events
    assert "calendar_pipeline_stage_succeeded" not in events


def test_classify_timeouterror_and_asyncio_timeouterror():
    assert _classify_error(TimeoutError()) == "timeout"
    assert _classify_error(TimeoutError()) == "timeout"
