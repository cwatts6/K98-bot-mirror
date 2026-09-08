"""Off-season daily/weekly delivery with durable fresh-dispatch ownership."""

import logging
from typing import Any

from embed_offseason_stats import send_offseason_stats_embed_v2
from file_utils import run_blocking_in_thread
from stats_alerts.dispatch_reservations import DispatchAttempt, DispatchUnavailable
from stats_alerts.guard import sent_today
from utils import utcnow

logger = logging.getLogger(__name__)


async def _send_period(bot, channel, *, weekly: bool, is_test: bool) -> None:
    period = "weekly" if weekly else "daily"
    kind = f"offseason_{period}"
    posted = (
        False
        if is_test
        else await run_blocking_in_thread(
            sent_today, kind, name=f"sent_today_offseason_{period}", meta={"key": kind}
        )
    )
    if posted:
        logger.info("[STATS EMBED] Offseason %s already posted today; skipping.", period)
        return

    async def publish(attempt=None):
        try:
            summary_posted = (
                False
                if is_test
                else await run_blocking_in_thread(
                    sent_today, f"kingdom_summary_{period}", name=f"sent_today_ks_{period}_check"
                )
            )
        except Exception:
            logger.exception(
                "[OFFSEASON] KS %s sent_today check failed; assuming not sent.", period
            )
            summary_posted = False
        options = {}
        if attempt is not None:
            options = {"before_send": attempt.start, "return_receipt": True}
        message = await send_offseason_stats_embed_v2(
            bot,
            channel=channel,
            is_weekly=weekly,
            mention_everyone=(not is_test and not weekly),
            include_kingdom_summary=(not summary_posted),
            **options,
        )
        if attempt is not None and message is not None:
            await attempt.accept(message.id)

    if is_test:
        await publish()
    else:
        async with DispatchAttempt(kind, channel.id) as attempt:
            await publish(attempt)


async def send_offseason_flow(bot: Any, channel, timestamp: str, *, is_test: bool = False) -> None:
    try:
        await _send_period(bot, channel, weekly=False, is_test=is_test)
    except DispatchUnavailable as exc:
        logger.info("[OFFSEASON] Daily dispatch unavailable: %s", exc)
    except Exception:
        logger.exception("[STATS EMBED] Off-season daily send failed.")

    # Preserve the existing Monday decision after the daily operation.
    if utcnow().weekday() == 0:
        try:
            await _send_period(bot, channel, weekly=True, is_test=is_test)
        except DispatchUnavailable as exc:
            logger.info("[OFFSEASON] Weekly dispatch unavailable: %s", exc)
        except Exception:
            logger.exception("[STATS EMBED] Off-season weekly send failed.")
