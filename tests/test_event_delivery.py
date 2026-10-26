import asyncio
from datetime import UTC, datetime, timedelta
import json
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
import pytest

import event_scheduler as scheduler
from services import event_delivery_service as delivery
from services.event_delivery_store import EventDeliveryStore, delivery_key
from services.overview_delivery_service import MessageAbsent, publish


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(delivery, "store", EventDeliveryStore(tmp_path / "receipts.json"))
    monkeypatch.setattr(delivery, "_locks", {})
    monkeypatch.setattr(delivery, "_children", set())
    monkeypatch.setattr(delivery, "_closed", False)
    monkeypatch.setattr(scheduler, "active_reminders", {})
    monkeypatch.setattr(scheduler, "_unresolved_active", {})
    monkeypatch.setattr(scheduler, "_active_load_failed", False)
    monkeypatch.setattr(scheduler, "dm_sent_tracker", {})
    monkeypatch.setattr(scheduler, "dm_scheduled_tracker", {})
    monkeypatch.setattr(scheduler, "REMINDER_TRACKING_FILE", str(tmp_path / "active.json"))
    monkeypatch.setattr(scheduler, "DM_SENT_TRACKER_FILE", str(tmp_path / "sent.json"))
    monkeypatch.setattr(scheduler, "DM_SCHEDULED_TRACKER_FILE", str(tmp_path / "scheduled.json"))
    monkeypatch.setattr(
        scheduler, "get_user_config", lambda _: {"subscriptions": ["all"], "reminder_times": ["1h"]}
    )
    monkeypatch.setattr(scheduler, "_get_main_governor_name_for_user", lambda _: "Governor")
    return tmp_path


def event():
    return dict(name="Battle", type="major", start_time=datetime.now(UTC) + timedelta(hours=1))


def user(send=None):
    return SimpleNamespace(
        id=17,
        display_name="Player",
        send=send or AsyncMock(return_value=SimpleNamespace(id=81, channel=SimpleNamespace(id=91))),
    )


def test_enter_is_atomic_across_store_instances_and_restart(tmp_path):
    path = tmp_path / "evidence.json"
    one, two = EventDeliveryStore(path), EventDeliveryStore(path)
    assert one.begin("key", kind="dm-send", target=1)
    assert not two.begin("key", kind="dm-send", target=1)
    assert two.get("key")["state"] == "entered"
    one.finish("key", "acknowledged", message_id=81, channel_id=91)
    assert not two.begin("key", kind="dm-send", target=1)
    assert two.get("key")["message_id"] == 81


@pytest.mark.asyncio
async def test_dm_concurrent_observers_send_once(isolated):
    recipient, occurrence = user(), event()
    await asyncio.gather(
        *(scheduler.send_user_reminder(recipient, occurrence, timedelta(hours=1)) for _ in range(2))
    )
    recipient.send.assert_awaited_once()
    assert delivery.store.rows()[0]["message_id"] == 81


@pytest.mark.asyncio
async def test_dm_cancelled_entered_send_remains_held_after_restart(isolated):
    entered = asyncio.Event()

    async def send(**kwargs):
        entered.set()
        await asyncio.Event().wait()

    recipient, occurrence = user(send), event()
    eid = scheduler.make_event_id(occurrence)
    scheduler.dm_scheduled_tracker[eid] = {"17": {3600}}
    task = asyncio.create_task(
        scheduler.send_user_reminder(recipient, occurrence, timedelta(hours=1))
    )
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert scheduler.dm_scheduled_tracker[eid]["17"] == {3600}
    recipient.send = AsyncMock()
    delivery.store = EventDeliveryStore(delivery.store.path)
    assert (
        await scheduler.send_user_reminder(recipient, occurrence, timedelta(hours=1)) == "entered"
    )
    recipient.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_dm_unsubscribe_prevents_restored_send(isolated, monkeypatch):
    recipient, occurrence = user(), event()
    eid = scheduler.make_event_id(occurrence)
    scheduler.dm_scheduled_tracker[eid] = {"17": {3600}}
    monkeypatch.setattr(scheduler, "get_user_config", lambda _: None)
    assert (
        await scheduler.send_user_reminder(recipient, occurrence, timedelta(hours=1))
        == "not_subscribed"
    )
    recipient.send.assert_not_awaited()
    assert scheduler.dm_scheduled_tracker[eid]["17"] == set()


