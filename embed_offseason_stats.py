# embed_offseason_stats.py
"""Offseason combo embed sender with SQL owned by the stats-alert DAL."""

from __future__ import annotations

import logging
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL
from file_utils import get_conn_with_retries
from stats_alerts.offseason_dal import (
    get_kingdom_summary,
    get_kingdom_summary_weekly,
    load_all_daily,
    load_all_weekly,
    pick_daily_snapshot_date as _pick_daily_snapshot_date,
)

logger = logging.getLogger(__name__)

try:
    from stats_alerts.embeds.kingdom_summary import (
        build_kingdom_summary_embed,
        load_latest_and_prev_rows,
    )
except Exception:
    load_latest_and_prev_rows = None
    build_kingdom_summary_embed = None


def _fmt_short(n: Any) -> str:
    try:
        x = float(int(n))
    except Exception:
        return str(n)
    absx = abs(x)
    if absx >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}B"
    if absx >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if absx >= 1_000:
        return f"{x/1_000:.2f}K"
    return f"{int(x):,}"


def _fmt(n: Any) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


# ----------------------------- Embeds -----------------------------


def _kingdom_summary_line(summary: dict) -> str:
    delta = int(summary["power_delta_top300"])
    arrow = "🟢⬆️" if delta > 0 else ("🔴⬇️" if delta < 0 else "⏸️")
    return (
        f"**Total (Top 300) Power:** {_fmt_short(summary['total_power_top300'])}  •  "
        f"**Power Delta:** {_fmt_short(abs(delta))} {arrow}  •  "
        f"**Players:** {_fmt(summary['total_players'])}"
    )


def _kingdom_summary_line_weekly(weekly: dict, players: int) -> str:
    delta = int(weekly["weekly_delta"])
    arrow = "🟢⬆️" if delta > 0 else ("🔴⬇️" if delta < 0 else "⏸️")
    return (
        f"**Total (Top 300) Power:** {_fmt_short(weekly['top300_end'])}  •  "
        f"**Power Delta (Weekly):** {_fmt_short(abs(delta))} {arrow}  •  "
        f"**Players:** {_fmt(players)}"
    )


def _fmt_list(title: str, rows: list[tuple[str, int]]) -> tuple[str, str]:
    if not rows:
        return title, "—"
    lines = [f"🥇 **{rows[0][0]}** — {_fmt(rows[0][1])}"]
    if len(rows) > 1:
        lines.append(f"🥈 {rows[1][0]} — {_fmt(rows[1][1])}")
    if len(rows) > 2:
        lines.append(f"🥉 {rows[2][0]} — {_fmt(rows[2][1])}")
    return title, "\n".join(lines)


# --- new small helper to format top lists with medals/numeric labels ---
def _fmt_top10_list(rows: list[tuple[str, int]], limit: int) -> str:
    """
    Format rows into multiline string:
    - rows: list[(name, value)]
    - limit: maximum number to show (safety)
    Uses medals for 1..3 and numeric labels for 4+.
    """
    if not rows:
        return "—"
    medals = ["🥇", "🥈", "🥉"]
    out_lines = []
    for i, (name, val) in enumerate(rows[:limit]):
        if i < 3:
            label = medals[i]
        else:
            label = f"{i+1}."
        # format values using existing _fmt_short / _fmt helpers where appropriate
        try:
            val_str = _fmt_short(val)
        except Exception:
            try:
                val_str = _fmt(val)
            except Exception:
                val_str = str(val)
        out_lines.append(f"{label} {name} — {val_str}")
    return "\n".join(out_lines)


