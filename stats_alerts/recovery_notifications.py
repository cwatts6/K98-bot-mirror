"""Recovery alert delivery; every alert links directly to guided actions."""

import discord

from services.legacy_export_snapshot_service import drain_thread
from services.recovery_runtime import alert_rows, claim_alert, record_alert
from ui.views.recovery_view import RecoveryEntryView, incident_embed


async def publish_recovery_alerts(bot):
    import bot_config

    rows = await drain_thread(alert_rows)
    if not rows:
        return True
    channel = bot.get_channel(bot_config.NOTIFY_CHANNEL_ID) or await bot.fetch_channel(
        bot_config.NOTIFY_CHANNEL_ID
    )
    if int(channel.guild.id) != int(bot_config.GUILD_ID):
        raise ValueError("Recovery notification guild differs from configuration.")
    complete = True
    for row in rows:
        embed = incident_embed(row)
        if not await drain_thread(claim_alert, row["IncidentID"]):
            complete = False
            continue
        message = None
        delivered_current_revision = False
        if row["AlertMessageID"] and row["AlertChannelID"] == channel.id:
            try:
                message = await channel.fetch_message(row["AlertMessageID"])
                delivered_current_revision = row["AlertedRevision"] == row["Revision"]
            except discord.NotFound:
                pass  # A deleted alert is recreated from durable incident state.
        if message is None:
            # Adopt an exactly marked bot alert after a lost send/SQL acknowledgement.
            # Bounded history absence is NOT proof that a business delivery failed.
            # These diagnostic alerts alone permit a five-minute duplicate-tolerant retry.
            async for candidate in channel.history(limit=100):
                if (
                    candidate.author.id == bot.user.id
                    and candidate.embeds
                    and getattr(candidate.embeds[0].footer, "text", None) == embed.footer.text
                ):
                    message = candidate
                    break
        if message is None:
            message = await channel.send(
                embed=embed,
                view=RecoveryEntryView(),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        elif not delivered_current_revision:
            await message.edit(
                embed=embed,
                view=RecoveryEntryView(),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        await drain_thread(record_alert, row["IncidentID"], row["Revision"], channel.id, message.id)
    return complete
