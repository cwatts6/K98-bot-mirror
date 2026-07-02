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


@pytest.mark.asyncio
async def test_list_vote_voter_audit_rows_maps_current_and_original_options(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "VotePostID": 42,
                "Title": "Best rally time?",
                "ClosedAtUtc": datetime(2026, 7, 1, 21, 0),
                "DiscordUserID": 123,
                "OptionID": 11,
                "OptionKey": "opt2",
                "OptionLabel": "19:00 UTC",
                "OriginalOptionID": 10,
                "OriginalOptionKey": "opt1",
                "OriginalOptionLabel": "18:00 UTC",
                "VoteCreatedAtUtc": datetime(2026, 7, 1, 20, 0),
                "VoteUpdatedAtUtc": datetime(2026, 7, 1, 20, 30),
            }
        ]

    monkeypatch.setattr(dal, "run_query_async", fake_run_query_async)

    rows = await dal.list_vote_voter_audit_rows(42)

    assert "FROM dbo.VotePostVotes" in str(captured["sql"])
    assert "JOIN dbo.VotePostOptions o" in str(captured["sql"])
    assert "LEFT JOIN dbo.VotePostOptions original" in str(captured["sql"])
    assert captured["params"] == (42,)
    assert rows[0].discord_user_id == 123
    assert rows[0].option_label == "19:00 UTC"
    assert rows[0].original_option_label == "18:00 UTC"
    assert rows[0].vote_updated_at_utc == datetime(2026, 7, 1, 20, 30, tzinfo=UTC)
