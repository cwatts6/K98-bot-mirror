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
from voting.rehydration import rehydrate_vote_post_views

logger = logging.getLogger(__name__)

ScheduleBackground = Callable[[str, float, Callable[[], Awaitable[Any]]], Any]


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


async def run_ready_event_cache_rehydration(
    *,
    bot: Any,
    schedule_bg: ScheduleBackground,
) -> set[Any]:
    """Load reminder/cache state and schedule the one-shot cache refresh."""
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
    try:
        schedule_bg("rehydrate_vote_post_views", 10.0, lambda: rehydrate_vote_post_views(bot))
        logger.info("[BOOT] Vote post view rehydration scheduled")
    except Exception:
        logger.exception("[BOOT] Failed to start rehydrate_vote_post_views")


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
