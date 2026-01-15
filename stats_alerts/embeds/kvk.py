# stats_alerts/embeds/kvk.py
"""
KVK embed builder/sender (async-safe).

Splits output into two embeds:
  - Embed 1 (orange): our kingdom highlights, metadata, quick commands, links
  - Embed 2 (aqua): overall KVK performance lists (Top 5)

Changes in this revision:
- Send both embeds together in a single channel.send(...) with embeds=[e1, e2]
  so they appear as a single grouped message.
- Add truncation safeguards for embed field values (Discord limit: 1024 chars).
  Truncation events are logged with logger.warning so they can be investigated.
- Embed 2 color set to Aqua (RGB 0,255,255).
- Top lists render Top 5 (medals for 1..3, numeric labels for 4..5).
"""
import asyncio
import logging
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL, KVK_BANNER_MAP, STATS_SHEET_ID
from stats_alerts.allkingdoms import load_allkingdom_blocks
from stats_alerts.formatters import abbr, fmt_dkp
from stats_alerts.honors import get_latest_honor_top
from stats_alerts.kvk_meta import get_latest_kvk_metadata, get_latest_kvk_metadata_sql

logger = logging.getLogger(__name__)

# Try once to import the centralized helper so we can use it consistently.
try:
    from file_utils import run_blocking_in_thread  # type: ignore
except Exception:
    run_blocking_in_thread = None  # type: ignore


def _truncate_and_log(field_name: str, text: str, max_len: int = 1024) -> str:
    """
    Truncate `text` to `max_len` characters if needed and log a warning.
    Discord embed field value max length is 1024.
    """
    if text is None:
        return "—"
    try:
        if len(text) > max_len:
            logger.warning(
                "[KVK EMBED] Field '%s' truncated from %d to %d characters",
                field_name,
                len(text),
                max_len,
            )
            # keep room for ellipsis
            return text[: max_len - 1] + "…"
    except Exception:
        # If len() fails for any weird reason, fall back to str() and truncate
        t = str(text)
        if len(t) > max_len:
            logger.warning(
                "[KVK EMBED] Field '%s' truncated (fallback) from %d to %d characters",
                field_name,
                len(t),
                max_len,
            )
            return t[: max_len - 1] + "…"
        return t
    return text


def _fmt_top_list(
    rows: list[dict], name_key: str, value_key: str, limit: int = 5, units=None
) -> str:
    if not rows:
        return "—"
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, r in enumerate(rows[:limit]):
        label = medals[i] if i < 3 else f"{i+1}."
        n = r.get(name_key) or r.get("name") or "Unknown"
        v = r.get(value_key)
        try:
            if units == "dkp":
                vstr = fmt_dkp(v)
            else:
                vstr = abbr(v)
        except Exception:
            vstr = str(v)
        lines.append(f"{label} {n} — `{vstr}`")
    return "\n".join(lines)


