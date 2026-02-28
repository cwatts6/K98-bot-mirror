from __future__ import annotations

from datetime import UTC, datetime

import pytest

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
