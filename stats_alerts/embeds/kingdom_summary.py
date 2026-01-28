# stats_alerts/embeds/kingdom_summary.py
"""
Daily Kingdom Summary embed (updated formatting).

Changes in this version:
- Kingdom Rank shown as a full integer (no fmt_short).
- Split stats into two groups: Core Stats (Power / Players / CH25) and
  Additional Stats (KP / Kills / Deads / HealedTroops).
- Enhanced indicators: colored emoji + arrow and bold formatting to make changes stand out.
  - For regular stats: 🟢 ↑ (increase), 🟠 – (no change/unknown), 🔴 ↓ (decrease)
  - Indicator is bolded (e.g. **🟢 ↑**) and the signed delta value is also bolded.
- Stat lines now include emojis for quicker scanning.
- Uses project's formatting helpers (fmt_short) where appropriate and CUSTOM_AVATAR_URL.
- Posts once-per-day using the existing CSV guard (key: "kingdom_summary_daily").
- Centralized loader + embed builder so callers (offseason, schedulers) can build
  the same embed for daily or weekly (days offset).
- send_kingdom_summary preserves the existing daily guard/claim behavior and uses
  the shared loader/builder.
- RangedPoints is fetched and available for later use but intentionally not displayed.
"""

import asyncio
from datetime import date, datetime, timedelta
import logging
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL
from file_utils import fetch_one_dict, get_conn_with_retries
from stats_alerts.guard import claim_send, sent_today
from utils import fmt_short

logger = logging.getLogger(__name__)


def _fmt_short_safe(v: float | None) -> str:
    if v is None:
        return "—"
    try:
        return fmt_short(v)
    except Exception:
        try:
            return f"{int(v):,}"
        except Exception:
            return str(v)


def _fmt_int_safe(v: float | None) -> str:
    if v is None:
        return "—"
    try:
        return f"{int(v):,}"
    except Exception:
        try:
            return str(int(float(v)))
        except Exception:
            return str(v)


def compute_delta(curr: float | None, prev: float | None) -> float | None:
    if curr is None or prev is None:
        return None
    try:
        return float(curr) - float(prev)
    except Exception:
        return None


def _indicator(delta: float | None, invert_for_rank: bool = False) -> str:
    """
    Return a colored, bold indicator for a delta:
      - Increase:    **🟢 ↑**
      - No change:   **🟠 –**
      - Decrease:    **🔴 ↓**
    If invert_for_rank is True the semantics are inverted (useful for rank when needed).
    If delta is None return "–" (not bolded).
    """
    if delta is None:
        return "–"
    try:
        # For regular stats: positive is good (green up). For invert_for_rank, flip sign interpretation.
        positive_is_good = not invert_for_rank
        if delta > 0:
            if positive_is_good:
                return "**🟢 ↑**"
            else:
                return "**🔴 ↓**"
        if delta < 0:
            if positive_is_good:
                return "**🔴 ↓**"
            else:
                return "**🟢 ↑**"
        # delta == 0
        return "**🟠 –**"
    except Exception:
        return "–"


def _fmt_signed_short(delta: float | None, *, integer: bool = False) -> str:
    if delta is None:
        return "—"
    try:
        if integer:
            val = int(round(delta))
            return f"{val:+d}"
        else:
            sign = "+" if delta > 0 else "-" if delta < 0 else "+"
            return f"{sign}{_fmt_short_safe(abs(delta))}"
    except Exception:
        try:
            return f"{float(delta):+.2f}"
        except Exception:
            return str(delta)


def load_latest_and_prev_rows(days: int = 1) -> tuple[dict | None, dict | None]:
    """
    Blocking DB access: returns (latest_row, previous_row).
    previous_row: tries to find a row with CONVERT(date, [Last Update]) == latest_date - days,
    otherwise falls back to the most recent row before latest.

    Use:
      - days=1 : daily semantics (yesterday or last prior)
      - days=7 : weekly semantics (7 days before latest or last prior)
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT TOP 1
                    [KINGDOM_POWER],
                    [Governors],
                    [KP],
                    [KILL],
                    [DEAD],
                    [CH25],
                    [HealedTroops],
                    [RangedPoints],
                    [Last Update],
                    [KINGDOM_RANK],
                    [KINGDOM_SEED]
                FROM ROK_TRACKER.dbo.KS
                ORDER BY [Last Update] DESC
                """)
            latest = fetch_one_dict(cur)
            if not latest:
                return None, None

            last_update = latest.get("Last Update")
            latest_dt = None
            try:
                if isinstance(last_update, (datetime, date)):
                    latest_dt = (
                        last_update.date() if isinstance(last_update, datetime) else last_update
                    )
                else:
                    latest_dt = datetime.fromisoformat(str(last_update)).date()
            except Exception:
                latest_dt = None

            prev_row = None
            if latest_dt:
                target_date = latest_dt - timedelta(days=days)
                cur.execute(
                    """
                    SELECT TOP 1
                        [KINGDOM_POWER],
                        [Governors],
                        [KP],
                        [KILL],
                        [DEAD],
                        [CH25],
                        [HealedTroops],
                        [RangedPoints],
                        [Last Update],
                        [KINGDOM_RANK],
                        [KINGDOM_SEED]
                    FROM ROK_TRACKER.dbo.KS
                    WHERE CONVERT(date, [Last Update]) = ?
                    ORDER BY [Last Update] DESC
                    """,
                    (target_date,),
                )
                prev_row = fetch_one_dict(cur)

            # fallback to most recent row before latest if exact target day isn't present
            if prev_row is None:
                cur.execute(
                    """
                    SELECT TOP 1
                        [KINGDOM_POWER],
                        [Governors],
                        [KP],
                        [KILL],
                        [DEAD],
                        [CH25],
                        [HealedTroops],
                        [RangedPoints],
                        [Last Update],
                        [KINGDOM_RANK],
                        [KINGDOM_SEED]
                    FROM ROK_TRACKER.dbo.KS
                    WHERE [Last Update] < ?
                    ORDER BY [Last Update] DESC
                    """,
                    (latest.get("Last Update"),),
                )
                prev_row = fetch_one_dict(cur)

            return latest, prev_row
    except Exception:
        logger.exception("[KINGDOM SUMMARY] DB fetch failed")
        return None, None


