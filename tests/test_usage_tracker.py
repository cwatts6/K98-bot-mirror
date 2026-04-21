# tests/test_usage_tracker.py
"""
Unit tests for usage_tracker.py — AsyncUsageTracker lifecycle and helpers.
No live database or SQL is required.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import datetime, timezone

import pytest

from usage_tracker import AsyncUsageTracker, prune_usage_jsonl_files, start_usage_tracker
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


# ---------------------------------------------------------------------------
# JSONL pruning tests
# ---------------------------------------------------------------------------


def _make_jsonl(directory: str, name: str) -> str:
    """Create an empty JSONL file with the given name in directory."""
    path = os.path.join(directory, name)
    with open(path, "w") as f:
        f.write("{}\n")
    return path


def test_prune_usage_jsonl_files_removes_old_files():
    """Files older than retention_days must be deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Old files (beyond retention window)
        old_usage = _make_jsonl(tmpdir, "command_usage_20200101.jsonl")
        old_metrics = _make_jsonl(tmpdir, "metrics_20200101.jsonl")
        old_alerts = _make_jsonl(tmpdir, "alerts_20200101.jsonl")

        deleted = prune_usage_jsonl_files(data_dir=tmpdir, retention_days=30)

        assert deleted == 3
        assert not os.path.exists(old_usage)
        assert not os.path.exists(old_metrics)
        assert not os.path.exists(old_alerts)


def test_prune_usage_jsonl_files_keeps_recent_files():
    """Files within retention_days must NOT be deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from utils import utcnow
        from datetime import timedelta

        recent_date = (utcnow() - timedelta(days=1)).strftime("%Y%m%d")
        recent = _make_jsonl(tmpdir, f"command_usage_{recent_date}.jsonl")

        deleted = prune_usage_jsonl_files(data_dir=tmpdir, retention_days=30)

        assert deleted == 0
        assert os.path.exists(recent)


def test_prune_usage_jsonl_files_unknown_prefix_not_deleted():
    """Files with an unrecognised prefix must never be touched."""
    with tempfile.TemporaryDirectory() as tmpdir:
        unrelated = _make_jsonl(tmpdir, "some_other_log_20200101.jsonl")

        deleted = prune_usage_jsonl_files(data_dir=tmpdir, retention_days=30)

        assert deleted == 0
        assert os.path.exists(unrelated)


def test_prune_usage_jsonl_files_boundary_day_excluded():
    """A file dated exactly *retention_days* ago is NOT deleted (cutoff is strictly older)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from utils import utcnow
        from datetime import timedelta

        boundary_date = (utcnow() - timedelta(days=30)).strftime("%Y%m%d")
        boundary_file = _make_jsonl(tmpdir, f"command_usage_{boundary_date}.jsonl")

        deleted = prune_usage_jsonl_files(data_dir=tmpdir, retention_days=30)

        # file dated exactly 30 days ago is ON the cutoff boundary — not strictly older
        assert deleted == 0
        assert os.path.exists(boundary_file)
