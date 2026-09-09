from __future__ import annotations

import asyncio
import math
import os

import pytest

from target_utils import _name_cache, sync_refresh_worker


def _is_missing(val) -> bool:
    if val is None:
        return True
    try:
        return math.isnan(float(val))
    except Exception:
        return False


@pytest.mark.asyncio
async def test_cityhalllevel_cache_populates():
    if os.getenv("RUN_CITYHALLLEVEL_TEST") != "1":
        pytest.skip("Set RUN_CITYHALLLEVEL_TEST=1 to run this DB-backed test.")

    # In-process refresh to populate this process' cache
    await asyncio.to_thread(sync_refresh_worker)

    rows = _name_cache.get("rows", [])
    assert rows, "name_cache rows empty after refresh."
    assert any(
        not _is_missing(r.get("CityHallLevel")) for r in rows
    ), "CityHallLevel missing from all cached rows."