async def send_kvk_embed(
    bot: Any,
    channel: discord.abc.Messageable,
    timestamp: str,
    *,
    is_test: bool = False,
) -> None:
    # Prefer SQL metadata (blocking) -> offload
    try:
        if run_blocking_in_thread is not None:
            meta_sql = await run_blocking_in_thread(
                get_latest_kvk_metadata_sql,
                name="get_latest_kvk_metadata_sql",
                meta={"caller": "stats_alerts.embeds.kvk.send_kvk_embed"},
            )
        else:
            logger.debug(
                "[KVK EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for get_latest_kvk_metadata_sql (consider converting to run_blocking_in_thread)"
            )
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
            if run_blocking_in_thread is not None:
                meta = await run_blocking_in_thread(
                    get_latest_kvk_metadata,
                    name="get_latest_kvk_metadata_sheets",
                    meta={"caller": "stats_alerts.embeds.kvk.send_kvk_embed"},
                )
            else:
                logger.debug(
                    "[KVK EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for get_latest_kvk_metadata (consider converting to run_blocking_in_thread)"
                )
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
        if run_blocking_in_thread is not None:
            blocks = await run_blocking_in_thread(
                load_allkingdom_blocks,
                kvk_no,
                name="load_allkingdom_blocks",
                meta={"kvk_no": kvk_no},
            )
        else:
            logger.debug(
                "[KVK EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for load_allkingdom_blocks (consider converting to run_blocking_in_thread)"
            )
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

    players_kills = _fmt_top_list(blocks.get("players_by_kills", []), "name", "kills_gain", limit=5)
    kingdoms_kills = _fmt_top_list(
        blocks.get("kingdoms_by_kills", []), "kingdom", "kills_gain", limit=5
    )
    camps_kills = _fmt_top_list(
        blocks.get("camps_by_kills", []), "camp_name", "kills_gain", limit=5
    )

    our_topk = blocks.get("our_top_players", []) or []
    our_lines = []
    # Our Top players block (Top 5)
    if our_topk:
        medals = ["🥇", "🥈", "🥉"]
        top_lines = []
        for i, r in enumerate(our_topk[:5]):
            if i < 3:
                label = medals[i]
            else:
                label = f"{i+1}."
            name = r.get("name") or r.get("GovernorName") or "Unknown"
            kills = r.get("kills_gain")
            try:
                kills_s = abbr(kills)
            except Exception:
                kills_s = str(kills)
            top_lines.append(f"{label} {name} — `{kills_s}`")
        our_lines.append("**1198 Top 5 (Kills):**\n" + "\n".join(top_lines))

    our_king = blocks.get("our_kingdom")[0] if blocks.get("our_kingdom") else None
    our_camp = blocks.get("our_camp")[0] if blocks.get("our_camp") else None

    if our_king:
        try:
            k_kills = abbr(our_king.get("kills_gain"))
        except Exception:
            k_kills = str(our_king.get("kills_gain"))
        try:
            k_deads = abbr(our_king.get("deads"))
        except Exception:
            k_deads = str(our_king.get("deads"))
        try:
            k_dkp = fmt_dkp(our_king.get("dkp"))
        except Exception:
            k_dkp = str(our_king.get("dkp"))
        our_lines.append(f"👑 **Kingdom:** kills `{k_kills}` | deads `{k_deads}` | dkp `{k_dkp}`")

    if our_camp:
        try:
            c_kills = abbr(our_camp.get("kills_gain"))
        except Exception:
            c_kills = str(our_camp.get("kills_gain"))
        try:
            c_deads = abbr(our_camp.get("deads"))
        except Exception:
            c_deads = str(our_camp.get("deads"))
        try:
            c_dkp = fmt_dkp(our_camp.get("dkp"))
        except Exception:
            c_dkp = str(our_camp.get("dkp"))
        our_lines.append(
            f"🏕️ **{our_camp.get('camp_name','Our Camp')}:** kills `{c_kills}` | deads `{c_deads}` | dkp `{c_dkp}`"
        )

    our_block = "\n".join(our_lines) if our_lines else "—"

    # Honor Top-5 (get_latest_honor_top may return fewer; format as Top 5 if available)
    honor_top = []
    try:
        honor_top = await get_latest_honor_top(5)
    except Exception:
        logger.exception("[KVK EMBED] Honor block failed")
        honor_top = []

    honor_block = "—"
    if honor_top:
        # format as medals/numbering up to 5
        parts = []
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(honor_top[:5]):
            label = medals[i] if i < 3 else f"{i+1}."
            name = r.get("name") or r.get("GovernorName") or "Unknown"
            pts = r.get("points") or r.get("Points") or r.get("PointsEarned") or 0
            try:
                pts_i = int(pts)
                parts.append(f"{label} {name} — {pts_i:,}")
            except Exception:
                parts.append(f"{label} {name} — {pts}")
        honor_block = "\n".join(parts)

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

    # Embed 1: Our kingdom highlights + metadata + quick commands + links
    e1 = discord.Embed(
        title=f"🔥 {kvk_name} (KVK {kvk_no})",
        description=(
            (f"**{kvk_date_range}**\n" if kvk_date_range else "")
            + f"Stats updated **{timestamp}**\n\n"
        ),
        color=discord.Color.orange(),
    )
    if CUSTOM_AVATAR_URL and CUSTOM_AVATAR_URL.lower().startswith(("http://", "https://")):
        try:
            e1.set_thumbnail(url=CUSTOM_AVATAR_URL)
        except Exception:
            logger.exception("[KVK EMBED] Failed to set thumbnail")
    if banner_url:
        e1.set_image(url=banner_url)

    e1_val = _truncate_and_log("Our Highlights", our_block)
    e1.add_field(name="⭐ Our Highlights", value=e1_val, inline=False)
    if honor_block and honor_block != "—":
        e1.add_field(
            name="🏅 Honor Rankings (Top 5)",
            value=_truncate_and_log("Honor Rankings", honor_block),
            inline=False,
        )

    quick_cmds = "Use **/mykvkstats** to view your stats\nUse **/kvkrankings** to see top players"
    e1.add_field(
        name="📎 Quick Commands",
        value=_truncate_and_log("Quick Commands", quick_cmds),
        inline=False,
    )
    links_val = f"[Full KVK Stats]({sheet_link}) • [Dashboard](https://lookerstudio.google.com/s/usgUxj1t59U)"
    e1.add_field(name="🔗 Links", value=_truncate_and_log("Links", links_val), inline=False)
    e1.set_footer(text="KD98 Discord Bot")

    # Embed 2: Overall performance lists (Top 5) - color Aqua
    e2 = discord.Embed(
        title="📊 KVK Performance — Top 5",
        description="Overview of Top 5 performers across players, kingdoms and camps",
        color=discord.Color.from_rgb(0, 255, 255),
    )
    e2.add_field(
        name="👥 All Players — Top Kills",
        value=_truncate_and_log("All Players — Top Kills", players_kills),
        inline=False,
    )
    e2.add_field(
        name="🏰 Kingdoms — Top Kills",
        value=_truncate_and_log("Kingdoms — Top Kills", kingdoms_kills),
        inline=False,
    )
    e2.add_field(
        name="⛺ Camps — Top Kills",
        value=_truncate_and_log("Camps — Top Kills", camps_kills),
        inline=False,
    )
    e2.set_footer(text="KD98 Discord Bot")

    content = "@everyone" if not is_test else None
    allowed_mentions = discord.AllowedMentions(everyone=(not is_test))

    # Send both embeds together in a single message (so they appear as a combo)
    try:
        await channel.send(content=content, embeds=[e1, e2], allowed_mentions=allowed_mentions)
    except Exception:
        logger.exception("[KVK EMBED] Failed sending combined embeds")
