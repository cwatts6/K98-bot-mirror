from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
import pytest

import event_scheduler as scheduler
import file_utils

NOW = datetime(2026, 9, 7, 12, tzinfo=UTC)


def event(**overrides):
    result = {
        "name": "Été 🐉",
        "type": "major",
        "start_time": NOW,
        "end_time": NOW + timedelta(hours=2),
    }
    result.update(overrides)
    return result


def message(message_id=101, channel_id=42):
    return SimpleNamespace(
        id=message_id,
        channel=SimpleNamespace(id=channel_id),
        delete=AsyncMock(),
        edit=AsyncMock(),
    )


def bot_for(msg):
    channel = SimpleNamespace(fetch_message=AsyncMock(return_value=msg))
    return SimpleNamespace(fetch_channel=AsyncMock(return_value=channel))


@pytest.fixture(autouse=True)
def isolated_tracker(monkeypatch, tmp_path):
    target = tmp_path / "active_reminders.json"
    monkeypatch.setattr(scheduler, "REMINDER_TRACKING_FILE", str(target))
    monkeypatch.setattr(scheduler, "active_reminders", {})
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [])
    monkeypatch.setattr(scheduler, "utcnow", lambda: NOW)
    return target


def test_save_preserves_path_payload_and_legacy_bytes(monkeypatch, isolated_tracker, caplog):
    start = NOW.astimezone(timezone(timedelta(hours=2)))
    live = event(start_time=start, extra={"z": "龍", "a": "line\nnext"})
    eid = scheduler.make_event_id(live)
    msg = message()
    scheduler.active_reminders.update({eid: msg, "legacy-id": message(102)})
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    writer = Mock(wraps=file_utils.atomic_json_write)
    monkeypatch.setattr(scheduler, "atomic_json_write", writer)
    caplog.set_level("DEBUG", logger=scheduler.__name__)

    scheduler.save_active_reminders()

    expected = {
        eid: {
            "channel_id": 42,
            "message_id": 101,
            "event": {
                **live,
                "start_time": NOW.isoformat(),
                "end_time": live["end_time"].isoformat(),
            },
        },
        "legacy-id": {"channel_id": 42, "message_id": 102},
    }
    writer.assert_called_once_with(
        str(isolated_tracker), expected, ensure_ascii=True, sort_keys=True, default=None
    )
    legacy = isolated_tracker.with_name("legacy.json")
    with legacy.open("w", encoding="utf-8") as stream:
        json.dump(expected, stream, indent=2, sort_keys=True)
    assert isolated_tracker.read_bytes() == legacy.read_bytes()
    assert json.loads(isolated_tracker.read_text()) == expected
    assert scheduler.active_reminders[eid] is msg
    assert "No event found for legacy-id — saving basic info only." in caplog.text
    assert "[REMINDER_CACHE] Saved active reminders to disk." in caplog.text


@pytest.mark.parametrize("failure", ["serialization", "replace"])
def test_save_failure_is_nonraising_and_preserves_old_file(
    monkeypatch, isolated_tracker, caplog, failure
):
    old = b'{"old": {"channel_id": 42, "message_id": 7}}'
    isolated_tracker.write_bytes(old)
    live = event(extra=object()) if failure == "serialization" else event()
    eid = scheduler.make_event_id(live)
    msg = message()
    scheduler.active_reminders[eid] = msg
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    if failure == "replace":
        attempts = []

        def fail_replace(*args):
            attempts.append(args)
            exc = PermissionError("sharing violation")
            exc.winerror = 32
            raise exc

        monkeypatch.setattr(file_utils.os, "replace", fail_replace)
        monkeypatch.setattr(file_utils.time, "sleep", lambda _: None)

    assert scheduler.save_active_reminders() is None
    assert isolated_tracker.read_bytes() == old
    assert scheduler.active_reminders[eid] is msg
    assert not list(isolated_tracker.parent.glob("*.tmp"))
    assert "[REMINDER_CACHE] Failed to save:" in caplog.text
    assert "Saved active reminders to disk" not in caplog.text
    if failure == "replace":
        assert len(attempts) == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("contents", [None, "{broken", "[]", "null", "{}"])
