from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

import discord

from embed_utils import fmt_short
from mge.dal import mge_event_dal

logger = logging.getLogger(__name__)


def _render_public_signup_list(names: list[str], limit: int = 1024) -> str:
    if not names:
        return "No signups yet."

    lines: list[str] = []
    used = 0

    for idx, name in enumerate(names):
        safe_name = str(name).replace("<", "‹").replace(">", "›")
        line = f"- {safe_name}\n"
        if used + len(line) > limit:
            remaining = len(names) - idx
            suffix = f"...and {remaining} more"
            if used + len(suffix) <= limit:
                lines.append(suffix)
            break
        lines.append(line)
        used += len(line)

    value = "".join(lines).rstrip()
    return value or "No signups yet."


def build_mge_signup_embed(
    event_row: dict[str, Any], public_signup_names: list[str] | None = None
) -> discord.Embed:
    embed = discord.Embed(
        title=f"🏆 {event_row.get('EventName', 'MGE Sign-Up')}",
        description="MGE signup is now open.",
        color=0x2ECC71,
        timestamp=datetime.now(UTC),
    )
    embed.add_field(
        name="Variant", value=str(event_row.get("VariantName") or "Unknown"), inline=True
    )
    embed.add_field(name="Mode", value=str(event_row.get("EventMode") or "controlled"), inline=True)
    embed.add_field(name="Status", value=str(event_row.get("Status") or "signup_open"), inline=True)

    if event_row.get("StartUtc"):
        embed.add_field(name="Start", value=fmt_short(event_row["StartUtc"]), inline=True)
    if event_row.get("EndUtc"):
        embed.add_field(name="End", value=fmt_short(event_row["EndUtc"]), inline=True)
    if event_row.get("SignupCloseUtc"):
        embed.add_field(
            name="Signup Closes", value=fmt_short(event_row["SignupCloseUtc"]), inline=True
        )

    names = public_signup_names or []
    embed.add_field(name="Signup Count", value=str(len(names)), inline=True)
    embed.add_field(name="Signups (Public)", value=_render_public_signup_list(names), inline=False)

    rules = str(event_row.get("RulesText") or "").strip()
    if rules:
        embed.add_field(name="Rules", value=rules[:1024], inline=False)

    embed.set_footer(text="MGE • Auto-created from calendar")
    return embed


async def sync_event_signup_embed(
    *,
    bot: discord.Client,
    event_id: int,
    signup_channel_id: int,
    now_utc: datetime | None = None,
) -> bool:
    row = mge_event_dal.fetch_event_for_embed(event_id)
    if not row:
        logger.warning("mge_embed_sync_skip reason=event_not_found event_id=%s", event_id)
        return False

    # TODO: replace with real query once signup service DAL lands
    public_signup_names: list[str] = mge_event_dal.fetch_public_signup_names(event_id)

    channel = bot.get_channel(signup_channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(signup_channel_id)
        except Exception:
            logger.exception(
                "mge_embed_sync_failed reason=channel_unavailable channel_id=%s", signup_channel_id
            )
            return False

    if not isinstance(channel, discord.abc.Messageable):
        logger.error(
            "mge_embed_sync_failed reason=channel_not_messageable channel_id=%s", signup_channel_id
        )
        return False

    embed = build_mge_signup_embed(row, public_signup_names=public_signup_names)
    msg_id = row.get("SignupEmbedMessageId")
    message = None

    if msg_id:
        try:
            message = await channel.fetch_message(int(msg_id))
            await message.edit(embed=embed)
        except discord.NotFound:
            message = None
        except Exception:
            logger.exception(
                "mge_embed_sync_edit_failed event_id=%s message_id=%s", event_id, msg_id
            )

    if message is None:
        try:
            message = await channel.send(embed=embed)
        except Exception:
            logger.exception("mge_embed_sync_send_failed event_id=%s", event_id)
            return False

    timestamp = now_utc.astimezone(UTC) if now_utc else datetime.now(UTC)
    return mge_event_dal.update_event_embed_ids(
        event_id=event_id,
        message_id=int(message.id),
        channel_id=int(channel.id),
        now_utc=timestamp,
    )


def build_mge_main_embed(event: dict, public_signup_names: list[str]) -> discord.Embed:
    mode = str(event.get("EventMode", "controlled")).lower()
    title = event.get("EventName", "MGE Event")
    variant = event.get("VariantName", "Unknown")
    start_utc = event.get("StartUtc")
    end_utc = event.get("EndUtc")
    close_utc = event.get("SignupCloseUtc")
    rules_text = event.get("RulesText") or "No rules configured."

    embed = discord.Embed(title=title, description=f"Variant: **{variant}**")
    embed.add_field(name="Start", value=fmt_short(start_utc), inline=True)
    embed.add_field(name="End", value=fmt_short(end_utc), inline=True)
    embed.add_field(name="Signup Close", value=fmt_short(close_utc), inline=True)
    embed.add_field(name="Mode", value=mode, inline=True)
    embed.add_field(name="Signup Count", value=str(len(public_signup_names)), inline=True)

    if public_signup_names:
        # Governor names only (no mentions, commander, priority)
        signup_block = "\n".join(f"- {name}" for name in public_signup_names[:50])
    else:
        signup_block = "No signups yet."

    embed.add_field(name="Signups (Public)", value=signup_block, inline=False)
    embed.add_field(name="Rules", value=rules_text[:1024], inline=False)
    return embed
