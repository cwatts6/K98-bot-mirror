"""
In-process TTL cache for the governor registry dict.

Owned by this module only. All reads/writes go through the public API.
registry_service.py is the only consumer that writes to this cache.
"""

from __future__ import annotations

import copy
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level private state
# ---------------------------------------------------------------------------

_cache_data: dict | None = None
_cache_ts: float = 0.0
_cache_lock: threading.Lock = threading.Lock()
_last_invalidation_reason: str = "never_populated"


def _parse_ttl() -> float:
    """Parse REGISTRY_CACHE_TTL_SECONDS from env, falling back to 45.0 on any error."""
    raw = os.environ.get("REGISTRY_CACHE_TTL_SECONDS", "")
    if raw:
        try:
            return float(raw)
        except ValueError:
            logger.warning(
                "[registry_cache] Invalid REGISTRY_CACHE_TTL_SECONDS=%r — using default 45s",
                raw,
            )
    return 45.0


_CACHE_TTL: float = _parse_ttl()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_cached_or_none() -> dict | None:
    """
    Thread-safe read.

    Returns a deep copy of the cached dict if the cache is populated and
    within TTL, else returns None.

    A _cache_ts of 0.0 is used as a sentinel for "invalidated / never populated"
    and always results in a cache miss, regardless of TTL.
    """
    global _cache_data, _cache_ts

    with _cache_lock:
        if _cache_data is None:
            return None
        if _cache_ts == 0.0:
            return None
        age = time.monotonic() - _cache_ts
        if age > _CACHE_TTL:
            return None
        logger.debug(
            "[registry_cache] cache hit — age=%.1fs ttl=%.1fs",
            age,
            _CACHE_TTL,
        )
        return copy.deepcopy(_cache_data)


def store_cache(data: dict) -> None:
    """
    Thread-safe write. Stores a deep copy and records the current monotonic timestamp.
    """
    global _cache_data, _cache_ts

    with _cache_lock:
        _cache_data = copy.deepcopy(data)
        _cache_ts = time.monotonic()


def get_stale_or_none() -> dict | None:
    """
    Thread-safe stale-snapshot read for error-fallback paths.

    Unlike get_cached_or_none(), this ignores TTL expiry — it returns data
    that is beyond TTL but still safe to show.

    Critically, it DOES respect the _cache_ts == 0.0 invalidation sentinel:
    data that has been explicitly invalidated (e.g. after a successful write)
    is NOT returned, so callers cannot see pre-write state after a mutation.

    Returns None when:
      - cache is unpopulated (_cache_data is None), or
      - cache has been explicitly invalidated (_cache_ts == 0.0).
    """
    with _cache_lock:
        if _cache_data is None:
            return None
        if _cache_ts == 0.0:
            # Explicitly invalidated — do not return this snapshot.
            return None
        return copy.deepcopy(_cache_data)


def invalidate(reason: str = "unspecified") -> None:
    """
    Thread-safe invalidation.

    Sets _cache_ts to 0.0 so the next read is a cache miss.
    Logs at INFO level with the reason.
    """
    global _cache_ts, _last_invalidation_reason

    with _cache_lock:
        _cache_ts = 0.0
        _last_invalidation_reason = reason
    logger.info("[registry_cache] cache invalidated — reason=%s", reason)


def get_info() -> dict[str, object]:
    """
    Return diagnostic info about the current cache state.

    Keys:
      populated               — bool: whether the cache holds data
      age_seconds             — float | None: seconds since last store, or None if empty
      ttl_seconds             — float: configured TTL
      last_invalidation_reason — str: reason passed to the last invalidate() call
    """
    with _cache_lock:
        populated = _cache_data is not None
        if populated and _cache_ts > 0.0:
            age: float | None = time.monotonic() - _cache_ts
        else:
            age = None
        reason = _last_invalidation_reason

    return {
        "populated": populated,
        "age_seconds": age,
        "ttl_seconds": _CACHE_TTL,
        "last_invalidation_reason": reason,
    }
