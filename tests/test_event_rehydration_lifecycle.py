from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core import event_rehydration_lifecycle as lifecycle


@pytest.mark.asyncio
async def test_ready_event_cache_rehydration_refreshes_and_starts_event_bundle(monkeypatch):
    calls: list[str] = []

    async def fake_load_active_reminders(_bot):
        calls.append("load_active_reminders")
        return {"event-1"}

    async def fake_refresh_event_cache():
        calls.append("refresh_event_cache")
        return 1

    async def fake_start_event_dependent_tasks():
        calls.append("start_event_dependent_tasks")

    def fake_schedule_bg(name, timeout, coro_factory):
        calls.append(f"schedule_bg:{name}:{timeout}")
        assert callable(coro_factory)

    def fake_task_monitor_create(name, factory):
        calls.append(f"task_monitor:{name}")

    monkeypatch.setattr(lifecycle, "load_active_reminders", fake_load_active_reminders)
    monkeypatch.setattr(lifecycle, "load_event_cache", lambda: calls.append("load_event_cache"))
    monkeypatch.setattr(lifecycle, "is_cache_stale", lambda: True)
    monkeypatch.setattr(lifecycle, "get_all_upcoming_events", lambda: [{"name": "Ready"}])
    monkeypatch.setattr(lifecycle, "refresh_event_cache", fake_refresh_event_cache)
    monkeypatch.setattr(lifecycle, "wait_for_events", AsyncMock(return_value=True))

    loaded = await lifecycle.run_ready_event_cache_rehydration(
        bot=object(),
        schedule_bg=fake_schedule_bg,
        task_monitor_create=fake_task_monitor_create,
        start_event_dependent_tasks=fake_start_event_dependent_tasks,
    )

    assert loaded == {"event-1"}
    assert calls == [
        "load_active_reminders",
        "load_event_cache",
        "refresh_event_cache",
        "schedule_bg:refresh_event_cache_once:10.0",
        "start_event_dependent_tasks",
    ]


@pytest.mark.asyncio
async def test_ready_event_cache_rehydration_defers_event_bundle_until_ready(monkeypatch):
    calls: list[str] = []
    scheduled: dict[str, object] = {}

    async def fake_load_active_reminders(_bot):
        return set()

    async def fake_start_event_dependent_tasks():
        calls.append("start_event_dependent_tasks")

    def fake_schedule_bg(name, timeout, coro_factory):
        calls.append(f"schedule_bg:{name}:{timeout}")

    def fake_task_monitor_create(name, factory):
        scheduled["name"] = name
        scheduled["factory"] = factory
        calls.append(f"task_monitor:{name}")

    monkeypatch.setattr(lifecycle, "load_active_reminders", fake_load_active_reminders)
    monkeypatch.setattr(lifecycle, "load_event_cache", lambda: None)
    monkeypatch.setattr(lifecycle, "is_cache_stale", lambda: False)
    monkeypatch.setattr(lifecycle, "get_all_upcoming_events", lambda: [])

    async def fake_refresh_event_cache():
        calls.append("refresh_event_cache")
        return 0

    monkeypatch.setattr(lifecycle, "refresh_event_cache", fake_refresh_event_cache)
    monkeypatch.setattr(lifecycle, "wait_for_events", AsyncMock(return_value=False))

    loaded = await lifecycle.run_ready_event_cache_rehydration(
        bot=object(),
        schedule_bg=fake_schedule_bg,
        task_monitor_create=fake_task_monitor_create,
        start_event_dependent_tasks=fake_start_event_dependent_tasks,
    )

    assert loaded == set()
    assert calls == [
        "refresh_event_cache",
        "schedule_bg:refresh_event_cache_once:10.0",
        "task_monitor:event_tasks_when_ready",
    ]
    assert scheduled["name"] == "event_tasks_when_ready"
    assert callable(scheduled["factory"])


@pytest.mark.asyncio
async def test_ready_view_rehydration_helpers_schedule_expected_tasks(monkeypatch):
    calls: list[tuple[str, float]] = []

    def fake_schedule_bg(name, timeout, coro_factory):
        calls.append((name, timeout))
        assert callable(coro_factory)

    await lifecycle.run_ready_tracked_view_rehydration(bot=object(), schedule_bg=fake_schedule_bg)
    await lifecycle.run_ready_pinned_calendar_rehydration(
        bot=object(), schedule_bg=fake_schedule_bg
    )

    assert calls == [
        ("rehydrate_tracked_views", 10.0),
        ("rehydrate_pinned_calendar_view", 8.0),
    ]


@pytest.mark.asyncio
async def test_tracked_view_rehydration_schedule_failure_is_best_effort(caplog):
    def fail_schedule_bg(name, timeout, coro_factory):
        raise RuntimeError("scheduler unavailable")

    await lifecycle.run_ready_tracked_view_rehydration(
        bot=object(),
        schedule_bg=fail_schedule_bg,
    )

    assert "Failed to start rehydrate_tracked_views" in caplog.text


@pytest.mark.asyncio
async def test_pinned_calendar_rehydration_schedule_failure_is_best_effort(caplog):
    def fail_schedule_bg(name, timeout, coro_factory):
        raise RuntimeError("scheduler unavailable")

    await lifecycle.run_ready_pinned_calendar_rehydration(
        bot=object(),
        schedule_bg=fail_schedule_bg,
    )

    assert "failed to schedule pinned calendar rehydration" in caplog.text
