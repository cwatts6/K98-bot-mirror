"""Shared coordination helpers for player-location refresh workflows."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
import logging

logger = logging.getLogger(__name__)

_location_refresh_lock = asyncio.Lock()
_location_refresh_event = asyncio.Event()
_last_location_refresh_utc: datetime | None = None


def signal_location_refresh_complete() -> None:
    """Signal waiters that the location import/cache refresh has completed."""
    try:
        _location_refresh_event.set()
    except Exception:
        logger.exception("Failed to signal location refresh completion")


def is_location_refresh_running() -> bool:
    return _location_refresh_lock.locked()


def is_location_refresh_rate_limited() -> tuple[bool, int]:
    if not _last_location_refresh_utc:
        return False, 0
    now = datetime.now(UTC)
    delta = (now - _last_location_refresh_utc).total_seconds()
    remain = 3600 - int(delta)
    return (remain > 0), max(0, remain)


def mark_location_refresh_started() -> None:
    global _last_location_refresh_utc
    _last_location_refresh_utc = datetime.now(UTC)
    _location_refresh_event.clear()


async def wait_for_location_refresh(timeout_seconds: float) -> bool:
    try:
        await asyncio.wait_for(_location_refresh_event.wait(), timeout=timeout_seconds)
        return True
    except TimeoutError:
        return False


async def run_location_refresh_guarded(coro: Callable[[], Awaitable[object]]) -> bool:
    """Run one refresh at a time without queueing duplicate refresh requests."""
    if _location_refresh_lock.locked():
        return False

    async with _location_refresh_lock:
        limited, remain = is_location_refresh_rate_limited()
        if limited and remain > 0:
            return False
        await coro()
        return True