async def test_missing_or_invalid_root_keeps_existing_memory(isolated_tracker, contents):
    if contents is not None:
        isolated_tracker.write_text(contents, encoding="utf-8")
    existing = message()
    scheduler.active_reminders["existing"] = existing
    bot = bot_for(message())
    assert await scheduler.load_active_reminders(bot) == set()
    assert scheduler.active_reminders == {"existing": existing}
    bot.fetch_channel.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["live", "stored"])
@pytest.mark.parametrize("edit_fails", [False, True])
async def test_load_restores_identity_and_live_or_stored_event(
    monkeypatch, isolated_tracker, source, edit_fails
):
    live = event(type="major event")
    eid = scheduler.make_event_id(live)
    stored = {
        **live,
        "name": "Stored name",
        "start_time": "2026-09-07T14:00:00+02:00",
        "end_time": "2026-09-07T16:00:00+02:00",
    }
    if source == "live":
        stored["start_time"] = "invalid but ignored when live data exists"
        monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    isolated_tracker.write_text(
        json.dumps({eid: {"channel_id": 42, "message_id": 101, "event": stored}}),
        encoding="utf-8",
    )
    msg = message()
    if edit_fails:
        msg.edit.side_effect = RuntimeError("edit unavailable")
    bot = bot_for(msg)

    assert await scheduler.load_active_reminders(bot) == {eid}
    assert scheduler.active_reminders == {eid: msg}
    bot.fetch_channel.assert_awaited_once_with(42)
    bot.fetch_channel.return_value.fetch_message.assert_awaited_once_with(101)
    view = msg.edit.call_args.kwargs["view"]
    assert view.prefix == "reminder_major_event"
    assert view.complete_event_packing is True
    assert view.children[0].custom_id == "reminder_major_event_abcae1dd_local_time_toggle"
    assert view.events[0]["start_time"] == NOW
    assert view.events[0]["end_time"] == NOW + timedelta(hours=2)
    assert view.events[0]["name"] == (live["name"] if source == "live" else "Stored name")


@pytest.mark.asyncio
async def test_invalid_entries_return_raw_ids_without_restoration(isolated_tracker):
    raw = {
        "not-dict": [],
        "incomplete": {"message_id": 101},
        "basic-only": {"channel_id": 42, "message_id": 101},
        "bad-fallback": {"channel_id": 42, "message_id": 101, "event": {"start_time": "bad"}},
    }
    isolated_tracker.write_text(json.dumps(raw), encoding="utf-8")
    msg = message()
    assert await scheduler.load_active_reminders(bot_for(msg)) == set(raw)
    assert scheduler.active_reminders == {}
    msg.edit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["channel", "message"])
@pytest.mark.parametrize("not_found", [False, True])
async def test_fetch_failure_preserves_raw_ids(monkeypatch, isolated_tracker, boundary, not_found):
    live = event()
    eid = scheduler.make_event_id(live)
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    isolated_tracker.write_text(
        json.dumps({eid: {"channel_id": 42, "message_id": 101}}), encoding="utf-8"
    )
    bot = bot_for(message())
    fetch = (
        bot.fetch_channel if boundary == "channel" else bot.fetch_channel.return_value.fetch_message
    )
    fetch.side_effect = (
        discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "missing")
        if not_found
        else RuntimeError("unavailable")
    )
    assert await scheduler.load_active_reminders(bot) == {eid}
    assert scheduler.active_reminders == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["deleted", "missing", "error", "cancelled"])
async def test_delete_finally_persists_removal(isolated_tracker, outcome):
    msg = message()
    scheduler.active_reminders["old"] = msg
    scheduler.active_reminders["keep"] = message(102)
    if outcome == "missing":
        msg.delete.side_effect = discord.NotFound(
            SimpleNamespace(status=404, reason="Not Found"), "missing"
        )
    elif outcome == "error":
        msg.delete.side_effect = RuntimeError("delete failed")
    elif outcome == "cancelled":
        msg.delete.side_effect = asyncio.CancelledError()

    if outcome == "cancelled":
        with pytest.raises(asyncio.CancelledError):
            await scheduler.safe_delete_reminder("old")
    else:
        await scheduler.safe_delete_reminder("old")

    assert set(scheduler.active_reminders) == {"keep"}
    assert json.loads(isolated_tracker.read_text()) == {
        "keep": {"channel_id": 42, "message_id": 102}
    }


