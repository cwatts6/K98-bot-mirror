from __future__ import annotations

import pytest

from ark import admin_governor_lookup_service as svc


@pytest.mark.asyncio
async def test_resolve_admin_governor_query_exact_id(monkeypatch):
    async def _ensure_ready():
        return None

    monkeypatch.setattr(svc, "ensure_name_cache_ready", _ensure_ready)
    monkeypatch.setattr(
        svc,
        "get_name_cache_rows",
        lambda: [
            {"GovernorID": "12072972", "GovernorName": "Talita Tia"},
            {"GovernorID": "99999999", "GovernorName": "Other"},
        ],
    )

    result = await svc.resolve_admin_governor_query("12072972")

    assert result.status == "found"
    assert result.governor_id == "12072972"
    assert result.governor_name == "Talita Tia"


@pytest.mark.asyncio
async def test_resolve_admin_governor_query_partial_id_preserves_cache_order(monkeypatch):
    async def _ensure_ready():
        return None

    monkeypatch.setattr(svc, "ensure_name_cache_ready", _ensure_ready)
    monkeypatch.setattr(
        svc,
        "get_name_cache_rows",
        lambda: [
            {"GovernorID": "12072972", "GovernorName": "Talita Tia"},
            {"GovernorID": "12072999", "GovernorName": "Talita Two"},
            {"GovernorID": "99999999", "GovernorName": "Other"},
        ],
    )

    result = await svc.resolve_admin_governor_query("120729")

    assert result.status == "matches"
    assert [match["GovernorID"] for match in result.matches] == ["12072972", "12072999"]


@pytest.mark.asyncio
async def test_resolve_admin_governor_query_refreshes_and_uses_substring_fallback(monkeypatch):
    calls = {"lookup": 0, "ensure": 0}

    async def _lookup(_query):
        calls["lookup"] += 1
        return {"status": "not_found", "message": "Governor not found in the database"}

    async def _ensure_ready():
        calls["ensure"] += 1

    monkeypatch.setattr(svc, "lookup_governor_id", _lookup)
    monkeypatch.setattr(svc, "ensure_name_cache_ready", _ensure_ready)
    monkeypatch.setattr(
        svc,
        "get_name_cache_rows",
        lambda: [
            {"GovernorID": "12072972", "GovernorName": "Talita Tia"},
            {"GovernorID": "99999999", "GovernorName": "Other"},
        ],
    )

    result = await svc.resolve_admin_governor_query("tali")

    assert calls == {"lookup": 2, "ensure": 1}
    assert result.status == "matches"
    assert result.matches == ({"GovernorName": "Talita Tia", "GovernorID": "12072972"},)


@pytest.mark.asyncio
async def test_resolve_admin_governor_query_preserves_numeric_no_match_message(monkeypatch):
    async def _ensure_ready():
        return None

    monkeypatch.setattr(svc, "ensure_name_cache_ready", _ensure_ready)
    monkeypatch.setattr(svc, "get_name_cache_rows", lambda: [])

    result = await svc.resolve_admin_governor_query("123456")

    assert result.status == "not_found"
    assert result.message == "❌ GovernorID not found in name cache. Please verify the ID."
