from __future__ import annotations

from types import SimpleNamespace

import pytest

from event_calendar import service as service_module
from event_calendar.service import CalendarService


@pytest.mark.asyncio
async def test_pipeline_happy_path(monkeypatch):
    svc = CalendarService()

    def _refresh(*_a, **_k):
        return {"ok": True, "status": "success"}

    def _generate(*_a, **_k):
        return {"ok": True, "status": "success", "instances_generated": 12}

    def _publish(*_a, **_k):
        return {"ok": True, "status": "success", "events_written": 12}

    monkeypatch.setattr(
        service_module, "sync_sheets_to_sql", lambda *a, **k: SimpleNamespace(**_refresh(*a, **k))
    )
    monkeypatch.setattr(
        service_module,
        "generate_calendar_instances",
        lambda *a, **k: SimpleNamespace(**_generate(*a, **k)),
    )
    monkeypatch.setattr(
        service_module,
        "publish_event_calendar_cache",
        lambda *a, **k: SimpleNamespace(**_publish(*a, **k)),
    )
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

    def _refresh(*_a, **_k):
        return {"ok": False, "status": "failed_service", "details": "sync boom"}

    def _generate(*_a, **_k):
        raise AssertionError("generate should not be called")

    monkeypatch.setattr(
        service_module, "sync_sheets_to_sql", lambda *a, **k: SimpleNamespace(**_refresh(*a, **k))
    )
    monkeypatch.setattr(
        service_module,
        "generate_calendar_instances",
        lambda *a, **k: SimpleNamespace(**_generate(*a, **k)),
    )
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda _e: None)

    out = await svc.refresh_pipeline(sheet_id="abc")
    assert out["ok"] is False
    assert out["stage"] == "sync"
    assert out["sql_generation_success"] is False
    assert out["json_export_success"] is False


@pytest.mark.asyncio
async def test_pipeline_publish_preserve_counts_success(monkeypatch):
    svc = CalendarService()

    def _refresh(*_a, **_k):
        return {"ok": True, "status": "success"}

    def _generate(*_a, **_k):
        return {"ok": True, "status": "success", "instances_generated": 0}

    def _publish(*_a, **_k):
        return {"ok": True, "status": "skipped_empty_preserve_existing", "events_written": 0}

    monkeypatch.setattr(
        service_module, "sync_sheets_to_sql", lambda *a, **k: SimpleNamespace(**_refresh(*a, **k))
    )
    monkeypatch.setattr(
        service_module,
        "generate_calendar_instances",
        lambda *a, **k: SimpleNamespace(**_generate(*a, **k)),
    )
    monkeypatch.setattr(
        service_module,
        "publish_event_calendar_cache",
        lambda *a, **k: SimpleNamespace(**_publish(*a, **k)),
    )
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda _e: None)

    out = await svc.refresh_pipeline(sheet_id="abc")
    assert out["ok"] is True
    assert out["json_export_success"] is True
    assert out["publish_reason"] == "skipped_empty_preserve_existing"
