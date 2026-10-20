import os

import pytest

from constants import VIEW_TRACKING_FILE
from rehydrate_views import LockAcquireTimeout, remove_view_tracker_entry, save_view_tracker

LOCK_PATH = f"{VIEW_TRACKING_FILE}.lock"


def _ensure_cleanup():
    try:
        if os.path.exists(LOCK_PATH):
            os.remove(LOCK_PATH)
    except Exception:
        pass


def test_save_view_tracker_raises_on_lock(tmp_path, monkeypatch):
    # Ensure lock file exists to simulate another process holding the lock
    _ensure_cleanup()
    with open(LOCK_PATH, "w", encoding="utf-8") as f:
        f.write("99999\n")
        f.flush()
        # Keep file present; acquire_lock uses O_EXCL so creation will fail

        # reduce lock timeout to speed test
        monkeypatch.setenv("VIEW_TRACKER_LOCK_TIMEOUT", "0.5")
        # attempt to save -> should raise LockAcquireTimeout
        with pytest.raises(LockAcquireTimeout):
            save_view_tracker(
                "testkey",
                {
                    "channel_id": 1,
                    "message_id": 1,
                    "events": [{"name": "x", "start_time": "2025-11-19T10:00:00Z"}],
                },
            )

    # cleanup
    _ensure_cleanup()


def test_remove_view_tracker_entry_returns_false_when_locked(tmp_path, monkeypatch):
    _ensure_cleanup()
    with open(LOCK_PATH, "w", encoding="utf-8") as f:
        f.write("12345\n")
        f.flush()
        monkeypatch.setenv("VIEW_TRACKER_LOCK_TIMEOUT", "0.5")
        res = remove_view_tracker_entry("does_not_matter")
        assert res is False
    _ensure_cleanup()
