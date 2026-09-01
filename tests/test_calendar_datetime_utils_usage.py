from __future__ import annotations

import pytest

from event_calendar.datetime_utils import parse_iso_utc_nullable
from ui.views.calendar import CalendarLocalTimeToggleView


@pytest.mark.asyncio
async def test_calendar_view_uses_shared_datetime_parser_behavior():
    good = {"title": "ok", "type": "raid", "start_utc": "2099-01-01T00:00:00+00:00"}
    bad = {"title": "bad", "type": "raid", "start_utc": "not-a-datetime"}

    # shared helper expectations
    assert parse_iso_utc_nullable(good["start_utc"]) is not None
    assert parse_iso_utc_nullable(bad["start_utc"]) is None

    # constructing the discord View now happens under running event loop
    view = CalendarLocalTimeToggleView(events=[good, bad], prefix="x", timeout=10.0)
    assert len(view.events) == 1
    assert view.events[0]["title"] == "ok"
