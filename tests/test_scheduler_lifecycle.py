from __future__ import annotations

import pytest

from core import scheduler_lifecycle as lifecycle


class _LoopTask:
    def __init__(self, *, running: bool = False) -> None:
        self.running = running
        self.started = 0

    def is_running(self) -> bool:
        return self.running

    def start(self) -> None:
        self.started += 1
        self.running = True


@pytest.mark.asyncio
async def test_event_scheduler_tasks_start_when_events_are_ready():
    calls: list[str] = []

    async def wait_for_events(seconds: int) -> bool:
        calls.append(f"wait:{seconds}")
        return True

    async def start_tasks() -> None:
        calls.append("start")

    def create(*_args, **_kwargs):
        calls.append("create")

    await lifecycle.run_ready_event_scheduler_tasks(
        start_event_scheduler_tasks=start_tasks,
        wait_for_events=wait_for_events,
        task_monitor_create=create,
    )

    assert calls == ["wait:10", "start"]


@pytest.mark.asyncio
async def test_event_scheduler_tasks_defer_until_ready_when_cache_is_empty():
    calls: list[str] = []
    scheduled = {}

    async def wait_for_events(seconds: int) -> bool:
        calls.append(f"wait:{seconds}")
        return False

    async def start_tasks() -> None:
        calls.append("start")

    def create(name, factory, **_kwargs):
        scheduled["name"] = name
        scheduled["factory"] = factory
        calls.append(f"create:{name}")

    await lifecycle.run_ready_event_scheduler_tasks(
        start_event_scheduler_tasks=start_tasks,
        wait_for_events=wait_for_events,
        task_monitor_create=create,
    )

    assert calls == ["wait:10", "create:event_tasks_when_ready"]
    assert scheduled["name"] == "event_tasks_when_ready"
    assert callable(scheduled["factory"])


@pytest.mark.asyncio
async def test_domain_scheduler_tasks_register_in_existing_order():
    calls: list[str] = []

    def create(name, factory, **kwargs):
        calls.append(f"create:{name}:{kwargs.get('replace')}")
        assert callable(factory)

    def is_running(name: str) -> bool:
        calls.append(f"is_running:{name}")
        return False

    async def ark() -> None:
        return None

    async def mge_cache() -> None:
        return None

    async def mge() -> None:
        return None

    await lifecycle.run_ready_domain_scheduler_tasks(
        task_monitor_create=create,
        task_monitor_is_running=is_running,
        schedule_ark_lifecycle=ark,
        refresh_mge_caches_on_startup=mge_cache,
        schedule_mge_lifecycle=mge,
    )

    assert calls == [
        "create:ark_scheduler:None",
        "is_running:refresh_mge_caches_on_startup",
        "create:refresh_mge_caches_on_startup:False",
        "is_running:mge_lifecycle",
        "create:mge_lifecycle:False",
    ]


@pytest.mark.asyncio
async def test_domain_scheduler_tasks_skip_duplicate_mge_tasks():
    calls: list[str] = []

    def create(name, factory, **kwargs):
        calls.append(f"create:{name}:{kwargs.get('replace')}")

    def is_running(name: str) -> bool:
        calls.append(f"is_running:{name}")
        return name in {"refresh_mge_caches_on_startup", "mge_lifecycle"}

    async def noop() -> None:
        return None

    await lifecycle.run_ready_domain_scheduler_tasks(
        task_monitor_create=create,
        task_monitor_is_running=is_running,
        schedule_ark_lifecycle=noop,
        refresh_mge_caches_on_startup=noop,
        schedule_mge_lifecycle=noop,
    )

    assert calls == [
        "create:ark_scheduler:None",
        "is_running:refresh_mge_caches_on_startup",
        "is_running:mge_lifecycle",
    ]


@pytest.mark.asyncio
async def test_domain_scheduler_tasks_register_voting_lifecycle_when_provided():
    calls: list[str] = []

    def create(name, factory, **kwargs):
        calls.append(f"create:{name}:{kwargs.get('replace')}")
        assert callable(factory)

    def is_running(name: str) -> bool:
        calls.append(f"is_running:{name}")
        return False

    async def noop() -> None:
        return None

    await lifecycle.run_ready_domain_scheduler_tasks(
        task_monitor_create=create,
        task_monitor_is_running=is_running,
        schedule_ark_lifecycle=noop,
        refresh_mge_caches_on_startup=noop,
        schedule_mge_lifecycle=noop,
        schedule_voting_lifecycle=noop,
    )

    assert calls == [
        "create:ark_scheduler:None",
        "is_running:refresh_mge_caches_on_startup",
        "create:refresh_mge_caches_on_startup:False",
        "is_running:mge_lifecycle",
        "create:mge_lifecycle:False",
        "is_running:voting_lifecycle",
        "create:voting_lifecycle:False",
    ]


@pytest.mark.asyncio
async def test_calendar_scheduler_tasks_register_and_skip_duplicate_loop():
    calls: list[str] = []

    def create(name, factory, **kwargs):
        calls.append(f"create:{name}:{kwargs.get('replace')}")
        assert callable(factory)

    def is_running(name: str) -> bool:
        calls.append(f"is_running:{name}")
        return False

    async def noop() -> None:
        return None

    await lifecycle.run_ready_calendar_scheduler_tasks(
        task_monitor_create=create,
        task_monitor_is_running=is_running,
        schedule_daily_pinned_calendar_refresh=noop,
        calendar_reminder_task=noop,
    )

    assert calls == [
        "create:daily_pinned_calendar_refresh:None",
        "is_running:calendar_reminder_loop",
        "create:calendar_reminder_loop:False",
    ]


@pytest.mark.asyncio
async def test_scheduler_registration_failures_are_best_effort(caplog):
    def create(_name, _factory, **_kwargs):
        raise RuntimeError("monitor unavailable")

    async def noop() -> None:
        return None

    await lifecycle.run_ready_domain_scheduler_tasks(
        task_monitor_create=create,
        task_monitor_is_running=lambda _name: False,
        schedule_ark_lifecycle=noop,
        refresh_mge_caches_on_startup=noop,
        schedule_mge_lifecycle=noop,
    )

    assert "Failed to start Ark scheduler" in caplog.text
    assert "Failed to schedule MGE cache refresh" in caplog.text
    assert "Failed to start MGE scheduler" in caplog.text


@pytest.mark.asyncio
async def test_event_cache_refresh_loop_starts_at_dedicated_boundary():
    refresh_loop = _LoopTask()

    await lifecycle.start_event_cache_refresh_loop(refresh_event_cache_task=refresh_loop)

    assert refresh_loop.started == 1


@pytest.mark.asyncio
async def test_event_cache_refresh_loop_skips_when_already_running():
    refresh_loop = _LoopTask(running=True)

    await lifecycle.start_event_cache_refresh_loop(refresh_event_cache_task=refresh_loop)

    assert refresh_loop.started == 0
