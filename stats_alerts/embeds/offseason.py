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
        kvk_posted_today = False if is_test else await asyncio.to_thread(sent_today, "kvk")
        if kvk_posted_today:
            logger.info("[STATS EMBED] KVK already posted today; skipping off-season daily.")
        else:
            try:
                await send_offseason_stats_embed_v2(
                    bot, channel=channel, is_weekly=False, mention_everyone=(not is_test)
                )
                if not is_test and not await asyncio.to_thread(sent_today, "offseason_daily"):
                    await asyncio.to_thread(claim_send, "offseason_daily", max_per_day=1)
            except Exception:
                logger.exception("[STATS EMBED] Off-season daily send failed.")
    except Exception:
        logger.exception("[STATS EMBED] Off-season daily guard check failed.")

    # 2) Optional weekly post — only on Mondays
    try:
        if utcnow().weekday() == 0:
            if not is_test and await asyncio.to_thread(sent_today, "kvk"):
                logger.info("[STATS EMBED] KVK already posted today; skipping off-season weekly.")
            elif is_test or not await asyncio.to_thread(sent_today, "offseason_weekly"):
                try:
                    await send_offseason_stats_embed_v2(
                        bot, channel=channel, is_weekly=True, mention_everyone=False
                    )
                    if not is_test and not await asyncio.to_thread(sent_today, "offseason_weekly"):
                        await asyncio.to_thread(claim_send, "offseason_weekly", max_per_day=1)
                except Exception:
                    logger.exception("[STATS EMBED] Off-season weekly send failed.")
            else:
                logger.info("[STATS EMBED] Off-season weekly already sent this Monday; skipping.")
    except Exception:
        logger.exception("[STATS EMBED] Weekly off-season dashboard failed")
