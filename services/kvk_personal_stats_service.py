# services/kvk_personal_stats_service.py
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


async def resolve_governor_accounts(
    user_id: int,
    manual_governor_id: str | None = None,
    registry: dict | None = None,
) -> dict:
    """
    Resolve governor accounts for a Discord user.
    
    Returns dict with keys:
      mode: "manual" | "single" | "multi" | "none"
      accounts: list of account dicts
      governor_id: str | None (set for "manual" mode)
    """
    t0 = time.monotonic()

    # Manual path: validate and return immediately
    if manual_governor_id is not None:
        gid = str(manual_governor_id).strip()
        elapsed_ms = (time.monotonic() - t0) * 1000
        if gid.isdigit():
            logger.info(
                "[kvk_personal_stats_service] resolve user_id=%s mode=manual governor_id=%s elapsed_ms=%.1f",
                user_id, gid, elapsed_ms,
            )
            return {"mode": "manual", "accounts": [], "governor_id": gid}
        logger.warning(
            "[kvk_personal_stats_service] resolve user_id=%s manual_governor_id=%r is invalid elapsed_ms=%.1f",
            user_id, gid, elapsed_ms,
        )
        return {"mode": "none", "accounts": [], "governor_id": None}

    # Load registry if not provided
    if registry is None:
        try:
            from registry.governor_registry import load_registry
            registry = await asyncio.to_thread(load_registry)
        except Exception:
            logger.exception(
                "[kvk_personal_stats_service] resolve user_id=%s failed to load registry",
                user_id,
            )
            registry = {}

    user_block = (registry or {}).get(str(user_id)) or {}
    accounts = user_block.get("accounts") or {}
    elapsed_ms = (time.monotonic() - t0) * 1000

    if not accounts:
        logger.info(
            "[kvk_personal_stats_service] resolve user_id=%s mode=none elapsed_ms=%.1f",
            user_id, elapsed_ms,
        )
        return {"mode": "none", "accounts": accounts, "governor_id": None}

    if len(accounts) == 1:
        logger.info(
            "[kvk_personal_stats_service] resolve user_id=%s mode=single elapsed_ms=%.1f",
            user_id, elapsed_ms,
        )
        return {"mode": "single", "accounts": accounts, "governor_id": None}

    logger.info(
        "[kvk_personal_stats_service] resolve user_id=%s mode=multi count=%d elapsed_ms=%.1f",
        user_id, len(accounts), elapsed_ms,
    )
    return {"mode": "multi", "accounts": accounts, "governor_id": None}


async def load_target_data(governor_id: str) -> dict | None:
    """
    Load KVK target data for a governor.
    Delegates to run_target_lookup from target_utils.py.
    Returns the result dict or None on failure.
    """
    t0 = time.monotonic()
    gid = str(governor_id).strip()

    try:
        from target_utils import run_target_lookup
        result = await run_target_lookup(gid)
        elapsed_ms = (time.monotonic() - t0) * 1000
        status = result.get("status") if isinstance(result, dict) else "unknown"
        logger.info(
            "[kvk_personal_stats_service] load_target_data governor_id=%s status=%s elapsed_ms=%.1f",
            gid, status, elapsed_ms,
        )
        return result
    except Exception:
        elapsed_ms = (time.monotonic() - t0) * 1000
        logger.exception(
            "[kvk_personal_stats_service] load_target_data governor_id=%s failed elapsed_ms=%.1f",
            gid, elapsed_ms,
        )
        return None


async def load_stats_data(governor_id: str) -> dict:
    """
    Load stats data for a governor.
    Returns dict with keys: 'row' (stat row dict or None), 'last_kvk_map' (dict).
    Uses stats_cache_helpers.load_last_kvk_map() ONLY as KVK map load path.
    """
    t0 = time.monotonic()
    gid = str(governor_id).strip()
    result: dict[str, Any] = {"row": None, "last_kvk_map": {}}
    cache_hit = False

    try:
        from utils import load_stat_row
        row = await asyncio.to_thread(load_stat_row, gid)
        result["row"] = row
        cache_hit = row is not None
    except Exception:
        logger.exception(
            "[kvk_personal_stats_service] load_stats_data governor_id=%s load_stat_row failed", gid
        )

    try:
        from stats_cache_helpers import load_last_kvk_map
        lkmap = await load_last_kvk_map()
        result["last_kvk_map"] = lkmap if isinstance(lkmap, dict) else {}
    except Exception:
        logger.exception(
            "[kvk_personal_stats_service] load_stats_data governor_id=%s load_last_kvk_map failed", gid
        )

    elapsed_ms = (time.monotonic() - t0) * 1000
    logger.info(
        "[kvk_personal_stats_service] load_stats_data governor_id=%s cache_hit=%s elapsed_ms=%.1f",
        gid, cache_hit, elapsed_ms,
    )
    return result


def decide_post_channel(guild, preferred_channel_ids: list) -> Any | None:
    """
    Centralized channel fallback policy.
    
    Args:
        guild: Discord guild object (or None)
        preferred_channel_ids: list of channel IDs in preference order
    
    Returns:
        A Discord channel object, or None if none available.
    """
    if guild is None:
        return None

    for channel_id in preferred_channel_ids:
        if not channel_id:
            continue
        try:
            ch = guild.get_channel(int(channel_id))
            if ch is not None:
                logger.debug(
                    "[kvk_personal_stats_service] decide_post_channel resolved channel_id=%s",
                    channel_id,
                )
                return ch
        except Exception:
            logger.debug(
                "[kvk_personal_stats_service] decide_post_channel failed for channel_id=%s",
                channel_id,
            )

    logger.warning(
        "[kvk_personal_stats_service] decide_post_channel no available channel from ids=%s",
        preferred_channel_ids,
    )
    return None
