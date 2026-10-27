import asyncio
from datetime import UTC, datetime, timedelta
import json
from types import SimpleNamespace

import pytest

from core.scheduler_lifecycle import EventTaskBundle, EventTaskMember
from services.event_cache_service import UpcomingEventCacheSnapshot


def snapshot(*, available=True, populated=True):
    return UpcomingEventCacheSnapshot(
        available,
        ({"name": "event"},) if populated else (),
        datetime.now(UTC) if available else None,
        False,
    )


@pytest.mark.asyncio
async def test_empty_starts_loops_but_defers_one_shots_until_populated():
    current = snapshot(populated=False)
    running, once = set(), []

    async def restore():
        once.append(1)
        return {"status": "complete"}

    bundle = EventTaskBundle(
        [
            EventTaskMember("loop", lambda: running.add("loop"), registration=True),
            EventTaskMember("restore", restore, needs_events=True),
        ],
        snapshot=lambda: current,
        is_running=lambda name: name in running,
    )
    assert (await bundle.tick())["needs_observation"]
    assert running == {"loop"} and not once
    current = snapshot()
    await asyncio.gather(bundle.tick(), bundle.tick())
    await asyncio.sleep(0)
    assert (await bundle.tick())["status"] == "complete"
    assert once == [1]
    await bundle.tick()
    assert once == [1]


@pytest.mark.asyncio
async def test_late_and_uncertain_one_shot_is_never_replayed():
    release = asyncio.Event()
    calls = 0
    clock = [0]

    async def operation():
        nonlocal calls
        calls += 1
        await release.wait()
        raise RuntimeError("lost response")

    bundle = EventTaskBundle(
        [EventTaskMember("edit", operation)],
        snapshot=snapshot,
        is_running=lambda name: False,
        clock=lambda: clock[0],
    )
    await bundle.tick()
    await asyncio.sleep(0)
    clock[0] = 11
    assert (await bundle.tick())["members"]["edit"]["state"] == "pending_after_deadline"
    release.set()
    await asyncio.sleep(0)
    assert (await bundle.tick())["members"]["edit"]["state"] == "outcome_unconfirmed"
    await bundle.tick()
    assert calls == 1


@pytest.mark.asyncio
async def test_partial_registration_retries_only_failed_member():
    counts, running, clock = {"a": 0, "b": 0}, set(), [0]

    def register(name):
        counts[name] += 1
        if name == "b" and counts[name] < 2:
            raise RuntimeError("before registration")
        running.add(name)

    bundle = EventTaskBundle(
        [EventTaskMember(name, lambda n=name: register(n), registration=True) for name in counts],
        snapshot=snapshot,
        is_running=lambda name: name in running,
        clock=lambda: clock[0],
    )
    await bundle.tick()
    clock[0] = 2
    assert (await bundle.tick())["status"] == "complete"
    assert counts == {"a": 1, "b": 2}


@pytest.mark.asyncio
async def test_shutdown_cancels_original_and_closes_admission():
    entered = asyncio.Event()

    async def operation():
        entered.set()
        await asyncio.Event().wait()

    bundle = EventTaskBundle(
        [EventTaskMember("restore", operation)], snapshot=snapshot, is_running=lambda name: False
    )
    await bundle.tick()
    await entered.wait()
    await bundle.shutdown()
    report = await bundle.tick()
    assert report["admission_closed"]
    assert report["members"]["restore"]["state"] == "cancelled_outcome_unconfirmed"


@pytest.mark.asyncio
async def test_dm_empty_preserves_markers_without_saving(monkeypatch):
    import event_cache
    import event_scheduler as scheduler

    markers = {"retained": {"123": {60}}}
    monkeypatch.setattr(scheduler, "dm_scheduled_tracker", markers)
    monkeypatch.setattr(
        event_cache, "get_upcoming_event_cache_snapshot", lambda: snapshot(populated=False)
    )
    monkeypatch.setattr(
        scheduler, "save_dm_scheduled_tracker", lambda: pytest.fail("unexpected save")
    )
    result = await scheduler.rehydrate_dm_scheduled_tasks(object())
    assert result["status"] == "deferred"
    assert markers == {"retained": {"123": {60}}}


