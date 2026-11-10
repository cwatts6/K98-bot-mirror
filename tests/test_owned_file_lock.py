"""Real local filesystem/process regressions for the shared ownership contract."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from core import file_lock as locks


@pytest.fixture(autouse=True)
def custody(monkeypatch):
    monkeypatch.setattr(locks, "_uncertain", {})


def available(path):
    with locks.acquire_lock(path, timeout=0):
        pass


@pytest.mark.parametrize(
    "error",
    [
        ValueError("body"),
        FileExistsError("body"),
        asyncio.CancelledError("body"),
        KeyboardInterrupt("body"),
    ],
)
def test_body_runs_once_and_first_failure_survives(tmp_path, error):
    path, calls = tmp_path / "lock", []
    with pytest.raises(type(error)) as caught:
        with locks.acquire_lock(path, timeout=0):
            calls.append(1)
            raise error
    assert caught.value is error
    assert calls == [1]
    available(path)


def test_threads_reentry_alias_and_zero_budget(tmp_path):
    path = tmp_path / "lock"
    alias = path.parent / "." / path.name
    with locks.acquire_lock(path):
        with pytest.raises(TimeoutError):
            available(alias)
        with ThreadPoolExecutor(1) as executor:
            future = executor.submit(available, alias)
            with pytest.raises(TimeoutError):
                future.result(timeout=5)
    available(alias)


@pytest.mark.parametrize("raw", [b"foreign", b"", b"999999\n", locks._HELD, b"partial"])
def test_foreign_and_crashed_sentinels_are_not_recovered(tmp_path, raw):
    path = tmp_path / "lock"
    path.write_bytes(raw)
    with pytest.raises(TimeoutError):
        available(path)
    assert path.read_bytes() == raw


def test_monotonic_budget_bounded_sleep_and_no_wall_clock(tmp_path, monkeypatch):
    path = tmp_path / "lock"
    path.write_bytes(b"foreign")
    ticks, sleeps = iter([100, 100.01, 100.03]), []
    monkeypatch.setattr(locks.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(locks.time, "time", lambda: pytest.fail("wall clock used"))
    monkeypatch.setattr(locks.time, "sleep", sleeps.append)
    with pytest.raises(TimeoutError):
        with locks.acquire_lock(path, timeout=0.02, poll=0.1):
            pytest.fail("entered foreign lock")
    assert sleeps == pytest.approx([0.01])


def test_cancel_while_waiting_preserves_foreign_sentinel(tmp_path, monkeypatch):
    path = tmp_path / "lock"
    path.write_bytes(b"foreign")
    error = asyncio.CancelledError()
    monkeypatch.setattr(locks.time, "sleep", lambda _: (_ for _ in ()).throw(error))
    with pytest.raises(asyncio.CancelledError) as caught:
        with locks.acquire_lock(path):
            pytest.fail("foreign lock entered")
    assert caught.value is error
    assert path.read_bytes() == b"foreign"


@pytest.mark.parametrize(
    "timeout,poll", [(-1, 0.1), (float("nan"), 0.1), (1, 0), (1, float("inf"))]
)
def test_invalid_wait_parameters_do_not_create_files(tmp_path, timeout, poll):
    path = tmp_path / "lock"
    with pytest.raises(ValueError):
        with locks.acquire_lock(path, timeout=timeout, poll=poll):
            pass
    assert not path.exists()


def test_parent_creation_failure_is_not_retried(tmp_path):
    parent = tmp_path / "parent"
    parent.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        available(parent / "lock")
    assert parent.read_bytes() == b"keep"


def test_failed_metadata_initialization_releases_owned_object(tmp_path, monkeypatch):
    cls = locks._WindowsOwner if os.name == "nt" else locks._PosixOwner
    error = OSError("metadata")
    with monkeypatch.context() as patch:
        patch.setattr(cls, "initialize", lambda self: (_ for _ in ()).throw(error))
        with pytest.raises(OSError) as caught:
            available(tmp_path / "lock")
    assert caught.value is error
    available(tmp_path / "lock")


@pytest.mark.parametrize("body_error", [None, FileExistsError("first"), asyncio.CancelledError()])
def test_cleanup_uncertainty_retains_owner_and_first_failure(tmp_path, monkeypatch, body_error):
    cls = locks._WindowsOwner if os.name == "nt" else locks._PosixOwner
    real_release = cls.release
    owners = []

    def fail(owner):
        owners.append(owner)
        raise OSError("release refused")

    path = tmp_path / "lock"
    try:
        with monkeypatch.context() as patch:
            patch.setattr(cls, "release", fail)
            expected = type(body_error) if body_error is not None else locks.LockCleanupError
            with pytest.raises(expected) as caught:
                with locks.acquire_lock(path):
                    if body_error is not None:
                        raise body_error
            if body_error is not None:
                assert caught.value is body_error
                assert "cleanup also failed" in body_error.__notes__[0]
            with pytest.raises(locks.LockCleanupError):
                available(path)
            assert len(owners) == 1  # no automatic cleanup retry
            assert locks._uncertain
    finally:
        for owner in owners:
            real_release(owner)  # fixture-owned recovery, never production policy


def test_close_failure_does_not_retry_reused_handle(tmp_path, monkeypatch):
    cls = locks._WindowsOwner if os.name == "nt" else locks._PosixOwner
    real_close, calls = cls.close, []

    def close_then_error(owner):
        real_close(owner)
        calls.append(1)
        raise OSError("acknowledgement lost")

    monkeypatch.setattr(cls, "close", close_then_error)
    with pytest.raises(locks.LockCleanupError):
        available(tmp_path / "lock")
    with pytest.raises(locks.LockCleanupError):
        available(tmp_path / "lock")
    assert calls == [1]


def child(path, mode):
    code = """
