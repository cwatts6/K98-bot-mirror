from __future__ import annotations

import asyncio

import pytest

from event_calendar import scheduler as sched


@pytest.mark.asyncio
async def test_scheduler_runs_refresh_full_once(monkeypatch):
    called = {"refresh_full": 0, "lock": 0}

    class _Lock:
        async def __aenter__(self):
            called["lock"] += 1

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Svc:
        async def refresh_full(self, **kwargs):
            called["refresh_full"] += 1
            return {"ok": True}

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(sched, "get_operation_lock", lambda _n: _Lock())
    monkeypatch.setattr(sched, "get_calendar_service", lambda: _Svc())
    monkeypatch.setattr(sched.asyncio, "sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await sched.run_calendar_pipeline_loop(poll_interval_seconds=1)

    assert called["lock"] == 1
    assert called["refresh_full"] == 1
