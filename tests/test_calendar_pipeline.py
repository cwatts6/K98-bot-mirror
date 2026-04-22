from __future__ import annotations

import pytest

from event_calendar.service import CalendarService


@pytest.mark.asyncio
async def test_pipeline_happy_path(monkeypatch):
    svc = CalendarService()

    async def _refresh(**_k):
        return {"ok": True, "status": "success"}

    async def _generate(**_k):
        return {"ok": True, "status": "success", "instances_generated": 12}

    async def _publish(**_k):
        return {"ok": True, "status": "success", "events_written": 12}

    monkeypatch.setattr(svc, "refresh", _refresh)
    monkeypatch.setattr(svc, "generate", _generate)
    monkeypatch.setattr(svc, "publish_cache", _publish)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda _e: None)

    out = await svc.refresh_pipeline(sheet_id="abc", actor_source="scheduler")
    assert out["ok"] is True
    assert out["sheets_sync_success"] is True
    assert out["sql_generation_success"] is True
    assert out["json_export_success"] is True
    assert out["events_generated"] == 12
    assert out["stage"] == "done"


@pytest.mark.asyncio
async def test_pipeline_stops_on_sync_failure(monkeypatch):
    svc = CalendarService()

    async def _refresh(**_k):
        return {"ok": False, "status": "failed_service", "details": "sync boom"}

    async def _generate(**_k):
        raise AssertionError("generate should not be called")

    monkeypatch.setattr(svc, "refresh", _refresh)
    monkeypatch.setattr(svc, "generate", _generate)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda _e: None)

    out = await svc.refresh_pipeline(sheet_id="abc")
    assert out["ok"] is False
    assert out["stage"] == "sync"
    assert out["sql_generation_success"] is False
    assert out["json_export_success"] is False


@pytest.mark.asyncio
async def test_pipeline_publish_preserve_counts_success(monkeypatch):
    svc = CalendarService()

    async def _refresh(**_k):
        return {"ok": True, "status": "success"}

    async def _generate(**_k):
        return {"ok": True, "status": "success", "instances_generated": 0}

    async def _publish(**_k):
        return {"ok": True, "status": "skipped_empty_preserve_existing", "events_written": 0}

    monkeypatch.setattr(svc, "refresh", _refresh)
    monkeypatch.setattr(svc, "generate", _generate)
    monkeypatch.setattr(svc, "publish_cache", _publish)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda _e: None)

    out = await svc.refresh_pipeline(sheet_id="abc")
    assert out["ok"] is True
    assert out["json_export_success"] is True
    assert out["publish_reason"] == "skipped_empty_preserve_existing"
