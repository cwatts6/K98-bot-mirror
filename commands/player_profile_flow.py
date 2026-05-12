"""Player profile interaction flow helpers."""

from __future__ import annotations

from io import BytesIO
import logging

import discord

from core.interaction_safety import response_is_done, send_or_followup
from embed_player_profile import build_player_profile_embed
from profile_cache import get_profile_cached, warm_cache
from ui.views.location_views import ProfileLinksView

logger = logging.getLogger(__name__)


def _clone_file_to_bytes(dfile: discord.File | None) -> tuple[bytes | None, str | None]:
    if not dfile:
        return None, None
    try:
        fp = getattr(dfile, "fp", None)
        if fp is None:
            logger.exception("[player_profile] discord.File has no fp; cannot clone")
            return None, dfile.filename
        try:
            fp.seek(0)
        except Exception:
            logger.exception("[player_profile] could not seek file %r", dfile.filename)
        data = fp.read()
        size = len(data) if data else 0
        logger.info("[player_profile] cloned file %r to bytes: %s bytes", dfile.filename, size)
        return (data if size > 0 else None), dfile.filename
    except Exception:
        logger.exception(
            "[player_profile] failed to clone file %r",
            getattr(dfile, "filename", None),
        )
        return None, getattr(dfile, "filename", None)


async def send_profile_to_channel(
    inter: discord.Interaction, gid: int, channel: discord.abc.Messageable
) -> None:
    logger.info("[player_profile] start gid=%s channel=%s", gid, getattr(channel, "id", "?"))

    warm_cache()
    data = get_profile_cached(gid)
    if not data:
        await send_or_followup(inter, f"GovernorID **{gid}** not found.", ephemeral=True)
        logger.info("[player_profile] not found gid=%s", gid)
        return

    card_file, profile_embed, _chart_file = await build_player_profile_embed(
        inter, data, card_scale=1.0
    )

    if card_file:
        try:
            profile_embed.set_image(url=f"attachment://{card_file.filename}")
        except Exception:
            logger.debug("[player_profile] failed setting attachment image", exc_info=True)

    card_bytes, card_name = _clone_file_to_bytes(card_file)
    fresh_files: list[discord.File] = []
    if card_bytes:
        fresh_files.append(discord.File(BytesIO(card_bytes), filename=card_name))

    if not response_is_done(inter):
        try:
            await inter.response.defer(ephemeral=True)
        except Exception:
            logger.debug("[player_profile] defer failed; continuing", exc_info=True)

    try:
        primary_msg = await channel.send(embeds=[profile_embed], files=fresh_files or None)
    except discord.Forbidden:
        logger.exception("[player_profile] forbidden to send in target channel")
        try:
            await inter.followup.send(
                "I don't have permission to post in that channel. Sending your profile here instead.",
                ephemeral=True,
            )
            await inter.followup.send(
                embeds=[profile_embed], files=fresh_files or None, ephemeral=True
            )
        except Exception:
            logger.exception("[player_profile] fallback ephemeral send failed")
        return

    logger.info(
        "[player_profile] sent message id=%s attachments=%s",
        primary_msg.id,
        len(primary_msg.attachments),
    )

    fallback_msg = None
    if len(primary_msg.attachments) == 0 and card_bytes:
        try:
            fallback_msg = await channel.send(
                file=discord.File(BytesIO(card_bytes), filename=card_name)
            )
            logger.info(
                "[player_profile] fallback upload id=%s attachments=%s",
                fallback_msg.id,
                len(fallback_msg.attachments),
            )
        except Exception:
            logger.exception("[player_profile] fallback upload failed")

    target_msg = primary_msg
    if not primary_msg.attachments and fallback_msg and fallback_msg.attachments:
        try:
            await primary_msg.delete()  # architecture-check: allow
        except Exception:
            logger.exception(
                "[player_profile] could not delete empty primary"
            )  # architecture-check: allow
        target_msg = fallback_msg

    def resolve_card_url(msg: discord.Message | None) -> str | None:
        if not msg or not msg.attachments:
            return None
        for att in msg.attachments:
            if card_name and att.filename == card_name:
                return att.url
        for att in msg.attachments:
            if (att.content_type or "").lower().startswith("image/"):
                return att.url
        return None

    card_url = resolve_card_url(target_msg)
    view = ProfileLinksView(card_url=card_url)

    try:
        await target_msg.edit(embeds=[profile_embed], view=view)
        logger.info(
            "[player_profile] edited message id=%s button=%s",
            target_msg.id,
            "yes" if card_url else "no",
        )
    except Exception:
        logger.exception("[player_profile] could not edit canonical message with button")

    try:
        await inter.followup.send(
            f"Posted profile for **{data.get('GovernorName') or gid}**.", ephemeral=True
        )
    except Exception:
        logger.debug("[player_profile] private ack failed", exc_info=True)
