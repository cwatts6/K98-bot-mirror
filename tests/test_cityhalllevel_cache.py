from __future__ import annotations

import asyncio
import math
import os

import pytest

from target_utils import get_name_cache_rows, sync_refresh_worker


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

    rows = get_name_cache_rows()
    assert rows, "name_cache rows empty after refresh."
    assert any(
        not _is_missing(r.get("CityHallLevel")) for r in rows
    ), "CityHallLevel missing from all cached rows."


@pytest.mark.asyncio
@pytest.mark.parametrize("consumer", ["script", "integration_test"])
async def test_cityhall_readers_follow_snapshot_publication(monkeypatch, capsys, consumer):
    import target_utils
    import verify_cityhalllevel_cache as verifier

    monkeypatch.setattr(target_utils, "_name_cache", {"rows": []})

    def publish():
        # Reproduce the owner's atomic swap after consumers have imported.
        target_utils._name_cache = {
            "rows": [{"GovernorID": "123", "GovernorName": "Example", "CityHallLevel": 25}]
        }

    async def unexpected_sql():
        pytest.fail("Published rows must not trigger the empty-cache SQL diagnostic")

    monkeypatch.setattr(verifier, "sync_refresh_worker", publish)
    monkeypatch.setattr(verifier, "_count_view_rows", unexpected_sql)
    if consumer == "script":
        await verifier.main()
        assert "Total rows: 1" in capsys.readouterr().out
    else:
        monkeypatch.setenv("RUN_CITYHALLLEVEL_TEST", "1")
        monkeypatch.setitem(globals(), "sync_refresh_worker", publish)
        await test_cityhalllevel_cache_populates()