import os, sys
from core.file_lock import acquire_lock
try:
    with acquire_lock(sys.argv[1], timeout=0):
        if sys.argv[2] == 'crash':
            os._exit(23)
except TimeoutError:
    sys.exit(17)
"""
    return subprocess.run(
        [sys.executable, "-c", code, str(path), mode],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_native_process_contention_release_and_restart(tmp_path):
    path = tmp_path / "lock"
    with locks.acquire_lock(path):
        result = child(path, "try")
        assert result.returncode == 17, result.stderr
    result = child(path, "try")
    assert result.returncode == 0, result.stderr
    result = child(path, "crash")
    assert result.returncode == 23, result.stderr
    result = child(path, "try")
    assert result.returncode == 17, result.stderr


@pytest.mark.skipif(os.name != "nt", reason="Windows handle sharing")
def test_native_windows_refuses_delete_rename_and_case_alias(tmp_path):
    path = tmp_path / "lock"
    with locks.acquire_lock(path):
        for mutation in (path.unlink, lambda: path.rename(tmp_path / "moved")):
            with pytest.raises(PermissionError):
                mutation()
        with pytest.raises(TimeoutError):
            available(Path(str(path).upper()))
    assert not path.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows close/delete regression")
def test_successor_created_at_close_is_never_deleted(tmp_path, monkeypatch):
    path = tmp_path / "lock"
    close = locks._WindowsOwner.close

    def successor(owner):
        close(owner)
        path.write_bytes(b"successor")

    monkeypatch.setattr(locks._WindowsOwner, "close", successor)
    available(path)
    assert path.read_bytes() == b"successor"


@pytest.mark.skipif(os.name != "nt", reason="Windows permission error contract")
def test_windows_permission_refusal_keeps_native_error(tmp_path, monkeypatch):
    def denied(*args):
        locks.ctypes.set_last_error(5)
        return locks.ctypes.c_void_p(-1).value

    monkeypatch.setattr(locks, "_create", denied)
    with pytest.raises(PermissionError) as caught:
        available(tmp_path / "lock")
    assert caught.value.winerror == 5
    assert not (tmp_path / "lock").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX rendezvous identity")
@pytest.mark.parametrize("replacement", ["missing", "file", "symlink", "hardlink"])
def test_posix_never_modifies_replacement_on_release(tmp_path, replacement):
    path, foreign = tmp_path / "lock", tmp_path / "foreign"
    foreign.write_bytes(b"foreign")
    try:
        with pytest.raises(locks.LockCleanupError):
            with locks.acquire_lock(path):
                path.unlink()
                if replacement == "file":
                    path.write_bytes(b"successor")
                elif replacement == "symlink":
                    path.symlink_to(foreign)
                elif replacement == "hardlink":
                    os.link(foreign, path)
        assert foreign.read_bytes() == b"foreign"
        if replacement != "missing":
            assert path.read_bytes() == (b"successor" if replacement == "file" else b"foreign")
    finally:
        for entries in locks._uncertain.values():
            for owner, _ in entries:
                owner.close()


@pytest.mark.skipif(os.name == "nt", reason="POSIX no-follow and hardlink rejection")
@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_posix_rejects_aliased_existing_marker(tmp_path, kind):
    path, foreign = tmp_path / "lock", tmp_path / "foreign"
    foreign.write_bytes(locks._FREE)
    if kind == "symlink":
        path.symlink_to(foreign)
    else:
        os.link(foreign, path)
    with pytest.raises((OSError, locks.LockOwnershipError)):
        available(path)
    assert foreign.read_bytes() == locks._FREE


def test_concurrent_threads_serialize_real_read_modify_write(tmp_path):
    path, counter = tmp_path / "lock", tmp_path / "counter"
    counter.write_text("0")
    start = threading.Barrier(4)

    def increment():
        start.wait(timeout=5)
        for _ in range(5):
            with locks.acquire_lock(path, timeout=3, poll=0.001):
                value = int(counter.read_text())
                counter.write_text(str(value + 1))

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: increment(), range(4)))
    assert counter.read_text() == "20"
