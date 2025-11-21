# stats_alerts/embeds/kvk.py
"""
KVK embed builder/sender (async-safe).

All blocking DB/IO calls are delegated off the event loop.
"""
import asyncio
import logging
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL, KVK_BANNER_MAP, STATS_SHEET_ID
from stats_alerts.allkingdoms import load_allkingdom_blocks
from stats_alerts.formatters import abbr, fmt_dkp, fmt_honor, fmt_top
from stats_alerts.honors import get_latest_honor_top
from stats_alerts.kvk_meta import get_latest_kvk_metadata, get_latest_kvk_metadata_sql

logger = logging.getLogger(__name__)


async def send_kvk_embed(
    bot: Any,
    channel: discord.abc.Messageable,
    timestamp: str,
    *,
    is_test: bool = False,
) -> None:
    # Prefer SQL metadata (blocking) -> offload
    try:
        meta_sql = await asyncio.to_thread(get_latest_kvk_metadata_sql)
    except Exception:
        logger.exception("[KVK EMBED] get_latest_kvk_metadata_sql failed")
        meta_sql = None

    if meta_sql and meta_sql.get("start_date") and meta_sql.get("end_date"):
        kvk_no = meta_sql["kvk_no"]
        kvk_name = meta_sql["kvk_name"]
        start_dt, end_dt = meta_sql["start_date"], meta_sql["end_date"]
        try:
            kvk_date_range = f"{start_dt:%d %b} – {end_dt:%d %b}"
        except Exception:
            kvk_date_range = ""
        banner_url = KVK_BANNER_MAP.get((kvk_name or "KVK").lower(), None)
    else:
        # sheets fallback (blocking) -> offload
        try:
            meta = await asyncio.to_thread(get_latest_kvk_metadata)
        except Exception:
            logger.exception("[KVK EMBED] get_latest_kvk_metadata (sheets) failed")
            meta = None

        if meta:
            kvk_no = meta["kvk_no"]
            kvk_name = meta["kvk_name"]
            kvk_date_range = f"{meta['start_date']} – {meta['end_date']}"
            banner_url = KVK_BANNER_MAP.get(kvk_name.lower(), None)
        else:
            kvk_no = "?"
            kvk_name = "KVK"
            kvk_date_range = ""
            banner_url = None

    # Load heavy all-kingdom blocks off-thread
    try:
        # load_allkingdom_blocks uses get_conn_with_retries internally
        blocks = await asyncio.to_thread(load_allkingdom_blocks, kvk_no)
    except Exception:
        logger.exception("[KVK EMBED] Failed to load all kingdom blocks")
        blocks = {
            "players_by_kills": [],
            "players_by_deads": [],
            "players_by_dkp": [],
            "kingdoms_by_kills": [],
            "kingdoms_by_deads": [],
            "kingdoms_by_dkp": [],
            "camps_by_kills": [],
            "camps_by_deads": [],
            "camps_by_dkp": [],
            "our_top_players": [],
            "our_kingdom": [],
            "our_camp": [],
        }

    players_kills = fmt_top(blocks.get("players_by_kills", []), "name", "kills_gain")

    kingdoms_kills = fmt_top(blocks.get("kingdoms_by_kills", []), "kingdom", "kills_gain")

    camps_kills = fmt_top(blocks.get("camps_by_kills", []), "camp_name", "kills_gain")

    our_king = blocks.get("our_kingdom")[0] if blocks.get("our_kingdom") else None
    our_camp = blocks.get("our_camp")[0] if blocks.get("our_camp") else None
    our_topk = blocks.get("our_top_players", []) or []

    topk_lines = []
    for i, r in enumerate(our_topk[:3]):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        topk_lines.append(f"{medal} {r.get('name')} — `{abbr(r.get('kills_gain'))}`")

    our_lines = []
    if topk_lines:
        our_lines.append("**1198 Top 3 (Kills):**\n" + "\n".join(topk_lines))
    if our_king:
        our_lines.append(
            f"👑 **Kingdom:** kills `{abbr(our_king.get('kills_gain'))}` | deads `{abbr(our_king.get('deads'))}` | dkp `{fmt_dkp(our_king.get('dkp'))}`"
        )
    if our_camp:
        our_lines.append(
            f"🏕️ **{our_camp.get('camp_name','Our Camp')}:** kills `{abbr(our_camp.get('kills_gain'))}` | deads `{abbr(our_camp.get('deads'))}` | dkp `{fmt_dkp(our_camp.get('dkp'))}`"
        )

    our_block = "\n".join(our_lines) if our_lines else "—"

    logger.info(
        "[KVK EMBED] Rows -> players(kills=%d) | kingdoms(kills=%d) | camps(kills=%d)",
        len(blocks.get("players_by_kills", [])),
        len(blocks.get("kingdoms_by_kills", [])),
        len(blocks.get("camps_by_kills", [])),
    )

    sheet_link = (
        f"https://docs.google.com/spreadsheets/d/{STATS_SHEET_ID}"
        if STATS_SHEET_ID
        else "https://docs.google.com"
    )
    embed = discord.Embed(
        title=f"🔥 {kvk_name} (KVK {kvk_no})",
        description=(
            (f"**{kvk_date_range}**\n" if kvk_date_range else "")
            + f"Stats updated **{timestamp}**\n\n"
        ),
        color=discord.Color.orange(),
    )

    if CUSTOM_AVATAR_URL and CUSTOM_AVATAR_URL.lower().startswith(("http://", "https://")):
        try:
            embed.set_thumbnail(url=CUSTOM_AVATAR_URL)
        except Exception:
            logger.exception("[KVK EMBED] Failed to set thumbnail")

    if banner_url:
        embed.set_image(url=banner_url)

    embed.add_field(name="⭐ Our Highlights", value=our_block, inline=False)

    # Honour Top-3
    try:
        honor_top = await get_latest_honor_top(3)
        if honor_top:
            embed.add_field(
                name="🏅 Honor Rankings (Top 3)", value=fmt_honor(honor_top), inline=False
            )
    except Exception:
        logger.exception("[KVK EMBED] Honor block failed")

    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="👥 All Players — Top Kills", value=players_kills, inline=False)
    embed.add_field(name="🏰 Kingdoms — Top Kills", value=kingdoms_kills, inline=False)
    embed.add_field(name="⛺ Camps — Top Kills", value=camps_kills, inline=False)

    embed.add_field(
        name="📎 Quick Commands",
        value="Use **/mykvkstats** to view your stats\nUse **/kvkrankings** to see top players",
        inline=False,
    )
    embed.add_field(
        name="🔗 Links",
        value=f"[Full KVK Stats]({sheet_link}) • [Dashboard](https://lookerstudio.google.com/s/usgUxj1t59U)",
        inline=False,
    )
    embed.set_footer(text="KD98 Discord Bot")

    content = "@everyone" if not is_test else None
    await channel.send(
        embed=embed, content=content, allowed_mentions=discord.AllowedMentions(everyone=True)
    )
