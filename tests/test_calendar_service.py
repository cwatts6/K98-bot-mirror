from __future__ import annotations

import asyncio
import threading

import pytest

from event_calendar import service as svc_mod
from event_calendar.cache_publisher import PublishResult
from event_calendar.event_generator import GenerationResult
from event_calendar.mutation_owner import get_owner
from event_calendar.service import CalendarService, _classify_error
from event_calendar.sheets_sync import SyncResult


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,physical,result,key",
    [
        ("refresh", "sync_sheets_to_sql", SyncResult(True, "success", rows_read_oneoff=2), "sync"),
        (
            "generate",
            "generate_calendar_instances",
            GenerationResult(True, "success", instances_generated=10),
            "generate",
        ),
        (
            "publish_cache",
            "publish_event_calendar_cache",
            PublishResult(True, "success", events_written=7),
            "publish",
        ),
    ],
)
async def test_stage_runs_once_on_worker_and_preserves_result(
    monkeypatch, method, physical, result, key
):
    calls = []
    main_thread = threading.get_ident()

    def work(*args, **kwargs):
        calls.append(threading.get_ident())
        return result

    monkeypatch.setattr(svc_mod, physical, work)
    svc = CalendarService()
    output = await getattr(svc, method)(**({"sheet_id": "offline"} if key == "sync" else {}))
    assert output["ok"] and output["status"] == "success"
    assert len(calls) == 1 and calls[0] != main_thread
    status = await svc.get_status()
    assert status[key]["status"] == "success"
    assert status["calendar_health"]["last_successful_pipeline_utc"] == "not_started"
    output["status"] = "tampered"
    assert (await svc.get_status())[key]["status"] == "success"
    await get_owner().audit.drain()


@pytest.mark.asyncio
async def test_calendar_service_refresh_missing_sheet_id():
    result = await CalendarService().refresh(sheet_id=None)
    assert not result["ok"] and result["status"] == "failed_service"
    assert result["effect"] == "failed_before_effects"


@pytest.mark.asyncio
async def test_refresh_failure_emits_telemetry(monkeypatch):
    events = []

    def fail(*args):
        raise ValueError("private input must not leak")

    monkeypatch.setattr(svc_mod, "sync_sheets_to_sql", fail)
    monkeypatch.setattr(svc_mod, "emit_telemetry_event", events.append)
    svc = CalendarService()
    result = await svc.refresh(sheet_id="offline")
    assert not result["ok"] and result["status"] == "failed_service"
    assert "private input" not in str(result)
    assert any(e.get("event") == "calendar_refresh" and e["ok"] is False for e in events)
    await get_owner().audit.drain()


@pytest.mark.asyncio
async def test_refresh_full_stops_on_sync_failure(monkeypatch):
    monkeypatch.setattr(
        svc_mod, "sync_sheets_to_sql", lambda *a: SyncResult(False, "validation_failed")
    )

    def forbidden(**kwargs):
        raise AssertionError("later stage entered")

    monkeypatch.setattr(svc_mod, "generate_calendar_instances", forbidden)
    result = await CalendarService().refresh_full(sheet_id="offline")
    assert not result["ok"] and result["stage"] == "sync"
    assert result["remaining_stages"] == ["generate", "publish"]
    await get_owner().audit.drain()


@pytest.mark.asyncio
async def test_pipeline_success_and_failure_history(monkeypatch):
    monkeypatch.setattr(svc_mod, "sync_sheets_to_sql", lambda *a: SyncResult(True, "success"))
    monkeypatch.setattr(
        svc_mod,
        "generate_calendar_instances",
        lambda **k: GenerationResult(True, "success", instances_generated=12),
    )
    monkeypatch.setattr(
        svc_mod,
        "publish_event_calendar_cache",
        lambda **k: PublishResult(True, "success", events_written=11),
    )
    svc = CalendarService()
    good = await svc.refresh_pipeline(sheet_id="offline")
    assert good["ok"] and good["events_generated"] == 12 and good["events_written"] == 11
    status = await svc.get_status()
    assert status["pipeline"]["pipeline_run_id"] == good["pipeline_run_id"]
    previous_success = status["calendar_health"]["last_successful_pipeline_utc"]
    assert previous_success != "not_started"
    monkeypatch.setattr(
        svc_mod,
        "generate_calendar_instances",
        lambda **k: GenerationResult(False, "rolled_back", error_message="RuntimeError"),
    )
    failed = await svc.refresh_pipeline(sheet_id="offline")
    assert not failed["ok"] and failed["stage"] == "generate"
    status = await svc.get_status()
    assert status["pipeline"]["status"] == "failed_generate"
    assert status["latest_error"]["stage"] == "generate"
    assert status["calendar_health"]["last_successful_pipeline_utc"] == previous_success
    await get_owner().audit.drain()


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
  "horizon_days": 365,
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
async def test_generic_failed_service_never_authorizes_mutation_retry(monkeypatch):
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

    assert result["ok"] is False
    assert attempts == 1
    assert calls["n"] == 1
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
