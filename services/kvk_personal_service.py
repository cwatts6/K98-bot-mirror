# services/kvk_personal_service.py
"""
Service layer for /mykvktargets and /mykvkstats personal command flows.

Owns orchestration: account resolution, stats loading, channel posting.
Does NOT import Discord view classes or accept discord.Interaction objects.
May accept discord.ApplicationContext as ctx where needed for channel resolution.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

import discord

import stats_cache_helpers

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Account slot ordering — canonical single definition (matches account_picker._PREFERRED_ORDER)
from account_picker import ACCOUNT_ORDER


async def resolve_user_accounts(user_id: int) -> dict:
    """
    Load the governor registry and return the accounts dict for the given user_id.
    Returns an empty dict if the user is not found or on any error.
    Logs the outcome with user_id.
    """
    try:
        from registry.governor_registry import load_registry

        registry = await asyncio.to_thread(load_registry)
        registry = registry or {}
        user_block = registry.get(str(user_id)) or registry.get(user_id) or {}
        accounts = user_block.get("accounts") or {}
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


async def post_stats_embeds(
    bot,
    ctx: discord.ApplicationContext,
    embeds: list,
    file,
) -> tuple[bool, str]:
    """
    Post stats embeds using the full channel fallback chain.

    Chain: original invoking channel → KVK_PLAYER_STATS_CHANNEL_ID → NOTIFY_CHANNEL_ID → DM.

    Args:
        bot:    The Discord bot instance (used for get_channel lookups).
        ctx:    The ApplicationContext (used to resolve the original channel).
        embeds: List of discord.Embed objects to post.
        file:   A discord.File object (or None) to attach. If a fallback channel is tried,
                the file's underlying stream is rewound to position 0 before each attempt
                so the same file object can be used across multiple sends.

    Returns:
        (posted: bool, channel_used: str) — whether posting succeeded and which channel was used.
    """
    from bot_config import KVK_PLAYER_STATS_CHANNEL_ID, NOTIFY_CHANNEL_ID

    def _rewind_file() -> None:
        """Rewind a discord.File's fp to position 0 so it can be resent on fallback."""
        if file is None:
            return
        fp = getattr(file, "fp", None)
        if fp is not None and hasattr(fp, "seek"):
            try:
                fp.seek(0)
            except Exception:
                pass

    async def _send_to(ch: discord.abc.Messageable, *, label: str) -> bool:
        _rewind_file()
        try:
            if file is not None:
                await ch.send(embeds=embeds, files=[file])
            else:
                await ch.send(embeds=embeds)
            logger.info("[kvk_personal_service] post_stats_embeds posted to %s", label)
            return True
        except discord.Forbidden:
            logger.warning(
                "[kvk_personal_service] post_stats_embeds Forbidden in %s (id=%s)",
                label,
                getattr(ch, "id", None),
            )
            return False
        except Exception:
            logger.exception(
                "[kvk_personal_service] post_stats_embeds error in %s (id=%s)",
                label,
                getattr(ch, "id", None),
            )
            return False

    def _can_send(ch: discord.abc.Messageable) -> bool:
        try:
            guild = getattr(ch, "guild", None)
            if not guild:
                return True
            me = guild.get_member(bot.user.id) if hasattr(guild, "get_member") else None
            if me is None:
                return True
            return ch.permissions_for(me).send_messages
        except Exception:
            return True

    # 1) Original invoking channel
    try:
        orig_ch = getattr(ctx, "channel", None)
        if orig_ch and _can_send(orig_ch):
            if await _send_to(orig_ch, label=f"orig_channel:{getattr(orig_ch, 'id', '?')}"):
                return (True, "orig_channel")
    except Exception:
        logger.exception("[kvk_personal_service] post_stats_embeds orig_channel attempt failed")

    # 2) KVK player stats channel
    try:
        kvk_ch = bot.get_channel(KVK_PLAYER_STATS_CHANNEL_ID)
        if kvk_ch and _can_send(kvk_ch):
            if await _send_to(kvk_ch, label=f"kvk_channel:{KVK_PLAYER_STATS_CHANNEL_ID}"):
                return (True, "kvk_channel")
    except Exception:
        logger.exception("[kvk_personal_service] post_stats_embeds kvk_channel attempt failed")

    # 3) Notify channel
    try:
        notify_ch = bot.get_channel(NOTIFY_CHANNEL_ID)
        if notify_ch and _can_send(notify_ch):
            if await _send_to(notify_ch, label=f"notify_channel:{NOTIFY_CHANNEL_ID}"):
                return (True, "notify_channel")
    except Exception:
        logger.exception("[kvk_personal_service] post_stats_embeds notify_channel attempt failed")

    # 4) DM fallback — attempt to DM via the ctx user
    try:
        user = getattr(ctx, "user", None) or getattr(ctx, "author", None)
        if user:
            if await _send_to(user, label=f"dm:{getattr(user, 'id', '?')}"):
                return (True, "dm")
    except Exception:
        logger.exception("[kvk_personal_service] post_stats_embeds DM attempt failed")

    logger.warning("[kvk_personal_service] post_stats_embeds all channels failed")
    return (False, "none")


async def load_last_kvk_map() -> dict:
    """
    Thin async wrapper around stats_cache_helpers.load_last_kvk_map().
    Single call point for all command-layer consumers.
    """
    return await stats_cache_helpers.load_last_kvk_map()
