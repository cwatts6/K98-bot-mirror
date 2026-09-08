# stats_alerts/embeds/offseason.py
"""
Off-season flow wrapper - delegates blocking guard/file IO to threads and uses the existing
async send_offseason_stats_embed_v2 to post embeds.

Adjusted to avoid duplicate Kingdom Summary posts: if the KS for the period has already
been sent, pass include_kingdom_summary=False to the combo sender so it doesn't send KS again.
"""

import asyncio
import logging
from typing import Any

from embed_offseason_stats import send_offseason_stats_embed_v2
from stats_alerts.guard import claim_send, sent_today
from utils import utcnow

logger = logging.getLogger(__name__)


async def send_offseason_flow(bot: Any, channel, timestamp: str, *, is_test: bool = False) -> None:
    # 1) Daily post — strictly once per day + 12h cooldown (cooldown handled in scheduling logic outside of this wrapper)
    try:
        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        if run_blocking_in_thread is not None:
            daily_posted_today = (
                False
                if is_test
                else await run_blocking_in_thread(
                    sent_today,
                    "offseason_daily",
                    name="sent_today_offseason_daily",
                    meta={
                        "key": "offseason_daily",
                        "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                    },
                )
            )
        else:
            logger.debug(
                "[STATS EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for sent_today(offseason_daily)"
            )
            daily_posted_today = (
                False if is_test else await asyncio.to_thread(sent_today, "offseason_daily")
            )

        if daily_posted_today:
            logger.info("[STATS EMBED] Offseason daily already posted today; skipping.")
        else:
            # Decide if KS was already sent today. If yes, don't include KS in the combo to avoid duplication.
            try:
                if run_blocking_in_thread is not None:
                    ks_posted_today = (
                        False
                        if is_test
                        else await run_blocking_in_thread(
                            sent_today,
                            "kingdom_summary_daily",
                            name="sent_today_kingdom_summary_check",
                        )
                    )
                else:
                    ks_posted_today = (
                        False
                        if is_test
                        else await asyncio.to_thread(sent_today, "kingdom_summary_daily")
                    )
            except Exception:
                logger.exception("[OFFSEASON] KS sent_today check failed; assuming not sent.")
                ks_posted_today = False

            try:
                await send_offseason_stats_embed_v2(
                    bot,
                    channel=channel,
                    is_weekly=False,
                    mention_everyone=(not is_test),
                    include_kingdom_summary=(not ks_posted_today),
                )
                # After sending, record claim_send for offseason_daily
                try:
                    if not is_test:
                        if run_blocking_in_thread is not None:
                            await run_blocking_in_thread(
                                claim_send,
                                "offseason_daily",
                                name="claim_send_offseason_daily",
                                meta={
                                    "key": "offseason_daily",
                                    "max_per_day": 1,
                                    "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                                },
                            )
                        else:
                            await asyncio.to_thread(claim_send, "offseason_daily", max_per_day=1)
                except Exception:
                    logger.exception("[STATS EMBED] claim_send for offseason_daily failed")
            except Exception:
                logger.exception("[STATS EMBED] Off-season daily send failed.")
    except Exception:
        logger.exception("[STATS EMBED] Off-season daily guard check failed.")

    # 2) Optional weekly post — only on Mondays
    try:
        if utcnow().weekday() == 0:
            try:
                try:
                    from file_utils import run_blocking_in_thread
                except Exception:
                    run_blocking_in_thread = None

                weekly_posted_today = (
                    False
                    if is_test
                    else (
                        await run_blocking_in_thread(
                            sent_today,
                            "offseason_weekly",
                            name="sent_today_offseason_weekly",
                            meta={
                                "key": "offseason_weekly",
                                "context": "weekly",
                                "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                            },
                        )
                        if run_blocking_in_thread is not None
                        else await asyncio.to_thread(sent_today, "offseason_weekly")
                    )
                )
            except Exception:
                weekly_posted_today = False

            if weekly_posted_today:
                logger.info("[STATS EMBED] Offseason weekly already posted today; skipping.")
            else:
                # Decide if weekly KS was already posted; avoid duplicating it inside the weekly combo if so.
                try:
                    if run_blocking_in_thread is not None:
                        ks_weekly_posted = (
                            False
                            if is_test
                            else await run_blocking_in_thread(
                                sent_today,
                                "kingdom_summary_weekly",
                                name="sent_today_ks_weekly_check",
                            )
                        )
                    else:
                        ks_weekly_posted = (
                            False
                            if is_test
                            else await asyncio.to_thread(sent_today, "kingdom_summary_weekly")
                        )
                except Exception:
                    logger.exception(
                        "[OFFSEASON] KS weekly sent_today check failed; assuming not sent."
                    )
                    ks_weekly_posted = False

                try:
                    await send_offseason_stats_embed_v2(
                        bot,
                        channel=channel,
                        is_weekly=True,
                        mention_everyone=False,
                        include_kingdom_summary=(not ks_weekly_posted),
                    )
                    if not is_test:
                        try:
                            if run_blocking_in_thread is not None:
                                await run_blocking_in_thread(
                                    claim_send,
                                    "offseason_weekly",
                                    name="claim_send_offseason_weekly",
                                    meta={
                                        "key": "offseason_weekly",
                                        "max_per_day": 1,
                                        "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                                    },
                                )
                            else:
                                await asyncio.to_thread(
                                    claim_send, "offseason_weekly", max_per_day=1
                                )
                        except Exception:
                            logger.exception("[STATS EMBED] claim_send for offseason_weekly failed")
                except Exception:
                    logger.exception("[STATS EMBED] Off-season weekly send failed.")
    except Exception:
        logger.exception("[STATS EMBED] Weekly off-season guard failed")
