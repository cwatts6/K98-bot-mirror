from __future__ import annotations

import asyncio
from io import BytesIO
import logging
import os

import discord

from kvk.models.kvk_targets_card import KvkTargetsCardPayload
from kvk.rendering.kvk_targets_card_renderer import render_kvk_targets_card
from kvk.services.kvk_targets_card_service import build_kvk_targets_card_payload
from targets_embed import build_targets_fallback_embed

logger = logging.getLogger(__name__)


def _card_enabled() -> bool:
    return os.environ.get("KVK_TARGETS_CARD_ENABLED", "1").strip().lower() not in {
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
        logger.debug("kvk_targets_card_avatar_read_failed user_id=%s", getattr(user, "id", None))
    return None


async def _send_followup(
    interaction: discord.Interaction,
    *,
    ephemeral: bool,
    file: discord.File | None = None,
    embed: discord.Embed | None = None,
) -> None:
    if file is not None:
        file.reset(seek=True)
        await interaction.followup.send(file=file, ephemeral=ephemeral)
        return
    await interaction.followup.send(embed=embed, ephemeral=ephemeral)


async def _send_or_edit(
    interaction: discord.Interaction,
    *,
    ephemeral: bool,
    file: discord.File | None = None,
    embed: discord.Embed | None = None,
) -> None:
    message = getattr(interaction, "message", None)
    if message is not None:
        kwargs = {"content": None, "view": None, "attachments": []}
        if file is not None:
            kwargs["files"] = [file]
            kwargs["embeds"] = []
        if embed is not None:
            kwargs["embed"] = embed
        try:
            await message.edit(**kwargs)
            return
        except Exception:
            logger.warning(
                "kvk_targets_message_edit_failed falling_back_to_followup",
                exc_info=True,
            )
    await _send_followup(interaction, ephemeral=ephemeral, file=file, embed=embed)


async def _render_targets_file(
    payload: KvkTargetsCardPayload,
    *,
    user,
) -> discord.File | None:
    if not _card_enabled():
        return None
    avatar_bytes = await _read_avatar_bytes(user)
    rendered = await asyncio.to_thread(
        render_kvk_targets_card,
        payload,
        avatar_bytes=avatar_bytes,
    )
    if rendered is None:
        return None
    return discord.File(
        BytesIO(rendered.image_bytes.getvalue()),
        filename=rendered.filename,
    )


async def post_kvk_targets_output(
    interaction: discord.Interaction,
    governor_id: str | int,
    *,
    ephemeral: bool,
) -> KvkTargetsCardPayload:
    """Build and send modern targets output, falling back to an embed if image rendering fails."""
    payload = await build_kvk_targets_card_payload(governor_id)
    try:
        rendered_file = await _render_targets_file(
            payload,
            user=getattr(interaction, "user", None),
        )
        if rendered_file is not None:
            await _send_or_edit(
                interaction,
                file=rendered_file,
                ephemeral=ephemeral,
            )
            return payload
    except Exception:
        logger.exception("kvk_targets_card_render_or_send_failed governor_id=%s", governor_id)

    await _send_or_edit(
        interaction,
        embed=build_targets_fallback_embed(payload),
        ephemeral=ephemeral,
    )
    return payload


async def post_kvk_targets_channel_output(
    interaction: discord.Interaction,
    governor_id: str | int,
) -> KvkTargetsCardPayload:
    """Post the canonical target output publicly, retaining an ephemeral fallback."""
    payload = await build_kvk_targets_card_payload(governor_id)
    channel = getattr(interaction, "channel", None)
    try:
        rendered_file = await _render_targets_file(
            payload,
            user=getattr(interaction, "user", None),
        )
        if channel is not None and rendered_file is not None:
            await channel.send(file=rendered_file)
            return payload
    except Exception:
        logger.exception("kvk_targets_public_card_send_failed governor_id=%s", governor_id)

    embed = build_targets_fallback_embed(payload)
    if channel is not None:
        try:
            await channel.send(embed=embed)
            return payload
        except Exception:
            logger.exception("kvk_targets_public_embed_send_failed governor_id=%s", governor_id)
    await interaction.followup.send(embed=embed, ephemeral=True)
    return payload
