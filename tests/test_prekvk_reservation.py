from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import subprocess
import sys
import threading

import pytest

from stats_alerts import dispatch_reservations as dispatch, guard, state


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "LOG_PATH", str(tmp_path / "alerts.csv"))
    monkeypatch.setattr(state, "STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setattr(state, "_STATE_LOCK_PATH", str(tmp_path / "state.lck"))
    now = [datetime(2026, 9, 8, 12, tzinfo=UTC)]
    result = dispatch.ReservationStore(clock=lambda: now[0])
    result.now = now
    return result


def test_reservation_is_not_success_and_owner_is_checked(store):
    token = store.reserve("prekvk_daily", 99)
    assert token
    assert list(guard.iter_log_rows()) == []
    assert store.reserve("prekvk_daily", 100) is None  # global, not per channel
    for method in (store.start, store.finish_failure):
        with pytest.raises(dispatch.DispatchUnavailable):
            method("wrong-owner")
    with pytest.raises(dispatch.DispatchUnavailable):
        store.accept("wrong-owner", 123)
    store.start(token)
    store.accept(token, 123)
    store.accept(token, 123)
    assert state.load_state() == {"prekvk_msg_id": 123}
    assert list(guard.iter_log_rows()) == [
        {"date": "2026-09-08", "time_utc": "12:00:00", "kind": "prekvk_daily"}
    ]
    with pytest.raises(dispatch.DispatchUnavailable):
        store.accept(token, 124)


@pytest.mark.parametrize(
    "kind,other,blocked",
    [
        ("prekvk_daily", "prekvk_daily", True),
        ("prekvk_daily", "offseason_daily", True),
        ("offseason_daily", "prekvk_daily", True),
        ("prekvk_daily", "offseason_weekly", True),
        ("offseason_weekly", "prekvk_daily", True),
        ("offseason_daily", "offseason_weekly", False),
    ],
)
def test_active_conflict_matrix(store, kind, other, blocked):
    assert store.reserve(kind, 99)
    assert (store.reserve(other, 99) is None) == blocked


@pytest.mark.parametrize(
    "first,second,blocked",
    [
        ("prekvk_daily", "offseason_daily", False),
        ("prekvk_daily", "offseason_weekly", False),
        ("offseason_daily", "prekvk_daily", True),
        ("offseason_weekly", "prekvk_daily", True),
    ],
)
def test_completed_exclusion_preserves_existing_direction(store, first, second, blocked):
    token = store.reserve(first, 99)
    store.start(token)
    store.accept(token, 123)
    assert (store.reserve(second, 99) is None) == blocked


def test_thread_contenders_have_one_owner(store):
    barrier = threading.Barrier(4)

    def reserve():
        barrier.wait(timeout=3)
        return dispatch.ReservationStore(store.log_path).reserve("prekvk_daily", 99)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: reserve(), range(4)))
    assert sum(result is not None for result in results) == 1


