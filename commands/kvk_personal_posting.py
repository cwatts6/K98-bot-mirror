# commands/kvk_personal_posting.py
"""Command-adjacent helper: Discord channel fallback posting for KVK personal stats.

Contains post_stats_embeds(), which requires Discord transport types.
Extracted from services.kvk_personal_service to keep the service layer Discord-free.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger(__name__)


async def post_stats_embeds(
    bot,
    ctx: discord.ApplicationContext,
    embeds: list,
    file,
) -> tuple[bool, str]:
    """
    Post stats embeds using the full channel fallback chain.

    Chain: original invoking channel → KVK_PLAYER_STATS_CHANNEL_ID → NOTIFY_CHANNEL_ID → DM.

    Args:
        bot:    The Discord bot instance (used for get_channel lookups).
        ctx:    The ApplicationContext (used to resolve the original channel).
        embeds: List of embed objects to post.
        file:   A file object (or None) to attach. If a fallback channel is tried,
                the file's underlying stream is rewound to position 0 before each attempt
                so the same file object can be used across multiple sends.

    Returns:
        (posted: bool, channel_used: str) — whether posting succeeded and which channel was used.
    """
    files = [file] if file is not None else None
    return await post_stats_message(bot, ctx, embeds=embeds, files=files)


async def post_stats_message(
    bot,
    ctx: discord.ApplicationContext,
    *,
    content: str | None = None,
    embeds: list | None = None,
    files: list | None = None,
    view=None,
) -> tuple[bool, str]:
    """Post a KVK personal stats message through the existing fallback channel chain."""
    from bot_config import KVK_PLAYER_STATS_CHANNEL_ID, NOTIFY_CHANNEL_ID

    def _rewind_file() -> None:
        """Rewind attached file streams so they can be resent on fallback."""
        if not files:
            return
        for item in files:
            fp = getattr(item, "fp", None)
            if fp is not None and hasattr(fp, "seek"):
                try:
                    fp.seek(0)
                except Exception:
                    pass

    async def _send_to(ch: discord.abc.Messageable, *, label: str) -> bool:
        _rewind_file()
        try:
            kwargs = {
                "content": content,
                "embeds": embeds or None,
                "files": files or None,
                "view": view,
            }
            kwargs = {key: value for key, value in kwargs.items() if value is not None}
            message = await ch.send(**kwargs)
            if view is not None and hasattr(view, "message"):
                view.message = message
            logger.info("[kvk_personal_posting] post_stats_embeds posted to %s", label)
            return True
        except discord.Forbidden:
            logger.warning(
                "[kvk_personal_posting] post_stats_embeds Forbidden in %s (id=%s)",
                label,
                getattr(ch, "id", None),
            )
            return False
        except Exception:
            logger.exception(
                "[kvk_personal_posting] post_stats_embeds error in %s (id=%s)",
                label,
                getattr(ch, "id", None),
            )
            return False

    def _can_send(ch: discord.abc.Messageable) -> bool:
        try:
            guild = getattr(ch, "guild", None)
            if not guild:
                return True
            me = guild.get_member(bot.user.id) if hasattr(guild, "get_member") else None
            if me is None:
                return True
            return ch.permissions_for(me).send_messages
        except Exception:
            return True

    # 1) Original invoking channel
    try:
        orig_ch = getattr(ctx, "channel", None)
        if orig_ch and _can_send(orig_ch):
            if await _send_to(orig_ch, label=f"orig_channel:{getattr(orig_ch, 'id', '?')}"):
                return (True, "orig_channel")
    except Exception:
        logger.exception("[kvk_personal_posting] post_stats_embeds orig_channel attempt failed")

    # 2) KVK player stats channel
    try:
        kvk_ch = bot.get_channel(KVK_PLAYER_STATS_CHANNEL_ID)
        if kvk_ch and _can_send(kvk_ch):
            if await _send_to(kvk_ch, label=f"kvk_channel:{KVK_PLAYER_STATS_CHANNEL_ID}"):
                return (True, "kvk_channel")
    except Exception:
        logger.exception("[kvk_personal_posting] post_stats_embeds kvk_channel attempt failed")

    # 3) Notify channel
    try:
        notify_ch = bot.get_channel(NOTIFY_CHANNEL_ID)
        if notify_ch and _can_send(notify_ch):
            if await _send_to(notify_ch, label=f"notify_channel:{NOTIFY_CHANNEL_ID}"):
                return (True, "notify_channel")
    except Exception:
        logger.exception("[kvk_personal_posting] post_stats_embeds notify_channel attempt failed")

    # 4) DM fallback
    try:
        user = getattr(ctx, "user", None) or getattr(ctx, "author", None)
        if user:
            if await _send_to(user, label=f"dm:{getattr(user, 'id', '?')}"):
                return (True, "dm")
    except Exception:
        logger.exception("[kvk_personal_posting] post_stats_embeds DM attempt failed")

    logger.warning("[kvk_personal_posting] post_stats_embeds all channels failed")
    return (False, "none")
