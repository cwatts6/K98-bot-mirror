"""Shared-helper regressions through actual cache/state callers, with inert data."""

import asyncio
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import threading

import pytest

from core import file_lock
from file_utils import acquire_lock


def assert_available(path):
    with acquire_lock(path, timeout=0):
        pass


def test_path_only_release_cannot_delete_foreign_file(tmp_path):
    from file_utils import release_lock

    path = tmp_path / "lock"
    path.write_bytes(b"keep")
    with pytest.raises(RuntimeError, match="owning context"):
        release_lock(path)
    assert path.read_bytes() == b"keep"


def cache_setup(monkeypatch, tmp_path):
    import player_stats_cache as cache

    target = tmp_path / "cache.json"
    target.write_bytes(b'{"old":true}')
    monkeypatch.setattr(cache, "PLAYER_STATS_CACHE", str(target))
    output = {
        "1": {"GovernorID": "1"},
        "_meta": {
            "count": 1,
            "source_row_count": 1,
            "source_kvk_no": 16,
            "source_last_refresh": "2026-11-10T00:00:00Z",
            "source_refresh_status": "skipped",
            "cache_write_status": "written",
            "existing_json_preserved": False,
        },
    }
    monkeypatch.setattr(cache, "_build_cache_sync", lambda **kwargs: output)
    monkeypatch.setattr(cache, "_build_last_kvk_cache_sync", lambda: None)
    return cache, target, output


@pytest.mark.parametrize("route", ["ordinary", "guided"])
def test_real_cache_write_failure_preserves_prior_and_releases(monkeypatch, tmp_path, route):
    cache, target, _ = cache_setup(monkeypatch, tmp_path)
    before, error = target.read_bytes(), FileExistsError("write failed")
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise error

    monkeypatch.setattr(cache, "_atomic_write_json_with_retries", fail)
    operation = (
        cache._build_and_persist_cache_sync
        if route == "ordinary"
        else cache.rebuild_validated_cache_only
    )
    with pytest.raises(FileExistsError) as caught:
        operation()
    assert caught.value is error and calls == [1]
    assert target.read_bytes() == before
    assert_available(cache._cache_lock_path())


@pytest.mark.parametrize("route", ["ordinary", "guided"])
def test_cleanup_after_cache_commit_does_not_erase_or_replay(monkeypatch, tmp_path, route):
    cache, target, output = cache_setup(monkeypatch, tmp_path)
    cls = file_lock._WindowsOwner if file_lock.os.name == "nt" else file_lock._PosixOwner
    release, owners = cls.release, []
    monkeypatch.setattr(file_lock, "_uncertain", {})

    def fail(owner):
        owners.append(owner)
        raise OSError("release")

    try:
        monkeypatch.setattr(cls, "release", fail)
        operation = (
            cache._build_and_persist_cache_sync
            if route == "ordinary"
            else cache.rebuild_validated_cache_only
        )
        with pytest.raises(file_lock.LockCleanupError, match="not be replayed"):
            operation()
        assert json.loads(target.read_bytes()) == output
        with pytest.raises(file_lock.LockCleanupError):
            assert_available(cache._cache_lock_path())
        assert len(owners) == 1
    finally:
        for owner in owners:
            release(owner)


@pytest.mark.parametrize("logging_failure", [False, True])
def test_guided_staging_cleanup_preserves_readback_failure(monkeypatch, tmp_path, logging_failure):
    import shutil

    cache, target, _ = cache_setup(monkeypatch, tmp_path)
    before = target.read_bytes()
    monkeypatch.setattr(
        cache, "_atomic_write_json_with_retries", lambda path, _: Path(path).write_bytes(b"{}")
    )
    monkeypatch.setattr(shutil, "rmtree", lambda *a: (_ for _ in ()).throw(OSError("cleanup")))
    if logging_failure:
        monkeypatch.setattr(
            cache.logger, "exception", lambda *a, **k: (_ for _ in ()).throw(OSError("logging"))
        )
    with pytest.raises(
        cache.CacheSnapshotValidationError, match="cache_readback_differs"
    ) as caught:
        cache.rebuild_validated_cache_only()
    assert "staging cleanup" in caught.value.__notes__[0]
    if logging_failure:
        assert "diagnostic also failed" in caught.value.__notes__[1]
    assert target.read_bytes() == before
    assert_available(cache._cache_lock_path())


