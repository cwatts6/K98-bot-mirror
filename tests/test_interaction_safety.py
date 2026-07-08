# tests/test_interaction_safety.py

import asyncio
import logging

from core.interaction_safety import get_operation_lock, safe_command, safe_defer


class _Response:
    def __init__(self, done=False):
        self._done = done
        self.defer_calls = []

    def is_done(self):
        return self._done

    async def defer(self, *, ephemeral=True):
        self.defer_calls.append(ephemeral)
        self._done = True


class _Followup:
    def __init__(self):
        self.messages = []

    async def send(self, message, ephemeral=True):
        self.messages.append((message, ephemeral))


class _Ctx:
    def __init__(self, response_done=False, has_respond=True):
        self.interaction = type("I", (), {})()
        self.interaction.response = _Response(done=response_done)
        self.followup = _Followup()
        self.interaction.followup = self.followup
        self.respond_calls = []
        if has_respond:
            self.respond = self._respond

    async def _respond(self, message, ephemeral=True):
        self.respond_calls.append((message, ephemeral))


def test_safe_defer_idempotence_when_already_done_and_no_ctx_defer():
    ctx = _Ctx(response_done=True)
    ok = asyncio.run(safe_defer(ctx, ephemeral=True))
    assert ok is False
    assert ctx.interaction.response.defer_calls == []


def test_safe_command_catches_and_logs_exceptions(caplog):
    caplog.set_level(logging.ERROR)
    ctx = _Ctx(response_done=False, has_respond=True)

    @safe_command
    async def boom(c):
        raise RuntimeError("kaboom")

    result = asyncio.run(boom(ctx))
    assert result is None
    assert any("[CMD ERROR]" in rec.message for rec in caplog.records)
    assert ctx.respond_calls == [("⚠️ Something went wrong. The team has been notified.", True)]


def test_op_lock_prevents_concurrent_execution_same_key():
    lock = get_operation_lock("test_interaction_safety_lock")

    order = []

    async def worker(name):
        async with lock:
            order.append(f"start-{name}")
            await asyncio.sleep(0.03)
            order.append(f"end-{name}")

    async def _run():
        await asyncio.gather(worker("a"), worker("b"))

    asyncio.run(_run())

    # Mutex should serialize sections: second start appears only after first end.
    assert order in (
        ["start-a", "end-a", "start-b", "end-b"],
        ["start-b", "end-b", "start-a", "end-a"],
    )
