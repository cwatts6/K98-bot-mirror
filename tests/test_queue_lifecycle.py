from __future__ import annotations

import asyncio

import pytest

from core.queue_lifecycle import run_ready_queue_lifecycle


@pytest.mark.asyncio
async def test_queue_lifecycle_registers_workers_loads_queue_and_starts_loops():
    calls: list[str] = []
    bot = object()

    def create(name, factory, **_kwargs):
        calls.append(f"create:{name}")
        assert callable(factory)

    async def queue_worker(channel_id: int) -> None:
        calls.append(f"worker:{channel_id}")

    def load_live_queue() -> None:
        calls.append("load")

    async def update_live_queue_embed(_bot, notify_channel_id: int) -> None:
        assert _bot is bot
        calls.append(f"embed:{notify_channel_id}")

    async def queue_cleanup_loop() -> None:
        calls.append("cleanup")

    async def connection_watchdog(_bot) -> None:
        assert _bot is bot
        calls.append("watchdog")

    await run_ready_queue_lifecycle(
        channel_ids=[10, 20],
        task_monitor_create=create,
        queue_worker=queue_worker,
        load_live_queue=load_live_queue,
        update_live_queue_embed=update_live_queue_embed,
        bot=bot,
        notify_channel_id=99,
        queue_cleanup_loop=queue_cleanup_loop,
        connection_watchdog=connection_watchdog,
    )

    assert calls == [
        "create:queue_worker:10",
        "create:queue_worker:20",
        "load",
        "embed:99",
        "create:queue_cleanup",
        "create:connection_watchdog",
    ]


@pytest.mark.asyncio
async def test_queue_lifecycle_awaits_live_queue_load_before_embed_refresh():
    calls: list[str] = []
    load_can_finish = asyncio.Event()

    def create(_name, _factory, **_kwargs):
        return object()

    async def load_live_queue() -> None:
        calls.append("load:start")
        await load_can_finish.wait()
        calls.append("load:done")

    async def update_live_queue_embed(_bot, _notify_channel_id: int) -> None:
        calls.append("embed")

    async def noop() -> None:
        return None

    task = asyncio.create_task(
        run_ready_queue_lifecycle(
            channel_ids=[10],
            task_monitor_create=create,
            queue_worker=lambda _channel_id: noop(),
            load_live_queue=load_live_queue,
            update_live_queue_embed=update_live_queue_embed,
            bot=object(),
            notify_channel_id=99,
            queue_cleanup_loop=noop,
            connection_watchdog=lambda _bot: noop(),
        )
    )

    await asyncio.sleep(0)
    assert calls == ["load:start"]

    load_can_finish.set()
    await task

    assert calls == ["load:start", "load:done", "embed"]


@pytest.mark.asyncio
async def test_queue_lifecycle_embed_refresh_failure_is_best_effort(caplog):
    caplog.set_level("ERROR", logger="core.queue_lifecycle")
    calls: list[str] = []

    def create(name, factory, **_kwargs):
        calls.append(f"create:{name}")

    async def queue_worker(_channel_id: int) -> None:
        return None

    def load_live_queue() -> None:
        calls.append("load")

    async def update_live_queue_embed(_bot, _notify_channel_id: int) -> None:
        calls.append("embed")
        raise RuntimeError("discord unavailable")

    async def queue_cleanup_loop() -> None:
        return None

    async def connection_watchdog(_bot) -> None:
        return None

    await run_ready_queue_lifecycle(
        channel_ids=[10],
        task_monitor_create=create,
        queue_worker=queue_worker,
        load_live_queue=load_live_queue,
        update_live_queue_embed=update_live_queue_embed,
        bot=object(),
        notify_channel_id=99,
        queue_cleanup_loop=queue_cleanup_loop,
        connection_watchdog=connection_watchdog,
    )

    assert calls == [
        "create:queue_worker:10",
        "load",
        "embed",
        "create:queue_cleanup",
        "create:connection_watchdog",
    ]
    assert "Failed to update live queue embed during startup" in caplog.text


@pytest.mark.asyncio
async def test_queue_lifecycle_preserves_task_monitor_duplicate_prevention_contract():
    created: list[str] = []
    skipped: list[str] = []
    running = {"queue_worker:10", "queue_cleanup", "connection_watchdog"}

    def create(name, factory, **_kwargs):
        if name in running:
            skipped.append(name)
            return object()
        created.append(name)
        return factory

    async def noop_worker(_channel_id: int) -> None:
        return None

    async def noop() -> None:
        return None

    await run_ready_queue_lifecycle(
        channel_ids=[10, 20],
        task_monitor_create=create,
        queue_worker=noop_worker,
        load_live_queue=lambda: None,
        update_live_queue_embed=lambda _bot, _notify_channel_id: noop(),
        bot=object(),
        notify_channel_id=99,
        queue_cleanup_loop=noop,
        connection_watchdog=lambda _bot: noop(),
    )

    assert skipped == ["queue_worker:10", "queue_cleanup", "connection_watchdog"]
    assert created == ["queue_worker:20"]
