from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import Any

from constants import REMINDER_TRACKING_FILE
from event_cache import (
    get_all_upcoming_events,
    is_cache_stale,
    load_event_cache,
    refresh_event_cache,
)
from event_calendar.pinned_embed import rehydrate_pinned_calendar_view
from event_scheduler import load_active_reminders
from rehydrate_views import rehydrate_tracked_views

logger = logging.getLogger(__name__)

ScheduleBackground = Callable[[str, float, Callable[[], Awaitable[Any]]], Any]
TaskMonitorCreate = Callable[[str, Callable[[], Awaitable[Any]]], Any]
StartupCoroutine = Callable[[], Awaitable[Any]]


async def wait_for_events(timeout_seconds: int = 10) -> bool:
    """Return True once the event cache has upcoming events, otherwise False on timeout."""
    checks = int(max(1, timeout_seconds) * 10)
    for _ in range(checks):
        try:
            if get_all_upcoming_events():
                return True
        except Exception:
            logger.debug("[EVENT_CACHE] Upcoming-event readiness check failed", exc_info=True)
        await asyncio.sleep(0.1)
    return False


async def _start_event_tasks_when_ready(
    *,
    start_event_dependent_tasks: StartupCoroutine,
    max_wait_seconds: int,
) -> None:
    try:
        ready = await wait_for_events(timeout_seconds=max_wait_seconds)
        if not ready:
            logger.warning(
                "[BOOT] Event cache still not ready after %ss; "
                "skipping event-dependent task start for now.",
                max_wait_seconds,
            )
            return
        await start_event_dependent_tasks()
    except Exception:
        logger.exception("[BOOT] event_tasks_when_ready failed")


async def run_ready_event_cache_rehydration(
    *,
    bot: Any,
    schedule_bg: ScheduleBackground,
    task_monitor_create: TaskMonitorCreate,
    start_event_dependent_tasks: StartupCoroutine,
) -> set[Any]:
    """Load reminder/cache state and start the existing event-ready startup bundle."""
    logger.info("[REMINDER_CACHE] Attempting to load from %s", REMINDER_TRACKING_FILE)
    loaded_ids = await load_active_reminders(bot)

    try:
        load_event_cache()
        logger.info("[EVENT_CACHE] Loaded cache from disk")
        if is_cache_stale() or not get_all_upcoming_events():
            logger.info("[EVENT_CACHE] Cache was stale or empty; refreshing from GSheet")
            await refresh_event_cache()

        try:
            count = len(get_all_upcoming_events() or [])
            logger.info("[EVENT_CACHE] Ready with %s upcoming events.", count)
        except Exception:
            logger.info("[EVENT_CACHE] Ready; but could not count events.")
    except Exception:
        logger.exception("[STARTUP] Failed to load or refresh event cache")

    schedule_bg("refresh_event_cache_once", 10.0, lambda: refresh_event_cache())

    ready = await wait_for_events(10)
    if ready:
        logger.info(
            "[BOOT] Starting current event-dependent task bundle; scheduler ownership "
            "split is deferred to Phase 6G."
        )
        await start_event_dependent_tasks()
    else:
        logger.warning(
            "[BOOT] Event cache not ready; will wait in background and start "
            "event-dependent tasks when populated."
        )
        task_monitor_create(
            "event_tasks_when_ready",
            lambda: _start_event_tasks_when_ready(
                start_event_dependent_tasks=start_event_dependent_tasks,
                max_wait_seconds=300,
            ),
        )

    return set(loaded_ids or set())


async def run_ready_tracked_view_rehydration(
    *,
    bot: Any,
    schedule_bg: ScheduleBackground,
) -> None:
    try:
        schedule_bg("rehydrate_tracked_views", 10.0, lambda: rehydrate_tracked_views(bot))
        logger.info("[BOOT] View tracker rehydration scheduled")
    except Exception:
        logger.exception("[BOOT] Failed to start rehydrate_tracked_views")


async def run_ready_pinned_calendar_rehydration(
    *,
    bot: Any,
    schedule_bg: ScheduleBackground,
) -> None:
    try:
        schedule_bg(
            "rehydrate_pinned_calendar_view",
            8.0,
            lambda: rehydrate_pinned_calendar_view(bot),
        )
        logger.info("[BOOT] pinned calendar view rehydration scheduled")
    except Exception:
        logger.exception("[BOOT] failed to schedule pinned calendar rehydration")
