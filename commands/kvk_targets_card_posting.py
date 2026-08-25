from __future__ import annotations

import asyncio
from io import BytesIO
import logging
import os

import discord

from kvk.models.kvk_targets_card import KvkTargetsCardPayload
from kvk.rendering.kvk_targets_card_renderer import render_kvk_targets_card
from kvk.services.kvk_targets_card_service import build_kvk_targets_card_payload

logger = logging.getLogger(__name__)


def _card_enabled() -> bool:
    return os.environ.get("KVK_TARGETS_CARD_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _compact(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    val = float(value)
    abs_val = abs(val)
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs_val >= limit:
            return f"{val / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{int(val):,}"


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def build_targets_fallback_embed(payload: KvkTargetsCardPayload) -> discord.Embed:
    embed = discord.Embed(
        title=f"KVK Targets - {payload.governor_name}",
        description=f"{payload.display_kvk_label} | {payload.display_mode}",
        color=discord.Color.gold() if payload.target_state == "complete" else discord.Color.blue(),
    )
    embed.add_field(name="Status", value=payload.status_detail, inline=False)
    if payload.metrics:
        for metric in payload.metrics:
            if not metric.has_target:
                lines = [_compact(metric.current)]
                if metric.note:
                    lines.append(metric.note)
                embed.add_field(
                    name=metric.label,
                    value="\n".join(lines),
                    inline=False,
                )
                continue
            if metric.remaining is None:
                remaining = "progress unavailable"
            elif metric.remaining <= 0:
                remaining = "complete"
            else:
                remaining = f"{_compact(metric.remaining)} remaining"
            embed.add_field(
                name=metric.label,
                value=(
                    f"{_compact(metric.current)} / {_compact(metric.target)} - "
                    f"{_pct(metric.percent)}\n{remaining}"
                ),
                inline=False,
            )
    embed.add_field(name="Next Action", value=payload.next_action, inline=False)
    footer = f"GovernorID: {payload.governor_id}"
    if payload.last_refreshed:
        footer += f" | Targets refreshed {payload.last_refreshed}"
    embed.set_footer(text=footer)
    return embed


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


async def post_kvk_targets_output(
    interaction: discord.Interaction,
    governor_id: str | int,
    *,
    ephemeral: bool,
) -> KvkTargetsCardPayload:
    """Build and send modern targets output, falling back to an embed if image rendering fails."""
    payload = await build_kvk_targets_card_payload(governor_id)
    if _card_enabled():
        try:
            avatar_bytes = await _read_avatar_bytes(getattr(interaction, "user", None))
            rendered = await asyncio.to_thread(
                render_kvk_targets_card, payload, avatar_bytes=avatar_bytes
            )
            if rendered is not None:
                await _send_or_edit(
                    interaction,
                    file=discord.File(
                        BytesIO(rendered.image_bytes.getvalue()),
                        filename=rendered.filename,
                    ),
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