@pytest.mark.asyncio
async def test_orphan_cleanup_uses_raw_ids_and_skips_empty_cache(monkeypatch, isolated_tracker):
    live = event()
    eid = scheduler.make_event_id(live)
    msg = message()
    raw = {
        eid: {"channel_id": 42, "message_id": 101},
        "broken-orphan": [],
        "unrestored-orphan": {"channel_id": 42, "message_id": 102},
    }
    isolated_tracker.write_text(json.dumps(raw), encoding="utf-8")
    previous = isolated_tracker.read_bytes()
    await scheduler.cleanup_orphaned_reminders(set(raw))
    assert isolated_tracker.read_bytes() == previous

    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    loaded = await scheduler.load_active_reminders(bot_for(msg))
    await scheduler.cleanup_orphaned_reminders(loaded)
    assert set(json.loads(isolated_tracker.read_text())) == {eid}
    assert scheduler.active_reminders == {eid: msg}
    msg.delete.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("hours", [24, 12, 4, 1, 0])
@pytest.mark.parametrize("delete_fails", [False, True])
async def test_public_send_preserves_order_mentions_and_saved_identity(
    monkeypatch, isolated_tracker, hours, delete_fails
):
    live = event(start_time=NOW + timedelta(hours=hours))
    live.pop("end_time")  # Expiry is exercised separately without background tasks.
    eid = scheduler.make_event_id(live)
    previous, new = message(100), message(101)
    scheduler.active_reminders[eid] = previous
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    calls = []

    async def delete():
        calls.append("delete")
        if delete_fails:
            raise RuntimeError("delete failed")

    async def send(**kwargs):
        calls.append("send")
        assert scheduler.active_reminders[eid] is previous
        assert not isolated_tracker.exists()
        assert kwargs["content"] == ("@everyone" if hours in (0, 1) else None)
        assert set(kwargs) == {"content", "embed", "view"}
        assert kwargs["view"].prefix == "reminder_major"
        assert kwargs["view"].complete_event_packing is True
        return new

    original_save = scheduler.save_active_reminders

    def save():
        calls.append("save")
        assert scheduler.active_reminders[eid] is new
        original_save()

    previous.delete.side_effect = delete
    monkeypatch.setattr(scheduler, "save_active_reminders", save)
    channel = SimpleNamespace(send=AsyncMock(side_effect=send))
    bot = SimpleNamespace(get_channel=Mock(return_value=channel))
    await scheduler.send_reminder_at(bot, 42, live, timedelta(hours=hours))
    assert calls == ["delete", "send", "save"]
    assert json.loads(isolated_tracker.read_text())[eid]["message_id"] == 101


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["channel", "send", "save", "false-t0"])
async def test_public_send_failure_keeps_existing_contract(
    monkeypatch, isolated_tracker, failure, caplog
):
    live = event(start_time=NOW - timedelta(minutes=2) if failure == "false-t0" else NOW)
    live.pop("end_time")
    eid = scheduler.make_event_id(live)
    previous, new = message(100), message(101)
    scheduler.active_reminders[eid] = previous
    scheduler.save_active_reminders()
    old_bytes = isolated_tracker.read_bytes()
    channel = SimpleNamespace(send=AsyncMock(return_value=new))
    if failure == "send":
        channel.send.side_effect = RuntimeError("send failed")
    if failure == "save":
        monkeypatch.setattr(scheduler, "atomic_json_write", Mock(side_effect=OSError("disk full")))
    bot = SimpleNamespace(get_channel=Mock(return_value=None if failure == "channel" else channel))
    await scheduler.send_reminder_at(bot, 42, live, timedelta(0))
    assert isolated_tracker.read_bytes() == old_bytes
    assert scheduler.active_reminders[eid] is (new if failure == "save" else previous)
    if failure == "false-t0":
        previous.delete.assert_not_awaited()
        channel.send.assert_not_awaited()
    else:
        previous.delete.assert_awaited_once()
    if failure == "save":
        assert "[REMINDER_CACHE] Failed to save: disk full" in caplog.text
        channel.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_coroutine_saves_keep_accumulated_state(monkeypatch, isolated_tracker):
    async def publish(index):
        await asyncio.sleep(0)
        scheduler.active_reminders[str(index)] = message(index)
        scheduler.save_active_reminders()

    await asyncio.gather(*(publish(i) for i in range(8)))
    persisted = json.loads(isolated_tracker.read_text())
    assert {key: value["message_id"] for key, value in persisted.items()} == {
        str(i): i for i in range(8)
    }
    assert not list(isolated_tracker.parent.glob("*.tmp"))


