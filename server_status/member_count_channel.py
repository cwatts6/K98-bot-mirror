from __future__ import annotations

import asyncio
import logging

import discord

from bot_config import MEMBER_COUNT_CHANNEL_ID, SERVER_STATUS_ENABLED

logger = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 600


def format_member_count_channel_name(member_count: int) -> str:
    count = max(0, int(member_count or 0))
    return f"Members: {count:,}"


async def _resolve_channel(bot: discord.Client, channel_id: int | None):
    if not channel_id:
        return None
    channel = bot.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await bot.fetch_channel(int(channel_id))
        except Exception:
            logger.warning(
                "member_count_channel_fetch_failed channel_id=%s", channel_id, exc_info=True
            )
            return None
    return channel


def _resolve_member_count(channel) -> int | None:
    guild = getattr(channel, "guild", None)
    if guild is None:
        return None
    count = getattr(guild, "member_count", None)
    if count is not None:
        return int(count)
    members = getattr(guild, "members", None)
    if members is not None:
        return len(members)
    return None


async def update_member_count_channel_once(bot: discord.Client) -> bool:
    if not SERVER_STATUS_ENABLED:
        return False
    channel = await _resolve_channel(bot, MEMBER_COUNT_CHANNEL_ID)
    if channel is None:
        logger.warning("member_count_channel_missing channel_id=%s", MEMBER_COUNT_CHANNEL_ID)
        return False

    count = _resolve_member_count(channel)
    if count is None:
        logger.warning("member_count_channel_guild_missing channel_id=%s", MEMBER_COUNT_CHANNEL_ID)
        return False

    desired = format_member_count_channel_name(count)
    if getattr(channel, "name", None) == desired:
        return False

    try:
        await channel.edit(name=desired, reason="K98 member count status channel refresh")
        logger.info(
            "member_count_channel_updated channel_id=%s count=%s",
            MEMBER_COUNT_CHANNEL_ID,
            count,
        )
        return True
    except discord.Forbidden:
        logger.warning("member_count_channel_forbidden channel_id=%s", MEMBER_COUNT_CHANNEL_ID)
    except discord.HTTPException:
        logger.warning(
            "member_count_channel_http_failed channel_id=%s", MEMBER_COUNT_CHANNEL_ID, exc_info=True
        )
    except Exception:
        logger.exception(
            "member_count_channel_update_failed channel_id=%s", MEMBER_COUNT_CHANNEL_ID
        )
    return False


async def run_member_count_channel_loop(bot: discord.Client) -> None:
    logger.info(
        "member_count_channel_loop_started enabled=%s channel_id=%s interval_seconds=%s",
        SERVER_STATUS_ENABLED,
        MEMBER_COUNT_CHANNEL_ID,
        UPDATE_INTERVAL_SECONDS,
    )
    try:
        while True:
            await update_member_count_channel_once(bot)
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("member_count_channel_loop_cancelled")
        raise
    finally:
        logger.info("member_count_channel_loop_stopped")
