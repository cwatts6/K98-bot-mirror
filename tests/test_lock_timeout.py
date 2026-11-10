import pytest

import rehydrate_views as views


@pytest.fixture
def foreign_lock(tmp_path, monkeypatch):
    target = tmp_path / "views.json"
    lock = tmp_path / "views.json.lock"
    target.write_text("{}", encoding="utf-8")
    lock.write_bytes(b"99999\n")
    monkeypatch.setattr(views, "VIEW_TRACKING_FILE", str(target))
    monkeypatch.setattr(views, "_LOCK_PATH", str(lock))
    monkeypatch.setattr(views, "VIEW_TRACKER_LOCK_TIMEOUT", 0)
    return target, lock


def test_save_view_tracker_raises_on_lock(foreign_lock):
    target, lock = foreign_lock
    with pytest.raises(views.LockAcquireTimeout):
        views.save_view_tracker(
            "testkey",
            {
                "channel_id": 1,
                "message_id": 1,
                "events": [{"name": "x", "start_time": "2025-11-19T10:00:00Z"}],
            },
        )
    assert target.read_text() == "{}"
    assert lock.read_bytes() == b"99999\n"


def test_remove_view_tracker_entry_returns_false_when_locked(foreign_lock):
    target, lock = foreign_lock
    assert views.remove_view_tracker_entry("does_not_matter") is False
    assert target.read_text() == "{}"
    assert lock.read_bytes() == b"99999\n"
