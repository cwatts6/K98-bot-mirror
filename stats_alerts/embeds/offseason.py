# stats_alerts/embeds/offseason.py
"""
Off-season flow wrapper - delegates blocking guard/file IO to threads and uses the existing
async send_offseason_stats_embed_v2 to post embeds.
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
    # Use guard functions in a thread since they are sync file-IO
    try:
        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        if run_blocking_in_thread is not None:
            kvk_posted_today = (
                False
                if is_test
                else await run_blocking_in_thread(
                    sent_today,
                    "kvk",
                    name="sent_today_kvk",
                    meta={
                        "key": "kvk",
                        "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                    },
                )
            )
        else:
            logger.debug(
                "[STATS EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for sent_today(kvk) (consider converting to run_blocking_in_thread)"
            )
            kvk_posted_today = False if is_test else await asyncio.to_thread(sent_today, "kvk")

        if kvk_posted_today:
            logger.info("[STATS EMBED] KVK already posted today; skipping off-season daily.")
        else:
            try:
                await send_offseason_stats_embed_v2(
                    bot, channel=channel, is_weekly=False, mention_everyone=(not is_test)
                )
                # After sending, record claim_send via run_blocking_in_thread when available
                try:
                    if not is_test:
                        try:
                            from file_utils import run_blocking_in_thread
                        except Exception:
                            run_blocking_in_thread = None

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

                kvk_posted_today = (
                    False
                    if is_test
                    else (
                        await run_blocking_in_thread(
                            sent_today,
                            "kvk",
                            name="sent_today_kvk_weekly",
                            meta={
                                "key": "kvk",
                                "context": "weekly",
                                "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                            },
                        )
                        if run_blocking_in_thread is not None
                        else await asyncio.to_thread(sent_today, "kvk")
                    )
                )
            except Exception:
                kvk_posted_today = False

            if kvk_posted_today:
                logger.info("[STATS EMBED] KVK already posted today; skipping off-season weekly.")
            else:
                try:
                    # Check weekly guard
                    already_weekly = False
                    if not is_test:
                        try:
                            try:
                                from file_utils import run_blocking_in_thread
                            except Exception:
                                run_blocking_in_thread = None

                            if run_blocking_in_thread is not None:
                                already_weekly = await run_blocking_in_thread(
                                    sent_today,
                                    "offseason_weekly",
                                    name="sent_today_offseason_weekly",
                                    meta={
                                        "key": "offseason_weekly",
                                        "caller": "stats_alerts.embeds.offseason.send_offseason_flow",
                                    },
                                )
                            else:
                                already_weekly = await asyncio.to_thread(
                                    sent_today, "offseason_weekly"
                                )
                        except Exception:
                            already_weekly = False

                    if is_test or not already_weekly:
                        try:
                            await send_offseason_stats_embed_v2(
                                bot, channel=channel, is_weekly=True, mention_everyone=False
                            )
                            if not is_test:
                                try:
                                    try:
                                        from file_utils import run_blocking_in_thread
                                    except Exception:
                                        run_blocking_in_thread = None

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
                                    logger.exception(
                                        "[STATS EMBED] claim_send for offseason_weekly failed"
                                    )
                        except Exception:
                            logger.exception("[STATS EMBED] Off-season weekly send failed.")
                    else:
                        logger.info(
                            "[STATS EMBED] Off-season weekly already sent this Monday; skipping."
                        )
                except Exception:
                    logger.exception("[STATS EMBED] Weekly off-season dashboard failed")
    except Exception:
        logger.exception("[STATS EMBED] Weekly off-season guard failed")