def test_process_contenders_have_one_owner(store):
    code = """
import sys
from stats_alerts.dispatch_reservations import ReservationStore
print('ready', flush=True)
sys.stdin.readline()
token = ReservationStore(sys.argv[1]).reserve('prekvk_daily', 99)
print('result:' + str(token), flush=True)
# Keep the owner alive until both results have been observed.
sys.stdin.readline()
"""
    children = [
        subprocess.Popen(
            [sys.executable, "-B", "-c", code, store.log_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    try:
        for child in children:
            assert child.stdout.readline().strip() == "ready"
        for child in children:
            child.stdin.write("go\n")
            child.stdin.flush()
        results = [child.stdout.readline().strip() for child in children]
        assert (
            sum(result.startswith("result:") and result != "result:None" for result in results) == 1
        )
        for child in children:
            _, err = child.communicate("done\n", timeout=20)
            assert child.returncode == 0, err
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)


def test_lock_contention_does_not_send_or_overwrite(store, monkeypatch):
    monkeypatch.setattr(guard, "LOCK_TIMEOUT_SECONDS", 0.03)
    with guard.coordination_lock(store.log_path):
        with pytest.raises(TimeoutError):
            store.reserve("prekvk_daily", 99)
    assert not store.path.exists()
    assert store.reserve("prekvk_daily", 99)


@pytest.mark.parametrize(
    "phase,alive,available",
    [
        ("reserved", False, True),
        ("reserved", True, False),
        ("reserved", None, False),
        ("sending", False, False),
        ("sending", True, False),
        ("uncertain", False, False),
    ],
)
def test_restart_owner_and_phase_recovery(store, phase, alive, available):
    token = store.reserve("prekvk_daily", 99)
    if phase != "reserved":
        store.start(token)
    if phase == "uncertain":
        store.finish_failure(token)
    store.now[0] += timedelta(days=2)
    restarted = dispatch.ReservationStore(
        store.log_path, clock=store.clock, owner_alive=lambda _: alive
    )
    assert (restarted.reserve("prekvk_daily", 99) is not None) == available


def test_midnight_success_uses_success_day_and_unresolved_blocks_rollover(store):
    store.now[0] = datetime(2026, 9, 8, 23, 59, 59, tzinfo=UTC)
    token = store.reserve("prekvk_daily", 99)
    store.start(token)
    store.now[0] += timedelta(seconds=2)
    assert store.reserve("prekvk_daily", 99) is None
    store.accept(token, 123)
    assert next(guard.iter_log_rows())["date"] == "2026-09-09"
    assert store.reserve("prekvk_daily", 99) is None


def test_midnight_preparation_rechecks_new_day_quota(store):
    token = store.reserve("prekvk_daily", 99)
    store.now[0] += timedelta(days=1)
    with guard.coordination_lock():
        guard._append_success_unlocked(store.log_path, "offseason_daily", store.clock())
    with pytest.raises(dispatch.DispatchUnavailable):
        store.start(token)
    store.finish_failure(token)
    assert store._read()["attempts"][token]["phase"] == "released"


@pytest.mark.parametrize("boundary", ["receipt", "state", "csv", "committed"])
def test_accepted_send_failure_boundaries_never_grant_another_send(store, monkeypatch, boundary):
    token = store.reserve("prekvk_daily", 99)
    store.start(token)
    original_write = store._write

    def fail_write(data):
        phase = data["attempts"][token]["phase"]
        if (boundary == "receipt" and phase == "accepted") or (
            boundary == "committed" and phase == "committed"
        ):
            raise OSError("disk unavailable")
        original_write(data)

    def fail(*args, **kwargs):
        raise OSError("disk unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_write", fail_write)
        if boundary == "state":
            patch.setattr(state, "update_prekvk_message", fail)
        if boundary == "csv":
            patch.setattr(guard, "atomic_write_csv", fail)
        with pytest.raises(OSError):
            store.accept(token, 123)
    restarted = dispatch.ReservationStore(
        store.log_path, clock=store.clock, owner_alive=lambda _: False
    )
    assert restarted.reserve("prekvk_daily", 99) is None
    if boundary == "receipt":
        assert restarted._read()["attempts"][token]["phase"] == "uncertain"
        assert list(guard.iter_log_rows()) == []
    else:
        assert restarted._read()["attempts"][token]["phase"] == "committed"
        assert len(list(guard.iter_log_rows())) == 1


@pytest.mark.parametrize(
    "contents",
    ["", "{", "[]", '{"version":99}', '{"version":1,"message_generation":0,"attempts":{"bad":{}}}'],
)
def test_corrupt_store_fails_closed_without_replacing_evidence(store, contents):
    store.path.write_text(contents, encoding="utf-8")
    with pytest.raises((ValueError, dispatch.DispatchUnavailable)):
        store.reserve("prekvk_daily", 99)
    assert store.path.read_text(encoding="utf-8") == contents


def test_reconciliation_requires_positive_receipt_and_matching_destination(store):
    token = store.reserve("prekvk_daily", 99)
    store.start(token)
    store.finish_failure(token)
    with pytest.raises(dispatch.DispatchUnavailable):
        store.reconcile_receipt(token, channel_id=100, message_id=123, accepted_at=store.clock())
    store.reconcile_receipt(token, channel_id=99, message_id=123, accepted_at=store.clock())
    assert store._read()["attempts"][token]["phase"] == "committed"
    assert len(list(guard.iter_log_rows())) == 1


def test_fighting_clear_fences_late_accepted_receipt(store):
    token = store.reserve("prekvk_daily", 99)
    store.start(token)
    store.clear_message()
    store.accept(token, 123)
    assert state.load_state() == {}
    assert len(list(guard.iter_log_rows())) == 1


@pytest.mark.asyncio
async def test_coroutine_overlap_one_actual_dispatch_lifetime(store):
    entered = asyncio.Event()
    done = asyncio.Event()
    sends = []

    async def first():
        async with dispatch.DispatchAttempt("prekvk_daily", 99) as attempt:
            await attempt.start()
            sends.append(1)
            entered.set()
            await done.wait()
            await attempt.accept(123)

    task = asyncio.create_task(first())
    await asyncio.wait_for(entered.wait(), 3)
    try:
        with pytest.raises(dispatch.DispatchUnavailable):
            async with dispatch.DispatchAttempt("prekvk_daily", 99):
                sends.append(2)
    finally:
        done.set()
        await task
    assert sends == [1]


@pytest.mark.asyncio
@pytest.mark.parametrize("started", [False, True])
async def test_cancellation_releases_only_before_send(store, started):
    entered = asyncio.Event()

    async def send():
        async with dispatch.DispatchAttempt("prekvk_daily", 99) as attempt:
            if started:
                await attempt.start()
            entered.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(send())
    await asyncio.wait_for(entered.wait(), 3)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    row = next(iter(store._read()["attempts"].values()))
    assert row["phase"] == ("uncertain" if started else "released")


@pytest.mark.asyncio
async def test_backend_exception_is_not_reexecuted(store, monkeypatch):
    calls = []

    def failing_reserve(self, *args):
        calls.append(args)
        raise OSError("after entry")

    monkeypatch.setattr(dispatch.ReservationStore, "reserve", failing_reserve)
    with pytest.raises(OSError):
        async with dispatch.DispatchAttempt("prekvk_daily", 99):
            pytest.fail("must not send")
    assert len(calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 403, 404, 500])
async def test_final_http_rejection_does_not_prove_no_earlier_client_retry(store, status):
    class Rejection(Exception):
        pass

    error = Rejection("final status may follow an ambiguous client retry")
    error.status = status
    with pytest.raises(Rejection):
        async with dispatch.DispatchAttempt("prekvk_daily", 99) as attempt:
            await attempt.start()
            raise error
    assert next(iter(store._read()["attempts"].values()))["phase"] == "uncertain"


@pytest.mark.asyncio
async def test_cancel_during_thread_reservation_waits_and_releases_once(store, monkeypatch):
    entered = threading.Event()
    finish = threading.Event()
    original = dispatch.ReservationStore.reserve
    calls = []

    def reserve(self, *args):
        calls.append(args)
        token = original(self, *args)
        entered.set()
        assert finish.wait(5)
        return token

    monkeypatch.setattr(dispatch.ReservationStore, "reserve", reserve)

    async def send():
        async with dispatch.DispatchAttempt("prekvk_daily", 99):
            pytest.fail("cancelled admission must not send")

    task = asyncio.create_task(send())
    assert await asyncio.to_thread(entered.wait, 3)
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()  # repeated shutdown cancellation still cannot abandon the writer
    finish.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(calls) == 1
    assert next(iter(store._read()["attempts"].values()))["phase"] == "released"


def test_stale_clear_does_not_invalidate_newer_message(store):
    state.update_prekvk_message(123)
    token = store.reserve("prekvk_daily", 99)
    assert not store.clear_message(expected_id=122)
    store.start(token)
    store.accept(token, 124)
    assert state.load_state()["prekvk_msg_id"] == 124
