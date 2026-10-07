from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.discord_embed_limits import require_valid_embed_payload
from embed_utils import LocalTimeToggleView


@pytest.mark.asyncio
async def test_local_time_embed_title_truncates():
    long_name = "A" * 300
    view = LocalTimeToggleView(
        events=[{"name": long_name, "type": "ruins", "start_time": datetime.now(UTC)}],
        prefix="arkmatch_2",
        timeout=None,
    )

    embed = await view.build_local_time_embed()

    assert embed.title is not None
    assert len(embed.title) <= 256
    assert embed.title.endswith("…")
    assert len(embed.fields[0].name) == 256
    assert embed.fields[0].name.endswith("…")
    require_valid_embed_payload(embed)


@pytest.mark.asyncio
async def test_complete_event_packing_uses_exact_omission_marker_without_partial_events():
    events = [
        {
            "name": f"{index}-" + ("N" * 2000),
            "type": "ruins",
            "start_time": datetime.now(UTC),
        }
        for index in range(12)
    ]
    view = LocalTimeToggleView(
        events=events,
        prefix="phase2a",
        timeout=None,
        complete_event_packing=True,
    )
    embed = await view.build_local_time_embed()
    values = "\n".join(field.value for field in embed.fields)
    shown = values.count("• **")

    assert f"{len(events) - shown} additional events omitted" in values
    assert not values.rstrip().endswith("\n…")
    require_valid_embed_payload(embed)


@pytest.mark.asyncio
async def test_complete_event_packing_is_opt_in():
    default_view = LocalTimeToggleView(events=[], prefix="prekvk", timeout=None)
    opted_in = LocalTimeToggleView(
        events=[], prefix="daily_kvk_overview", timeout=None, complete_event_packing=True
    )

    assert default_view.complete_event_packing is False
    assert opted_in.complete_event_packing is True
