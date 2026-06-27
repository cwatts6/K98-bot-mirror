import asyncio

import pytest

import file_utils

pytestmark = pytest.mark.asyncio


async def test_run_step_delegates_to_run_blocking_in_thread(monkeypatch):
    calls = []

    async def fake_run_blocking(func, *args, name=None, meta=None, timeout=None, **kwargs):
        # simulate the real behaviour: run sync func in thread and return result
        calls.append({"name": name, "meta": meta, "func": func})
        # If func is callable, run it synchronously here for test simplicity
        return func(*args, **kwargs)

    monkeypatch.setattr(file_utils, "run_blocking_in_thread", fake_run_blocking)

    def sync_fn(x, y=0):
        return x + y

    res = await file_utils.run_step(sync_fn, 2, y=3, name="test_sync", meta={"k": "v"})
    assert res == 5
    assert calls and calls[0]["name"] == "test_sync"

    # test coroutine function path - should be awaited directly
    async def coro_fn(a, b=0):
        await asyncio.sleep(0)
        return a * b

    res2 = await file_utils.run_step(coro_fn, 4, b=5, name="test_coro", meta={"m": "n"})
    assert res2 == 20


async def test_run_step_emits_failure_telemetry(monkeypatch):
    evts = []

    def fake_emit(payload, *, max_snippet=2000):
        evts.append(payload)

    monkeypatch.setattr(file_utils, "emit_telemetry_event", fake_emit)

    async def raising_coro():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await file_utils.run_step(raising_coro, name="failing")

    assert any(
        evt.get("event") == "run_step.failed" or "run_step.failed" in str(evt) for evt in evts
    )