@pytest.mark.asyncio
async def test_dm_loads_once_and_restores_before_normal_admission(monkeypatch):
    import event_cache
    import event_scheduler as scheduler

    current = snapshot(populated=False)
    calls = []
    monkeypatch.setattr(scheduler, "_dm_startup_state", "not_started")
    monkeypatch.setattr(scheduler, "_dm_startup_error", None)
    monkeypatch.setattr(scheduler, "_dm_startup_lock", asyncio.Lock())

    async def load_sent():
        calls.append("sent")

    async def load_scheduled():
        calls.append("scheduled")

    monkeypatch.setattr(scheduler, "load_dm_sent_tracker_async", load_sent)
    monkeypatch.setattr(scheduler, "load_dm_scheduled_tracker_async", load_scheduled)
    monkeypatch.setattr(event_cache, "get_upcoming_event_cache_snapshot", lambda: current)

    async def restore(_bot):
        assert calls == ["sent", "scheduled"]
        calls.append("restore")
        return {"status": "complete"}

    monkeypatch.setattr(scheduler, "rehydrate_dm_scheduled_tasks", restore)
    owner = asyncio.create_task(scheduler._ensure_dm_startup(object()))
    try:
        for _ in range(100):
            if scheduler.dm_startup_report()["state"] == "waiting_for_events":
                break
            await asyncio.sleep(0.01)
        assert calls == ["sent", "scheduled"]
        assert not owner.done()
        current = snapshot()
        assert await asyncio.wait_for(owner, 2)
        assert await scheduler._ensure_dm_startup(object())
        assert calls == ["sent", "scheduled", "restore"]
    finally:
        owner.cancel()
        await asyncio.gather(owner, return_exceptions=True)


@pytest.mark.asyncio
async def test_corrupt_dm_tracker_blocks_startup_and_is_not_reloaded(monkeypatch, tmp_path):
    import event_scheduler as scheduler

    path = tmp_path / "sent.json"
    path.write_text('{"event": 99}', encoding="utf-8")
    monkeypatch.setattr(scheduler, "DM_SENT_TRACKER_FILE", str(path))
    monkeypatch.setattr(scheduler, "dm_sent_tracker", {"retained": {"123": [0]}})
    monkeypatch.setattr(scheduler, "_dm_startup_state", "not_started")
    monkeypatch.setattr(scheduler, "_dm_startup_error", None)
    monkeypatch.setattr(scheduler, "_dm_startup_lock", asyncio.Lock())
    assert not await scheduler._ensure_dm_startup(object())
    path.write_text("{}", encoding="utf-8")
    assert not await scheduler._ensure_dm_startup(object())
    assert scheduler.dm_sent_tracker == {"retained": {"123": [0]}}
    assert scheduler.dm_startup_report() == {"state": "unconfirmed", "error": "ValueError"}


