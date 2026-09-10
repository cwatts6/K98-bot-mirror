from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

import event_scheduler as scheduler


@pytest.mark.asyncio
async def test_live_scheduler_consumes_shared_authorized_at_start_candidate(monkeypatch) -> None:
    now = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
    event = {
        "name": "Ancient Ruins",
        "type": "ruins",
        "start_time": now + timedelta(hours=1),
        "end_time": now + timedelta(hours=2),
    }
    captured: list[dict] = []

    class FakeUser:
        id = 42

    class FakeBot:
        async def fetch_user(self, user_id: int):
            assert user_id == 42
            return FakeUser()

    async def no_op_async(*_args, **_kwargs):
        return None

    def capture_task(user_id, task, *, meta):
        captured.append({"user_id": user_id, "meta": meta})
        task.cancel()

    monkeypatch.setattr(scheduler, "load_dm_sent_tracker_async", no_op_async)
    monkeypatch.setattr(scheduler, "load_dm_scheduled_tracker_async", no_op_async)
    monkeypatch.setattr(scheduler, "rehydrate_dm_scheduled_tasks", no_op_async)
    monkeypatch.setattr(scheduler, "cleanup_dm_scheduled_tracker_async", no_op_async)
    monkeypatch.setattr(scheduler, "cleanup_dm_sent_tracker_async", no_op_async)
    monkeypatch.setattr(scheduler, "save_dm_scheduled_tracker", lambda: None)
    monkeypatch.setattr(scheduler, "REMINDER_WINDOWS", ())
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [event])
    monkeypatch.setattr(
        scheduler,
        "get_all_subscribers",
        lambda: {
            "42": {
                "subscriptions": ["ruins"],
                "reminder_times": ["now"],
            }
        },
    )
    monkeypatch.setattr(scheduler, "utcnow", lambda: now)
    monkeypatch.setattr(scheduler, "register_user_task", capture_task)
    monkeypatch.setattr(scheduler, "dm_sent_tracker", {})
    monkeypatch.setattr(scheduler, "dm_scheduled_tracker", {})

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(
            scheduler.schedule_event_reminders(FakeBot(), notify_channel_id=1),
            timeout=0.05,
        )

    assert captured == [
        {
            "user_id": 42,
            "meta": {
                "event_id": scheduler.make_event_id(event),
                "delta_seconds": 0,
            },
        }
    ]