@pytest.mark.asyncio
async def test_dm_ack_repairs_projection_without_resending(isolated, monkeypatch):
    recipient, occurrence = user(), event()
    eid = scheduler.make_event_id(occurrence)
    key = delivery_key("dm-send", "17", eid, 3600)
    delivery.store.begin(key, kind="dm-send", target=17, event=eid, window=3600)
    delivery.store.finish(key, "acknowledged", message_id=81, channel_id=91)
    scheduler.dm_scheduled_tracker[eid] = {"17": {3600}}
    await scheduler.send_user_reminder(recipient, occurrence, timedelta(hours=1))
    recipient.send.assert_not_awaited()
    assert json.loads((isolated / "sent.json").read_text())[eid]["17"] == [3600]
    assert json.loads((isolated / "scheduled.json").read_text())[eid]["17"] == []


@pytest.mark.asyncio
async def test_old_expiry_cannot_delete_replacement(isolated):
    msg = SimpleNamespace(id=82, channel=SimpleNamespace(id=91), delete=AsyncMock())
    scheduler.active_reminders["event"] = msg
    await scheduler.expire_single_reminder("event", 0, 81)
    msg.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_failure_retains_original_and_blocks_reentry(isolated):
    msg = SimpleNamespace(
        id=82, channel=SimpleNamespace(id=91), delete=AsyncMock(side_effect=RuntimeError())
    )
    scheduler.active_reminders["event"] = msg
    assert await scheduler.safe_delete_reminder("event") == "unconfirmed"
    assert await scheduler.safe_delete_reminder("event") == "unconfirmed"
    msg.delete.assert_awaited_once()
    assert scheduler.active_reminders["event"] is msg


