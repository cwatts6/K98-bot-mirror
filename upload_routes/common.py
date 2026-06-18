"""Shared helpers for DL_bot upload message routes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from typing import Any


async def resolve_notify_channel(
    get_notify_channel: Callable[[], Awaitable[Any | None]],
    fallback_channel: Any,
    logger: logging.Logger,
    route_name: str,
) -> Any:
    """Resolve the notification channel, falling back to the source channel."""
    try:
        return await get_notify_channel() or fallback_channel
    except Exception:
        logger.debug(
            "%s_notify_channel_resolution_failed",
            route_name,
            exc_info=True,
        )
        return fallback_channel


def message_source_fields(message: Any) -> dict[str, str]:
    """Return the common source/uploader fields used by upload result embeds."""
    return {
        "Channel": f"#{message.channel.name} ({message.channel.id})",
        "Uploader": f"{message.author} ({message.author.id})",
    }


def schedule_best_effort(
    create_task: Callable[[Awaitable[Any]], Any],
    awaitable: Awaitable[Any],
    logger: logging.Logger,
    failure_message: str,
) -> None:
    """Schedule a best-effort background task without affecting the route result."""
    try:
        create_task(awaitable)
    except Exception:
        close = getattr(awaitable, "close", None)
        if callable(close):
            close()
        logger.exception(failure_message)
