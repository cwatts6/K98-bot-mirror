from __future__ import annotations

import pytest

from event_calendar.service import CalendarService


@pytest.mark.asyncio
async def test_generate_failure_emits_telemetry(monkeypatch):
    svc = CalendarService()
    events = []

    async def fake_to_thread(fn, *args, **kwargs):
        raise RuntimeError("generate failed")

    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: events.append(e))

    out = await svc.generate(actor_user_id=7, horizon_days=30)
    assert out["ok"] is False
    assert any(e.get("event") == "calendar_generate" and e.get("ok") is False for e in events)


@pytest.mark.asyncio
async def test_publish_failure_emits_telemetry(monkeypatch):
    svc = CalendarService()
    events = []

    async def fake_to_thread(fn, *args, **kwargs):
        raise RuntimeError("publish failed")

    monkeypatch.setattr("event_calendar.service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("event_calendar.service.emit_telemetry_event", lambda e: events.append(e))

    out = await svc.publish_cache(actor_user_id=7, horizon_days=30, force_empty=False)
    assert out["ok"] is False
    assert any(e.get("event") == "calendar_publish_cache" and e.get("ok") is False for e in events)
