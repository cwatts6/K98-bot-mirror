# tests/test_usage_tracker.py
"""
Unit tests for usage_tracker.py — AsyncUsageTracker lifecycle and helpers.
No live database or SQL is required.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from usage_tracker import AsyncUsageTracker, start_usage_tracker
from telemetry.dal.command_usage_dal import _coerce_ts


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


def test_tracker_not_started_before_start_called():
    """A freshly constructed tracker must not have a running task."""
    tracker = AsyncUsageTracker()
    assert tracker._task is None


def test_start_usage_tracker_creates_task():
    """start_usage_tracker() returns a tracker with a running task."""

    async def _inner():
        tracker = start_usage_tracker()
        try:
            assert tracker._task is not None
        finally:
            # Cancel the background task so the test loop can exit cleanly
            tracker._task.cancel()
            try:
                await tracker._task
            except (asyncio.CancelledError, Exception):
                pass
            tracker._task = None

    asyncio.run(_inner())


# ---------------------------------------------------------------------------
# log() tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_enqueues_event():
    """Calling log() on a non-started tracker enqueues the event."""
    tracker = AsyncUsageTracker()
    await tracker.log({"command_name": "test", "executed_at_utc": "2026-04-21T00:00:00Z"})
    assert tracker.queue.qsize() == 1


@pytest.mark.asyncio
async def test_log_queue_full_drops_and_logs_warning():
    """When the queue is full, log() swallows QueueFull without raising."""
    tracker = AsyncUsageTracker(queue_max=1)
    # Fill the queue
    await tracker.log({"command_name": "first", "executed_at_utc": "2026-04-21T00:00:00Z"})
    assert tracker.queue.qsize() == 1
    # Second log call must not raise even though queue is full
    await tracker.log({"command_name": "second", "executed_at_utc": "2026-04-21T00:00:00Z"})
    # Queue size stays at 1 (second event was dropped)
    assert tracker.queue.qsize() == 1


# ---------------------------------------------------------------------------
# _coerce_ts tests (now lives in command_usage_dal)
# ---------------------------------------------------------------------------


def test_coerce_ts_string_iso():
    """ISO string with UTC offset produces a naive datetime."""
    result = _coerce_ts("2026-04-21T12:00:00+00:00")
    assert isinstance(result, datetime)
    assert result.tzinfo is None


def test_coerce_ts_aware_datetime():
    """Timezone-aware datetime is coerced to a naive UTC datetime."""
    aware_dt = datetime(2026, 4, 21, 12, 0, 0, tzinfo=timezone.utc)
    result = _coerce_ts(aware_dt)
    assert isinstance(result, datetime)
    assert result.tzinfo is None


def test_coerce_ts_passthrough_on_bad_input():
    """Non-parseable string must not raise and must be returned as-is."""
    result = _coerce_ts("not-a-date")
    assert result == "not-a-date"