def build_kingdom_summary_embed(
    latest_row: dict | None,
    prev_row: dict | None,
    timestamp: str,
    *,
    title_prefix: str = "Daily Kingdom Summary",
) -> discord.Embed:
    """
    Build a discord.Embed for the kingdom summary using a consistent layout.
    """
    if not latest_row:
        embed = discord.Embed(
            title=f"📊 {title_prefix}",
            description=(f"Snapshot updated **{timestamp}**\n\nNo KS data available."),
            color=discord.Color.dark_blue(),
        )
        embed.set_footer(text="KD98 Discord Bot — Kingdom Summary")
        return embed

    kpwr = latest_row.get("KINGDOM_POWER")
    governors = latest_row.get("Governors")
    kp = latest_row.get("KP")
    kills = latest_row.get("KILL")
    deads = latest_row.get("DEAD")
    ch25 = latest_row.get("CH25")
    rank = latest_row.get("KINGDOM_RANK")
    seed = latest_row.get("KINGDOM_SEED")
    healed = latest_row.get("HealedTroops")
    # ranged_points = latest_row.get("RangedPoints")

    prev_kpwr = prev_row.get("KINGDOM_POWER") if prev_row else None
    prev_governors = prev_row.get("Governors") if prev_row else None
    prev_kp = prev_row.get("KP") if prev_row else None
    prev_kills = prev_row.get("KILL") if prev_row else None
    prev_deads = prev_row.get("DEAD") if prev_row else None
    prev_ch25 = prev_row.get("CH25") if prev_row else None
    prev_rank = prev_row.get("KINGDOM_RANK") if prev_row else None
    prev_healed = prev_row.get("HealedTroops") if prev_row else None
    # prev_ranged = prev_row.get("RangedPoints") if prev_row else None

    # Deltas
    d_kpwr = compute_delta(kpwr, prev_kpwr)
    d_governors = compute_delta(governors, prev_governors)
    d_kp = compute_delta(kp, prev_kp)
    d_kills = compute_delta(kills, prev_kills)
    d_deads = compute_delta(deads, prev_deads)
    d_ch25 = compute_delta(ch25, prev_ch25)
    d_rank = compute_delta(rank, prev_rank)  # positive => rank number increased
    d_healed = compute_delta(healed, prev_healed)
    ##d_ranged = compute_delta(ranged_points, prev_ranged)

    embed = discord.Embed(
        title=f"📊 {title_prefix}",
        description=(f"Snapshot updated **{timestamp}**\n\n"),
        color=discord.Color.dark_blue(),
    )

    if (
        CUSTOM_AVATAR_URL
        and isinstance(CUSTOM_AVATAR_URL, str)
        and CUSTOM_AVATAR_URL.lower().startswith(("http://", "https://"))
    ):
        try:
            embed.set_thumbnail(url=CUSTOM_AVATAR_URL)
        except Exception:
            logger.exception("[KINGDOM SUMMARY] Failed to set thumbnail")

    embed.add_field(name="🏷️ Kingdom Seed", value=str(seed or "—"), inline=False)

    try:
        rank_display = _fmt_int_safe(rank)
    except Exception:
        rank_display = "—"

    # Rank emoji mapping:
    # 🔴 rank number decreased (bad)
    # 🟠 rank same
    # 🟢 rank number increased (good)
    if d_rank is None:
        rank_ind = "–"
    else:
        try:
            if d_rank > 0:
                rank_ind = "🟢"
            elif d_rank == 0:
                rank_ind = "🟠"
            else:
                rank_ind = "🔴"
        except Exception:
            rank_ind = "–"

    rank_delta = (
        _fmt_signed_short(d_rank, integer=True) + " vs prior" if d_rank is not None else "—"
    )
    embed.add_field(
        name="👑 Kingdom Rank",
        value=f"{rank_display}  {rank_ind}  {rank_delta}",
        inline=False,
    )

    # Core stats - include emojis and bolded colored indicators & deltas
    core_lines = []
    core_lines.append(
        f"📈 **Total Kingdom Power:** {_fmt_short_safe(kpwr)}  {_indicator(d_kpwr)}  **{_fmt_signed_short(d_kpwr)}**"
    )
    core_lines.append(
        f"👥 **Players (Governors):** {_fmt_int_safe(governors)}  {_indicator(d_governors)}  **{_fmt_signed_short(d_governors, integer=True)}**"
    )
    core_lines.append(
        f"🏰 **CH25 Count:** {_fmt_short_safe(ch25)}  {_indicator(d_ch25)}  **{_fmt_signed_short(d_ch25, integer=True)}**"
    )
    embed.add_field(name="📈 Core Stats", value="\n".join(core_lines), inline=False)

    # Additional stats with emojis
    add_lines = []
    add_lines.append(
        f"⚔️ **Total Kill Points (KP):** {_fmt_short_safe(kp)}  {_indicator(d_kp)}  **{_fmt_signed_short(d_kp)}**"
    )
    add_lines.append(
        f"🗡️ **Total T4 & T5 Kills:** {_fmt_short_safe(kills)}  {_indicator(d_kills)}  **{_fmt_signed_short(d_kills)}**"
    )
    add_lines.append(
        f"💀 **Total Deads:** {_fmt_short_safe(deads)}  {_indicator(d_deads)}  **{_fmt_signed_short(d_deads)}**"
    )
    # HealedTroops added to Additional Stats
    add_lines.append(
        f"🩺 **Total Healed Troops:** {_fmt_short_safe(healed)}  {_indicator(d_healed)}  **{_fmt_signed_short(d_healed, integer=True)}**"
    )
    # RangedPoints is fetched and available (d_ranged) but intentionally not shown yet

    embed.add_field(name="📊 Additional Stats", value="\n".join(add_lines), inline=False)

    embed.set_footer(text="KD98 Discord Bot — Kingdom Summary")
    return embed


