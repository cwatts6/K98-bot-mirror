# stats_cache_helpers.py
from __future__ import annotations

import logging
import time
from typing import Any

from constants import PLAYER_STATS_LAST_CACHE
from file_utils import read_json_safe, run_blocking_in_thread

logger = logging.getLogger(__name__)

# Simple in-process cache for the last-KVK map to avoid repeated disk reads.
# TTL is in seconds; default 5 minutes (tunable via env var if desired).
_CACHE_TTL = int(__import__("os").environ.get("PLAYER_STATS_LAST_CACHE_TTL", "300"))

# Module-level cache structure
_last_kvk_cache: dict = {
    "ts": 0,  # epoch seconds when cache was populated
    "data": {},  # the dict keyed by GovernorID
}


def _read_last_kvk_sync() -> dict[str, Any]:
    """
    Synchronous read of the PLAYER_STATS_LAST_CACHE file.
    Returns a dict keyed by GovernorID (strings). Returns {} on any failure.
    Intended to be executed via run_blocking_in_thread.
    """
    try:
        data = read_json_safe(PLAYER_STATS_LAST_CACHE)
        if isinstance(data, dict):
            data.pop("_meta", None)
            # Keep only non-meta keys (should already be the correct shape)
            return {k: v for k, v in data.items() if k != "_meta"}
    except FileNotFoundError:
        # Missing file: treat as empty
        return {}
    except Exception:
        logger.exception(
            "[STATS_CACHE_HELPERS] _read_last_kvk_sync failed reading %s", PLAYER_STATS_LAST_CACHE
        )
    return {}


async def load_last_kvk_map() -> dict[str, Any]:
    """
    Async loader that returns the cached last-KVK map (reads file if cache expired).
    Guarantees a dict return (possibly empty). Uses a simple in-process TTL cache.
    """
    now = int(time.time())
    try:
        # serve from cache if still valid
        if now - int(_last_kvk_cache.get("ts", 0)) < _CACHE_TTL and isinstance(
            _last_kvk_cache.get("data"), dict
        ):
            return _last_kvk_cache["data"]

        # otherwise read from disk off the event loop
        data = await run_blocking_in_thread(_read_last_kvk_sync, name="read_last_kvk_cache")
        if not isinstance(data, dict):
            data = {}

        # update cache
        _last_kvk_cache["data"] = data
        _last_kvk_cache["ts"] = int(time.time())
        return data
    except Exception:
        logger.exception("[STATS_CACHE_HELPERS] load_last_kvk_map failed")
        # On failure, return whatever is in the cache even if stale, else empty dict
        try:
            return _last_kvk_cache.get("data", {}) or {}
        except Exception:
            return {}
