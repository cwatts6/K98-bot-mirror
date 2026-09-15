from __future__ import annotations

import asyncio
from io import BytesIO
import logging
import os

import discord

from commands.kvk_personal_posting import post_stats_message
from embed_utils import build_stats_embed
from kvk.models.kvk_stats_card import KvkStatsCardContext, card_context_label
from kvk.rendering.kvk_stats_card_renderer import render_kvk_stats_card
from kvk.services.kvk_stats_card_service import (
    build_kvk_stats_card_payload,
    require_card_current,
    suppress_card_context,
)
from ui.views.kvk_stats_card_views import (
    KvkStatsCardView,
    require_card_destination,
)

logger = logging.getLogger(__name__)


def _card_enabled() -> bool:
    return os.environ.get("KVK_STATS_CARD_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


async def _read_avatar_bytes(user) -> bytes | None:
    avatar = getattr(user, "display_avatar", None) or getattr(user, "avatar", None)
    if avatar is None:
        return None
    try:
        if hasattr(avatar, "with_size"):
            avatar = avatar.with_size(128)
        if hasattr(avatar, "read"):
            return await avatar.read()
    except Exception:
        logger.debug("kvk_stats_card_avatar_read_failed user_id=%s", getattr(user, "id", None))
    return None


async def _build_card(
    row: dict, user, *, payload=None
) -> tuple[discord.File, KvkStatsCardView] | None:
    if not _card_enabled():
        return None
    payload = payload if payload is not None else await build_kvk_stats_card_payload(row)
    avatar_bytes = await _read_avatar_bytes(user)
    rendered = await asyncio.to_thread(render_kvk_stats_card, payload, avatar_bytes=avatar_bytes)
    if rendered is None:
        return None
    file = discord.File(BytesIO(rendered.image_bytes.getvalue()), filename=rendered.filename)
    view = KvkStatsCardView(payload=payload, rendered=rendered, owner_id=user.id)
    return file, view


async def post_kvk_stats_output(
    *,
    bot,
    ctx: discord.ApplicationContext,
    row: dict,
    user,
    use_fallback_chain: bool = False,
) -> tuple[bool, str]:
    """Use source-safe independent output whenever a card cannot be sent safely."""
    context = None if _card_enabled() else KvkStatsCardContext()
    payload = await build_kvk_stats_card_payload(row, context=context)
    channel = getattr(ctx, "channel", None)
    try:
        card = await _build_card(row, user, payload=payload)
        if card is not None and channel is not None:
            file, view = card
            await require_card_destination(ctx, user=user)
            await require_card_current(payload)
            view.guild_id = getattr(getattr(channel, "guild", None), "id", None)
            view.channel_id = getattr(channel, "id", None)
            view.message = await channel.send(
                files=[file], view=view, allowed_mentions=discord.AllowedMentions.none()
            )
            return True, "orig_channel"
    except Exception:
        logger.warning(
            "kvk_stats_card_unavailable governor_id=%s", payload.governor_id, exc_info=True
        )

    # No SQL-based legacy context, avatars or context-bearing file can escape on retry.
    safe_payload = suppress_card_context(payload)
    # The existing text formatter retains independent history, MM and tier breakdowns.
    # It does not consume camp/overall-rank context. Discard its optional dial attachment
    # and avatar so retries contain only independent text and the suppression notice.
    embeds, dial_file = await asyncio.to_thread(build_stats_embed, row, user)
    if dial_file is not None:
        dial_file.close()
    for embed in embeds:
        embed.set_image(url=None)
        embed.set_thumbnail(url=None)
    embeds[0].add_field(name="Source context", value=card_context_label(safe_payload), inline=False)
    embeds[0].set_footer(text="Independent stats retained. Request a new card for source context.")
    if use_fallback_chain:
        return await post_stats_message(bot, ctx, embeds=embeds)
    if channel is None:
        return False, "none"
    try:
        await channel.send(embeds=embeds, allowed_mentions=discord.AllowedMentions.none())
        return True, "orig_channel"
    except Exception:
        logger.warning("kvk_stats_fallback_send_failed governor_id=%s", payload.governor_id)
        return False, "none"
