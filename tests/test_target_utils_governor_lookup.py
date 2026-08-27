from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_lookup_governor_row_by_id_uses_existing_cache(monkeypatch):
    import target_utils

    target_utils._name_cache["rows"] = [
        {"GovernorID": "123", "GovernorName": "Ada"},
        {"GovernorID": "456", "GovernorName": "Grace"},
    ]

    async def fail_refresh():
        raise AssertionError("refresh should not be called when rows are present")

    monkeypatch.setattr(target_utils, "refresh_name_cache_from_sql", fail_refresh)

    assert await target_utils.lookup_governor_row_by_id("123") == {
        "GovernorID": "123",
        "GovernorName": "Ada",
    }
    assert await target_utils.lookup_governor_row_by_id("999") is None


@pytest.mark.asyncio
async def test_lookup_governor_row_by_id_warms_empty_cache(monkeypatch):
    import target_utils

    target_utils._name_cache["rows"] = []

    async def fake_refresh():
        target_utils._name_cache["rows"] = [{"GovernorID": "789", "GovernorName": "Lin"}]

    monkeypatch.setattr(target_utils, "refresh_name_cache_from_sql", fake_refresh)

    assert await target_utils.lookup_governor_row_by_id("789") == {
        "GovernorID": "789",
        "GovernorName": "Lin",
    }


@pytest.mark.asyncio
async def test_lookup_governor_row_by_id_rejects_non_numeric():
    import target_utils

    assert await target_utils.lookup_governor_row_by_id("not-a-number") is None