@pytest.mark.asyncio
async def test_saved_tracker_rehydrates_after_memory_reset(monkeypatch, isolated_tracker):
    live = event()
    eid = scheduler.make_event_id(live)
    scheduler.active_reminders[eid] = message()
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    scheduler.save_active_reminders()
    before = isolated_tracker.read_bytes()
    monkeypatch.setattr(scheduler, "active_reminders", {})
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [])
    restored = message()

    assert await scheduler.load_active_reminders(bot_for(restored)) == {eid}
    assert scheduler.active_reminders[eid] is restored
    assert restored.edit.call_args.kwargs["view"].events == [live]
    assert isolated_tracker.read_bytes() == before


@pytest.mark.asyncio
async def test_t0_expiry_preserves_end_time_delay_and_persists_deletion(
    monkeypatch, isolated_tracker
):
    live = event()
    eid = scheduler.make_event_id(live)
    msg = message()
    channel = SimpleNamespace(send=AsyncMock(return_value=msg))
    bot = SimpleNamespace(get_channel=Mock(return_value=channel))
    pending = []
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    monkeypatch.setattr(scheduler.asyncio, "create_task", pending.append)
    sleep = AsyncMock()
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep)

    await scheduler.send_reminder_at(bot, 42, live, timedelta(0))
    assert len(pending) == 1
    try:
        assert scheduler.active_reminders[eid] is msg
        assert json.loads(isolated_tracker.read_text())[eid]["message_id"] == msg.id
    finally:
        await pending[0]
    sleep.assert_awaited_once_with(3 * 3600)
    msg.delete.assert_awaited_once()
    assert scheduler.active_reminders == {}
    assert json.loads(isolated_tracker.read_text()) == {}


@pytest.mark.asyncio
async def test_cleanup_loop_keeps_threshold_cadence_and_invalid_ids(monkeypatch, isolated_tracker):
    old = scheduler.make_event_id(event(start_time=NOW - timedelta(minutes=16)))
    boundary = scheduler.make_event_id(event(start_time=NOW - timedelta(minutes=15)))
    expired, retained, malformed = message(100), message(101), message(102)
    scheduler.active_reminders.update({old: expired, boundary: retained, "bad-id": malformed})
    sleep = AsyncMock(side_effect=asyncio.CancelledError())
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler.reminder_cleanup_loop()

    sleep.assert_awaited_once_with(600)
    expired.delete.assert_awaited_once()
    retained.delete.assert_not_awaited()
    malformed.delete.assert_not_awaited()
    assert set(scheduler.active_reminders) == {boundary, "bad-id"}
    assert set(json.loads(isolated_tracker.read_text())) == {boundary, "bad-id"}


@pytest.mark.asyncio
async def test_refresh_keeps_message_view_and_tracker(monkeypatch, isolated_tracker):
    live = event()
    eid = scheduler.make_event_id(live)
    msg = message()
    scheduler.active_reminders[eid] = msg
    monkeypatch.setattr(scheduler, "get_all_upcoming_events", lambda: [live])
    scheduler.save_active_reminders()
    before = isolated_tracker.read_bytes()

    await scheduler.refresh_reminder_format(object(), 42)

    msg.edit.assert_awaited_once()
    assert set(msg.edit.call_args.kwargs) == {"embed"}
    assert scheduler.active_reminders[eid] is msg
    assert isolated_tracker.read_bytes() == before


def test_hard_exit_before_replace_preserves_target_and_ignores_stale_temp(isolated_tracker):
    previous = b'{"old": {"channel_id": 42, "message_id": 7}}'
    isolated_tracker.write_bytes(previous)
    script = (
        "import os, sys, file_utils\n"
        "file_utils.os.replace = lambda *args: os._exit(23)\n"
        "file_utils.atomic_json_write(sys.argv[1], {'new': True})\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(isolated_tracker)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 23, result.stderr.decode(errors="replace")
    assert isolated_tracker.read_bytes() == previous
    abandoned = list(isolated_tracker.parent.glob("*.tmp"))
    assert len(abandoned) == 1
    scheduler.active_reminders["current"] = message()
    scheduler.save_active_reminders()
    assert set(json.loads(isolated_tracker.read_text())) == {"current"}
    assert abandoned[0].exists()  # Never scavenge a temp owned by another invocation.