@pytest.mark.asyncio
@pytest.mark.parametrize("seconds_until", [60, -5])
@pytest.mark.parametrize("failure", [None, "save", "item"])
async def test_dm_cleanup_admits_startup_only_after_confirmed_disposition(
    monkeypatch, tmp_path, seconds_until, failure
):
    import event_cache
    import event_scheduler as scheduler

    now = datetime.now(UTC)
    event = {"name": "event", "start_time": now + timedelta(hours=1)}
    delta = "invalid" if failure == "item" else 3600 - seconds_until
    markers = {"event": {"1": {delta}, "2": {3600 - seconds_until}}}
    tasks, fetched = [], []
    path = tmp_path / "scheduled.json"
    monkeypatch.setattr(scheduler, "DM_SCHEDULED_TRACKER_FILE", str(path))
    monkeypatch.setattr(scheduler, "dm_scheduled_tracker", markers)
    monkeypatch.setattr(scheduler, "_dm_startup_state", "not_started")
    monkeypatch.setattr(scheduler, "_dm_startup_error", None)
    monkeypatch.setattr(scheduler, "_dm_startup_lock", asyncio.Lock())

    async def loaded():
        pass

    monkeypatch.setattr(scheduler, "load_dm_sent_tracker_async", loaded)
    monkeypatch.setattr(scheduler, "load_dm_scheduled_tracker_async", loaded)
    monkeypatch.setattr(scheduler, "utcnow", lambda: now)
    monkeypatch.setattr(scheduler, "make_event_id", lambda _event: "event")
    monkeypatch.setattr(
        event_cache,
        "get_upcoming_event_cache_snapshot",
        lambda: UpcomingEventCacheSnapshot(True, (event,), now, False),
    )

    async def fetch_user(uid):
        fetched.append(uid)
        if uid == 1:
            raise RuntimeError("existing fetch-failure cleanup policy")
        return SimpleNamespace(id=uid)

    async def reminder(*_args):
        pass

    monkeypatch.setattr(scheduler, "_dm_eligible", lambda *_: True)
    monkeypatch.setattr(scheduler, "delayed_user_dm", reminder)
    monkeypatch.setattr(scheduler, "send_user_reminder", reminder)
    monkeypatch.setattr(
        scheduler, "register_user_task", lambda _uid, task, **_kw: tasks.append(task)
    )
    if failure == "save":

        def fail_save(*args):
            raise PermissionError("test persistence failure")

        monkeypatch.setattr(scheduler, "save_dm_scheduled_tracker", fail_save)

    try:
        assert await scheduler._ensure_dm_startup(SimpleNamespace(fetch_user=fetch_user)) is (
            failure is None
        )
        assert scheduler.dm_startup_report()["state"] == (
            "complete" if failure is None else "unconfirmed"
        )
        expected = {"event": {"2": {3600 - seconds_until}}}
        if failure == "item":
            expected["event"]["1"] = {"invalid"}
        assert markers == expected
        assert len(tasks) == 1
        if failure is None:
            assert json.loads(path.read_text(encoding="utf-8")) == {
                "event": {"2": [3600 - seconds_until]}
            }
        before = list(fetched)
        assert await scheduler._ensure_dm_startup(SimpleNamespace(fetch_user=fetch_user)) is (
            failure is None
        )
        assert fetched == before and len(tasks) == 1
    finally:
        await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_unavailable_cache_can_recover_after_multiple_observation_windows(monkeypatch):
    from core import scheduler_lifecycle as lifecycle

    calls, started = [], []
    original_sleep = asyncio.sleep

    async def wait(seconds):
        calls.append(seconds)
        return len(calls) == 3

    async def start():
        started.append(1)
        return {"needs_observation": False}

    monkeypatch.setattr(lifecycle.asyncio, "sleep", lambda _seconds: original_sleep(0))
    await lifecycle._start_event_tasks_when_ready(
        start_event_scheduler_tasks=start, wait_for_events=wait, max_wait_seconds=300
    )
    assert calls == [300, 300, 300]
    assert started == [1]


@pytest.mark.asyncio
async def test_failed_one_shot_factory_does_not_block_other_members_or_reenter():
    running = set()

    def fail():
        raise RuntimeError("entered adapter")

    bundle = EventTaskBundle(
        [
            EventTaskMember("uncertain", fail),
            EventTaskMember("loop", lambda: running.add("loop"), registration=True),
        ],
        snapshot=snapshot,
        is_running=lambda name: name in running,
    )
    await bundle.tick()
    report = await bundle.tick()
    assert report["members"]["uncertain"]["state"] == "outcome_unconfirmed"
    assert report["members"]["uncertain"]["attempts"] == 1
    assert running == {"loop"}


@pytest.mark.parametrize("path", ["bot_instance.py", "services/recovery_health.py"])
def test_historical_hash_bridge_rejects_foreign_runtime_bytes(tmp_path, path):
    from pathlib import Path

    from tests.updater_source_assertions import before_contention_hash

    fixture = Path("tests/fixtures/p1_startup_source_pairs.json")
    (tmp_path / fixture).parent.mkdir(parents=True)
    (tmp_path / fixture).write_bytes(fixture.read_bytes())
    monitoring = Path("tests/fixtures/p1_monitoring_source_pairs.json")
    (tmp_path / monitoring).write_bytes(monitoring.read_bytes())
    attempt = Path("tests/fixtures/procconfig_admission_source_pairs.json")
    (tmp_path / attempt).write_bytes(attempt.read_bytes())
    lifecycle = Path("tests/fixtures/coordination_lifecycle_source_pairs.json")
    (tmp_path / lifecycle).write_bytes(lifecycle.read_bytes())

    checkpoint = Path("tests/fixtures/checkpoint_observation_source_pairs.json")
    (tmp_path / checkpoint).write_bytes(checkpoint.read_bytes())
    health = Path("tests/fixtures/health_activity_source_pairs.json")
    (tmp_path / health).write_bytes(health.read_bytes())

    source = tmp_path / path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"unreviewed runtime image\n")
    with pytest.raises(AssertionError, match=path):
        before_contention_hash(tmp_path, path)
