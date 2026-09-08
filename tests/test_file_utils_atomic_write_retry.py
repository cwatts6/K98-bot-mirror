from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import threading

import pytest

import file_utils as fu


def test_atomic_write_json_retries_winerror32(monkeypatch, tmp_path: Path):
    target = tmp_path / "dm_scheduled_tracker.json"

    real_replace = os.replace
    calls = {"n": 0}

    class _FakePerm(PermissionError):
        def __init__(self):
            super().__init__(
                13, "The process cannot access the file because it is being used by another process"
            )
            self.winerror = 32

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] < 3:
            raise _FakePerm()
        return real_replace(src, dst)

    monkeypatch.setattr(fu.os, "replace", flaky_replace)
    monkeypatch.setattr(fu.time, "sleep", lambda _s: None)  # speed up test

    fu.atomic_write_json(target, {"ok": True}, replace_retries=5)

    assert target.exists()
    assert calls["n"] == 3


def test_atomic_write_json_raises_after_retry_exhaustion(monkeypatch, tmp_path: Path):
    target = tmp_path / "dm_sent_tracker.json"

    class _FakePerm(PermissionError):
        def __init__(self):
            super().__init__(
                13, "The process cannot access the file because it is being used by another process"
            )
            self.winerror = 32

    monkeypatch.setattr(
        fu.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(_FakePerm())
    )
    monkeypatch.setattr(fu.time, "sleep", lambda _s: None)

    with pytest.raises(PermissionError):
        fu.atomic_write_json(target, {"ok": False}, replace_retries=3)


def test_unique_writer_preserves_existing_defaults(tmp_path):
    target = tmp_path / "state.json"
    data = {"z": "été 🐉", "a": {"z": 1, "a": datetime(2026, 9, 7, tzinfo=UTC)}}

    fu.atomic_json_write(str(target), data)

    assert target.read_text(encoding="utf-8") == json.dumps(
        data, indent=2, ensure_ascii=False, default=str
    )
    assert not list(tmp_path.glob("*.tmp"))


def test_unique_writer_can_preserve_strict_legacy_format(tmp_path):
    target = tmp_path / "state.json"
    legacy = tmp_path / "legacy.json"
    data = {"z": "été 🐉", "a": {"z": 1, "a": "UTC\nline"}}
    with legacy.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)

    fu.atomic_json_write(str(target), data, ensure_ascii=True, sort_keys=True, default=None)

    assert target.read_bytes() == legacy.read_bytes()
    assert not target.read_bytes().endswith(b"\n")


@pytest.mark.parametrize("stage", ["serialize", "write", "flush", "fsync", "replace"])
def test_unique_writer_failure_preserves_target_and_cleans_temp(monkeypatch, tmp_path, stage):
    target = tmp_path / "state.json"
    previous = b'{"old": true}'
    target.write_bytes(previous)
    data = {"first": "written before unsupported value", "last": object()}

    def fail(*_args, **_kwargs):
        raise OSError("injected IO failure")

    if stage in {"write", "flush"}:
        real_fdopen = fu.os.fdopen

        class FailingStream:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def write(self, value):
                if stage == "write":
                    fail()
                return self.stream.write(value)

            def flush(self):
                fail()

        monkeypatch.setattr(fu.os, "fdopen", lambda *a, **kw: FailingStream(real_fdopen(*a, **kw)))
    elif stage in {"fsync", "replace"}:
        monkeypatch.setattr(fu.os, stage, fail)

    with pytest.raises(TypeError if stage == "serialize" else OSError):
        fu.atomic_json_write(
            str(target), data if stage == "serialize" else {"new": True}, default=None
        )

    assert target.read_bytes() == previous
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("succeed", [True, False])
def test_unique_writer_retries_only_sharing_violation(monkeypatch, tmp_path, caplog, succeed):
    target = tmp_path / "state.json"
    target.write_text('{"old": true}', encoding="utf-8")
    real_replace = fu.os.replace
    attempts = []
    sleeps = []

    def replace(src, dst):
        attempts.append(src)
        if not succeed or len(attempts) < 3:
            exc = PermissionError("sharing violation")
            exc.winerror = 32
            raise exc
        real_replace(src, dst)

    monkeypatch.setattr(fu.os, "replace", replace)
    monkeypatch.setattr(fu.time, "sleep", sleeps.append)
    monkeypatch.setattr(fu.random, "uniform", lambda low, high: high)

    if succeed:
        fu.atomic_json_write(str(target), {"new": True}, replace_retries=3)
    else:
        with pytest.raises(PermissionError):
            fu.atomic_json_write(str(target), {"new": True}, replace_retries=3)

    assert len(attempts) == 3
    assert len(set(attempts)) == 1
    assert sleeps == [0.02, 0.04]
    assert json.loads(target.read_text()) == ({"new": True} if succeed else {"old": True})
    assert caplog.text.count("[atomic_json_write] WinError32 contention") == 2
    assert not list(tmp_path.glob("*.tmp"))


def test_unique_writer_nonretryable_replace_failure_does_not_sleep(monkeypatch, tmp_path):
    def fail(*_args):
        raise OSError("disk unavailable")

    sleeps = []
    monkeypatch.setattr(fu.os, "replace", fail)
    monkeypatch.setattr(fu.time, "sleep", sleeps.append)
    target = tmp_path / "state.json"
    with pytest.raises(OSError):
        fu.atomic_json_write(str(target), {"new": True})
    assert not target.exists()
    assert not list(tmp_path.iterdir())
    assert sleeps == []


def test_unique_writer_flushes_and_closes_before_replace(monkeypatch, tmp_path):
    target = tmp_path / "state.json"
    real_fsync, real_replace = fu.os.fsync, fu.os.replace
    descriptors = []

    def fsync(fd):
        # Buffered JSON must already have reached the file descriptor.
        assert os.fstat(fd).st_size > 0
        descriptors.append(fd)
        real_fsync(fd)

    def replace(src, dst):
        assert len(descriptors) == 1
        with pytest.raises(OSError):
            os.fstat(descriptors[0])
        assert Path(src).parent == target.parent
        assert json.loads(Path(src).read_text()) == {"new": True}
        real_replace(src, dst)

    monkeypatch.setattr(fu.os, "fsync", fsync)
    monkeypatch.setattr(fu.os, "replace", replace)
    fu.atomic_json_write(str(target), {"new": True})
    assert json.loads(target.read_text()) == {"new": True}


def test_unique_writer_overlapping_calls_use_distinct_temps(monkeypatch, tmp_path):
    target = tmp_path / "state.json"
    barrier = threading.Barrier(2, timeout=10)
    replacement_lock = threading.Lock()
    real_replace = fu.os.replace
    snapshots = {}

    def replace(src, dst):
        snapshots[src] = json.loads(Path(src).read_text())
        barrier.wait()
        # Prove temp isolation under overlap without depending on simultaneous
        # Windows rename success (WinError 5 is intentionally not retried).
        with replacement_lock:
            real_replace(src, dst)

    monkeypatch.setattr(fu.os, "replace", replace)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fu.atomic_json_write, str(target), {"writer": i}) for i in (1, 2)]
        for future in futures:
            future.result(timeout=15)

    assert len(snapshots) == 2
    assert sorted(value["writer"] for value in snapshots.values()) == [1, 2]
    # Atomic snapshots remain last-writer-wins, not a cross-process merge contract.
    assert json.loads(target.read_text()) in snapshots.values()
    assert not list(tmp_path.glob("*.tmp"))
