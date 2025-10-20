# embed_offseason_stats.py
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from datetime import UTC, date, datetime
import io
from typing import Any

import discord
from PIL import Image, ImageDraw, ImageFont

try:
    from constants import CUSTOM_AVATAR_URL
except Exception:
    CUSTOM_AVATAR_URL = None

UTC = UTC


# ----------------------------- SQL helpers -----------------------------


def _fetchone(cur, sql: str, *params) -> tuple | None:
    cur.execute(sql, *params)
    return cur.fetchone()


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
    limit: int = 3,
    date_col: str | None = None,
):
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


def get_activity_top_week(cur, metric_col: str, limit: int = 3):
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
        "building": get_activity_top_daily(cur, "BuildingDelta", 3, snap_date),
        "tech": get_activity_top_daily(cur, "TechDonationDelta", 3, snap_date),
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
    def _top3(view: str, value_col: str, label_col: str = "GovernorName"):
        rows = _fetchall(
            cur,
            f"""
            SELECT TOP (3) {label_col}, {value_col} AS MetricValue
            FROM {view}
            ORDER BY {value_col} DESC, {label_col} ASC
        """,
        )
        return [(r[0], int(r[1] or 0)) for r in rows]

    return {
        "building": _top3("dbo.vAllianceActivity_WeeklyDelta", "BuildingDeltaWeek"),
        "tech": _top3("dbo.vAllianceActivity_WeeklyDelta", "TechDonationDeltaWeek"),
        "helps": _top3("dbo.vWTD_Helps", "WTD_HELPS"),
        "rss_gathered": _top3("dbo.vWTD_RSSGathered", "WTD_RssGathered"),
        # Add when available:
        "rss_assisted": _top3("dbo.vWTD_RSSAssisted", "[WTD_RSSAssisted]"),
        "forts": _top3("dbo.vFortsCompleted_WeekToDate", "TotalRallies"),
    }


# ----------------------------- Drawing -----------------------------


def _load_font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def _tile(img: Image.Image, xy: tuple[int, int, int, int], title: str, rows: list[tuple[str, int]]):
    x1, y1, x2, y2 = xy
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        xy, radius=24, fill=(255, 255, 255, 255), outline=(224, 226, 231, 255), width=2
    )

    f_title = _load_font(40, bold=True)
    draw.text((x1 + 28, y1 + 24), title, fill=(24, 26, 31, 255), font=f_title)

    f_label = _load_font(36, bold=False)
    f_val = _load_font(36, bold=True)
    y = y1 + 94
    row_step = 58

    for i, (name, val) in enumerate(rows[:3], 1):
        draw.ellipse((x1 + 28, y - 4, x1 + 44, y + 12), fill=(88, 101, 242, 255))
        draw.text((x1 + 54, y - 16), f"{name}", fill=(64, 67, 73, 255), font=f_label)
        val_text = _fmt(val)
        w = draw.textlength(val_text, font=f_val)
        draw.text((x2 - 28 - w, y - 20), val_text, fill=(24, 26, 31, 255), font=f_val)
        y += row_step


def render_2x2_dashboard(d: dict, *, header_text: str) -> bytes:
    W, H = 1400, 900
    base = Image.new("RGBA", (W, H), (32, 35, 42, 255))

    card = Image.new("RGBA", (W - 80, H - 140), (242, 243, 245, 255))
    shadow = Image.new("RGBA", (card.width + 30, card.height + 30), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (0, 0, shadow.width - 1, shadow.height - 1), radius=28, fill=(0, 0, 0, 70)
    )
    base.paste(shadow, (35, 45), shadow)
    base.paste(card, (50, 60))

    header = Image.new("RGBA", (card.width - 60, 100), (60, 64, 90, 255))
    mask = Image.new("L", header.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, header.width, header.height), radius=20, fill=255)
    header.putalpha(mask)
    base.paste(header, (80, 80), header)

    draw = ImageDraw.Draw(base)
    f_h1 = _load_font(44, bold=True)
    draw.text((100, 108), header_text, fill=(255, 255, 255, 255), font=f_h1)

    gx, gy = 80, 220
    gw, gh = card.width - 60, card.height - 180
    cols, rows = 2, 2
    gap = 28
    tile_w = (gw - gap * (cols - 1)) // cols
    tile_h = (gh - gap * (rows - 1)) // rows

    tiles = [
        ("Forts (Started + Joined)", d.get("forts", [])),
        ("Tech Donations", d.get("tech", [])),
        ("RSS Gathered", d.get("rss_gathered", [])),
        ("Helps", d.get("helps", [])),
    ]

    for i, (title, rows_data) in enumerate(tiles):
        cx = i % cols
        cy = i // cols
        x1 = gx + cx * (tile_w + gap)
        y1 = gy + cy * (tile_h + gap)
        x2 = x1 + tile_w
        y2 = y1 + tile_h
        _tile(base, (x1, y1, x2, y2), title, rows_data or [])

    out = io.BytesIO()
    base.save(out, format="PNG")
    out.seek(0)
    return out.read()


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


