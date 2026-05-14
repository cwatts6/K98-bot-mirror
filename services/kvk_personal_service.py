# services/kvk_personal_service.py
"""
Service layer for /mykvktargets and /mykvkstats personal command flows.

Owns orchestration: account resolution and stats loading.
Does not depend on chat-platform types.
Channel posting (which requires Discord transport) lives in commands/kvk_personal_posting.py.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from registry import registry_service
import stats_cache_helpers

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Account slot ordering — canonical single definition (matches account_picker._PREFERRED_ORDER)
from registry.account_slots import ACCOUNT_ORDER


async def resolve_user_accounts(user_id: int) -> dict:
    """
    Load the governor registry and return the accounts dict for the given user_id.
    Returns an empty dict if the user is not found or on any error.
    Logs the outcome with user_id.
    """
    try:
        accounts = await asyncio.to_thread(registry_service.get_user_accounts, int(user_id))
        accounts = accounts or {}
        logger.debug(
            "[kvk_personal_service] resolve_user_accounts user_id=%s accounts_count=%s",
            user_id,
            len(accounts),
        )
        return dict(accounts)
    except Exception:
        logger.exception(
            "[kvk_personal_service] resolve_user_accounts failed for user_id=%s", user_id
        )
        return {}


def classify_accounts(accounts: dict) -> tuple[str, str | None]:
    """
    Classify a user's accounts dict into one of three states.

    Returns:
        ("none", None)          — no accounts registered
        ("single", governor_id) — exactly one unique governor; returns the governor_id string
        ("multi", None)         — two or more unique governors
    """
    if not accounts:
        return ("none", None)

    # Gather unique, non-empty governor IDs in preferred slot order
    seen: set[str] = set()
    for slot in ACCOUNT_ORDER:
        info = accounts.get(slot)
        if not info or not isinstance(info, dict):
            continue
        gid = str(info.get("GovernorID") or info.get("GovernorId") or "").strip()
        if gid:
            seen.add(gid)

    # Also handle any slots not in ACCOUNT_ORDER
    for slot, info in accounts.items():
        if slot in ACCOUNT_ORDER:
            continue
        if not info or not isinstance(info, dict):
            continue
        gid = str(info.get("GovernorID") or info.get("GovernorId") or "").strip()
        if gid:
            seen.add(gid)

    if not seen:
        return ("none", None)

    if len(seen) == 1:
        # Return the single governor_id — find it via preferred ordering
        for slot in ACCOUNT_ORDER:
            info = accounts.get(slot)
            if not info or not isinstance(info, dict):
                continue
            gid = str(info.get("GovernorID") or info.get("GovernorId") or "").strip()
            if gid:
                return ("single", gid)
        # Fallback: return from set
        return ("single", next(iter(seen)))

    return ("multi", None)


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
