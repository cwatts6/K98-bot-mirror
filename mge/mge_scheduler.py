from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging

import discord

from bot_config import MGE_SIGNUP_CHANNEL_ID
from mge.mge_embed_manager import sync_event_signup_embed
from mge.mge_event_service import sync_mge_events_from_calendar

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = 300


async def schedule_mge_lifecycle(bot: discord.Client) -> None:
    """Run periodic Task-D/E MGE sync lifecycle loop."""
    logger.info("mge_scheduler_started interval_seconds=%s", _INTERVAL_SECONDS)

    try:
        channel_id = int(MGE_SIGNUP_CHANNEL_ID)
    except Exception:
        logger.error(
            "mge_scheduler_disabled reason=invalid_signup_channel_id value=%s",
            MGE_SIGNUP_CHANNEL_ID,
        )
        return

    if channel_id <= 0:
        logger.error(
            "mge_scheduler_disabled reason=invalid_signup_channel_id value=%s",
            MGE_SIGNUP_CHANNEL_ID,
        )
        return

    try:
        while True:
            now = datetime.now(UTC)
            try:
                result, event_ids = sync_mge_events_from_calendar(now_utc=now)
                for event_id in event_ids:
                    await sync_event_signup_embed(
                        bot=bot,
                        event_id=event_id,
                        signup_channel_id=channel_id,
                        now_utc=now,
                    )
                logger.info(
                    "mge_scheduler_tick_complete scanned=%s created=%s existing=%s skipped=%s errors=%s",
                    result.scanned,
                    result.created,
                    result.existing,
                    result.skipped,
                    result.errors,
                )
            except Exception:
                logger.exception("mge_scheduler_tick_failed")

            await asyncio.sleep(_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("mge_scheduler_cancelled")
        raise
    finally:
        logger.info("mge_scheduler_stopped")