async def send_offseason_stats_embed_v2(
    bot,
    ctx: discord.ApplicationContext | None = None,
    *,
    is_weekly: bool = False,
    channel: discord.abc.Messageable | None = None,
    target_channel_id: int | None = None,
    mention_everyone: bool = False,
) -> None:
    """
    Sends: [Summary (with hero 2×2)] + [Forts] + [Building/Tech/Helps] + [RSS].
    """
    from Commands import _conn

    try:
        from bot_config import NOTIFY_CHANNEL_ID
    except Exception:
        NOTIFY_CHANNEL_ID = None

    # Channel resolution
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

    with _conn() as conn:
        cur = conn.cursor()

        # Summary always from latest+previous scans
        summary = get_kingdom_summary(cur)

        if is_weekly:
            data = load_all_weekly(cur)
            header = "Off-season Stats — Top 3 (Last Week)"
            time_tag = "Last Week"
            weekly = get_kingdom_summary_weekly(cur)
            summary_text = _kingdom_summary_line_weekly(weekly, summary["total_players"])
            snapshot_text = "Last completed week (UTC)"
        else:
            data = load_all_daily(cur)
            header = "Daily Off-season Stats — Top 3"
            time_tag = "Most Recent Day"
            summary_text = _kingdom_summary_line(summary)
            snap_date = _pick_daily_snapshot_date(cur)
            snapshot_text = f"Stats for **{snap_date.isoformat()} (UTC day)**"

    png_bytes = render_2x2_dashboard(data, header_text=header)
    file = discord.File(io.BytesIO(png_bytes), filename="offseason_dashboard.png")

    # Embed 1: summary + hero
    e1 = discord.Embed(
        title=f"📊 KD98 Stats Update ({'Weekly' if is_weekly else 'Daily • Off-season'})",
        description=summary_text,
        colour=discord.Colour.blurple(),
    )
    e1.add_field(name="Snapshot", value=snapshot_text, inline=False)
    if CUSTOM_AVATAR_URL:
        e1.set_thumbnail(url=CUSTOM_AVATAR_URL)
    e1.set_image(url="attachment://offseason_dashboard.png")
    e1.set_footer(text="KD98 Discord Bot")

    # Embed 2: Forts
    e2 = discord.Embed(title=f"🛡️ Forts ({time_tag})", colour=discord.Colour.orange())
    name, val = _fmt_list("Forts (Started + Joined)", data.get("forts", []))
    e2.add_field(name=name, value=val or "—", inline=False)

    # Embed 3: Building / Tech / Helps
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

    # Embed 4: RSS
    e4 = discord.Embed(title=f"🌾 RSS ({time_tag})", colour=discord.Colour.green())
    name, val = _fmt_list("RSS Gathered", data.get("rss_gathered", []))
    e4.add_field(name=name, value=val or "—", inline=True)
    if data.get("rss_assisted"):
        name, val = _fmt_list("RSS Assisted", data.get("rss_assisted", []))
        e4.add_field(name=name, value=val or "—", inline=True)

    content = "@everyone" if mention_everyone else None
    allowed = discord.AllowedMentions(everyone=mention_everyone)
    await ch.send(content=content, embeds=[e1, e2, e3, e4], file=file, allowed_mentions=allowed)
