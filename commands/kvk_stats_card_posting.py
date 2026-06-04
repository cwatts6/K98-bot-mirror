from __future__ import annotations

import asyncio
from io import BytesIO
import logging
import os

import discord

from commands.kvk_personal_posting import post_stats_message
from embed_utils import build_stats_embed
from kvk.rendering.kvk_stats_card_renderer import render_kvk_stats_card
from kvk.services.kvk_stats_card_service import build_kvk_stats_card_payload
from ui.views.kvk_stats_card_views import KvkStatsCardView

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


async def _build_card(row: dict, user) -> tuple[discord.File, KvkStatsCardView] | None:
    if not _card_enabled():
        return None
    payload = await build_kvk_stats_card_payload(row)
    avatar_bytes = await _read_avatar_bytes(user)
    rendered = await asyncio.to_thread(render_kvk_stats_card, payload, avatar_bytes=avatar_bytes)
    if rendered is None:
        return None
    file = discord.File(BytesIO(rendered.image_bytes.getvalue()), filename=rendered.filename)
    view = KvkStatsCardView(payload=payload, rendered=rendered)
    return file, view


def _legacy_output(row: dict, user) -> tuple[list, list]:
    embeds, file = build_stats_embed(row, user)
    files = [file] if file is not None else []
    return embeds, files


async def post_kvk_stats_output(
    *,
    bot,
    ctx: discord.ApplicationContext,
    row: dict,
    user,
    use_fallback_chain: bool = False,
) -> tuple[bool, str]:
    """Post the modern KVK stats card, falling back to the legacy embeds on failure."""
    try:
        card = await _build_card(row, user)
    except Exception:
        logger.exception("kvk_stats_card_build_failed governor_id=%s", row.get("GovernorID"))
        card = None

    if card is not None:
        file, view = card
        if use_fallback_chain:
            return await post_stats_message(bot, ctx, files=[file], view=view)
        try:
            channel = getattr(ctx, "channel", None)
            if channel is not None:
                view.message = await channel.send(files=[file], view=view)
                return True, "orig_channel"
        except Exception:
            logger.exception(
                "kvk_stats_card_send_failed governor_id=%s falling_back=True",
                row.get("GovernorID"),
            )

    try:
        embeds, files = _legacy_output(row, user)
    except Exception:
        logger.exception(
            "kvk_stats_legacy_embed_build_failed governor_id=%s", row.get("GovernorID")
        )
        raise

    if use_fallback_chain:
        return await post_stats_message(bot, ctx, embeds=embeds, files=files)

    channel = getattr(ctx, "channel", None)
    if channel is None:
        return False, "none"
    try:
        if files:
            try:
                await channel.send(embeds=embeds, files=files)
            except Exception:
                logger.exception(
                    "kvk_stats_legacy_file_send_failed governor_id=%s retrying_embeds_only=True",
                    row.get("GovernorID"),
                )
                await channel.send(embeds=embeds)
        else:
            await channel.send(embeds=embeds)
        return True, "orig_channel"
    except Exception:
        logger.exception("kvk_stats_legacy_send_failed governor_id=%s", row.get("GovernorID"))
        return False, "none"
