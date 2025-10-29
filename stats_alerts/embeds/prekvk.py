# stats_alerts/embeds/prekvk.py
"""
Pre-KVK embed builder/sender (async-safe).

Blocking calls (DB, sheets, heavy IO) are delegated off the event loop using asyncio.to_thread
or via the async DB wrapper functions that themselves use to_thread.
"""
import asyncio
from datetime import timedelta
import logging
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL, KVK_BANNER_MAP, TARGETS_SHEET_ID, TIMELINE_SHEET_ID
from embed_utils import LocalTimeToggleView, format_event_time
from event_cache import get_all_upcoming_events
from stats_alerts.allkingdoms import load_allkingdom_blocks
from stats_alerts.formatters import fmt_honor
from stats_alerts.guard import claim_send, sent_today, sent_today_any
from stats_alerts.honors import get_latest_honor_top
from stats_alerts.kvk_meta import get_latest_kvk_metadata_sql
from stats_alerts.state import load_state, save_state
from utils import date_to_utc_start, ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)


class PreKvkSkip(Exception):
    """Raised to indicate the embed wasn't sent due to mutual exclusivity / limits."""


async def send_prekvk_embed(
    bot: Any,
    channel: discord.abc.Messageable,
    timestamp: str,
    *,
    is_test: bool = False,
) -> str:
    """
    Build and either edit or send the Pre-KVK embed. Returns 'edited' or 'sent'.
    Blocking work is offloaded using asyncio.to_thread or the async DB helpers.
    """
    # Load SQL metadata off thread (get_latest_kvk_metadata_sql uses get_conn_with_retries internally)
    try:
        meta_sql = await asyncio.to_thread(get_latest_kvk_metadata_sql)
    except Exception:
        logger.exception("[PREKVK] Failed to fetch KVK metadata (sql)")
        meta_sql = None

    kvk_no = meta_sql["kvk_no"] if meta_sql else "?"
    kvk_name = meta_sql["kvk_name"] if meta_sql else "KVK"
    reg_dt = meta_sql.get("registration") if meta_sql else None
    start_dt = meta_sql.get("start_date") if meta_sql else None
    end_dt = meta_sql.get("end_date") if meta_sql else None
    fight_start = meta_sql.get("fighting_start_date") if meta_sql else None
    pass4_scan = meta_sql.get("pass4_start_scan") if meta_sql else None

    # Date range (best-effort) — use simple formatting (avoid heavy operations)
    try:
        kvk_date_range = f"{start_dt:%d %b} – {end_dt:%d %b}" if start_dt and end_dt else ""
    except Exception:
        kvk_date_range = ""

    # Countdown helper
    def _days_until(d):
        if not d:
            return None
        try:
            td = date_to_utc_start(d)
            return (td.date() - utcnow().date()).days
        except Exception:
            return None

    def _fmt_dd(n):
        if n is None:
            return "—"
        if n < 0:
            return f"{abs(n)}d ago"
        if n == 0:
            return "today"
        return f"in {n}d"

    # Build embed skeleton
    embed = discord.Embed(
        title=f"🧭 Pre-KVK — {kvk_name} (KVK {kvk_no})",
        description=(f"**{kvk_date_range}**\n" if kvk_date_range else "")
        + f"Prep update **{timestamp}**\n\n"
        "Fighting hasn’t started yet. Here’s what’s ahead 👇",
        color=discord.Color.blurple(),
    )

    if CUSTOM_AVATAR_URL and CUSTOM_AVATAR_URL.lower().startswith(("http://", "https://")):
        try:
            embed.set_thumbnail(url=CUSTOM_AVATAR_URL)
        except Exception:
            pass

    banner_url = KVK_BANNER_MAP.get((kvk_name or "KVK").lower(), None)
    if banner_url:
        embed.set_image(url=banner_url)

    # Timeline
    tl_lines = []
    if reg_dt:
        try:
            tl_lines.append(f"📜 Registration: **{reg_dt:%d %b %Y}**")
        except Exception:
            tl_lines.append(f"📜 Registration: **{reg_dt}**")
    if start_dt:
        try:
            tl_lines.append(f"🗺 **KVK Map opens** : **{start_dt:%d %b %Y}**")
        except Exception:
            tl_lines.append(f"🗺 **KVK Map opens** : **{start_dt}**")
    if fight_start:
        df = _days_until(fight_start)
        try:
            tl_lines.append(f"⚔️ Fighting starts: **{fight_start:%d %b %Y}** ({_fmt_dd(df)})")
        except Exception:
            tl_lines.append(f"⚔️ Fighting starts: **{fight_start}** ({_fmt_dd(df)})")

    embed.add_field(
        name="Season timeline", value="\n".join(tl_lines) if tl_lines else "—", inline=False
    )

    # Pre-KVK Top-3s (overall + phases) — offload heavy DB aggregation
    try:
        tops = await asyncio.to_thread(
            load_allkingdom_blocks, int(kvk_no) if str(kvk_no).isdigit() else 0
        )
    except Exception:
        logger.exception("[PREKVK] Failed loading Pre-KVK top blocks")
        tops = {"overall": [], "p1": [], "p2": [], "p3": []}

    def _fmt_top_simple(rows, units="pts"):
        if not rows:
            return "—"
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, r in enumerate(rows[:3]):
            name = r.get("Name") or "Unknown"
            pts = int(r.get("Points") or 0)
            lines.append(f"{medals[i]} {name} — `{pts:,} {units}`")
        return "\n".join(lines)

    embed.add_field(
        name="🏆 Overall Pre-KVK Rankings:",
        value=_fmt_top_simple(tops.get("overall", []), "pts"),
        inline=False,
    )
    embed.add_field(
        name="🗡️ Phase 1 — Marauders", value=_fmt_top_simple(tops.get("p1", []), "pts"), inline=True
    )
    embed.add_field(
        name="🏗️ Phase 2 — Training", value=_fmt_top_simple(tops.get("p2", []), "pts"), inline=True
    )
    embed.add_field(
        name="🏕️ Phase 3 — Encampments",
        value=_fmt_top_simple(tops.get("p3", []), "pts"),
        inline=True,
    )

    # Honor rankings — fetch via honours module (runs off-thread)
    try:
        honor_top = await get_latest_honor_top(3)
    except Exception:
        logger.exception("[PREKVK] Honor block failed")
        honor_top = []

    if honor_top:
        embed.add_field(name="🏅 Honor Rankings (Top 3):", value=fmt_honor(honor_top), inline=False)
    else:
        next_lines = []
        if isinstance(pass4_scan, int):
            next_lines.append("📌 Honor Rankings will appear here as soon as available.")
        embed.add_field(
            name="🏅 Honor Rankings (Top 3):",
            value="\n".join(next_lines) if next_lines else "—",
            inline=False,
        )

    # Upcoming week (chronicle / major)
    try:
        upcoming = await asyncio.to_thread(get_all_upcoming_events)
    except Exception:
        logger.exception("[PREKVK] Failed to load events")
        upcoming = []

    now_utc = utcnow()
    week_ahead = now_utc + timedelta(days=7)

    week_events = []
    for e in upcoming:
        st = ensure_aware_utc(e.get("start_time"))
        if not st:
            continue
        if (now_utc - timedelta(hours=1)) <= st <= week_ahead:
            tnorm = (e.get("type") or "").strip().lower()
            if tnorm in ("chronicle", "major"):
                week_events.append({**e, "start_time": st})
    week_events = sorted(week_events, key=lambda ev: ev["start_time"])

    if week_events:

        def _event_line(e):
            name = (e.get("name") or e.get("title") or "Event").strip()
            ts = int(e["start_time"].timestamp())
            return f"• **{name}** — starts <t:{ts}:R>\n  {format_event_time(e['start_time'])}"

        embed.add_field(
            name="🗓️ Next 7 days:",
            value="\n".join(_event_line(e) for e in week_events[:12]),
            inline=False,
        )

    embed.add_field(
        name="📎 Get ready",
        value="Use **/mykvktargets** (targets are now LIVE) • **/subscribe** receive event reminders",
        inline=False,
    )

    tl_link = (
        f"https://docs.google.com/spreadsheets/d/{TIMELINE_SHEET_ID}" if TIMELINE_SHEET_ID else None
    )
    targets_link = (
        f"https://docs.google.com/spreadsheets/d/{TARGETS_SHEET_ID}" if TARGETS_SHEET_ID else None
    )
    link_parts = []
    if tl_link:
        link_parts.append(f"[Timeline]({tl_link})")
    if targets_link:
        link_parts.append(f"[Targets]({targets_link})")
    if link_parts:
        embed.add_field(name="🔗 Links", value=" • ".join(link_parts), inline=False)

    embed.set_footer(text="KD98 Discord Bot")

    view = (
        LocalTimeToggleView(week_events, prefix="prekvk_week", timeout=None)
        if week_events
        else None
    )

    # Load state and decide edit vs send (state is sync -> use directly)
    state = load_state()
    msg_id = state.get("prekvk_msg_id")
    message = None
    today_utc = utcnow().date()

    if msg_id:
        try:
            message = await channel.fetch_message(int(msg_id))
            if message and getattr(message, "created_at", None):
                try:
                    msg_created = ensure_aware_utc(message.created_at)
                except Exception:
                    msg_created = None
                if msg_created is None or msg_created.date() != today_utc:
                    message = None
                    state.pop("prekvk_msg_id", None)
                    save_state(state)
        except Exception:
            message = None
            if state.pop("prekvk_msg_id", None) is not None:
                save_state(state)

    # Silent edit path
    if message:
        try:
            await message.edit(embed=embed, view=view)
            logger.info(
                "[PREKVK] Edited existing message id=%s in channel=%s",
                getattr(message, "id", "?"),
                getattr(channel, "id", "?"),
            )
            return "edited"
        except Exception:
            logger.exception("[PREKVK] Edit failed; will send a fresh message.")
            if state.pop("prekvk_msg_id", None) is not None:
                save_state(state)

    # Fresh send path — mutual exclusivity + daily limits via guard (call via to_thread because guard uses file IO)
    if not is_test and await asyncio.to_thread(
        sent_today_any, ["offseason_daily", "offseason_weekly"]
    ):
        logger.info("[STATS EMBED] Off-season already posted today; skipping Pre-KVK.")
        raise PreKvkSkip()

    if not is_test and await asyncio.to_thread(sent_today, "prekvk_daily"):
        logger.info("[STATS EMBED] Pre-KVK already sent today; skipping.")
        raise PreKvkSkip()

    first_send_ping = not bool(state.get("prekvk_msg_id"))
    sent = await channel.send(
        embed=embed,
        content="@everyone" if (first_send_ping and not is_test) else None,
        view=view,
        allowed_mentions=discord.AllowedMentions(everyone=(first_send_ping and not is_test)),
    )
    logger.info(
        "[PREKVK] Sent new message id=%s in channel=%s",
        getattr(sent, "id", "?"),
        getattr(channel, "id", "?"),
    )

    try:
        state["prekvk_msg_id"] = sent.id
        save_state(state)
    except Exception:
        logger.exception("[PREKVK] Failed to persist message id")

    # Log to CSV claim_send (file IO) — do via to_thread to avoid blocking
    if not is_test:
        await asyncio.to_thread(claim_send, "prekvk_daily", max_per_day=1)

    return "sent"
