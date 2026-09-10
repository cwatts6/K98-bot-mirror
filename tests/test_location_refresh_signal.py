from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from services import location_refresh_signal as signal


@pytest.fixture(autouse=True)
def _reset_refresh_state(monkeypatch):
    monkeypatch.setattr(signal, "_location_refresh_lock", asyncio.Lock())
    monkeypatch.setattr(signal, "_location_refresh_event", asyncio.Event())
    monkeypatch.setattr(signal, "_last_location_refresh_utc", None)


@pytest.mark.asyncio
async def test_signal_location_refresh_complete_releases_waiter():
    waiter = asyncio.create_task(signal.wait_for_location_refresh(1.0))
    await asyncio.sleep(0)

    signal.signal_location_refresh_complete()

    assert await waiter is True


@pytest.mark.asyncio
async def test_wait_for_location_refresh_times_out():
    assert await signal.wait_for_location_refresh(0.01) is False


def test_location_refresh_rate_limit_reports_remaining(monkeypatch):
    monkeypatch.setattr(
        signal,
        "_last_location_refresh_utc",
        datetime.now(UTC) - timedelta(minutes=10),
    )

    limited, remain = signal.is_location_refresh_rate_limited()

    assert limited is True
    assert 0 < remain <= 3000


def test_mark_location_refresh_started_clears_existing_signal():
    signal.signal_location_refresh_complete()

    signal.mark_location_refresh_started()

    assert signal.is_location_refresh_rate_limited()[0] is True
    assert not signal._location_refresh_event.is_set()


@pytest.mark.asyncio
async def test_run_location_refresh_guarded_runs_and_reports_running_state():
    states = []

    async def refresh():
        states.append(signal.is_location_refresh_running())

    ran = await signal.run_location_refresh_guarded(refresh)

    assert ran is True
    assert states == [True]
    assert signal.is_location_refresh_running() is False


@pytest.mark.asyncio
async def test_run_location_refresh_guarded_does_not_queue_concurrent_call():
    started = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def first_refresh():
        calls.append("first")
        started.set()
        await release.wait()

    async def second_refresh():
        calls.append("second")

    first = asyncio.create_task(signal.run_location_refresh_guarded(first_refresh))
    await started.wait()

    second_ran = await signal.run_location_refresh_guarded(second_refresh)
    release.set()

    assert second_ran is False
    assert await first is True
    assert calls == ["first"]


@pytest.mark.asyncio
async def test_run_location_refresh_guarded_rechecks_rate_limit_inside_guard(monkeypatch):
    monkeypatch.setattr(signal, "_last_location_refresh_utc", datetime.now(UTC))
    calls = []

    async def refresh():
        calls.append("ran")

    ran = await signal.run_location_refresh_guarded(refresh)

    assert ran is False
    assert calls == []
