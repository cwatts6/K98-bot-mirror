from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from typing import Any

logger = logging.getLogger(__name__)

StartupCoroutine = Callable[[], Awaitable[Any]]
TaskMonitorCreate = Callable[..., Any]
TaskMonitorIsRunning = Callable[[str], bool]


async def _start_event_tasks_when_ready(
    *,
    start_event_scheduler_tasks: StartupCoroutine,
    wait_for_events: Callable[[int], Awaitable[bool]],
    max_wait_seconds: int,
) -> None:
    try:
        ready = await wait_for_events(max_wait_seconds)
        if not ready:
            logger.warning(
                "[BOOT] Event cache still not ready after %ss; "
                "skipping event-dependent scheduler start for now.",
                max_wait_seconds,
            )
            return
        await start_event_scheduler_tasks()
    except Exception:
        logger.exception("[BOOT] event_tasks_when_ready failed")


async def run_ready_event_scheduler_tasks(
    *,
    start_event_scheduler_tasks: StartupCoroutine,
    wait_for_events: Callable[[int], Awaitable[bool]],
    task_monitor_create: TaskMonitorCreate,
    ready_wait_seconds: int = 10,
    deferred_wait_seconds: int = 300,
) -> None:
    """Start event-cache-dependent scheduler tasks after event readiness."""
    ready = await wait_for_events(ready_wait_seconds)
    if ready:
        logger.info("[BOOT] Starting event-dependent scheduler task bundle.")
        await start_event_scheduler_tasks()
        return

    logger.warning(
        "[BOOT] Event cache not ready; will wait in background and start "
        "event-dependent scheduler tasks when populated."
    )
    task_monitor_create(
        "event_tasks_when_ready",
        lambda: _start_event_tasks_when_ready(
            start_event_scheduler_tasks=start_event_scheduler_tasks,
            wait_for_events=wait_for_events,
            max_wait_seconds=deferred_wait_seconds,
        ),
    )


async def run_ready_domain_scheduler_tasks(
    *,
    task_monitor_create: TaskMonitorCreate,
    task_monitor_is_running: TaskMonitorIsRunning,
    schedule_ark_lifecycle: StartupCoroutine,
    refresh_mge_caches_on_startup: StartupCoroutine,
    schedule_mge_lifecycle: StartupCoroutine,
    schedule_voting_lifecycle: StartupCoroutine | None = None,
) -> None:
    """Register domain scheduler tasks that run after event/view readiness."""
    try:
        task_monitor_create("ark_scheduler", schedule_ark_lifecycle)
        logger.info("[BOOT] Ark scheduler started")
    except Exception:
        logger.exception("[BOOT] Failed to start Ark scheduler")

    try:
        if not task_monitor_is_running("refresh_mge_caches_on_startup"):
            task_monitor_create(
                "refresh_mge_caches_on_startup",
                refresh_mge_caches_on_startup,
                replace=False,
            )
            logger.info("[BOOT] MGE cache refresh scheduled")
        else:
            logger.info("[BOOT] MGE cache refresh already running")
    except Exception:
        logger.exception("[BOOT] Failed to schedule MGE cache refresh")

    try:
        if not task_monitor_is_running("mge_lifecycle"):
            task_monitor_create(
                "mge_lifecycle",
                schedule_mge_lifecycle,
                replace=False,
            )
            logger.info("[BOOT] MGE scheduler started")
        else:
            logger.info("[BOOT] MGE scheduler already running")
    except Exception:
        logger.exception("[BOOT] Failed to start MGE scheduler")

    if schedule_voting_lifecycle is None:
        return

    try:
        if not task_monitor_is_running("voting_lifecycle"):
            task_monitor_create(
                "voting_lifecycle",
                schedule_voting_lifecycle,
                replace=False,
            )
            logger.info("[BOOT] Voting scheduler started")
        else:
            logger.info("[BOOT] Voting scheduler already running")
    except Exception:
        logger.exception("[BOOT] Failed to start Voting scheduler")


async def start_event_cache_refresh_loop(*, refresh_event_cache_task: Any) -> None:
    """Start the long-running event cache refresh loop at its existing startup point."""
    try:
        if not refresh_event_cache_task.is_running():
            refresh_event_cache_task.start()
        else:
            logger.info("[BOOT] refresh_event_cache_task already running; skipping start.")
    except Exception:
        logger.exception("[BOOT] Failed to start refresh_event_cache_task")


async def start_legacy_reminder_cleanup(
    *,
    task_monitor_create: TaskMonitorCreate,
    reminder_cleanup_loop: StartupCoroutine,
) -> None:
    """Register the legacy reminder cleanup loop at its existing startup point."""
    try:
        task_monitor_create("reminder_cleanup", reminder_cleanup_loop)
        logger.info("[BOOT] Reminder cleanup task started")
    except Exception:
        logger.exception("[BOOT] Failed to start reminder_cleanup_loop")


async def run_ready_calendar_scheduler_tasks(
    *,
    task_monitor_create: TaskMonitorCreate,
    task_monitor_is_running: TaskMonitorIsRunning,
    schedule_daily_pinned_calendar_refresh: StartupCoroutine,
    calendar_reminder_task: StartupCoroutine,
) -> None:
    """Register calendar scheduler tasks that run after pinned calendar rehydration."""
    try:
        task_monitor_create(
            "daily_pinned_calendar_refresh",
            schedule_daily_pinned_calendar_refresh,
        )
        logger.info("[BOOT] daily pinned calendar refresh started")
    except Exception:
        logger.exception("[BOOT] failed to start daily pinned calendar refresh")

    try:
        if not task_monitor_is_running("calendar_reminder_loop"):
            task_monitor_create(
                "calendar_reminder_loop",
                calendar_reminder_task,
                replace=False,
            )
            logger.info("[CALENDAR][REMINDER] reminder loop armed")
        else:
            logger.info("[CALENDAR][REMINDER] reminder loop already running; skipping")
    except Exception:
        logger.exception("[BOOT] failed to start calendar reminder loop")
