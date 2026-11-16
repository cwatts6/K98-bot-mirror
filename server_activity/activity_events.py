from __future__ import annotations

import logging

import discord

from bot_config import ACTIVITY_TRACKING_ENABLED
from server_activity.activity_models import ActivityEventType
from server_activity.activity_service import normalize_activity_event, record_activity_event

logger = logging.getLogger(__name__)

_LISTENERS_REGISTERED = False


def register_activity_listeners(bot: discord.Client) -> None:
    global _LISTENERS_REGISTERED
    if _LISTENERS_REGISTERED:
        logger.info("activity_listeners_already_registered")
        return

    bot.add_listener(_on_message_activity, "on_message")
    bot.add_listener(_on_raw_reaction_add_activity, "on_raw_reaction_add")
    bot.add_listener(_on_voice_state_update_activity, "on_voice_state_update")
    _LISTENERS_REGISTERED = True
    logger.info("activity_listeners_registered enabled=%s", ACTIVITY_TRACKING_ENABLED)


async def _on_message_activity(message: discord.Message) -> None:
    if not ACTIVITY_TRACKING_ENABLED:
        return
    if message.guild is None or getattr(message.author, "bot", False):
        return

    event = normalize_activity_event(
        event_type=ActivityEventType.MESSAGE,
        guild_id=getattr(message.guild, "id", None),
        channel_id=getattr(message.channel, "id", None),
        user_id=getattr(message.author, "id", None),
        metadata={"message_id": getattr(message, "id", None)},
    )
    await record_activity_event(event)


async def _on_raw_reaction_add_activity(payload: discord.RawReactionActionEvent) -> None:
    if not ACTIVITY_TRACKING_ENABLED:
        return
    if getattr(payload, "guild_id", None) is None:
        return

    member = getattr(payload, "member", None)
    if member is None:
        return
    if getattr(member, "bot", False):
        return

    event = normalize_activity_event(
        event_type=ActivityEventType.REACTION_ADD,
        guild_id=getattr(payload, "guild_id", None),
        channel_id=getattr(payload, "channel_id", None),
        user_id=getattr(payload, "user_id", None),
        metadata={
            "message_id": getattr(payload, "message_id", None),
            "emoji": str(getattr(payload, "emoji", ""))[:128],
        },
    )
    await record_activity_event(event)


async def _on_voice_state_update_activity(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
) -> None:
    if not ACTIVITY_TRACKING_ENABLED:
        return
    if getattr(member, "bot", False):
        return

    before_channel = getattr(before, "channel", None)
    after_channel = getattr(after, "channel", None)
    if before_channel == after_channel:
        return

    if before_channel is None and after_channel is not None:
        event_type = ActivityEventType.VOICE_JOIN
        channel_id = getattr(after_channel, "id", None)
    elif before_channel is not None and after_channel is None:
        event_type = ActivityEventType.VOICE_LEAVE
        channel_id = getattr(before_channel, "id", None)
    else:
        event_type = ActivityEventType.VOICE_MOVE
        channel_id = getattr(after_channel, "id", None)

    guild = getattr(member, "guild", None)
    event = normalize_activity_event(
        event_type=event_type,
        guild_id=getattr(guild, "id", None),
        channel_id=channel_id,
        user_id=getattr(member, "id", None),
        metadata={
            "before_channel_id": getattr(before_channel, "id", None),
            "after_channel_id": getattr(after_channel, "id", None),
        },
    )
    await record_activity_event(event)
