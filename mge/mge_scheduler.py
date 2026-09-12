from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging

import discord

from bot_config import MGE_SIMPLIFIED_FLOW_ENABLED
from mge import mge_completion_service
from mge.mge_embed_manager import (
    resolve_public_signup_channel_id,
    sync_event_leadership_embed,
    sync_event_signup_embed,
)
from mge.mge_event_service import sync_mge_events_from_calendar

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = 300
_MIN_INTERVAL_SECONDS = 30


def _resolve_interval_seconds() -> int:
    """
    Keep scheduler cadence sane even if constants/env get bad values later.
    """
    try:
        val = int(_INTERVAL_SECONDS)
    except Exception:
        return 300
    return val if val >= _MIN_INTERVAL_SECONDS else _MIN_INTERVAL_SECONDS


async def schedule_mge_lifecycle(bot: discord.Client) -> None:
    """Run periodic MGE lifecycle loop (calendar sync + embed sync + auto-completion)."""
    interval_seconds = _resolve_interval_seconds()
    logger.info("mge_scheduler_started interval_seconds=%s", interval_seconds)

    channel_id, raw_channel_id, source = resolve_public_signup_channel_id()
    if channel_id <= 0:
        logger.error(
            "mge_scheduler_disabled reason=invalid_signup_channel_id source=%s value=%s",
            source,
            raw_channel_id,
        )
        return

    try:
        while True:
            now = datetime.now(UTC)

            try:
                result, event_ids = sync_mge_events_from_calendar(now_utc=now)
                synced = 0
                for event_id in event_ids:
                    try:
                        await sync_event_signup_embed(
                            bot=bot,
                            event_id=event_id,
                            signup_channel_id=channel_id,
                            now_utc=now,
                        )
                        if MGE_SIMPLIFIED_FLOW_ENABLED:
                            await sync_event_leadership_embed(
                                bot=bot,
                                event_id=event_id,
                                now_utc=now,
                            )
                        synced += 1
                    except Exception:
                        logger.exception(
                            "mge_scheduler_embed_sync_failed event_id=%s signup_channel_id=%s",
                            event_id,
                            channel_id,
                        )

                logger.info(
                    "mge_scheduler_tick_complete scanned=%s created=%s existing=%s skipped=%s errors=%s embed_synced=%s",
                    result.scanned,
                    result.created,
                    result.existing,
                    result.skipped,
                    result.errors,
                    synced,
                )
            except Exception:
                logger.exception("mge_scheduler_tick_failed")

            try:
                completion_result = mge_completion_service.auto_complete_due_events(as_of_utc=now)
                logger.info(
                    "mge_scheduler_completion_tick due=%s completed=%s",
                    completion_result.get("due_count", 0),
                    completion_result.get("completed_count", 0),
                )
            except Exception:
                logger.exception("mge_scheduler_completion_tick_failed")

            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("mge_scheduler_cancelled")
        raise
    finally:
        logger.info("mge_scheduler_stopped")
