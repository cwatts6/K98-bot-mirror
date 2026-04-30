from datetime import UTC, datetime, timedelta

import pytest

from server_activity.activity_models import ActivityEvent, ActivityEventType, ActivityUserSummary
from server_activity.activity_service import (
    aggregate_events,
    cutoff_for_window,
    get_top_users,
    normalize_activity_event,
)
from server_activity.activity_store import insert_activity_event


def _event(days_ago: int, user_id: int, event_type: ActivityEventType) -> ActivityEvent:
    return ActivityEvent(
        occurred_at_utc=datetime(2026, 4, 28, 12, tzinfo=UTC) - timedelta(days=days_ago),
        guild_id=1,
        channel_id=2,
        user_id=user_id,
        event_type=event_type,
    )


def test_normalize_activity_event_rejects_missing_ids():
    assert (
        normalize_activity_event(
            event_type=ActivityEventType.MESSAGE,
            guild_id=None,
            channel_id=2,
            user_id=3,
        )
        is None
    )


def test_activity_aggregation_windows():
    now = datetime(2026, 4, 28, 12, tzinfo=UTC)
    events = [
        _event(0, 10, ActivityEventType.MESSAGE),
        _event(0, 10, ActivityEventType.REACTION_ADD),
        _event(2, 20, ActivityEventType.VOICE_JOIN),
        _event(6, 20, ActivityEventType.MESSAGE),
    ]

    rows_24h = aggregate_events(events, since_utc=cutoff_for_window("24h", as_of_utc=now))
    rows_3d = aggregate_events(events, since_utc=cutoff_for_window("3d", as_of_utc=now))
    rows_7d = aggregate_events(events, since_utc=cutoff_for_window("7d", as_of_utc=now))

    assert [(r.user_id, r.score) for r in rows_24h] == [(10, 2)]
    assert [(r.user_id, r.score) for r in rows_3d] == [(10, 2), (20, 1)]
    assert [(r.user_id, r.score) for r in rows_7d] == [(10, 2), (20, 2)]


@pytest.mark.asyncio
async def test_get_top_users_handles_empty_store(monkeypatch):
    async def _empty(**_kwargs):
        return []

    monkeypatch.setattr("server_activity.activity_service.fetch_activity_top_async", _empty)
    result = await get_top_users(
        guild_id=1,
        window="24h",
        as_of_utc=datetime(2026, 4, 28, 12, tzinfo=UTC),
    )
    assert result.rows == []
    assert result.window == "24h"


@pytest.mark.asyncio
async def test_get_top_users_hands_off_to_store(monkeypatch):
    calls = []

    async def _fetch(**kwargs):
        calls.append(kwargs)
        return [ActivityUserSummary(user_id=10, score=3)]

    monkeypatch.setattr("server_activity.activity_service.fetch_activity_top_async", _fetch)
    result = await get_top_users(
        guild_id=99,
        window="3d",
        limit=10,
        as_of_utc=datetime(2026, 4, 28, 12, tzinfo=UTC),
    )

    assert result.rows[0].user_id == 10
    assert calls[0]["guild_id"] == 99
    assert calls[0]["limit"] == 10


def test_insert_activity_event_persists_normalized_row(monkeypatch):
    calls = []

    def _execute(sql, params):
        calls.append((sql, params))
        return 1

    monkeypatch.setattr("server_activity.activity_store.execute", _execute)

    event = ActivityEvent(
        occurred_at_utc=datetime(2026, 4, 28, 12, 34, 56, 123456, tzinfo=UTC),
        guild_id=1,
        channel_id=2,
        user_id=3,
        event_type=ActivityEventType.MESSAGE,
        metadata={"message_id": 4},
    )

    assert insert_activity_event(event) == 1
    assert calls[0][1][0] == datetime(2026, 4, 28, 12, 34, 56)
    assert calls[0][1][4] == "message"
    assert calls[0][1][5] == '{"message_id":4}'
