from __future__ import annotations

import types

import pytest

from core.discord_embed_limits import validate_embed_payload
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


@pytest.mark.asyncio
async def test_pathological_page_keeps_page_size_and_marks_exact_whole_item_omissions():
    items = [
        {
            "instance_id": str(i),
            "title": f"{i}-" + ("T" * 2000),
            "variant": "V" * 500,
            "type": "raid",
            "start_utc": "2099-01-01T00:00:00+00:00",
            "end_utc": "2099-01-01T01:00:00+00:00",
            "link_url": "https://example.invalid/" + ("a" * 476),
        }
        for i in range(8)
    ]
    view = CalendarPaginationView(
        title="Test",
        items=items,
        cache_footer_text="footer",
        owner_user_id=None,
    )

    embed = view._build_current_embed()
    shown = (embed.description or "").count("starts:")
    omitted = len(items) - shown

    assert view._total_pages == 1
    assert (
        f"… {omitted} more events on this page omitted to fit Discord limits" in embed.description
    )
    assert not validate_embed_payload(embed)
