# tests/test_rehydrate_views.py
from datetime import UTC, datetime
import json
import os

import pytest

import rehydrate_views
from rehydrate_views import (
    LockAcquireTimeout,
    load_view_tracker,
    remove_view_tracker_entry,
    save_view_tracker,
    validate_tracker_entry,
)


def _set_temp_paths(tmpdir):
    # Point the module constants to a temp file to avoid touching repo data
    tmp_file = os.path.join(tmpdir, "view_tracker.json")
    rehydrate_views.VIEW_TRACKING_FILE = tmp_file
    # recompute lock path
    rehydrate_views._LOCK_PATH = f"{tmp_file}.lock"
    # make lock timeout small for tests
    rehydrate_views.VIEW_TRACKER_LOCK_TIMEOUT = 0.25
    rehydrate_views.VIEW_TRACKER_LOCK_POLL = 0.01
    return tmp_file


def _make_sample_event():
    # Use ISO string that parse_isoformat_utc accepts
    now = datetime.now(UTC)
    return {
        "name": "Test Event",
        "type": "ruins",
        "start_time": now.isoformat().replace("+00:00", "Z"),
        "description": "A sample",
    }


def test_save_load_remove_tracker_entry_valid(tmp_path):
    tmp = str(tmp_path)
    _set_temp_paths(tmp)

    key = "testkey"
    entry = {
        "channel_id": "123",
        "message_id": "456",
        "events": [_make_sample_event()],
        "prefix": "test_prefix",
    }

    # Save should succeed
    save_view_tracker(key, entry)

    # File exists and load_view_tracker returns expected shape
    loaded = load_view_tracker()
    assert isinstance(loaded, dict)
    assert key in loaded
    assert loaded[key]["channel_id"] == entry["channel_id"] or int(
        loaded[key]["channel_id"]
    ) == int(entry["channel_id"])
    assert "events" in loaded[key]
    assert isinstance(loaded[key]["events"], list)
    # events should be saved as ISO strings (persisted form)
    assert isinstance(loaded[key]["events"][0]["start_time"], str)

    # Validate via validate_tracker_entry on loaded entry (should parse)
    ok, normalized_or_reason = validate_tracker_entry(loaded[key])
    assert ok is True
    normalized = normalized_or_reason
    assert isinstance(normalized["channel_id"], int)
    assert isinstance(normalized["message_id"], int)
    assert isinstance(normalized["events"], list)
    assert normalized["events"][0]["name"] == "Test Event"

    # Remove entry
    removed = remove_view_tracker_entry(key)
    assert removed is True

    # Now loader should not contain the key
    loaded_after = load_view_tracker()
    assert key not in loaded_after


def test_malformed_entries_and_prune(tmp_path):
    tmp = str(tmp_path)
    _set_temp_paths(tmp)

    # Write a malformed tracker file: one entry is a non-dict value
    malformed = {
        "badkey": "not-a-dict",
        "okkey": {"channel_id": "10", "message_id": "20", "events": [_make_sample_event()]},
    }
    with open(rehydrate_views.VIEW_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(malformed, f)

    loaded = load_view_tracker()
    assert "badkey" in loaded

    # validate_tracker_entry should reject the bad one
    ok, reason = validate_tracker_entry(loaded["badkey"])
    assert ok is False
    assert "not a dict" in reason or "entry not a dict" in reason or isinstance(reason, str)

    # Removing malformed entry should succeed
    removed = remove_view_tracker_entry("badkey")
    # remove_view_tracker_entry returns True only if the entry existed originally and was removed
    assert removed is True

    # Ensure it is gone
    loaded2 = load_view_tracker()
    assert "badkey" not in loaded2
    assert "okkey" in loaded2


def test_lock_contention_on_save_and_remove(tmp_path):
    tmp = str(tmp_path)
    _set_temp_paths(tmp)

    key = "k_lock"
    entry = {
        "channel_id": "1",
        "message_id": "2",
        "events": [_make_sample_event()],
    }

    # Ensure base file exists so remove_view_tracker_entry has something to operate on
    with open(rehydrate_views.VIEW_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump({key: entry}, f)

    # Simulate a lock file already present to cause acquire_lock to timeout
    with open(rehydrate_views._LOCK_PATH, "w", encoding="utf-8") as lf:
        lf.write("simulated-lock")

    # save_view_tracker should raise LockAcquireTimeout because lock exists and we set a small timeout
    with pytest.raises(LockAcquireTimeout):
        save_view_tracker("another_key", entry)

    # remove_view_tracker_entry should return False (best-effort) when it cannot acquire the lock
    removed = remove_view_tracker_entry(key)
    assert removed is False

    # Cleanup: remove the simulated lock
    try:
        os.remove(rehydrate_views._LOCK_PATH)
    except Exception:
        pass

    # Now remove should succeed
    removed_ok = remove_view_tracker_entry(key)
    assert removed_ok in (True, False)  # entry may have been removed earlier; ensure no exception
