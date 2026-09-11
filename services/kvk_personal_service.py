# services/kvk_personal_service.py
"""
Service layer for /mykvktargets and /mykvkstats personal command flows.

Owns orchestration: stats loading and small cache wrappers.
Account resolution lives in services/governor_account_service.py.
Channel posting (which requires Discord transport) lives in commands/kvk_personal_posting.py.
"""

from __future__ import annotations

import asyncio
import logging
import time

import stats_cache_helpers

logger = logging.getLogger(__name__)


async def load_kvk_personal_stats(governor_id: str) -> dict | None:
    """
    Load the stats row for the given governor_id off the event loop.
    Logs timing and governor_id. Returns None on any failure.
    """
    t0 = time.monotonic()
    try:
        from utils import load_stat_row

        row = await asyncio.to_thread(load_stat_row, governor_id)
        elapsed = time.monotonic() - t0
        logger.debug(
            "[kvk_personal_service] load_kvk_personal_stats governor_id=%s elapsed=%.3fs found=%s",
            governor_id,
            elapsed,
            row is not None,
        )
        return row
    except Exception:
        elapsed = time.monotonic() - t0
        logger.exception(
            "[kvk_personal_service] load_kvk_personal_stats failed governor_id=%s elapsed=%.3fs",
            governor_id,
            elapsed,
        )
        return None


async def load_last_kvk_map() -> dict:
    """
    Thin async wrapper around stats_cache_helpers.load_last_kvk_map().
    Single call point for all command-layer consumers.
    """
    return await stats_cache_helpers.load_last_kvk_map()
