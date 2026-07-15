# tests/test_event_cache.py
import asyncio
from datetime import UTC, datetime, timedelta
import logging

import event_cache as ec
import event_data_loader as edl


def _make_event(offset_minutes=10):
    now = datetime.now(UTC).replace(microsecond=0)
    return {
        "name": "Existing",
        "type": "ruins",
        "start_time": now + timedelta(minutes=offset_minutes),
        "end_time": now + timedelta(minutes=offset_minutes + 15),
    }


def test_refresh_preserves_cache_on_empty(monkeypatch):
    """
    If loaders return empty lists but we already have an in-memory cache refreshed recently,
    refresh_event_cache should preserve the existing cache and not call save_event_cache.
    """
    # Pre-populate in-memory cache with one event and a recent last_refreshed
    with ec._CACHE_LOCK:
        ec.event_cache[:] = [_make_event()]
        ec.last_refreshed = datetime.now(UTC)

    # Patch loaders to return empty lists (successful but empty) — accept timeout kwarg
    monkeypatch.setattr(
        edl, "load_upcoming_ruins_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )
    monkeypatch.setattr(
        edl, "load_upcoming_altar_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )
    monkeypatch.setattr(
        edl, "load_upcoming_major_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )
    monkeypatch.setattr(
        edl, "load_upcoming_chronicle_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )

    # Capture save_event_cache calls
    saved = {"called": False}

    def fake_save():
        saved["called"] = True

    monkeypatch.setattr(ec, "save_event_cache", fake_save)

    # Run the refresh
    new_count = asyncio.run(ec.refresh_event_cache())

    # Expect preserve: cache remains unchanged, save_event_cache not called
    assert new_count == 1
    assert saved["called"] is False


def test_refresh_overwrites_cache_if_stale_and_empty(monkeypatch):
    """
    If loaders return empty lists and the previous cache is stale (older than threshold),
    allow overwrite (i.e., set cache to empty and call save_event_cache).
    """
    # Pre-populate in-memory cache and mark last_refreshed as stale
    stale = datetime.now(UTC) - timedelta(seconds=(ec.PRESERVE_EVENT_CACHE_ON_EMPTY_SECONDS + 10))
    with ec._CACHE_LOCK:
        ec.event_cache[:] = [_make_event()]
        ec.last_refreshed = stale

    # Patch loaders to return empty lists (successful but empty) — accept timeout kwarg
    monkeypatch.setattr(
        edl, "load_upcoming_ruins_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )
    monkeypatch.setattr(
        edl, "load_upcoming_altar_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )
    monkeypatch.setattr(
        edl, "load_upcoming_major_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )
    monkeypatch.setattr(
        edl, "load_upcoming_chronicle_events", lambda timeout=None: asyncio.sleep(0, result=[])
    )

    # Capture save_event_cache calls
    saved = {"called": False}

    def fake_save():
        saved["called"] = True

    monkeypatch.setattr(ec, "save_event_cache", fake_save)

    # Run the refresh
    new_count = asyncio.run(ec.refresh_event_cache())

    # Expect overwrite: cache becomes empty, save_event_cache called
    assert new_count == 0
    assert saved["called"] is True
    assert len(ec.event_cache) == 0


def test_refresh_event_cache_times_out(monkeypatch, caplog):
    """
    Simulate a loader that ignores its timeout and sleeps for longer than GSHEETS_CALL_TIMEOUT.
    Confirm that refresh_event_cache completes (bounded) and logs a timeout message.
    """
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(ec, "GSHEETS_CALL_TIMEOUT", 0.02)
    monkeypatch.setattr(ec, "EVENT_CACHE_MIN_REFRESH_TIMEOUT", 0.05)

    async def long_loader(timeout=None):
        # Sleep longer than per-loader timeout
        await asyncio.sleep(1)
        return []

    async def quick_loader(timeout=None):
        return []

    # Patch the loaders on event_data_loader module to our long/quick variants
    monkeypatch.setattr(
        edl, "load_upcoming_ruins_events", lambda timeout=None: long_loader(timeout)
    )
    monkeypatch.setattr(
        edl, "load_upcoming_altar_events", lambda timeout=None: quick_loader(timeout)
    )
    monkeypatch.setattr(
        edl, "load_upcoming_major_events", lambda timeout=None: quick_loader(timeout)
    )
    monkeypatch.setattr(
        edl, "load_upcoming_chronicle_events", lambda timeout=None: quick_loader(timeout)
    )

    # Run refresh_event_cache (should be bounded and return quickly)
    res = asyncio.run(ec.refresh_event_cache())

    # It should return an int (number of events) and not hang
    assert isinstance(res, int)

    # Log should include timeout or timed out message
    txt = caplog.text.lower()
    assert "timed out" in txt or "timeout" in txt or "timedout" in txt


def test_projection_snapshot_distinguishes_healthy_empty_from_never_loaded(monkeypatch):
    now = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(ec, "event_cache", [])
    monkeypatch.setattr(ec, "last_refreshed", None)

    unavailable = ec.get_upcoming_event_cache_snapshot(now_utc=now)
    monkeypatch.setattr(ec, "last_refreshed", now)
    healthy_empty = ec.get_upcoming_event_cache_snapshot(now_utc=now)

    assert unavailable.ok is False
    assert unavailable.error == "cache_unavailable"
    assert healthy_empty.ok is True
    assert healthy_empty.events == ()


def test_projection_snapshot_keeps_stale_cache_usable_like_live_dispatch(monkeypatch):
    now = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
    event = {
        "name": "Ancient Ruins",
        "type": "ruins",
        "start_time": now + timedelta(hours=2),
    }
    monkeypatch.setattr(ec, "event_cache", [event])
    monkeypatch.setattr(ec, "last_refreshed", now - timedelta(hours=13))

    snapshot = ec.get_upcoming_event_cache_snapshot(now_utc=now)

    assert snapshot.ok is True
    assert snapshot.stale is True
    assert snapshot.events == (event,)
    assert snapshot.events[0] is not event
