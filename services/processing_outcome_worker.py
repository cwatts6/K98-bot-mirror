"""One supervised observer for durable processing outcomes; no import/provider replay."""

import asyncio
import logging

logger = logging.getLogger(__name__)


def recover_failures():
    from services.legacy_export_snapshot_service import caller_runtime
    from services.stats_import_outcome_service import outcome_dal, settle_known_failure

    with caller_runtime() as runtime:
        if runtime is None:
            return
        for preparation_id in outcome_dal(runtime).pending_failures():
            settle_known_failure(runtime, preparation_id)


async def observe_processing_outcomes():
    from services.legacy_export_snapshot_service import drain_thread

    unavailable = False
    notifications_unavailable = False
    while True:
        try:
            await drain_thread(recover_failures)
            if unavailable:
                logger.info(
                    "processing_outcome_observer available=true action=resume_durable_discovery"
                )
            unavailable = False
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not unavailable:
                logger.warning(
                    "processing_outcome_observer available=false error_type=%s action=check_protected_runtime_and_SQL_receipt_contract",
                    type(exc).__name__,
                )
            unavailable = True
        try:
            from bot_loader import bot
            from stats_alerts.processing_notifications import observe_notifications

            await observe_notifications(bot)
            if notifications_unavailable:
                logger.info("processing_notifications available=true action=resume_registered_runs")
            notifications_unavailable = False
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not notifications_unavailable:
                logger.warning(
                    "processing_notifications available=false error_type=%s action=inspect_journal_and_protected_runtime",
                    type(exc).__name__,
                )
            notifications_unavailable = True
        await asyncio.sleep(30)


def register_processing_outcomes(task_monitor):
    import bot_config

    if bot_config.EXPORT_COORDINATION_ENABLED and not task_monitor.is_running(
        "processing_outcomes"
    ):
        task_monitor.create("processing_outcomes", observe_processing_outcomes)
