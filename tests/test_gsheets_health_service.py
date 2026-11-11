import asyncio
import threading

import pytest

from services.gsheets_health_service import HealthProbe


@pytest.mark.asyncio
async def test_slow_admission_retains_worker_and_delivers_late_result():
    entered, release = threading.Event(), threading.Event()
    calls = []
    now = [0.0]
    probe = HealthProbe(clock=lambda: now[0])

    def work():
        calls.append(1)
        entered.set()
        release.wait(5)
        return True, "closed and released"

    async def run():
        return await asyncio.to_thread(work)

    try:
        assert (await probe.observe(run, timeout=0.01))[0] is None
        assert entered.is_set()
        now[0] = 5.5  # Admission may take longer than the UI's five-second wait.
        assert (await probe.observe(run, timeout=0.01))[0] is None
        assert calls == [1]
        release.set()
        assert await probe.observe(run, timeout=1) == (True, "closed and released")
        assert calls == [1]
    finally:
        release.set()


@pytest.mark.asyncio
async def test_cancelled_observer_does_not_cancel_or_replace_probe():
    done = asyncio.Event()
    calls = []
    probe = HealthProbe()

    async def run():
        calls.append(1)
        await done.wait()
        return False, "real authority failure"

    observer = asyncio.create_task(probe.observe(run, timeout=20))
    await asyncio.sleep(0)
    observer.cancel()
    with pytest.raises(asyncio.CancelledError):
        await observer
    done.set()
    assert await probe.observe(run, timeout=1) == (False, "real authority failure")
    assert calls == [1]


@pytest.mark.asyncio
async def test_stalled_probe_alerts_but_never_starts_a_second_operation():
    done = asyncio.Event()
    calls = []
    now = [0.0]
    probe = HealthProbe(clock=lambda: now[0])

    async def run():
        calls.append(1)
        await done.wait()
        return True, "done"

    assert (await probe.observe(run, timeout=0.001))[0] is None
    now[0] = 301
    assert (await probe.observe(run, timeout=0.001))[0] is False
    assert (await probe.observe(run, timeout=0.001))[0] is False
    assert calls == [1]
    done.set()
    assert (await probe.observe(run, timeout=1))[0] is True


@pytest.mark.asyncio
async def test_exception_is_failed_without_logging_payload(caplog):
    probe = HealthProbe()

    async def run():
        raise RuntimeError("SECRET")

    assert (await probe.observe(run, timeout=1))[0] is False
    assert "SECRET" not in caplog.text


def test_health_consumers_distinguish_deferred_from_failed():
    # Importing the bot creates Discord infrastructure; inspect its two UI
    # consumers to guard the tri-state integration without starting a bot.
    import ast
    from pathlib import Path

    tree = ast.parse(Path("bot_instance.py").read_text(encoding="utf-8"))
    consumers = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.UnaryOp)
        and isinstance(n.op, ast.Not)
        and isinstance(n.operand, ast.Name)
        and n.operand.id == "gs_ok"
    ]
    assert not consumers
