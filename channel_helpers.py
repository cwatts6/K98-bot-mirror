# Small helper module: channel_helpers.py
# Purpose: hold minimal, dependency-free helpers related to channel resolution.
# Rationale: kept separate to avoid circular imports between bot_helpers and processing_pipeline.

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_channel_safe(bot, channel_id: int) -> object | None:
    """
    Resolve a channel via bot.get_channel but with helpful logging.

    Returns:
      - discord.abc.GuildChannel or None

    Behavior:
      - If bot.get_channel raises unexpectedly, we log.exception and return None.
      - If get_channel returns None (cache miss), we log a warning and return None.
      - On success, we log a debug line and return the channel.

    This module intentionally has no imports of bot_helpers or processing_pipeline
    to remain safe for import from either module.
    """
    try:
        channel = bot.get_channel(channel_id)
    except Exception as exc:
        logger.exception(
            "[CHANNEL_HELPERS] Error resolving channel id=%s using bot.get_channel(): %s",
            channel_id,
            exc,
        )
        return None

    if channel is None:
        logger.warning(
            "[CHANNEL_HELPERS] Channel id=%s not found in bot cache (get_channel returned None). "
            "If this persists, check gateway intents, bot cache warming, or restart sequencing.",
            channel_id,
        )
        return None

    logger.info("[CHANNEL_HELPERS] Resolved channel id=%s from bot cache.", channel_id)
    return channel
