# stats_alerts/interface.py
import asyncio
import logging
from typing import Any

from bot_config import OFFSEASON_STATS_CHANNEL_ID, STATS_ALERT_CHANNEL_ID
from utils import utcnow

from .delivery_outcomes import DeliveryResult, delivery_outcome
from .dispatch_reservations import clear_prekvk_message
from .embeds import (
    kvk as kvk_mod,
    offseason as off_mod,
    prekvk as prekvk_mod,
    send_kingdom_summary as ks_mod,
)
from .guard import claim_send, read_counts_for, sent_today_any
from .kvk_meta import is_kvk_fighting_open

logger = logging.getLogger(__name__)


@delivery_outcome("seasonal")
async def _send_stats_update_embed(
    bot: Any,
    timestamp: str,
    is_kvk: bool,
    is_test: bool = False,
    _delivery=None,
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
            await clear_prekvk_message()
        except Exception:
            logger.exception("[PREKVK] Failed to clear prekvk_msg_id on fighting-open.")

    # Choose channel id
    if effective_is_kvk:
        channel_id = STATS_ALERT_CHANNEL_ID
    elif is_kvk:
        channel_id = STATS_ALERT_CHANNEL_ID
    else:
        channel_id = OFFSEASON_STATS_CHANNEL_ID

    route = "fighting" if effective_is_kvk else "prekvk" if is_kvk else "offseason"
    _delivery.begin("kingdom_summary_daily", channel_id=OFFSEASON_STATS_CHANNEL_ID)
    _delivery.route = route
    channel = bot.get_channel(channel_id)
    if not channel:
        _delivery.skip("primary_destination_unavailable")
        _delivery.begin(route, channel_id=channel_id)
        _delivery.failure(ValueError("missing destination"))
        _delivery.update(reason="missing_destination")
        return

    def include(value, component, destination):
        if isinstance(value, DeliveryResult):
            _delivery.attempts[-1:] = value.attempts
        elif _delivery.attempts[-1].reason == "no_receipt":
            _delivery.update(reason="legacy_unverified")

    # Preserve the standalone summary before all primary guards.
    try:
        ks_channel = bot.get_channel(OFFSEASON_STATS_CHANNEL_ID)
        result = await ks_mod(bot, ks_channel, timestamp, is_test=is_test, _delivery=_delivery)
        include(result, "kingdom_summary_daily", OFFSEASON_STATS_CHANNEL_ID)
    except Exception as exc:
        _delivery.failure(exc)
        logger.exception("[STATS EMBED] Kingdom Summary send failed.")

    _delivery.begin(route, channel_id=channel_id)
    if effective_is_kvk:
        if not is_test and sent_today_any(["offseason_daily", "offseason_weekly"]):
            _delivery.skip("offseason_already_posted")
            return
        if not is_test and read_counts_for("kvk", utcnow().date().isoformat()) >= 3:
            _delivery.skip("daily_cap")
            return
        result = await kvk_mod.send_kvk_embed(
            bot, channel, timestamp, is_test=is_test, _delivery=_delivery
        )
        include(result, "fighting", channel_id)
        receipt = _delivery.attempts[-1]
        if (
            not is_test
            and receipt.outcome == "sent"
            and receipt.acknowledged
            and receipt.message_id
        ):
            _delivery.update(claim="not_confirmed")
            claimed = claim_send("kvk", max_per_day=3)
            _delivery.update(claim="confirmed" if claimed is True else "not_confirmed")
        return

    if is_kvk:
        result = await prekvk_mod.send_prekvk_embed(
            bot, channel, timestamp, is_test=is_test, _delivery=_delivery
        )
        include(result, "prekvk", channel_id)
        return

    result = await off_mod.send_offseason_flow(
        bot, channel, timestamp, is_test=is_test, _delivery=_delivery
    )
    include(result, "offseason", channel_id)


async def send_stats_update_embed(bot: Any, timestamp: str, is_kvk: bool, is_test: bool = False):
    """Publish once through the existing selectors and return per-attempt evidence."""
    return await _send_stats_update_embed(
        bot, timestamp, is_kvk, is_test=is_test, return_outcome=True
    )
