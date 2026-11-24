"""Shared helpers for DL_bot upload message routes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from typing import Any


async def observe_optional(function, *args, **kwargs):
    """One optional observation; an exception never changes business evidence.

    Cancellation propagates. No retry or second notification follows an uncertain
    send. Transport latency is handled separately by the qualified audit adapter.
    """
    try:
        return await function(*args, **kwargs)
    except Exception:
        logging.getLogger(__name__).warning("upload_optional_observation_failed", exc_info=True)
        return None


async def observe_upload_failure(outcome, record_phase, fail_batch, batch_ref, **kwargs):
    """Persist uncertainty without inventing a SQL terminal state or zero counts."""
    details = {**(kwargs.get("details") or {}), **outcome.details()}
    if outcome.business in {"outcome_unconfirmed", "committed", "duplicate"}:
        return await observe_optional(
            record_phase,
            batch_ref,
            phase_name="upload_observation",
            phase_status="failed",
            error_type=kwargs.get("error_type"),
            error_text=kwargs.get("error_text"),
            details=details,
        )
    return await observe_optional(fail_batch, batch_ref, **{**kwargs, "details": details})


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
) -> BaseException | None:
    """Schedule a best-effort background task without affecting the route result."""
    try:
        create_task(awaitable)
    except Exception as exc:
        close = getattr(awaitable, "close", None)
        if callable(close):
            close()
        logger.exception(failure_message)
        return exc
    return None


def schedule_factory_best_effort(create_task, factory, *args, **kwargs):
    """Observe scheduling admission only, including awaitable construction failure."""
    log = logging.getLogger(__name__)
    try:
        pending = factory(*args, **kwargs)
    except Exception as exc:
        log.warning("upload_optional_schedule_unavailable", exc_info=True)
        return exc
    return schedule_best_effort(create_task, pending, log, "upload_optional_schedule_unavailable")
