from __future__ import annotations

import pytest

from ark import admin_governor_lookup_service as svc
from services.governor_lookup_service import GovernorLookupResult


@pytest.mark.asyncio
async def test_resolve_admin_governor_query_wraps_shared_result(monkeypatch):
    async def _resolve(query):
        return GovernorLookupResult(
            status="matches",
            query=query,
            matches=({"GovernorID": "12072972", "GovernorName": "Talita Tia"},),
        )

    monkeypatch.setattr(svc, "resolve_governor_query", _resolve)

    result = await svc.resolve_admin_governor_query("120729")

    assert result.status == "matches"
    assert result.query == "120729"
    assert result.matches == ({"GovernorID": "12072972", "GovernorName": "Talita Tia"},)
