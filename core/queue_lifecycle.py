from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
import logging
from typing import Any

logger = logging.getLogger(__name__)

StartupCoroutine = Callable[[], Awaitable[Any]]
TaskMonitorCreate = Callable[..., Any]


async def run_ready_queue_lifecycle(
    *,
    channel_ids: Iterable[int],
    task_monitor_create: TaskMonitorCreate,
    queue_worker: Callable[[int], Awaitable[Any]],
    load_live_queue: Callable[[], Any],
    update_live_queue_embed: Callable[[Any, int], Awaitable[Any]],
    bot: Any,
    notify_channel_id: int,
    queue_cleanup_loop: StartupCoroutine,
    connection_watchdog: Callable[[Any], Awaitable[Any]],
) -> None:
    """Register queue workers and recover live queue state at the existing startup point."""
    for channel_id in channel_ids:
        task_monitor_create(
            f"queue_worker:{channel_id}",
            lambda channel_id=channel_id: queue_worker(channel_id),
        )
    logger.info("[QUEUE] Queue workers registered for monitored channels.")

    load_live_queue()
    logger.info("[QUEUE] Live queue state load requested.")

    try:
        await update_live_queue_embed(bot, notify_channel_id)
        logger.info("[QUEUE] Live queue embed refresh completed.")
    except Exception:
        logger.exception("[QUEUE] Failed to update live queue embed during startup")

    task_monitor_create("queue_cleanup", queue_cleanup_loop)
    logger.info("[QUEUE] Queue cleanup task registered.")

    task_monitor_create("connection_watchdog", lambda: connection_watchdog(bot))
    logger.info("[QUEUE] Connection watchdog task registered.")
