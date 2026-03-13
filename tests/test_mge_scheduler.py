from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from mge.mge_scheduler import schedule_mge_lifecycle


@pytest.mark.asyncio
async def test_scheduler_runs_and_calls_embed_sync(monkeypatch):
    calls = {"sync": 0, "embed": 0, "sleep": 0}

    def fake_sync(now_utc=None):
        calls["sync"] += 1
        assert isinstance(now_utc, datetime)
        assert now_utc.tzinfo == UTC
        return type(
            "R", (), {"scanned": 1, "created": 1, "existing": 0, "skipped": 0, "errors": 0}
        )(), [7]

    async def fake_embed(*, bot, event_id, signup_channel_id, now_utc=None):
        calls["embed"] += 1
        assert event_id == 7
        return True

    async def fake_sleep(_):
        calls["sleep"] += 1
        raise asyncio.CancelledError

    monkeypatch.setattr("mge.mge_scheduler.sync_mge_events_from_calendar", fake_sync)
    monkeypatch.setattr("mge.mge_scheduler.sync_event_signup_embed", fake_embed)
    monkeypatch.setattr("mge.mge_scheduler.MGE_SIGNUP_CHANNEL_ID", 123)
    monkeypatch.setattr("mge.mge_scheduler.asyncio.sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_mge_lifecycle(bot=object())

    assert calls["sync"] == 1
    assert calls["embed"] == 1
