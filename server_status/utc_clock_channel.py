from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging

import discord

from bot_config import SERVER_STATUS_ENABLED, UTC_CLOCK_CHANNEL_ID

logger = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 600


def format_utc_clock_channel_name(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    return dt.strftime("%a %d %b %H:%M UTC")


async def _resolve_channel(bot: discord.Client, channel_id: int | None):
    if not channel_id:
        return None
    channel = bot.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await bot.fetch_channel(int(channel_id))
        except Exception:
            logger.warning(
                "utc_clock_channel_fetch_failed channel_id=%s", channel_id, exc_info=True
            )
            return None
    return channel


async def update_utc_clock_channel_once(bot: discord.Client) -> bool:
    if not SERVER_STATUS_ENABLED:
        return False
    channel = await _resolve_channel(bot, UTC_CLOCK_CHANNEL_ID)
    if channel is None:
        logger.warning("utc_clock_channel_missing channel_id=%s", UTC_CLOCK_CHANNEL_ID)
        return False

    desired = format_utc_clock_channel_name(datetime.now(UTC))
    current = getattr(channel, "name", None)
    if current == desired:
        return False

    try:
        await channel.edit(name=desired, reason="K98 UTC status channel refresh")
        logger.info(
            "utc_clock_channel_updated channel_id=%s name=%s", UTC_CLOCK_CHANNEL_ID, desired
        )
        return True
    except discord.Forbidden:
        logger.warning("utc_clock_channel_forbidden channel_id=%s", UTC_CLOCK_CHANNEL_ID)
    except discord.HTTPException:
        logger.warning(
            "utc_clock_channel_http_failed channel_id=%s", UTC_CLOCK_CHANNEL_ID, exc_info=True
        )
    except Exception:
        logger.exception("utc_clock_channel_update_failed channel_id=%s", UTC_CLOCK_CHANNEL_ID)
    return False


async def run_utc_clock_channel_loop(bot: discord.Client) -> None:
    logger.info(
        "utc_clock_channel_loop_started enabled=%s channel_id=%s interval_seconds=%s",
        SERVER_STATUS_ENABLED,
        UTC_CLOCK_CHANNEL_ID,
        UPDATE_INTERVAL_SECONDS,
    )
    try:
        while True:
            await update_utc_clock_channel_once(bot)
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("utc_clock_channel_loop_cancelled")
        raise
    finally:
        logger.info("utc_clock_channel_loop_stopped")
