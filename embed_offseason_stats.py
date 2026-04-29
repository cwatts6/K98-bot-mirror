# embed_offseason_stats.py
"""
Offseason combo embed sender.

Changes:
- Removed hero dashboard image per latest requirement.
- Accepts include_kingdom_summary flag: if False, the combo will NOT include the KS embed (only supporting embeds).
- When including KS embed, uses centralized loader/builder from stats_alerts.embeds.kingdom_summary if available;
  otherwise falls back to legacy summary line.
- Attempts to claim kingdom_summary_daily / kingdom_summary_weekly before pinging.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from datetime import UTC, date, datetime
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL

UTC = UTC

from file_utils import fetch_one_dict, get_conn_with_retries

# Try to import the centralized KS helpers (optional)
try:
    from stats_alerts.embeds.kingdom_summary import (
        build_kingdom_summary_embed,
        load_latest_and_prev_rows,
    )
except Exception:
    load_latest_and_prev_rows = None
    build_kingdom_summary_embed = None

# ----------------------------- SQL helpers -----------------------------


def _fetchone(cur, sql: str, *params) -> tuple | None:
    """
    Execute SQL and return a single row as a positional tuple (or None).

    Internally uses file_utils.fetch_one_dict to obtain a robust column-name->value
    mapping based on cursor.description, then returns the values as a tuple
    in the same column order. Returning a tuple preserves existing callers'
    expectations while centralizing row->dict logic in file_utils.
    """
    cur.execute(sql, *params)
    rd = fetch_one_dict(cur)
    if rd is None:
        return None
    # cursor_row_to_dict in file_utils uses cursor.description to preserve column order,
    # so the dict.values() iteration order matches the original positional order.
    return tuple(rd.values())


def _fetchall(cur, sql: str, *params) -> list[tuple]:
    cur.execute(sql, *params)
    return cur.fetchall()


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


# ----------------------- Canonical snapshot pickers --------------------


def _pick_daily_snapshot_date(cur) -> date:
    """
    Canonical daily snapshot date (UTC): pick today if present in AllianceActivityDaily,
    else yesterday, else the latest available date in that table.
    """
    row = _fetchone(
        cur,
        """
        DECLARE @today date     = CONVERT(date, SYSUTCDATETIME());
        DECLARE @yesterday date = DATEADD(day, -1, @today);

        SELECT TOP (1) AsOfDate
        FROM dbo.AllianceActivityDaily
        WHERE AsOfDate IN (@today, @yesterday)
        GROUP BY AsOfDate
        ORDER BY AsOfDate DESC;
    """,
    )
    if row and row[0]:
        return row[0]
    row = _fetchone(cur, "SELECT MAX(AsOfDate) FROM dbo.AllianceActivityDaily;")
    return row[0] if row and row[0] else datetime.now(UTC).date()


# ----------------------------- Kingdom summary ------------------------


def get_kingdom_summary(cur) -> dict:
    """
    Headline is based on latest SCANORDER + prior SCANORDER (top-300 power).
    """
    row = _fetchone(
        cur,
        """
        ;WITH last AS (SELECT MAX(SCANORDER) AS cur_order FROM dbo.KingdomScanData4)
        SELECT
            (SELECT cur_order FROM last) AS cur_order,
            (SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4 WHERE SCANORDER < (SELECT cur_order FROM last)) AS prev_order;
    """,
    )
    cur_order, prev_order = row or (None, None)
    if cur_order is None:
        return {"total_power_top300": 0, "total_players": 0, "power_delta_top300": 0}

    total_players = (
        _fetchone(cur, "SELECT COUNT(*) FROM dbo.KingdomScanData4 WHERE SCANORDER = ?", cur_order)[
            0
        ]
        or 0
    )

    def _top300_at(scanorder: int) -> int:
        if scanorder is None:
            return 0
        row2 = _fetchone(
            cur,
            """
            SELECT SUM(CAST(Power AS BIGINT))
            FROM (
                SELECT TOP (300) Power
                FROM dbo.KingdomScanData4
                WHERE SCANORDER = ?
                ORDER BY Power DESC
            ) s
        """,
            scanorder,
        )
        return int(row2[0] or 0)

    cur_p = _top300_at(cur_order)
    prev_p = _top300_at(prev_order)
    return {
        "total_power_top300": cur_p,
        "total_players": int(total_players),
        "power_delta_top300": cur_p - prev_p,
    }


def get_kingdom_summary_weekly(cur) -> dict:
    """
    Last completed week (Mon→Mon), using scanorders just before each boundary.
    """
    latest_date = _fetchone(cur, "SELECT CAST(MAX(ScanDate) AS date) FROM dbo.KingdomScanData4;")[0]

    row = _fetchone(
        cur,
        """
        DECLARE @latest date = ?;
        DECLARE @dow int = (DATEPART(WEEKDAY, @latest) + 5) % 7; -- 0=Mon..6=Sun independent of DATEFIRST
        DECLARE @start_this_week date = DATEADD(day, -@dow, @latest);
        DECLARE @start_prev_week date = DATEADD(day, -7, @start_this_week);

        SELECT
            (SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4 WHERE ScanDate < @start_prev_week) AS so_start,
            (SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4 WHERE ScanDate < @start_this_week) AS so_end;
    """,
        latest_date,
    )
    so_start, so_end = row or (None, None)

    if so_start is None:
        so_start = _fetchone(cur, "SELECT MIN(SCANORDER) FROM dbo.KingdomScanData4;")[0]
    if so_end is None:
        so_end = _fetchone(
            cur, "SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4 WHERE ScanDate < ?", latest_date
        )[0]

    def _top300_at(so: int) -> int:
        if so is None:
            return 0
        row2 = _fetchone(
            cur,
            """
            SELECT SUM(CAST(Power AS BIGINT))
            FROM (SELECT TOP (300) Power
                  FROM dbo.KingdomScanData4
                  WHERE SCANORDER = ?
                  ORDER BY Power DESC) s
        """,
            so,
        )
        return int(row2[0] or 0)

    start_v = _top300_at(so_start)
    end_v = _top300_at(so_end)
    return {"top300_start": start_v, "top300_end": end_v, "weekly_delta": end_v - start_v}


# ----------------------------- Top pickers -----------------------------


def _top_names_for_day(cur, metric_sql_col: str, limit: int, snap_date: date):
    # Pull daily totals and attach a display name (latest seen in snapshots)
    rows = _fetchall(
        cur,
        f"""
        WITH d AS (
            SELECT GovernorID, SUM({metric_sql_col}) AS v
            FROM dbo.AllianceActivityDaily
            WHERE AsOfDate = ?
            GROUP BY GovernorID
        )
        SELECT TOP ({limit})
               COALESCE(n.GovernorName, CONCAT('#', CAST(d.GovernorID AS varchar(20)))) AS GovernorName,
               d.v
        FROM d
        OUTER APPLY (
            SELECT TOP (1) r.GovernorName
            FROM dbo.AllianceActivitySnapshotRow r
            JOIN dbo.AllianceActivitySnapshotHeader h ON h.SnapshotId = r.SnapshotId
            WHERE r.GovernorID = d.GovernorID
            ORDER BY h.SnapshotTsUtc DESC
        ) n
        ORDER BY d.v DESC, GovernorName ASC;
    """,
        snap_date,
    )
    return [(r[0], int(r[1] or 0)) for r in rows]


def get_activity_top_daily(cur, metric_col: str, limit: int, snap_date: date):
    # metric_col was "BuildingDelta"/"TechDonationDelta" before.
    # Map to the real AllianceActivityDaily column names.
    col_map = {
        "BuildingDelta": "BuildDonations",
        "TechDonationDelta": "TechDonations",
    }
    real_col = col_map.get(metric_col, metric_col)  # default to passed value
    return _top_names_for_day(cur, real_col, limit, snap_date)


def get_daily_top(
    cur,
    view_name: str,
    value_col: str,
    snap_date: date,
    label_col: str = "GovernorName",
    limit: int = 5,
    date_col: str | None = None,
):
    """
    Return list[(label, int(value))] for the top `limit` rows in view_name.
    Default limit changed to 5 for daily usage.
    """
    if date_col:
        rows = _fetchall(
            cur,
            f"""
            SELECT TOP ({limit}) {label_col}, {value_col}
            FROM {view_name}
            WHERE CAST({date_col} AS date) = ?
            ORDER BY {value_col} DESC, {label_col} ASC;
        """,
            snap_date,
        )
    else:
        rows = _fetchall(
            cur,
            f"""
            SELECT TOP ({limit}) {label_col}, {value_col}
            FROM {view_name}
            ORDER BY {value_col} DESC, {label_col} ASC;
        """,
        )
    return [(r[0], int(r[1] or 0)) for r in rows]


def get_activity_top_week(cur, metric_col: str, limit: int = 10):
    # no Python change here, but replace the SQL body entirely:
    col_map = {"BuildingDelta": "BuildDonations", "TechDonationDelta": "TechDonations"}
    mcol = col_map.get(metric_col, "BuildDonations")
    rows = _fetchall(
        cur,
        f"""
        DECLARE @latest date = (SELECT MAX(AsOfDate) FROM dbo.AllianceActivityDaily);
        IF @latest IS NULL
        BEGIN
            SELECT TOP (0) CAST(NULL AS nvarchar(1)) AS GovernorName, CAST(0 AS int) AS v;
            RETURN;
        END;

        -- Monday (UTC) for the @latest week
        DECLARE @dow int = (DATEPART(WEEKDAY, @latest) + 5) % 7; -- 0=Mon..6=Sun
        DECLARE @start_this_week date = DATEADD(day, -@dow, @latest);
        DECLARE @start_prev_week date = DATEADD(day, -7, @start_this_week);

        WITH w AS (
            SELECT GovernorID, SUM({mcol}) AS v
            FROM dbo.AllianceActivityDaily
            WHERE AsOfDate >= @start_prev_week AND AsOfDate < @start_this_week
            GROUP BY GovernorID
        )
        SELECT TOP ({limit})
               COALESCE(n.GovernorName, CONCAT('#', CAST(w.GovernorID AS varchar(20)))) AS GovernorName,
               w.v
        FROM w
        OUTER APPLY (
            SELECT TOP (1) r.GovernorName
            FROM dbo.AllianceActivitySnapshotRow r
            JOIN dbo.AllianceActivitySnapshotHeader h ON h.SnapshotId = r.SnapshotId
            WHERE r.GovernorID = w.GovernorID
            ORDER BY h.SnapshotTsUtc DESC
        ) n
        ORDER BY w.v DESC, GovernorName ASC;
    """,
    )
    return [(r[0], int(r[1] or 0)) for r in rows]


# ----------------------------- Loaders -----------------------------


def load_all_daily(cur) -> dict:
    snap_date = _pick_daily_snapshot_date(cur)
    return {
        "building": get_activity_top_daily(cur, "BuildingDelta", 5, snap_date),
        "tech": get_activity_top_daily(cur, "TechDonationDelta", 5, snap_date),
        "helps": get_daily_top(
            cur, "dbo.vDaily_Helps", "HelpsDelta", snap_date, date_col="AsOfDate"
        ),
        "rss_gathered": get_daily_top(
            cur, "dbo.vDaily_RSSGathered", "RSSGatheredDelta", snap_date, date_col="AsOfDate"
        ),
        "rss_assisted": get_daily_top(
            cur, "dbo.vDaily_RSSAssisted", "RSSAssistedDelta", snap_date, date_col="AsOfDate"
        ),
        "forts": get_daily_top(
            cur, "dbo.v_RallyDaily_Latest", "TotalRallies", snap_date, date_col=None
        ),
    }


def load_all_weekly(cur) -> dict:
    def _top10(view: str, value_col: str, label_col: str = "GovernorName"):
        rows = _fetchall(
            cur,
            f"""
            SELECT TOP (10) {label_col}, {value_col} AS MetricValue
            FROM {view}
            ORDER BY {value_col} DESC, {label_col} ASC
        """,
        )
        return [(r[0], int(r[1] or 0)) for r in rows]

    return {
        "building": _top10("dbo.vAllianceActivity_WeeklyDelta", "BuildingDeltaWeek"),
        "tech": _top10("dbo.vAllianceActivity_WeeklyDelta", "TechDonationDeltaWeek"),
        "helps": _top10("dbo.vWTD_Helps", "WTD_HELPS"),
        "rss_gathered": _top10("dbo.vWTD_RSSGathered", "WTD_RssGathered"),
        # Add when available:
        "rss_assisted": _top10("dbo.vWTD_RSSAssisted", "[WTD_RSSAssisted]"),
        "forts": _top10("dbo.vFortsCompleted_WeekToDate", "TotalRallies"),
    }


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
