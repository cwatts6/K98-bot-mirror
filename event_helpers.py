# event_helpers.py
from __future__ import annotations

from typing import Any

from event_cache import get_all_upcoming_events, is_cache_stale, refresh_event_cache
from utils import get_next_events as _get_next_events


async def load_all_upcoming_events(ensure_fresh: bool = True) -> list[dict[str, Any]]:
    """
    Returns upcoming events from the in-memory cache (sorted, future-only).
    Optionally refreshes the cache first if it looks stale.
    """
    if ensure_fresh and is_cache_stale():
        try:
            await refresh_event_cache()
        except Exception:
            # Best-effort: fall back to existing cache
            pass
    return get_all_upcoming_events()


async def get_next_event(event_type: str | None = None) -> dict[str, Any] | None:
    """
    Returns the next upcoming event, optionally restricted to a type.
    Uses shared normalization from utils.get_next_events.
    """
    events = _get_next_events(limit=1, event_type=event_type)
    return events[0] if events else None
