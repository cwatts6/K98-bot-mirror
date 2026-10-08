from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

import event_scheduler as es


class _DummyUser:
    def __init__(self, uid: int = 1001):
        self.id = uid
        self.display_name = f"user-{uid}"

    async def send(self, embed=None):
        return None


@pytest.mark.asyncio
async def test_save_trackers_coalesced_calls_each_once(monkeypatch):
    sent_calls = []
    sched_calls = []

    async def _save_sent():
        sent_calls.append("sent")

    async def _save_sched():
        sched_calls.append("sched")

    monkeypatch.setattr(es, "save_dm_sent_tracker_async", _save_sent)
    monkeypatch.setattr(es, "save_dm_scheduled_tracker_async", _save_sched)

    await es._save_trackers_coalesced_async(sent=True, scheduled=True)

    assert sent_calls == ["sent"]
    assert sched_calls == ["sched"]


@pytest.mark.asyncio
async def test_save_trackers_coalesced_noop_when_no_flags(monkeypatch):
    called = []

    async def _save_sent():
        called.append("sent")

    async def _save_sched():
        called.append("sched")

    monkeypatch.setattr(es, "save_dm_sent_tracker_async", _save_sent)
    monkeypatch.setattr(es, "save_dm_scheduled_tracker_async", _save_sched)

    await es._save_trackers_coalesced_async(sent=False, scheduled=False)
    assert called == []


@pytest.mark.asyncio
async def test_send_user_reminder_coalesced_single_persist(monkeypatch):
    # isolate globals
    es.dm_sent_tracker.clear()
    es.dm_scheduled_tracker.clear()

    now = datetime.now(UTC)
    event = {
        "name": "Next Ruins",
        "type": "ruins",
        "start_time": now + timedelta(hours=3),
        "end_time": now + timedelta(hours=4),
    }
    event_id = es.make_event_id(event)
    uid = "1001"
    delta = timedelta(hours=1)
    delta_seconds = int(delta.total_seconds())

    # pre-mark as scheduled
    es.dm_scheduled_tracker.setdefault(event_id, {}).setdefault(uid, set()).add(delta_seconds)

    # deterministic quote + gov lookup
    monkeypatch.setattr(es.random, "choice", lambda items: items[0])
    monkeypatch.setattr(es, "_get_main_governor_name_for_user", lambda _uid: "GovMain")

    persist_calls = []

    async def _coalesced(*, sent: bool = False, scheduled: bool = False):
        persist_calls.append((sent, scheduled))

    monkeypatch.setattr(es, "_save_trackers_coalesced_async", _coalesced)

    user = _DummyUser(uid=int(uid))
    await es.send_user_reminder(user, event, delta)

    # sent tracker updated
    assert delta_seconds in es.dm_sent_tracker[event_id][uid]
    # scheduled marker removed
    assert delta_seconds not in es.dm_scheduled_tracker[event_id][uid]
    # exactly one coalesced persist call
    assert persist_calls == [(True, True)]


@pytest.mark.asyncio
async def test_send_user_reminder_duplicate_no_persist(monkeypatch):
    es.dm_sent_tracker.clear()
    es.dm_scheduled_tracker.clear()

    now = datetime.now(UTC)
    event = {
        "name": "Next Ruins",
        "type": "ruins",
        "start_time": now + timedelta(hours=3),
        "end_time": now + timedelta(hours=4),
    }
    event_id = es.make_event_id(event)
    uid = "1002"
    delta = timedelta(hours=1)
    delta_seconds = int(delta.total_seconds())

    es.dm_sent_tracker.setdefault(event_id, {}).setdefault(uid, []).append(delta_seconds)

    called = []

    async def _coalesced(*, sent: bool = False, scheduled: bool = False):
        called.append((sent, scheduled))

    monkeypatch.setattr(es, "_save_trackers_coalesced_async", _coalesced)

    user = _DummyUser(uid=int(uid))
    await es.send_user_reminder(user, event, delta)

    # duplicate path returns early; no write
    assert called == []
