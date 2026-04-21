# tests/test_usage_tracker_lifecycle.py
"""
Tests for AsyncUsageTracker lifecycle: start/stop idempotency, queue drain on stop,
and the global singleton helpers.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub heavy deps so we can import usage_tracker without a real DB / pyodbc
# ---------------------------------------------------------------------------
for _mod in ("pyodbc",):
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)


# Minimal stubs for constants and utils needed by usage_tracker
_constants_stub = types.ModuleType("constants")
_constants_stub.BASE_DIR = "/tmp"
_constants_stub.DATA_DIR = "/tmp/data"
_constants_stub._conn = MagicMock(side_effect=RuntimeError("no DB in tests"))
_constants_stub.USAGE_JSONL_RETENTION_DAYS = 30
_constants_stub.USAGE_METRICS_JSONL_RETENTION_DAYS = 30
_constants_stub.USAGE_ALERTS_JSONL_RETENTION_DAYS = 30
sys.modules["constants"] = _constants_stub

from datetime import UTC, datetime

_utils_stub = types.ModuleType("utils")
_utils_stub.ensure_aware_utc = lambda dt: dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt
_utils_stub.utcnow = lambda: datetime.now(UTC)
sys.modules["utils"] = _utils_stub

# Now import the module under test
import importlib

import usage_tracker as _ut

# Reload to pick up the stubs if already imported
importlib.reload(_ut)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tracker(**kwargs) -> _ut.AsyncUsageTracker:
    return _ut.AsyncUsageTracker(flush_interval_sec=1, batch_size=10, **kwargs)


def _dummy_event(name: str = "test_cmd") -> dict:
    return {
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "command_name": name,
        "version": None,
        "app_context": "slash",
        "user_id": 1,
        "user_display": "Test User",
        "guild_id": None,
        "channel_id": None,
        "success": True,
        "error_code": None,
        "latency_ms": 42,
        "args_shape": None,
        "error_text": None,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_creates_task():
    """start() should create a background task."""
    tracker = _make_tracker()
    assert tracker._task is None
    tracker.start()
    assert tracker._task is not None
    # clean up
    await tracker.stop()


@pytest.mark.asyncio
async def test_start_is_idempotent():
    """Calling start() a second time should be a no-op (same task object)."""
    tracker = _make_tracker()
    tracker.start()
    task_first = tracker._task
    tracker.start()  # second call — should be no-op
    assert tracker._task is task_first, "start() should not replace the existing task"
    await tracker.stop()


@pytest.mark.asyncio
async def test_stop_clears_task():
    """stop() should await the task and clear _task."""
    tracker = _make_tracker()
    tracker.start()
    assert tracker._task is not None
    await tracker.stop()
    assert tracker._task is None


@pytest.mark.asyncio
async def test_stop_without_start_is_safe():
    """stop() before start() should not raise."""
    tracker = _make_tracker()
    await tracker.stop()  # should not raise


@pytest.mark.asyncio
async def test_log_queues_event():
    """log() should enqueue the event even before the task is started."""
    tracker = _make_tracker()
    # Patch _flush so it does nothing (no DB)
    tracker._flush = AsyncMock()
    # Patch local JSONL write to avoid file I/O
    with patch("asyncio.create_task"):
        await tracker.log(_dummy_event())
    assert tracker.queue.qsize() == 1


@pytest.mark.asyncio
async def test_queue_full_drops_and_logs(caplog):
    """When the queue is full, the event is dropped and a warning is logged."""
    tracker = _ut.AsyncUsageTracker(queue_max=1)
    tracker._flush = AsyncMock()
    # Fill the queue
    with patch("asyncio.create_task"):
        await tracker.log(_dummy_event("cmd_a"))
        # Queue is now full; second event should be dropped with a warning
        await tracker.log(_dummy_event("cmd_b"))

    import logging

    assert any(
        "Queue full" in r.message or "dropping usage event" in r.message
        for r in caplog.records
        if r.levelno >= logging.WARNING
    ), "Expected a warning about a dropped event"


@pytest.mark.asyncio
async def test_final_drain_on_stop():
    """stop() should flush events that were queued before stop() was called."""
    tracker = _make_tracker()
    flushed: list[list] = []

    async def _capture_flush(events):
        flushed.extend(events)

    tracker._flush = _capture_flush
    tracker.start()

    # Queue events then immediately stop
    with patch("asyncio.create_task"):
        await tracker.log(_dummy_event("drain_a"))
        await tracker.log(_dummy_event("drain_b"))

    await tracker.stop()

    # Both events should have been flushed
    names = [e.get("command_name") for e in flushed]
    assert "drain_a" in names
    assert "drain_b" in names


# ---------------------------------------------------------------------------
# Global singleton helpers
# ---------------------------------------------------------------------------


def test_ensure_global_tracker_returns_same_instance():
    """_ensure_global_tracker() should always return the same object."""
    # Reset global state
    _ut._GLOBAL_TRACKER = None
    t1 = _ut._ensure_global_tracker()
    t2 = _ut._ensure_global_tracker()
    assert t1 is t2


def test_ensure_global_tracker_does_not_auto_start():
    """_ensure_global_tracker() must NOT start the tracker automatically."""
    _ut._GLOBAL_TRACKER = None
    tracker = _ut._ensure_global_tracker()
    assert tracker._task is None, "_ensure_global_tracker must not auto-start the tracker"


def test_get_usage_tracker_returns_global():
    """get_usage_tracker() should return the same singleton as _ensure_global_tracker."""
    _ut._GLOBAL_TRACKER = None
    t = _ut.get_usage_tracker()
    assert t is _ut._GLOBAL_TRACKER
