"""Fallback monitored-channel queue route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from asyncio import QueueFull
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any

from upload_routes.common import schedule_best_effort

logger = logging.getLogger(__name__)

SUPPORTED_FALLBACK_EXTENSIONS = (".xlsx", ".xls", ".csv")


@dataclass(frozen=True)
class FallbackQueueRouteDeps:
    channel_ids: set[int] | list[int] | tuple[int, ...]
    channel_queues: Mapping[int, Any]
    live_queue: dict[str, Any]
    live_queue_lock: Any
    bot: Any
    notify_channel_id: int
    update_live_queue_embed: Callable[[Any, int], Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    utcnow: Callable[[], Any]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task


async def handle_fallback_queue_upload(message: Any, deps: FallbackQueueRouteDeps) -> bool:
    """Queue supported attachments from monitored channels for worker processing."""
    if message.channel.id not in deps.channel_ids:
        return False

    logger.info("✅ Channel %s is monitored.", message.channel.id)

    for attachment in message.attachments:
        logger.info("📎 Attachment: %s", attachment.filename)
        if not attachment.filename.lower().endswith(SUPPORTED_FALLBACK_EXTENSIONS):
            continue

        logger.info("📥 Enqueuing message %s for worker", message.id)
        queue = deps.channel_queues.get(message.channel.id)
        if not queue:
            logger.warning(
                "No queue configured for channel %s; message %s not enqueued",
                message.channel.id,
                message.id,
            )
            continue

        try:
            queue.put_nowait(message)
        except QueueFull:
            logger.warning(
                "⚠️ Queue full for channel %s; dropping message %s",
                message.channel.id,
                message.id,
            )
        else:
            try:
                async with deps.live_queue_lock:
                    deps.live_queue["jobs"].append(
                        {
                            "filename": attachment.filename,
                            "user": str(message.author),
                            "channel": message.channel.name,
                            "uploaded": deps.utcnow().isoformat(),
                            "status": "🕐 Queued",
                        }
                    )
            except Exception:
                logger.debug("Failed to append to live_queue (continuing)", exc_info=True)

            try:
                await deps.update_live_queue_embed(deps.bot, deps.notify_channel_id)
            except Exception:
                logger.exception("Failed to update live queue embed")

            try:
                backup_task = deps.trigger_log_backup_background()
            except Exception:
                logger.exception(
                    "Failed to schedule background log-backup trigger for queued import"
                )
            else:
                schedule_best_effort(
                    deps.create_task,
                    backup_task,
                    logger,
                    "Failed to schedule background log-backup trigger for queued import",
                )

    return True
