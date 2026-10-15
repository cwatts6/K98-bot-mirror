"""Independent supervised recovery monitor; no dependency on new processing work."""

import asyncio
import logging

import discord

from services import recovery_health
from services.legacy_export_snapshot_service import drain_thread
from services.recovery_runtime import observe_recovery
from stats_alerts.recovery_notifications import publish_recovery_alerts
from ui.views.recovery_view import RecoveryEntryView

logger = logging.getLogger(__name__)


async def observe_recovery_outcomes(bot):
    import bot_config

    unavailable = False
    outage_message = None
    while True:
        try:
            failures = await drain_thread(observe_recovery)
            await publish_recovery_alerts(bot)
            if failures:
                raise RuntimeError("One or more incident checks are unavailable")
            recovery_health.record_success()
            if unavailable:
                logger.info("recovery_observer available=true")
            unavailable = False
            if outage_message:
                await outage_message.edit(
                    content="Recovery monitoring has resumed. Review the recovery centre for outstanding incidents.",
                    view=RecoveryEntryView(),
                )
                outage_message = None
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            recovery_health.record_failure(exc)
            if not unavailable:
                logger.warning(
                    "recovery_observer available=false error_type=%s", type(exc).__name__
                )
            unavailable = True
            if outage_message is None:
                try:
                    channel = bot.get_channel(
                        bot_config.NOTIFY_CHANNEL_ID
                    ) or await bot.fetch_channel(bot_config.NOTIFY_CHANNEL_ID)
                    if int(channel.guild.id) != int(bot_config.GUILD_ID):
                        raise ValueError("Recovery notification guild differs.")
                    outage_message = await channel.send(
                        "Recovery monitoring is unavailable. Existing incidents and reservations are retained. The bot will retry checks automatically; recovery status must not be treated as healthy.",
                        view=RecoveryEntryView(),
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except Exception as alert_error:
                    logger.warning(
                        "recovery_monitor_alert_unavailable error_type=%s",
                        type(alert_error).__name__,
                    )
        await asyncio.sleep(30)


def register_recovery_monitor(bot, task_monitor):
    import bot_config

    bot.add_view(RecoveryEntryView())
    if bot_config.EXPORT_COORDINATION_ENABLED and not task_monitor.is_running("guided_recovery"):

        async def run():
            await observe_recovery_outcomes(bot)

        task_monitor.create("guided_recovery", run)
