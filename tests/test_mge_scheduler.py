from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from mge.mge_scheduler import schedule_mge_lifecycle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("simplified_flow_enabled", "expected_leadership_calls"),
    [
        (False, 0),
        (True, 1),
    ],
)
async def test_scheduler_runs_and_calls_embed_sync(
    monkeypatch, simplified_flow_enabled, expected_leadership_calls
):
    calls = {"sync": 0, "embed": 0, "leadership": 0, "sleep": 0}

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
        assert signup_channel_id == 123
        return True

    async def fake_sleep(_):
        calls["sleep"] += 1
        raise asyncio.CancelledError

    async def fake_leadership(*, bot, event_id, now_utc=None):
        calls["leadership"] += 1
        assert event_id == 7
        return True

    monkeypatch.setattr(
        "mge.mge_scheduler.resolve_public_signup_channel_id", lambda: (123, 123, "primary")
    )
    monkeypatch.setattr("mge.mge_scheduler.sync_mge_events_from_calendar", fake_sync)
    monkeypatch.setattr("mge.mge_scheduler.sync_event_signup_embed", fake_embed)
    monkeypatch.setattr("mge.mge_scheduler.sync_event_leadership_embed", fake_leadership)
    monkeypatch.setattr("mge.mge_scheduler.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("mge.mge_scheduler.MGE_SIMPLIFIED_FLOW_ENABLED", simplified_flow_enabled)

    with pytest.raises(asyncio.CancelledError):
        await schedule_mge_lifecycle(bot=object())

    assert calls["sync"] == 1
    assert calls["embed"] == 1
    assert calls["leadership"] == expected_leadership_calls
