from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_warm_target_cache_uses_isolated_single_flight_entrypoint(monkeypatch):
    import file_utils
    import target_utils

    calls = []

    async def fake_isolation(fn, **kwargs):
        calls.append((fn, kwargs))
        return {"status": "ok"}

    monkeypatch.setattr(file_utils, "run_maintenance_with_isolation", fake_isolation)

    await target_utils.warm_target_cache()

    assert calls == [
        (
            target_utils.refresh_targets_cache,
            {
                "name": "refresh_targets_cache",
                "prefer_process": True,
                "meta": {"caller": "warm_target_cache"},
            },
        )
    ]


def test_sync_refresh_worker_uses_target_dal_directory_contract(monkeypatch):
    import target_utils

    monkeypatch.setattr(
        target_utils.kvk_targets_dal,
        "fetch_governor_lookup_rows",
        lambda: [
            {"GovernorID": 123, "GovernorName": " Ada ", "CityHallLevel": 25.0},
            {"GovernorID": None, "GovernorName": "Invalid", "CityHallLevel": 1.0},
        ],
    )

    result = target_utils.sync_refresh_worker()

    assert result["rows"] == [{"GovernorID": "123", "GovernorName": "Ada", "CityHallLevel": 25.0}]
    assert result["norm_to_row"]["ada"]["GovernorID"] == "123"


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
