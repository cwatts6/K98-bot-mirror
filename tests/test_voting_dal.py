from __future__ import annotations

from datetime import UTC, datetime

import pytest

from voting import dal


@pytest.mark.asyncio
async def test_search_closed_vote_posts_filters_to_closed_votes(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "VotePostID": 42,
                "Title": "Best rally time?",
                "Status": "Closed",
                "ChannelID": 5,
                "ClosesAtUtc": datetime(2026, 7, 1, 20, 0),
                "ClosedAtUtc": datetime(2026, 7, 1, 21, 0),
            }
        ]

    monkeypatch.setattr(dal, "run_query_async", fake_run_query_async)

    choices = await dal.search_closed_vote_posts("rally", limit=99)

    assert "Status = 'Closed'" in str(captured["sql"])
    assert "MessageID IS NOT NULL" in str(captured["sql"])
    assert captured["params"] == (25, "rally", "%rally%", None)
    assert choices[0].vote_post_id == 42
    assert choices[0].closed_at_utc == datetime(2026, 7, 1, 21, 0, tzinfo=UTC)