@pytest.mark.parametrize("raw", [b"{", b"{}", b"[]"])
def test_startup_failed_readback_allows_next_writer(monkeypatch, tmp_path, raw):
    from services.player_stats_startup import _verify_completion

    cache, target, output = cache_setup(monkeypatch, tmp_path)
    target.write_bytes(raw)
    with pytest.raises((ValueError, cache.CacheSnapshotValidationError)):
        _verify_completion(output)
    assert target.read_bytes() == raw
    assert_available(cache._cache_lock_path())


def test_startup_decodes_captured_generation_outside_lock(monkeypatch, tmp_path):
    from services import player_stats_startup as startup

    cache, target, output = cache_setup(monkeypatch, tmp_path)
    raw = json.dumps(output).encode()
    target.write_bytes(raw)
    loads = json.loads

    def successor(data):
        # This would fail if parsing still held the writer lock. A successor
        # cannot change the immutable bytes being certified.
        with acquire_lock(cache._cache_lock_path(), timeout=0):
            target.write_bytes(b'{"successor":true}')
        return loads(data)

    monkeypatch.setattr(startup.json, "loads", successor)
    receipt = startup._verify_completion(output)
    assert receipt["sha256"] == hashlib.sha256(raw).hexdigest()
    assert target.read_bytes() == b'{"successor":true}'


def test_startup_oversized_capture_releases_lock(monkeypatch, tmp_path):
    import builtins
    import io

    from services.player_stats_startup import _verify_completion

    cache, target, output = cache_setup(monkeypatch, tmp_path)
    real_open = builtins.open

    def oversized(path, *args, **kwargs):
        if str(path) == str(target):
            return io.BytesIO(b" " * (64 * 1024 * 1024 + 1))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", oversized)
    with pytest.raises(cache.CacheSnapshotValidationError, match="too_large"):
        _verify_completion(output)
    assert_available(cache._cache_lock_path())


def test_ark_team_failed_write_preserves_saved_state(monkeypatch, tmp_path):
    from ark import team_state

    target = tmp_path / "teams.json"
    store = team_state.ArkTeamStateStore(path=target)
    store.save()
    before, error = target.read_bytes(), FileExistsError("write")
    monkeypatch.setattr(
        team_state, "atomic_write_json", lambda *a, **k: (_ for _ in ()).throw(error)
    )
    with pytest.raises(FileExistsError) as caught:
        store.save()
    assert caught.value is error
    assert target.read_bytes() == before
    assert_available(str(target) + ".lock")


def test_ark_second_file_failure_is_partial_save_not_replay(monkeypatch, tmp_path):
    from ark.state import ark_state

    message, reminder = tmp_path / "messages.json", tmp_path / "reminders.json"
    reminder.write_bytes(b'{"old":true}')
    state = ark_state.ArkJsonState(
        message_state_path=str(message), reminder_state_path=str(reminder)
    )
    write, calls = ark_state.atomic_write_json, []

    def fail_second(path, payload, **kwargs):
        calls.append(path)
        if path == str(reminder):
            raise OSError("second write")
        return write(path, payload, **kwargs)

    monkeypatch.setattr(ark_state, "atomic_write_json", fail_second)
    with pytest.raises(OSError, match="second write"):
        state.save()
    assert json.loads(message.read_bytes()) == {"matches": {}}
    assert reminder.read_bytes() == b'{"old":true}'
    assert calls == [str(message), str(reminder)]
    assert_available(str(message) + ".lock")
    assert_available(str(reminder) + ".lock")


async def wait_entered(event):
    for _ in range(1000):
        if event.is_set():
            return
        await asyncio.sleep(0.001)
    pytest.fail("worker did not enter")


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["ark", "ordinary"])
async def test_cancelled_caller_drains_actual_locked_writer(monkeypatch, tmp_path, route):
    entered, finish = threading.Event(), threading.Event()
    path, calls = tmp_path / "lock", []

    def work():
        with acquire_lock(path):
            calls.append(1)
            entered.set()
            assert finish.wait(5)

    if route == "ark":
        from ark.state.ark_state import ArkJsonState

        state = ArkJsonState()
        monkeypatch.setattr(state, "save", work)
        operation = state.save_async()
    else:
        cache, _, _ = cache_setup(monkeypatch, tmp_path)
        from services import legacy_export_snapshot_service as legacy

        monkeypatch.setattr(legacy, "caller_runtime", lambda: nullcontext())
        monkeypatch.setattr(legacy, "_writer_runtime", lambda: None)
        monkeypatch.setattr(cache, "_build_and_persist_cache_sync", work)
        operation = cache.build_player_stats_cache()
    task = asyncio.create_task(operation)
    try:
        await wait_entered(entered)
        task.cancel()
        await asyncio.sleep(0.01)
        task.cancel()
        await asyncio.sleep(0.01)
        assert not task.done()
        with pytest.raises(TimeoutError):
            assert_available(path)
    finally:
        finish.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert calls == [1]
    assert_available(path)


