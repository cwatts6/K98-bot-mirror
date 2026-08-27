# stats_alerts/interface.py
import asyncio
import logging
from typing import Any

from bot_config import OFFSEASON_STATS_CHANNEL_ID, STATS_ALERT_CHANNEL_ID
from utils import utcnow

from .embeds import (
    kvk as kvk_mod,
    offseason as off_mod,
    prekvk as prekvk_mod,
    send_kingdom_summary as ks_mod,
)
from .guard import claim_send, read_counts_for, sent_today_any
from .kvk_meta import is_kvk_fighting_open
from .state import load_state, save_state

logger = logging.getLogger(__name__)


async def send_stats_update_embed(
    bot: Any,
    timestamp: str,
    is_kvk: bool,
    is_test: bool = False,
) -> None:
    """
    Public orchestrator. Keeps the original behaviour but delegates to embed modules.
    """

    # Prefer run_blocking_in_thread (telemetry); fallback to asyncio.to_thread otherwise
    try:
        from file_utils import run_blocking_in_thread

        fighting_open = await run_blocking_in_thread(
            is_kvk_fighting_open,
            name="is_kvk_fighting_open",
            meta={
                "caller": "stats_alerts.interface.send_stats_update_embed",
                "timestamp": timestamp,
                "is_kvk_request": bool(is_kvk),
            },
        )
    except Exception:
        # Flag: fallback path still uses asyncio.to_thread and should be converted
        logger.debug(
            "[STATS ALERT] run_blocking_in_thread not available; using asyncio.to_thread fallback for is_kvk_fighting_open (consider converting to run_blocking_in_thread)"
        )
        try:
            fighting_open = await asyncio.to_thread(is_kvk_fighting_open)
        except Exception:
            fighting_open = False

    effective_is_kvk = bool(is_kvk and fighting_open)

    # If fighting opened, clear any stored Pre-KVK message id
    if effective_is_kvk:
        try:
            state = load_state()
            if state.pop("prekvk_msg_id", None) is not None:
                save_state(state)
                logger.info("[PREKVK] Fighting opened — cleared stored prekvk_msg_id.")
        except Exception:
            logger.exception("[PREKVK] Failed to clear prekvk_msg_id on fighting-open.")

    # Choose channel id
    if effective_is_kvk:
        channel_id = STATS_ALERT_CHANNEL_ID
    elif is_kvk:
        channel_id = STATS_ALERT_CHANNEL_ID
    else:
        channel_id = OFFSEASON_STATS_CHANNEL_ID

    channel = bot.get_channel(channel_id)
    if not channel:
        logger.warning("[STATS ALERT] Could not find channel id %s.", channel_id)
        return

    # New: attempt to send the daily Kingdom Summary first (runs once-per-day guard inside)
    try:
        kschannel_id = OFFSEASON_STATS_CHANNEL_ID
        ks_channel = bot.get_channel(kschannel_id)
        await ks_mod(bot, ks_channel, timestamp, is_test=is_test)
    except Exception:
        logger.exception("[STATS EMBED] Kingdom Summary send failed.")

    # KVK path (only once Pass 4 opened)
    if effective_is_kvk:
        # off-season mutual exclusivity
        if not is_test and sent_today_any(["offseason_daily", "offseason_weekly"]):
            logger.info("[STATS EMBED] Off-season already posted today; skipping KVK.")
            return
        # respect daily cap
        if not is_test and read_counts_for("kvk", utcnow().date().isoformat()) >= 3:
            logger.info("[STATS EMBED] KVK daily limit reached, skipping broadcast.")
            return
        try:
            await kvk_mod.send_kvk_embed(bot, channel, timestamp, is_test=is_test)
            if not is_test:
                claim_send("kvk", max_per_day=3)
        except Exception:
            logger.exception("[STATS EMBED] KVK send failed.")
        return

    # Pre-KVK path (KVK but before Pass 4)
    if is_kvk:
        # If a Pre-KVK msg id exists, do silent edit path in module
        try:
            action = await prekvk_mod.send_prekvk_embed(bot, channel, timestamp, is_test=is_test)
            # If fresh send happened, log
            if action == "sent" and not is_test:
                claim_send("prekvk_daily", max_per_day=1)
            return
        except prekvk_mod.PreKvkSkip:
            # The module signals it skipped due to mutual exclusivity or limits
            return
        except Exception:
            logger.exception("[STATS EMBED] Pre-KVK send failed.")
            return

    # Off-season path
    try:
        await off_mod.send_offseason_flow(bot, channel, timestamp, is_test=is_test)
    except Exception:
        logger.exception("[STATS EMBED] Off-season flow failed.")
