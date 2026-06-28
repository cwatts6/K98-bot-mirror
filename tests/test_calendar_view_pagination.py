from __future__ import annotations

import types

import pytest

from ui.views.calendar import CalendarPaginationView


@pytest.mark.asyncio
async def test_next_button_increments_and_respects_upper_bound(monkeypatch):
    items = [
        {
            "instance_id": str(i),
            "title": f"Event {i}",
            "type": "raid",
            "importance": "high",
            "start_utc": "2099-01-01T00:00:00+00:00",
            "end_utc": "2099-01-01T01:00:00+00:00",
        }
        for i in range(20)
    ]

    view = CalendarPaginationView(
        title="Test",
        items=items,
        cache_footer_text="footer",
        owner_user_id=None,
        timeout=30.0,
    )
    assert view._page == 1
    assert view._total_pages == 3

    class DummyResponse:
        async def edit_message(self, **kwargs):
            return None

    interaction = types.SimpleNamespace(response=DummyResponse(), user=types.SimpleNamespace(id=1))

    # Call callback via class function; second arg is the button object (unused in method)
    await CalendarPaginationView.next_button(view, None, interaction)
    assert view._page == 2

    await CalendarPaginationView.next_button(view, None, interaction)
    assert view._page == 3

    # should stay at upper bound
    await CalendarPaginationView.next_button(view, None, interaction)
    assert view._page == 3
