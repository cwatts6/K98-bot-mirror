"""Off-season daily/weekly delivery with durable fresh-dispatch ownership."""

import logging
from typing import Any

from embed_offseason_stats import send_offseason_stats_embed_v2
from file_utils import run_blocking_in_thread
from stats_alerts.delivery_outcomes import delivery_outcome
from stats_alerts.dispatch_reservations import DispatchAttempt, DispatchGuarded, DispatchUnavailable
from stats_alerts.guard import sent_today
from utils import utcnow

logger = logging.getLogger(__name__)


async def _send_period(bot, channel, *, weekly: bool, is_test: bool, _delivery=None) -> None:
    period = "weekly" if weekly else "daily"
    kind = f"offseason_{period}"
    if _delivery:
        _delivery.update(component=kind, requested_channel_id=getattr(channel, "id", None))
    posted = (
        False
        if is_test
        else await run_blocking_in_thread(
            sent_today, kind, name=f"sent_today_offseason_{period}", meta={"key": kind}
        )
    )
    if posted:
        if _delivery:
            _delivery.skip("already_posted")
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
        if _delivery:
            options.update(_delivery=_delivery, return_receipt=True)
        message = await send_offseason_stats_embed_v2(
            bot,
            channel=channel,
            is_weekly=weekly,
            mention_everyone=(not is_test and not weekly),
            include_kingdom_summary=(not summary_posted),
            **options,
        )
        if attempt is not None and message is not None:
            try:
                await attempt.accept(message.id)
            finally:
                if _delivery:
                    _delivery.observe_commit(attempt)

    if is_test:
        await publish()
    else:
        attempt = DispatchAttempt(kind, channel.id)
        try:
            async with attempt:
                await publish(attempt)
        finally:
            if _delivery:
                _delivery.observe_commit(attempt)


@delivery_outcome("offseason")
async def send_offseason_flow(
    bot: Any, channel, timestamp: str, *, is_test: bool = False, _delivery=None
) -> None:
    try:
        await _send_period(bot, channel, weekly=False, is_test=is_test, _delivery=_delivery)
    except DispatchUnavailable as exc:
        if _delivery:
            if isinstance(exc, DispatchGuarded):
                _delivery.skip("dispatch_guarded")
            else:
                _delivery.failure(exc)
        logger.info("[OFFSEASON] Daily dispatch unavailable: %s", exc)
    except Exception as exc:
        if _delivery:
            _delivery.failure(exc)
        logger.exception("[STATS EMBED] Off-season daily send failed.")

    # Preserve the existing Monday decision after the daily operation.
    if _delivery:
        _delivery.begin("offseason_weekly", channel_id=getattr(channel, "id", None))
    if utcnow().weekday() == 0:
        try:
            await _send_period(bot, channel, weekly=True, is_test=is_test, _delivery=_delivery)
        except DispatchUnavailable as exc:
            if _delivery:
                if isinstance(exc, DispatchGuarded):
                    _delivery.skip("dispatch_guarded")
                else:
                    _delivery.failure(exc)
            logger.info("[OFFSEASON] Weekly dispatch unavailable: %s", exc)
        except Exception as exc:
            if _delivery:
                _delivery.failure(exc)
            logger.exception("[STATS EMBED] Off-season weekly send failed.")
    elif _delivery:
        _delivery.skip("not_scheduled")
