"""Fallback monitored-channel queue route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from asyncio import QueueFull
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any

from services.fallback_queue_item import FallbackQueueItem
from services.upload_lifecycle import tracked_upload
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


@tracked_upload
async def handle_fallback_queue_upload(message: Any, deps: FallbackQueueRouteDeps) -> bool:
    """Queue supported attachments from monitored channels for worker processing."""
    if message.channel.id not in deps.channel_ids:
        return False

    logger.info("✅ Channel %s is monitored.", message.channel.id)

    attachments = tuple(
        a for a in message.attachments if a.filename.lower().endswith(SUPPORTED_FALLBACK_EXTENSIONS)
    )
    if not attachments:
        return True
    queue = deps.channel_queues.get(message.channel.id)
    if queue is None:
        logger.warning("No fallback queue for channel %s", message.channel.id)
        return True
    try:
        queue.put_nowait(FallbackQueueItem(message, attachments))
    except QueueFull:
        logger.warning("Fallback queue full for channel %s", message.channel.id)
        return True

    try:
        async with deps.live_queue_lock:
            for index, attachment in enumerate(attachments):
                deps.live_queue["jobs"].append(
                    {
                        "filename": attachment.filename,
                        "source_message_id": message.id,
                        "source_channel_id": message.channel.id,
                        "source_attachment_id": getattr(attachment, "id", None),
                        "attachment_index": index,
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
        backup = deps.trigger_log_backup_background()
    except Exception:
        logger.exception("Failed to schedule fallback backup")
    else:
        schedule_best_effort(deps.create_task, backup, logger, "Failed to schedule fallback backup")
    return True
