import json
import os
from pathlib import Path
import sys
import time

import pytest

import singleton_lock


def read_lock(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_acquire_and_release_creates_file(tmp_path):
    lock_path = str(tmp_path / "bot_lock.json")
    # Ensure no early exit in tests
    meta = singleton_lock.acquire_singleton_lock(lock_path, exit_on_conflict=False)
    assert meta is not None
    assert Path(lock_path).exists()
    data = read_lock(lock_path)
    assert int(data.get("pid")) == os.getpid()
    # Release and verify removed
    singleton_lock.release_singleton_lock(lock_path)
    assert not Path(lock_path).exists()


def test_stale_lock_is_removed_and_replaced(tmp_path, monkeypatch):
    lock_path = Path(tmp_path / "bot_lock.json")
    # Create stale lock file (pid unlikely to exist)
    stale = {
        "pid": 99999999,
        "created": time.time() - 1000,
        "exe": "/nonexistent/python",
        "cwd": "/tmp",
    }
    lock_path.write_text(json.dumps(stale), encoding="utf-8")
    # Acquire should remove stale and create new lock
    meta = singleton_lock.acquire_singleton_lock(str(lock_path), exit_on_conflict=False)
    assert meta is not None
    data = read_lock(str(lock_path))
    assert int(data.get("pid")) == os.getpid()
    singleton_lock.release_singleton_lock(str(lock_path))


def test_conflict_detected_with_psutil_simulated(tmp_path, monkeypatch):
    lock_path = Path(tmp_path / "bot_lock.json")
    # Simulate an existing running process (PID=12345)
    saved_created = time.time() - 10
    existing = {"pid": 12345, "created": saved_created, "exe": sys.executable, "cwd": "/tmp"}
    lock_path.write_text(json.dumps(existing), encoding="utf-8")

    class FakeProc:
        def __init__(self, pid):
            self._pid = pid

        def is_running(self):
            return True

        def exe(self):
            return sys.executable

        def create_time(self):
            # Return a create_time <= saved_created so that it's treated as live
            return saved_created - 1

    class FakePsutil:
        @staticmethod
        def pid_exists(pid):
            return True

        @staticmethod
        def Process(pid):
            return FakeProc(pid)

    # Replace module-level psutil with our fake
    monkeypatch.setattr(singleton_lock, "psutil", FakePsutil)
    with pytest.raises(RuntimeError):
        # We expect a RuntimeError because raise_on_conflict=True and process appears live
        singleton_lock.acquire_singleton_lock(
            str(lock_path), exit_on_conflict=False, raise_on_conflict=True
        )
    # Clean up: restore psutil to None for other tests
    monkeypatch.setattr(singleton_lock, "psutil", None)