# New: send_offseason_stats_embed_v2 now accepts include_kingdom_summary
async def send_offseason_stats_embed_v2(
    bot,
    ctx: discord.ApplicationContext | None = None,
    *,
    is_weekly: bool = False,
    channel: discord.abc.Messageable | None = None,
    target_channel_id: int | None = None,
    mention_everyone: bool = False,
    include_kingdom_summary: bool = True,
) -> None:
    """
    Sends a combo of embeds (kingdom summary + 3 supporting embeds) for either:
      - daily (is_weekly=False): kingdom summary with daily comparison
      - weekly (is_weekly=True): kingdom summary with 7-day comparison

    include_kingdom_summary controls whether the KS embed is included in the combo;
    off-season wrapper will set this False when KS was already sent to avoid duplication.
    """
    try:
        from bot_config import NOTIFY_CHANNEL_ID
    except Exception:
        NOTIFY_CHANNEL_ID = None

    # Channel resolution (same as before)
    ch = getattr(ctx, "channel", None) if ctx else None
    if ch is None and channel is not None:
        ch = channel
    if ch is None and target_channel_id is not None:
        ch = bot.get_channel(target_channel_id)
    if ch is None and NOTIFY_CHANNEL_ID is not None:
        ch = bot.get_channel(NOTIFY_CHANNEL_ID)
    if ch is None:
        logger.warning("[OFFSEASON EMBED] No channel resolved.")
        return

    # Load supporting data
    with get_conn_with_retries() as conn:
        cur = conn.cursor()

        if is_weekly:
            data = load_all_weekly(cur)
            time_tag = "Last Week"
            snapshot_text = "Last completed week (UTC)"
        else:
            data = load_all_daily(cur)
            time_tag = "Most Recent Day"
            snap_date = _pick_daily_snapshot_date(cur)
            snapshot_text = f"Stats for **{snap_date.isoformat()} (UTC day)**"

    # Build kingdom summary embed (if requested)
    e1 = None
    if include_kingdom_summary:
        # If centralized builder available, use it with days offset
        if callable(build_kingdom_summary_embed) and callable(load_latest_and_prev_rows):
            days = 7 if is_weekly else 1
            try:
                try:
                    from file_utils import run_blocking_in_thread
                except Exception:
                    run_blocking_in_thread = None

                if run_blocking_in_thread is not None:
                    latest_row, prev_row = await run_blocking_in_thread(
                        load_latest_and_prev_rows, days, name="offseason_load_ks_rows"
                    )
                else:
                    import asyncio

                    latest_row, prev_row = await asyncio.to_thread(load_latest_and_prev_rows, days)
            except Exception:
                logger.exception("[OFFSEASON] Failed to load KS rows via centralized loader")
                latest_row, prev_row = None, None

            title_prefix = "Weekly Kingdom Summary" if is_weekly else "Daily Kingdom Summary"
            timestamp = snapshot_text
            try:
                e1 = build_kingdom_summary_embed(
                    latest_row, prev_row, timestamp, title_prefix=title_prefix
                )
            except Exception:
                logger.exception("[OFFSEASON] build_kingdom_summary_embed failed; falling back.")
                e1 = None

            # If builder produced embed, attempt to claim KS ping (same key as standalone)
            if e1 is not None:
                try:
                    try:
                        from stats_alerts.guard import claim_send
                    except Exception:
                        claim_send = None
                    if claim_send is not None and not mention_everyone:
                        # attempt to claim via run_blocking_in_thread else to_thread
                        try:
                            from file_utils import run_blocking_in_thread
                        except Exception:
                            run_blocking_in_thread = None

                        key = "kingdom_summary_weekly" if is_weekly else "kingdom_summary_daily"
                        ping_allowed = False
                        if run_blocking_in_thread is not None:
                            try:
                                ping_allowed = bool(
                                    await run_blocking_in_thread(
                                        claim_send, key, name="claim_send_offseason_ks"
                                    )
                                )
                            except Exception:
                                logger.exception("[OFFSEASON] claim_send for KS failed")
                        else:
                            try:
                                import asyncio

                                ping_allowed = bool(await asyncio.to_thread(claim_send, key))
                            except Exception:
                                logger.exception("[OFFSEASON] claim_send (to_thread) failed")
                        if ping_allowed and not is_weekly:
                            # set mention only if requested and claim_successful
                            e1.content = "@everyone" if mention_everyone else None
                            # the actual channel.send call below will set allowed_mentions,
                            # we use a local flag instead to control mention behavior.
                except Exception:
                    logger.exception("[OFFSEASON] KS claim/ping attempt failed")
        else:
            # Fallback simple summary if no centralized builder
            with get_conn_with_retries() as conn:
                cur = conn.cursor()
                try:
                    summary = get_kingdom_summary(cur)
                    if is_weekly:
                        weekly = get_kingdom_summary_weekly(cur)
                        summary_text = _kingdom_summary_line_weekly(
                            weekly, summary["total_players"]
                        )
                        e1 = discord.Embed(
                            title="📊 KD98 Stats Update (Weekly • Off-season)",
                            description=summary_text,
                            colour=discord.Colour.blurple(),
                        )
                        e1.add_field(
                            name="Snapshot", value="Last completed week (UTC)", inline=False
                        )
                    else:
                        snap_date = _pick_daily_snapshot_date(cur)
                        summary_text = _kingdom_summary_line(summary)
                        e1 = discord.Embed(
                            title="📊 KD98 Stats Update (Daily • Off-season)",
                            description=summary_text,
                            colour=discord.Colour.blurple(),
                        )
                        e1.add_field(name="Snapshot", value=snapshot_text, inline=False)
                    if CUSTOM_AVATAR_URL:
                        e1.set_thumbnail(url=CUSTOM_AVATAR_URL)
                    e1.set_footer(text="KD98 Discord Bot")
                except Exception:
                    logger.exception("[OFFSEASON EMBED] Fallback summary embed creation failed.")
                    e1 = None

    # Supporting embeds (always included in off-season combo)
    e2 = discord.Embed(title=f"🛡️ Forts ({time_tag})", colour=discord.Colour.orange())
    name, val = _fmt_list("Forts (Started + Joined)", data.get("forts", []))
    e2.add_field(name=name, value=val or "—", inline=False)

    e3 = discord.Embed(
        title=f"🏗️ Building • 🧪 Tech • 🤝 Helps ({time_tag})", colour=discord.Colour.blue()
    )
    for key, label in [
        ("building", "Building Minutes"),
        ("tech", "Tech Donations"),
        ("helps", "Helps"),
    ]:
        name, val = _fmt_list(label, data.get(key, []))
        e3.add_field(name=name, value=val or "—", inline=True)

    e4 = discord.Embed(title=f"🌾 RSS ({time_tag})", colour=discord.Colour.green())
    name, val = _fmt_list("RSS Gathered", data.get("rss_gathered", []))
    e4.add_field(name=name, value=val or "—", inline=True)
    if data.get("rss_assisted"):
        name, val = _fmt_list("RSS Assisted", data.get("rss_assisted", []))
        e4.add_field(name=name, value=val or "—", inline=True)

    # Decide content/mentions:
    content = "@everyone" if (mention_everyone and include_kingdom_summary) else None
    allowed = discord.AllowedMentions(everyone=(mention_everyone and include_kingdom_summary))
    embeds_to_send = [e for e in (e1, e2, e3, e4) if e is not None]
    if not embeds_to_send:
        logger.warning("[OFFSEASON EMBED] Nothing to send.")
        return

    await ch.send(content=content, embeds=embeds_to_send, allowed_mentions=allowed)
