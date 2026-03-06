from __future__ import annotations

import asyncio
import logging

from constants import (
    EVENT_CALENDAR_PIPELINE_INTERVAL_SECONDS,
    EVENT_CALENDAR_PIPELINE_TIMEOUT_SECONDS,
    EVENT_CALENDAR_SHEET_ID,
)
from core.interaction_safety import get_operation_lock
from event_calendar.service import get_calendar_service

logger = logging.getLogger(__name__)


async def run_calendar_pipeline_loop(*, poll_interval_seconds: int | None = None) -> None:
    interval = int(poll_interval_seconds or EVENT_CALENDAR_PIPELINE_INTERVAL_SECONDS)
    svc = get_calendar_service()

    while True:
        async with get_operation_lock("calendar_refresh"):
            try:
                await asyncio.wait_for(
                    svc.refresh_full(
                        actor_user_id=None,
                        sheet_id=EVENT_CALENDAR_SHEET_ID,
                        horizon_days=365,
                        force_empty=False,
                    ),
                    timeout=EVENT_CALENDAR_PIPELINE_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                logger.warning("[CALENDAR] scheduled pipeline timed out")
            except Exception:
                logger.exception("[CALENDAR] scheduled pipeline failed")

        await asyncio.sleep(interval)
