from __future__ import annotations

import asyncio
import logging
import os

import discord

from bot_config import GUILD_ID, MGE_LEADERSHIP_CHANNEL_ID
from mge.mge_review_service import get_review_pool_with_summary
from mge.mge_roster_service import load_roster_state

logger = logging.getLogger(__name__)


async def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set")

    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info("Connected as %s", client.user)
        logger.info(
            "Guild ID configured: %s | Leadership channel: %s",
            GUILD_ID,
            MGE_LEADERSHIP_CHANNEL_ID,
        )

        event_id = int(os.getenv("MGE_SMOKE_EVENT_ID", "1"))

        payload = get_review_pool_with_summary(event_id)
        state = load_roster_state(event_id)
        logger.info("Review rows: %s", len(payload.get("rows", [])))
        logger.info("Roster awarded=%s waitlist=%s", len(state.awarded), len(state.waitlist))

        channel = client.get_channel(int(MGE_LEADERSHIP_CHANNEL_ID))
        if channel is None:
            channel = await client.fetch_channel(int(MGE_LEADERSHIP_CHANNEL_ID))

        await channel.send(
            f"✅ Task I smoke check passed for event {event_id}: "
            f"review_rows={len(payload.get('rows', []))}, "
            f"awarded={len(state.awarded)}, waitlist={len(state.waitlist)}"
        )
        await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
