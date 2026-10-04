from __future__ import annotations

import asyncio

import pytest

from event_calendar import scheduler as sched


@pytest.mark.asyncio
async def test_scheduler_runs_refresh_full_once(monkeypatch):
    # keep test name for backward compatibility, but validate new canonical call
    called = {"refresh_pipeline": 0, "lock": 0}

    class _Lock:
        async def __aenter__(self):
            called["lock"] += 1

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Svc:
        async def refresh_pipeline(self, **kwargs):
            called["refresh_pipeline"] += 1
            return {"ok": True}

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(sched, "get_operation_lock", lambda _n: _Lock())
    monkeypatch.setattr(sched, "get_calendar_service", lambda: _Svc())
    monkeypatch.setattr(sched.asyncio, "sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await sched.run_calendar_pipeline_loop(poll_interval_seconds=1)

    assert called["lock"] == 1
    assert called["refresh_pipeline"] == 1


@pytest.mark.asyncio
async def test_interval_zero_raises():
    with pytest.raises(ValueError):
        await sched.run_calendar_pipeline_loop(poll_interval_seconds=0)


@pytest.mark.asyncio
async def test_scheduler_runs_pipeline_once(monkeypatch):
    called = {"pipeline": 0, "lock": 0}

    class _Lock:
        async def __aenter__(self):
            called["lock"] += 1

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Svc:
        async def refresh_pipeline(self, **kwargs):
            called["pipeline"] += 1
            assert kwargs["actor_source"] == "scheduler"
            return {"ok": True}

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(sched, "get_operation_lock", lambda _n: _Lock())
    monkeypatch.setattr(sched, "get_calendar_service", lambda: _Svc())
    monkeypatch.setattr(sched.asyncio, "sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await sched.run_calendar_pipeline_loop(poll_interval_seconds=1)

    assert called["lock"] == 1
    assert called["pipeline"] == 1


@pytest.mark.asyncio
async def test_scheduler_logs_and_continues_on_pipeline_exception(monkeypatch):
    called = {"pipeline": 0, "lock": 0, "sleep": 0}
    logged = {"exception": 0}

    class _Lock:
        async def __aenter__(self):
            called["lock"] += 1

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Svc:
        async def refresh_pipeline(self, **kwargs):
            called["pipeline"] += 1
            raise RuntimeError("boom")

    async def _sleep(_):
        called["sleep"] += 1
        raise asyncio.CancelledError

    monkeypatch.setattr(sched, "get_operation_lock", lambda _n: _Lock())
    monkeypatch.setattr(sched, "get_calendar_service", lambda: _Svc())
    monkeypatch.setattr(sched.asyncio, "sleep", _sleep)
    monkeypatch.setattr(
        sched.logger,
        "exception",
        lambda *args, **kwargs: logged.__setitem__("exception", logged["exception"] + 1),
    )

    with pytest.raises(asyncio.CancelledError):
        await sched.run_calendar_pipeline_loop(poll_interval_seconds=1)

    assert called["lock"] == 1
    assert called["pipeline"] == 1
    assert called["sleep"] == 1
    assert logged["exception"] == 1


@pytest.mark.asyncio
async def test_scheduler_does_not_use_outer_wait_for(monkeypatch):
    """
    Task 7 regression guard:
    scheduler loop must not wrap refresh_pipeline in asyncio.wait_for.
    """
    called = {"pipeline": 0}

    class _Lock:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Svc:
        async def refresh_pipeline(self, **kwargs):
            called["pipeline"] += 1
            return {"ok": True}

    async def _sleep(_):
        raise asyncio.CancelledError

    def _wait_for(*args, **kwargs):
        raise AssertionError("scheduler should not call asyncio.wait_for")

    monkeypatch.setattr(sched, "get_operation_lock", lambda _n: _Lock())
    monkeypatch.setattr(sched, "get_calendar_service", lambda: _Svc())
    monkeypatch.setattr(sched.asyncio, "sleep", _sleep)
    monkeypatch.setattr(sched.asyncio, "wait_for", _wait_for)

    with pytest.raises(asyncio.CancelledError):
        await sched.run_calendar_pipeline_loop(poll_interval_seconds=1)

    assert called["pipeline"] == 1


@pytest.mark.asyncio
async def test_daily_sequence_pipeline_then_embed(monkeypatch):
    import asyncio
    from datetime import UTC, datetime

    import bot_instance as bi

    order = []

    class _Svc:
        async def refresh_pipeline(self, **kwargs):
            order.append("pipeline")
            return {"ok": True}

    async def _upd(*args, **kwargs):
        order.append("embed")
        return {"ok": True}

    class _Lock:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            return False

    # Make scheduler think target is "now" so first sleep delay becomes 0.
    monkeypatch.setattr(bi, "utcnow", lambda: datetime(2026, 3, 9, 8, 5, 0, tzinfo=UTC))
    monkeypatch.setattr(bi, "get_calendar_service", lambda: _Svc())
    monkeypatch.setattr(bi, "update_calendar_embed", _upd)
    monkeypatch.setattr(bi, "CALENDAR_PINNED_CHANNEL_ID", 1)
    monkeypatch.setattr(bi, "get_operation_lock", lambda _n: _Lock(), raising=False)

    sleep_calls = {"n": 0}

    async def _sleep(_):
        sleep_calls["n"] += 1
        # first sleep = scheduling delay, allow it
        if sleep_calls["n"] == 1:
            return None
        # second sleep = next loop tick, stop test
        raise asyncio.CancelledError

    monkeypatch.setattr(bi.asyncio, "sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await bi.schedule_daily_pinned_calendar_refresh()

    assert order[:2] == ["pipeline", "embed"]
    assert order[2:4] == ["pipeline", "embed"]
