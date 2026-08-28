from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_calendar_status_uses_nested_blocks(monkeypatch):
    # lightweight guard to ensure expected keys consumed by status renderer logic
    from event_calendar.service import CalendarService

    svc = CalendarService()
    st = await svc.get_status()
    assert "sync" in st
    assert "generate" in st
    assert "publish" in st
    assert "calendar_health" in st
