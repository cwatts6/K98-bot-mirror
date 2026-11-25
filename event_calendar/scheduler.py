from __future__ import annotations

import asyncio
import logging

from constants import (
    EVENT_CALENDAR_PIPELINE_INTERVAL_SECONDS,
    EVENT_CALENDAR_SHEET_ID,
)
from event_calendar.service import get_calendar_service

logger = logging.getLogger(__name__)


async def run_calendar_pipeline_loop(*, poll_interval_seconds: int | None = None) -> None:
    if poll_interval_seconds is None:
        interval = int(EVENT_CALENDAR_PIPELINE_INTERVAL_SECONDS)
    else:
        interval = int(poll_interval_seconds)
        if interval < 1:
            raise ValueError("poll_interval_seconds must be at least 1 second")

    svc = get_calendar_service()

    while True:
        try:
            # Task 7: no outer wait_for here.
            # Service admission retains one bounded scheduled intent.
            await svc.refresh_pipeline(
                actor_user_id=None,
                actor_source="scheduler",
                sheet_id=EVENT_CALENDAR_SHEET_ID,
                horizon_days=365,
                force_empty=False,
                scheduled=True,
            )
        except Exception:
            logger.exception("[CALENDAR] scheduled pipeline failed")

        await asyncio.sleep(interval)