async def send_kingdom_summary(
    bot: Any,
    channel: discord.abc.Messageable,
    timestamp: str,
    *,
    is_test: bool = False,
) -> None:
    """
    Attempt to send the daily Kingdom Summary embed. Guarded by 'kingdom_summary_daily'.
    """
    # Guard check (sent_today)
    try:
        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        if not is_test and run_blocking_in_thread is not None:
            if await run_blocking_in_thread(
                sent_today,
                "kingdom_summary_daily",
                name="sent_today_kingdom_summary",
                meta={"key": "kingdom_summary_daily"},
            ):
                logger.info("[KINGDOM SUMMARY] Already sent today; skipping.")
                return
        elif not is_test:
            if await asyncio.to_thread(sent_today, "kingdom_summary_daily"):
                logger.info("[KINGDOM SUMMARY] Already sent today; skipping.")
                return
    except Exception:
        logger.exception("[KINGDOM SUMMARY] Guard check failed (continuing)")

    # Load daily rows off-thread
    try:
        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        if run_blocking_in_thread is not None:
            latest_row, prev_row = await run_blocking_in_thread(
                load_latest_and_prev_rows,
                1,
                name="load_ks_latest_and_prev",
                meta={"caller": "stats_alerts.embeds.kingdom_summary"},
            )
        else:
            latest_row, prev_row = await asyncio.to_thread(load_latest_and_prev_rows, 1)
    except Exception:
        logger.exception("[KINGDOM SUMMARY] Failed loading KS rows")
        latest_row, prev_row = None, None

    if not latest_row:
        logger.info("[KINGDOM SUMMARY] No KS data available; skipping.")
        return

    # Build embed using centralized builder
    embed = build_kingdom_summary_embed(latest_row, prev_row, timestamp)

    # Claim/ping and send
    content = None
    allowed_mentions = None
    try:
        first_ping = False
        if not is_test:
            try:
                try:
                    from file_utils import run_blocking_in_thread
                except Exception:
                    run_blocking_in_thread = None

                if run_blocking_in_thread is not None:
                    res = await run_blocking_in_thread(
                        claim_send,
                        "kingdom_summary_daily",
                        name="claim_send_kingdom_summary",
                        meta={"key": "kingdom_summary_daily", "max_per_day": 1},
                    )
                    first_ping = bool(res)
                else:
                    res = await asyncio.to_thread(
                        claim_send, "kingdom_summary_daily", max_per_day=1
                    )
                    first_ping = bool(res)
            except Exception:
                logger.exception(
                    "[KINGDOM SUMMARY] claim_send failed; will still send without ping"
                )
        if first_ping and not is_test:
            content = "@everyone"
            allowed_mentions = discord.AllowedMentions(everyone=True)
    except Exception:
        logger.exception("[KINGDOM SUMMARY] Claim/ping logic failed; sending without ping")

    try:
        await channel.send(embed=embed, content=content, allowed_mentions=allowed_mentions)
        logger.info("[KINGDOM SUMMARY] Sent summary to channel %s", getattr(channel, "id", "?"))
    except Exception:
        logger.exception("[KINGDOM SUMMARY] Failed sending summary")
