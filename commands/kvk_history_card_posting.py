from __future__ import annotations

import asyncio
from io import BytesIO
import logging

import discord

from kvk.rendering.kvk_history_renderer import (
    build_last3_text_fallback,
    render_kvk_history_last3_card,
)
from services import kvk_history_service
from ui.views.kvk_history_card_views import KvkHistoryCardView

logger = logging.getLogger(__name__)


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
        logger.debug("kvk_history_card_avatar_read_failed user_id=%s", getattr(user, "id", None))
    return None


async def _send_followup(
    target: discord.ApplicationContext | discord.Interaction,
    *,
    content: str | None = None,
    file: discord.File | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool,
) -> discord.Message | None:
    kwargs = {"content": content, "view": view, "ephemeral": ephemeral}
    if file is not None:
        kwargs["file"] = file
    if hasattr(target, "followup"):
        try:
            return await target.followup.send(wait=True, **kwargs)
        except TypeError:
            return await target.followup.send(**kwargs)
    return None


async def post_kvk_history_output(
    target: discord.ApplicationContext | discord.Interaction,
    *,
    user: discord.User | discord.Member,
    governor_id: str | int,
    ephemeral: bool,
) -> None:
    """Post the modern KVK history card journey, falling back to text if rendering fails."""
    payload = await asyncio.to_thread(kvk_history_service.build_kvk_history_payload, governor_id)
    avatar_bytes = await _read_avatar_bytes(user)
    try:
        rendered = await asyncio.to_thread(
            render_kvk_history_last3_card,
            payload,
            avatar_bytes=avatar_bytes,
        )
    except Exception:
        logger.exception("kvk_history_last3_card_render_failed governor_id=%s", governor_id)
        rendered = None

    if rendered is None:
        await _send_followup(
            target,
            content=build_last3_text_fallback(payload),
            ephemeral=ephemeral,
        )
        return

    view = KvkHistoryCardView(
        payload=payload,
        rendered=rendered,
        author_id=user.id,
        avatar_bytes=avatar_bytes,
    )
    file = discord.File(BytesIO(rendered.image_bytes.getvalue()), filename=rendered.filename)
    message = await _send_followup(target, file=file, view=view, ephemeral=ephemeral)
    view.message = message