def overview_adapter():
    return SimpleNamespace(
        prepare=AsyncMock(),
        identity=AsyncMock(return_value=None),
        send=AsyncMock(return_value=81),
        fetch=AsyncMock(),
        edit=AsyncMock(return_value=81),
        pin=AsyncMock(return_value=81),
        delete=AsyncMock(return_value=81),
        absent=AsyncMock(side_effect=MessageAbsent()),
        save_projection=AsyncMock(),
        remove_projection=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_overview_partial_projection_is_repairable_without_duplicate(isolated):
    adapter = overview_adapter()
    adapter.save_projection.side_effect = OSError("disk full")
    with pytest.raises(OSError):
        await publish(adapter, 91, enabled=True, has_events=True, revision="r1")
    adapter.save_projection.side_effect = None
    assert await publish(adapter, 91, enabled=True, has_events=True, revision="r1") == "updated"
    adapter.send.assert_awaited_once()
    adapter.pin.assert_awaited_once()


@pytest.mark.asyncio
async def test_overview_edit_notfound_never_becomes_send(isolated):
    adapter = overview_adapter()
    adapter.identity.return_value = 81
    adapter.edit.side_effect = discord.NotFound(
        SimpleNamespace(status=404, reason="Not Found"), {"code": 10008, "message": "gone"}
    )
    with pytest.raises(discord.NotFound):
        await publish(adapter, 91, enabled=True, has_events=True, revision="r1")
    assert (
        await publish(adapter, 91, enabled=True, has_events=True, revision="r2")
        == "unconfirmed_previous_operation"
    )
    adapter.send.assert_not_awaited()
    adapter.remove_projection.assert_not_awaited()


@pytest.mark.asyncio
async def test_overview_offseason_removal_retains_failed_disposition(isolated):
    adapter = overview_adapter()
    adapter.identity.return_value = 81
    adapter.delete.side_effect = RuntimeError()
    with pytest.raises(RuntimeError):
        await publish(adapter, 91, enabled=False, has_events=False, revision="r1")
    adapter.remove_projection.assert_not_awaited()
    assert (
        await publish(adapter, 91, enabled=False, has_events=False, revision="r1")
        == "unconfirmed_previous_operation"
    )


@pytest.mark.asyncio
async def test_shutdown_waits_for_child_finalizer_and_closes_admission(isolated):
    entered, finalizing, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def child():
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            finalizing.set()
            await release.wait()

    delivery.own(child(), name="test")
    await entered.wait()
    shutdown = asyncio.create_task(delivery.shutdown())
    await finalizing.wait()
    shutdown.cancel()
    await asyncio.sleep(0)
    assert not shutdown.done()
    assert delivery.own(child(), name="late") is None
    release.set()
    await shutdown


@pytest.mark.asyncio
async def test_corrupt_journal_prevents_send(isolated):
    delivery.store.path.write_text("{")
    recipient = user()
    await scheduler.send_user_reminder(recipient, event(), timedelta(hours=1))
    recipient.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_ack_restores_exact_message_after_projection_loss_and_empty_cache(
    isolated, monkeypatch
):
    occurrence = event()
    eid = scheduler.make_event_id(occurrence)
    msg = SimpleNamespace(id=81, channel=SimpleNamespace(id=91), edit=AsyncMock())
    channel = SimpleNamespace(
        send=AsyncMock(return_value=msg), fetch_message=AsyncMock(return_value=msg)
    )
    bot = SimpleNamespace(
        get_channel=lambda _: channel,
        fetch_channel=AsyncMock(return_value=channel),
        add_view=Mock(),
    )
    monkeypatch.setattr(
        scheduler, "save_active_reminders", lambda: (_ for _ in ()).throw(OSError("disk full"))
    )
    await scheduler.send_reminder_at(bot, 91, occurrence, timedelta(hours=1))
    assert delivery.store.rows()[0]["state"] == "acknowledged"
    scheduler.active_reminders.clear()
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [])
    assert await scheduler.load_active_reminders(bot) == {eid}
    assert scheduler.active_reminders[eid] is msg
    channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_dm_cancelled_save_drains_snapshot_before_next_writer(isolated, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = scheduler.atomic_write_json

    def write(path, data, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(path, data, **kwargs)

    monkeypatch.setattr(scheduler, "atomic_write_json", write)
    scheduler.dm_scheduled_tracker["event"] = {"17": {3600}}
    task = asyncio.create_task(scheduler.save_dm_scheduled_tracker_async())
    assert await asyncio.to_thread(entered.wait, 5)
    scheduler.dm_scheduled_tracker["event"]["18"] = {3600}
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert json.loads((isolated / "scheduled.json").read_text()) == {"event": {"17": [3600]}}
    await scheduler.save_dm_scheduled_tracker_async()
    assert json.loads((isolated / "scheduled.json").read_text())["event"]["18"] == [3600]


@pytest.mark.asyncio
async def test_overview_real_projections_create_and_remove_together(isolated, monkeypatch):
    import daily_KVK_overview_embed as overview
    from services.tracked_view_store import TrackedViewStore

    daily_path, view_path = isolated / "daily.json", isolated / "views.json"
    store = TrackedViewStore(view_path, str(isolated / "views.lock"))
    monkeypatch.setattr(overview, "DAILY_KVK_OVERVIEW_TRACKER", str(daily_path))
    monkeypatch.setattr(overview, "_tracker_store", lambda: store)
    monkeypatch.setattr(overview, "is_currently_kvk", lambda: True)
    monkeypatch.setattr(overview, "get_all_upcoming_events", lambda: [event()])
    msg = SimpleNamespace(id=81, pin=AsyncMock(), edit=AsyncMock(), delete=AsyncMock())
    channel = SimpleNamespace(
        id=91, send=AsyncMock(return_value=msg), fetch_message=AsyncMock(return_value=msg)
    )
    bot = SimpleNamespace(fetch_channel=AsyncMock(return_value=channel))
    assert await overview.post_or_update_daily_KVK_overview(bot, 91) == "created"
    assert json.loads(daily_path.read_text()) == {"message_id": 81}
    assert (await store.snapshot())["daily_kvk_overview"]["message_id"] == 81
    monkeypatch.setattr(overview, "is_currently_kvk", lambda: False)
    assert await overview.post_or_update_daily_KVK_overview(bot, 91) == "removed"
    assert json.loads(daily_path.read_text()) == {}
    assert await store.snapshot() == {}
    channel.send.assert_awaited_once()
    msg.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_passive_report_does_not_read_or_replay(isolated, monkeypatch):
    def forbidden():
        pytest.fail("passive report performed I/O")

    monkeypatch.setattr(delivery.store, "rows", forbidden)
    report = delivery.report()
    assert "Not visual or end-to-end acceptance" in report["verification"]


@pytest.mark.asyncio
async def test_public_second_restart_registers_handler_without_second_edit(isolated, monkeypatch):
    occurrence = event()
    eid = scheduler.make_event_id(occurrence)
    key = delivery_key("public-send", 91, eid, 3600)
    delivery.store.begin(key, kind="public-send", target=91, event=eid, window=3600)
    delivery.store.finish(key, "acknowledged", message_id=81, channel_id=91)
    msg = SimpleNamespace(id=81, channel=SimpleNamespace(id=91), edit=AsyncMock())
    channel = SimpleNamespace(fetch_message=AsyncMock(return_value=msg))
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [occurrence])
    for _ in range(2):
        scheduler.active_reminders.clear()
        bot = SimpleNamespace(fetch_channel=AsyncMock(return_value=channel), add_view=Mock())
        await scheduler.load_active_reminders(bot)
        bot.add_view.assert_called_once()
        assert bot.add_view.call_args.kwargs == {"message_id": 81}
        assert bot.add_view.call_args.args[0].is_persistent()
    msg.edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_unsubscribe_releases_only_unowned_undispatched_windows(isolated, monkeypatch):
    from player_self_service import reminder_service
    import reminder_task_registry as registry

    occurrence = event()
    eid = scheduler.make_event_id(occurrence)
    scheduler.dm_scheduled_tracker[eid] = {"17": {3600, 1800, 600, 300, 60}}
    scheduler.dm_sent_tracker[eid] = {"17": [60]}
    for window, state in [(1800, "entered"), (600, "acknowledged")]:
        key = delivery_key("dm-send", "17", eid, window)
        delivery.store.begin(key, kind="dm-send", target=17, event=eid, window=window)
        if state == "acknowledged":
            delivery.store.finish(key, state, message_id=81, channel_id=91)
    sleeper = asyncio.create_task(asyncio.Event().wait())
    registry.register_user_task(17, sleeper, meta={"event_id": eid, "delta_seconds": 3600})
    # A still-active owner must remain retained even after cancellation observation.
    original_snapshot = registry.user_task_snapshot
    monkeypatch.setattr(
        registry,
        "user_task_snapshot",
        lambda uid: {**original_snapshot(uid), "17": [{"event_id": eid, "delta_seconds": 300}]},
    )
    await reminder_service._cancel_user_tasks_for_unsubscribe(17)
    assert sleeper.done()
    assert scheduler.dm_scheduled_tracker[eid]["17"] == {1800, 600, 300, 60}
    recipient = user()
    # A resubscription can now schedule/send the cancelled unsent window in this process.
    scheduler.dm_scheduled_tracker[eid]["17"].add(3600)
    await scheduler.send_user_reminder(recipient, occurrence, timedelta(hours=1))
    recipient.send.assert_awaited_once()
    assert 3600 in scheduler.dm_sent_tracker[eid]["17"]


@pytest.mark.asyncio
async def test_public_settlement_cancellation_recovers_identity_before_next_window(
    isolated, monkeypatch
):
    occurrence = event()
    eid = scheduler.make_event_id(occurrence)
    old = SimpleNamespace(id=81, channel=SimpleNamespace(id=91), delete=AsyncMock())
    new = SimpleNamespace(id=82, channel=SimpleNamespace(id=91))
    channel = SimpleNamespace(
        send=AsyncMock(side_effect=[old, new]), fetch_message=AsyncMock(return_value=old)
    )
    bot = SimpleNamespace(get_channel=lambda _: channel)
    original_finish = delivery.store.finish
    entered, release = threading.Event(), threading.Event()

    def finish(key, state, **kwargs):
        result = original_finish(key, state, **kwargs)
        if kwargs.get("message_id") == 81 and delivery.store.get(key)["kind"] == "public-send":
            entered.set()
            assert release.wait(5)
        return result

    monkeypatch.setattr(delivery.store, "finish", finish)
    first = asyncio.create_task(scheduler.send_reminder_at(bot, 91, occurrence, timedelta(hours=1)))
    assert await asyncio.to_thread(entered.wait, 5)
    first.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert eid not in scheduler.active_reminders
    monkeypatch.setattr(
        scheduler, "utcnow", lambda: occurrence["start_time"] - timedelta(minutes=30)
    )
    assert (
        await scheduler.send_reminder_at(bot, 91, occurrence, timedelta(minutes=30))
        == "acknowledged"
    )
    channel.fetch_message.assert_awaited_once_with(81)
    old.delete.assert_awaited_once()
    assert scheduler.active_reminders[eid].id == 82


@pytest.mark.asyncio
@pytest.mark.parametrize("removal", [False, True])
async def test_overview_read_failure_before_dispatch_is_retryable(isolated, monkeypatch, removal):
    import daily_KVK_overview_embed as overview

    adapter = overview._OverviewAdapter(
        SimpleNamespace(fetch_channel=AsyncMock(side_effect=OSError())), 91, [event()]
    )
    adapter.identity = AsyncMock(return_value=81 if removal else None)
    adapter.save_projection = AsyncMock()
    adapter.remove_projection = AsyncMock()
    with pytest.raises(OSError):
        await publish(adapter, 91, enabled=not removal, has_events=True, revision="r1")
    assert delivery.store.rows() == []
    msg = SimpleNamespace(id=81, pin=AsyncMock(), delete=AsyncMock())
    channel = SimpleNamespace(
        send=AsyncMock(return_value=msg), fetch_message=AsyncMock(return_value=msg)
    )
    adapter.bot.fetch_channel = AsyncMock(return_value=channel)
    assert await publish(adapter, 91, enabled=not removal, has_events=True, revision="r1") == (
        "removed" if removal else "created"
    )


@pytest.mark.asyncio
async def test_overview_generation_survives_clock_rollback_and_projection_loss(
    isolated, monkeypatch
):
    from services import event_delivery_store as journal

    for generation, message_id, stamp in [(0, 81, 200), (1, 82, 100)]:
        monkeypatch.setattr(journal.time, "time", lambda: stamp)
        key = delivery_key("overview-send", 91, generation)
        delivery.store.begin(key, kind="overview-send", target=91, generation=generation)
        delivery.store.finish(key, "acknowledged", message_id=message_id, channel_id=91)
    key = delivery_key("overview-delete", 91, 81)
    delivery.store.begin(key, kind="overview-delete", target=91, message_id=81)
    delivery.store.finish(key, "acknowledged", message_id=81, channel_id=91)
    adapter = overview_adapter()
    adapter.edit.return_value = adapter.pin.return_value = 82
    assert await publish(adapter, 91, enabled=True, has_events=True, revision="r2") == "updated"
    adapter.send.assert_not_awaited()
    adapter.fetch.assert_awaited_once_with(82)
    adapter.save_projection.assert_awaited_once_with(82)


def test_journal_capacity_reserves_actual_serialized_settlement_bytes(isolated, monkeypatch):
    from services import event_delivery_store as journal

    monkeypatch.setattr(journal, "MAX_JOURNAL_BYTES", 1600)
    accepted = []
    for index in range(20):
        key = str(index)
        try:
            delivery.store.begin(key, kind="dm-send", target=17, event="é" * 20, window=3600)
            accepted.append(key)
        except journal.DeliveryHeld:
            break
    assert 0 < len(accepted) < 20
    for key in accepted:
        delivery.store.finish(key, "acknowledged", message_id=2**64 - 1, channel_id=2**64 - 1)
        assert delivery.store.path.stat().st_size <= 1600
    assert all(row["state"] == "acknowledged" for row in delivery.store.rows())


@pytest.mark.asyncio
async def test_cleanup_does_not_report_held_deletion_as_removed(isolated, monkeypatch, caplog):
    caplog.set_level("INFO", logger="event_scheduler")
    occurrence = event()
    occurrence["start_time"] = datetime.now(UTC) - timedelta(hours=1)
    scheduler.active_reminders[scheduler.make_event_id(occurrence)] = object()
    monkeypatch.setattr(scheduler, "safe_delete_reminder", AsyncMock(return_value="unconfirmed"))
    monkeypatch.setattr(scheduler.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await scheduler.reminder_cleanup_loop()
    assert "Cleanup loop removed" not in caplog.text


@pytest.mark.asyncio
async def test_health_shutdown_keeps_reference_when_observer_clears_task():
    from services.gsheets_health_service import HealthProbe

    probe = HealthProbe()
    started, release = asyncio.Event(), asyncio.Event()

    async def run():
        started.set()
        await release.wait()
        return True, "healthy"

    observer = asyncio.create_task(probe.observe(run, timeout=5))
    await started.wait()
    shutdown = asyncio.create_task(probe.shutdown())
    await asyncio.sleep(0)
    release.set()
    assert await observer == (True, "healthy")
    await shutdown
    assert probe._task is None


@pytest.mark.asyncio
async def test_conflicting_public_projection_survives_save_and_restart(isolated, monkeypatch):
    occurrence = event()
    eid = scheduler.make_event_id(occurrence)
    original = {eid: {"message_id": 80, "channel_id": 91}}
    (isolated / "active.json").write_text(json.dumps(original))
    key = delivery_key("public-send", 91, eid, 3600)
    delivery.store.begin(key, kind="public-send", target=91, event=eid, window=3600)
    delivery.store.finish(key, "acknowledged", message_id=81, channel_id=91)
    bot = SimpleNamespace(fetch_channel=AsyncMock(), add_view=Mock())
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [occurrence])
    await scheduler.load_active_reminders(bot)
    scheduler.save_active_reminders()
    assert json.loads((isolated / "active.json").read_text()) == original
    scheduler._unresolved_active.clear()
    await scheduler.load_active_reminders(bot)
    assert scheduler._unresolved_active[eid]["message_id"] == 80
    bot.fetch_channel.assert_not_awaited()