@pytest.mark.asyncio
async def test_tracker_body_failure_preserved_when_release_fails(monkeypatch, tmp_path):
    from services.tracked_view_store import TrackedViewStore

    cls = file_lock._WindowsOwner if file_lock.os.name == "nt" else file_lock._PosixOwner
    release, owners = cls.release, []
    monkeypatch.setattr(file_lock, "_uncertain", {})

    def fail(owner):
        owners.append(owner)
        raise OSError("release")

    error = FileExistsError("body")
    try:
        monkeypatch.setattr(cls, "release", fail)
        store = TrackedViewStore(tmp_path / "state", tmp_path / "lock")
        with pytest.raises(FileExistsError) as caught:
            async with store.locked():
                raise error
        assert caught.value is error
        assert "cleanup also failed" in error.__notes__[0]
    finally:
        for owner in owners:
            release(owner)


@pytest.mark.asyncio
async def test_tracker_cancellation_while_waiting_drains_then_releases(tmp_path):
    from services.tracked_view_store import TrackedViewStore

    path = tmp_path / "lock"
    store = TrackedViewStore(tmp_path / "state", path, poll=0.001)
    body = []

    async def wait():
        async with store.locked():
            body.append(1)

    with acquire_lock(path):
        task = asyncio.create_task(wait())
        await asyncio.sleep(0.02)
        task.cancel()
        await asyncio.sleep(0.01)
        task.cancel()
        await asyncio.sleep(0.01)
        assert not task.done()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert body == []
    assert_available(path)


@pytest.mark.asyncio
@pytest.mark.parametrize("body_failure", [False, True])
async def test_tracker_cancel_during_release_drains_and_preserves_first_error(
    monkeypatch, tmp_path, body_failure
):
    from services.tracked_view_store import TrackedViewStore

    cls = file_lock._WindowsOwner if file_lock.os.name == "nt" else file_lock._PosixOwner
    entered, finish = threading.Event(), threading.Event()
    release = cls.release
    path = tmp_path / "lock"
    error = ValueError("original")

    def slow_release(owner):
        entered.set()
        assert finish.wait(5)
        release(owner)

    monkeypatch.setattr(cls, "release", slow_release)
    store = TrackedViewStore(tmp_path / "state", path)

    async def work():
        async with store.locked():
            if body_failure:
                raise error

    task = asyncio.create_task(work())
    try:
        await wait_entered(entered)
        task.cancel()
        await asyncio.sleep(0.01)
        task.cancel()
        await asyncio.sleep(0.01)
        assert not task.done()
        with pytest.raises(TimeoutError):
            assert_available(path)
    finally:
        finish.set()
    with pytest.raises(ValueError if body_failure else asyncio.CancelledError) as caught:
        await task
    if body_failure:
        assert caught.value is error
    assert_available(path)


@pytest.mark.asyncio
@pytest.mark.parametrize("cleanup_error", [OSError("release"), asyncio.CancelledError("release")])
async def test_tracker_success_inside_except_does_not_suppress_release_error(
    monkeypatch, tmp_path, cleanup_error
):
    from contextlib import contextmanager

    from services import tracked_view_store

    @contextmanager
    def failing_release(*args, **kwargs):
        yield
        raise cleanup_error

    monkeypatch.setattr(tracked_view_store, "tracker_lock", failing_release)
    store = tracked_view_store.TrackedViewStore(tmp_path / "state", tmp_path / "lock")
    ambient = ValueError("already handled")
    try:
        raise ambient
    except ValueError:
        with pytest.raises(type(cleanup_error)) as caught:
            async with store.locked():
                pass
    assert caught.value is cleanup_error
    assert not getattr(ambient, "__notes__", [])


def test_guided_success_inside_except_does_not_suppress_cleanup_failure(monkeypatch, tmp_path):
    import shutil

    cache, target, output = cache_setup(monkeypatch, tmp_path)
    error = OSError("staging cleanup")
    monkeypatch.setattr(shutil, "rmtree", lambda *args: (_ for _ in ()).throw(error))
    ambient = ValueError("already handled")
    try:
        raise ambient
    except ValueError:
        with pytest.raises(OSError) as caught:
            cache.rebuild_validated_cache_only()
    assert caught.value is error
    assert json.loads(target.read_bytes()) == output
    assert not getattr(ambient, "__notes__", [])
    assert_available(cache._cache_lock_path())
