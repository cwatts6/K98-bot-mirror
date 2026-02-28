# kvk_history_utils.py
from __future__ import annotations

from collections.abc import Iterable
import io
import logging

logger = logging.getLogger(__name__)

import os
import warnings

import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.ticker import FuncFormatter
import pandas as pd

# --- Project constants / helpers
from file_utils import fetch_one_dict, get_conn_with_retries
from utils import fmt_short  # centralised formatter used across project

# Prioritize widely available families; adjust list if you know what’s on the host
_CJK_FONT_CANDIDATES = [
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "Noto Sans CJK KR",
    "Microsoft YaHei",
    "MS Gothic",
    "Yu Gothic",
    "SimHei",
    "WenQuanYi Zen Hei",
    "Arial Unicode MS",
]

_CJK_FAMILY = None


def _configure_fonts_for_cjk():
    global _CJK_FAMILY
    try:
        # Try to find one of the candidates already installed
        fm._load_fontmanager(try_read_cache=True)
        all_fonts = {f.name: f.fname for f in fm.fontManager.ttflist}
        for fam in _CJK_FONT_CANDIDATES:
            if fam in all_fonts and os.path.exists(all_fonts[fam]):
                _CJK_FAMILY = fam
                # Make it the first sans-serif choice and keep common fallbacks
                matplotlib.rcParams["font.family"] = "sans-serif"
                matplotlib.rcParams["font.sans-serif"] = [
                    fam,
                    "DejaVu Sans",
                    "Arial",
                    "Liberation Sans",
                ]
                matplotlib.rcParams["axes.unicode_minus"] = False
                logger.info(f"[KVK_HISTORY] Using CJK font: {fam} ({all_fonts[fam]})")
                break

        if _CJK_FAMILY is None:
            logger.warning("[KVK_HISTORY] No CJK font found; non-ASCII glyphs may not render.")
            # Optional: silence noisy warning while we work without a CJK font
            warnings.filterwarnings(
                "ignore",
                message=r"Glyph .* missing from font",
                category=UserWarning,
                module=r"matplotlib\..*|.*kvk_history_utils",
            )
    except Exception as e:
        logger.warning(f"[KVK_HISTORY] Font config failed: {e}")


_configure_fonts_for_cjk()


def _safe_text(s: str) -> str:
    """If no CJK font is available, strip unsupported glyphs to avoid tofu boxes."""
    if _CJK_FAMILY:
        return s
    try:
        return (s or "").encode("ascii", "ignore").decode("ascii")
    except Exception:
        return str(s or "")


def get_started_kvks() -> list[int]:
    """
    Return a contiguous integer range of started KVKs from the earliest we track (>=3)
    up to the latest actually started. Robust even if older rows are missing in KVK_Details.
    """
    with get_conn_with_retries() as cn:
        with cn.cursor() as cur:
            # Latest started KVK from KVK_Details (preferred)
            cur.execute("""
                SELECT MAX(KVK_NO)
                FROM dbo.KVK_Details
                WHERE KVK_START_DATE IS NOT NULL
                  AND KVK_START_DATE <= SYSUTCDATETIME();
            """)
            r = fetch_one_dict(cur)
            # prefer next(iter(...)) over single-element slice
            if r:
                max_started = int(next(iter(r.values())) or 0)
            else:
                max_started = 0

            if max_started == 0:
                # Fallback: anything present in EXCEL_FOR_KVK_* view/tables
                cur.execute("SELECT ISNULL(MAX([KVK_NO]), 0) FROM dbo.v_EXCEL_FOR_KVK_All;")
                r2 = fetch_one_dict(cur)
                if r2:
                    max_started = int(next(iter(r2.values())) or 0)
                else:
                    max_started = 0

            # Earliest KVK present in physical tables; fallback to 3
            cur.execute("""
                SELECT MIN(TRY_CONVERT(int, REPLACE(name, 'EXCEL_FOR_KVK_', '')))
                FROM sys.tables
                WHERE name LIKE 'EXCEL_FOR_KVK[_]%';
            """)
            r3 = fetch_one_dict(cur)
            if r3:
                v3 = next(iter(r3.values()))
                min_kvk = int(v3) if v3 is not None else 3
            else:
                min_kvk = 3
            min_kvk = max(3, min_kvk)

    if max_started < min_kvk:
        return [min_kvk]
    return list(range(min_kvk, max_started + 1))


def fetch_history_for_governors(governor_ids: Iterable[int]) -> pd.DataFrame:
    """
    Returns one tidy DataFrame across ALL started KVKs for the given Gov_IDs.
    Pulls from v_EXCEL_FOR_KVK_Started so future KVKs are auto-hidden.
    """
    ids = list({int(x) for x in governor_ids if x is not None})
    if not ids:
        return pd.DataFrame()

    # Parameterize IN (...) safely by building ?,?,?
    placeholders = ",".join(["?"] * len(ids))
    sql = f"""
        SELECT
            CAST([Gov_ID] AS BIGINT)      AS Gov_ID,
            [Governor_Name],
            CAST([KVK_NO] AS INT)         AS KVK_NO,
            CAST([T4_KILLS] AS BIGINT)    AS T4_KILLS,
            CAST([T5_KILLS] AS BIGINT)    AS T5_KILLS,
            CAST([T4&T5_Kills] AS BIGINT) AS T4T5_Kills,
            CAST([% of Kill target] AS DECIMAL(9,2)) AS KillPct,
            CAST([Deads] AS BIGINT)       AS Deads,
            CAST([% of Dead_Target] AS DECIMAL(9,2)) AS DeadPct,
            CAST([DKP_SCORE] AS BIGINT)   AS DKP_SCORE,
            CAST([% of DKP Target] AS DECIMAL(9,2)) AS DKPPct,
            CAST([Pass 4 Kills] AS BIGINT) AS P4_Kills,
            CAST([Pass 6 Kills] AS BIGINT) AS P6_Kills,
            CAST([Pass 7 Kills] AS BIGINT) AS P7_Kills,
            CAST([Pass 8 Kills] AS BIGINT) AS P8_Kills,
            CAST([Pass 4 Deads] AS BIGINT) AS P4_Deads,
            CAST([Pass 6 Deads] AS BIGINT) AS P6_Deads,
            CAST([Pass 7 Deads] AS BIGINT) AS P7_Deads,
            CAST([Pass 8 Deads] AS BIGINT) AS P8_Deads
        FROM dbo.v_EXCEL_FOR_KVK_Started
        WHERE [Gov_ID] IN ({placeholders})
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, ids)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
    df = pd.DataFrame.from_records(rows, columns=cols)

    # Fill missing KVK rows per Gov_ID with zeros so charts & table show full range
    started = get_started_kvks()
    if df.empty:
        # Return zero-frame with all KVKs for the first ID (or empty if none)
        return pd.DataFrame(
            {
                "Gov_ID": [],
                "Governor_Name": [],
                "KVK_NO": [],
                "T4_KILLS": [],
                "T5_KILLS": [],
                "T4T5_Kills": [],
                "KillPct": [],
                "Deads": [],
                "DeadPct": [],
                "DKP_SCORE": [],
                "DKPPct": [],
                "P4_Kills": [],
                "P6_Kills": [],
                "P7_Kills": [],
                "P8_Kills": [],
                "P4_Deads": [],
                "P6_Deads": [],
                "P7_Deads": [],
                "P8_Deads": [],
            }
        )

    frames = []
    for gid, gdf in df.groupby("Gov_ID", dropna=False):
        # Ensure Governor_Name preserved (take first non-null)
        gname = (
            gdf["Governor_Name"].dropna().iloc[0]
            if not gdf["Governor_Name"].dropna().empty
            else None
        )
        existing = set(int(x) for x in gdf["KVK_NO"].tolist())
        missing = [k for k in started if k not in existing]
        if missing:
            zeros = pd.DataFrame(
                {
                    "Gov_ID": gid,
                    "Governor_Name": gname,
                    "KVK_NO": missing,
                    "T4_KILLS": 0,
                    "T5_KILLS": 0,
                    "T4T5_Kills": 0,
                    "KillPct": 0.0,
                    "Deads": 0,
                    "DeadPct": 0.0,
                    "DKP_SCORE": 0,
                    "DKPPct": 0.0,
                    "P4_Kills": 0,
                    "P6_Kills": 0,
                    "P7_Kills": 0,
                    "P8_Kills": 0,
                    "P4_Deads": 0,
                    "P6_Deads": 0,
                    "P7_Deads": 0,
                    "P8_Deads": 0,
                }
            )
            gdf = pd.concat([gdf, zeros], ignore_index=True)

        gdf = gdf.sort_values(["KVK_NO"])
        frames.append(gdf)

    return pd.concat(frames, ignore_index=True).sort_values(["Gov_ID", "KVK_NO"])


# ---------- Metric dictionary & chart ----------

LEFT_METRICS = {
    "T4 Kills": "T4_KILLS",
    "T5 Kills": "T5_KILLS",
    "T4&T5 Kills": "T4T5_Kills",
    "Deads": "Deads",
    "DKP Score": "DKP_SCORE",
    "Pass 4 Kills": "P4_Kills",
    "Pass 6 Kills": "P6_Kills",
    "Pass 7 Kills": "P7_Kills",
    "Pass 8 Kills": "P8_Kills",
    "Pass 4 Deads": "P4_Deads",
    "Pass 6 Deads": "P6_Deads",
    "Pass 7 Deads": "P7_Deads",
    "Pass 8 Deads": "P8_Deads",
}

RIGHT_METRICS = {
    "% of Kill target": "KillPct",
    "% of Dead_Target": "DeadPct",
    "% of DKP Target": "DKPPct",
}

DEFAULT_LEFT = ["T4&T5 Kills"]
DEFAULT_RIGHT = "% of Kill target"


def build_dual_axis_chart(
    df: pd.DataFrame,
    overlay: dict[int, str],
    left_metrics: list[str],
    right_metric: str | None,
    title: str = "KVK History",
    show_point_labels: str = "none",
) -> io.BytesIO:
    # Work on a local copy to avoid mutating caller DataFrame
    try:
        df = df.copy()
    except Exception:
        if df is None:
            df = pd.DataFrame()

    if not left_metrics:
        left_metrics = DEFAULT_LEFT[:]
    left_cols = [LEFT_METRICS[m] for m in left_metrics if m in LEFT_METRICS]

    # Sanitize overlay labels once
    overlay_safe: dict[int, str] = {gid: _safe_text(lbl) for gid, lbl in (overlay or {}).items()}

    # Ensure integer KVKs
    if "KVK_NO" in df.columns:
        df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce").fillna(0).astype(int)

    # Compute full X range from the data we’re plotting
    all_kvks = sorted(set(df["KVK_NO"].tolist())) if not df.empty else []
    if not all_kvks:
        all_kvks = [3]

    fig, ax_left = plt.subplots(figsize=(9, 4.8), dpi=200)
    ax_right = None

    # Plot left metrics, overlaying accounts
    y_max = 0.0
    for gid, label in overlay_safe.items():
        gdf = df[df["Gov_ID"] == gid].sort_values("KVK_NO")
        if gdf.empty:
            continue
        x = gdf["KVK_NO"].astype(int).tolist()
        for mcol in left_cols:
            y = pd.to_numeric(gdf[mcol], errors="coerce").fillna(0.0).astype(float).tolist()
            if y:
                y_max = max(y_max, max(y))
            ax_left.plot(x, y, label=f"{label} • {mcol.replace('_',' ')}")

    # X axis
    ax_left.set_xlabel(_safe_text("KVK"))
    ax_left.set_xlim(min(all_kvks) - 0.5, max(all_kvks) + 0.5)
    ax_left.set_xticks(all_kvks)
    ax_left.xaxis.set_major_locator(mticker.FixedLocator(all_kvks))
    ax_left.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))

    # Left axis
    ax_left.set_ylabel(_safe_text(", ".join(left_metrics)))
    top = y_max * 1.05 if y_max > 0 else 1.0
    ax_left.set_ylim(0, top)
    ax_left.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: fmt_short(v)))
    ax_left.grid(True, alpha=0.25)

    # helpers for optional data point labels
    def _annotate_points(ax_obj, xs, ys, fmt):
        for x, y in zip(xs, ys, strict=False):
            ax_obj.annotate(
                fmt(y),
                xy=(x, y),
                xytext=(0, 6),
                textcoords="offset points",
                fontsize=8,
                ha="center",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.7, linewidth=0),
            )

    # Optional right axis (%)
    if right_metric and right_metric in RIGHT_METRICS:
        rcol = RIGHT_METRICS[right_metric]
        if rcol not in df.columns:
            df[rcol] = 0.0
        df[rcol] = pd.to_numeric(df[rcol], errors="coerce").astype(float)

        ax_right = ax_left.twinx()
        for_kvk = df.groupby("KVK_NO", sort=True, as_index=False)[rcol].mean().fillna({rcol: 0.0})
        ax_right.plot(
            for_kvk["KVK_NO"].astype(int),
            for_kvk[rcol],
            linestyle="--",
            marker="o",
            label=right_metric,
        )
        ax_right.set_ylabel("%")
        ymax = float(for_kvk[rcol].max() or 0.0)
        ax_right.set_ylim(0, max(100.0, ymax))

        # Right-axis labels (percent)
        if show_point_labels in ("latest", "all") and not for_kvk.empty:
            xs_r = for_kvk["KVK_NO"].astype(int).tolist()
            ys_r = for_kvk[rcol].astype(float).tolist()
            fmt_pct = lambda v: f"{float(v):.1f}%"
            if show_point_labels == "latest":
                _annotate_points(ax_right, [xs_r[-1]], [ys_r[-1]], fmt_pct)
            else:
                _annotate_points(ax_right, xs_r, ys_r, fmt_pct)

        # Unified legend (sanitize)
        lines_left, labels_left = ax_left.get_legend_handles_labels()
        lines_right, labels_right = ax_right.get_legend_handles_labels()
        labels_left = [_safe_text(s) for s in labels_left]
        labels_right = [_safe_text(s) for s in labels_right]
        ax_left.legend(
            lines_left + lines_right, labels_left + labels_right, loc="upper left", fontsize=8
        )
    else:
        lines_left, labels_left = ax_left.get_legend_handles_labels()
        labels_left = [_safe_text(s) for s in labels_left]
        ax_left.legend(lines_left, labels_left, loc="upper left", fontsize=8)

    # Optional data point labels on left axis
    if show_point_labels in ("latest", "all"):
        for gid, _label in overlay_safe.items():
            gdf = df[df["Gov_ID"] == gid].sort_values("KVK_NO")
            if gdf.empty:
                continue
            xs_all = gdf["KVK_NO"].astype(int).tolist()
            for mcol in left_cols:
                ys_all = (
                    pd.to_numeric(gdf[mcol], errors="coerce").fillna(0.0).astype(float).tolist()
                )
                if not xs_all:
                    continue
                if show_point_labels == "latest" and xs_all:
                    _annotate_points(ax_left, [xs_all[-1]], [ys_all[-1]], fmt_short)
                elif show_point_labels == "all":
                    _annotate_points(ax_left, xs_all, ys_all, fmt_short)

    ax_left.set_title(_safe_text(title))
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_history_table_image(
    df: pd.DataFrame,
    overlay: dict[int, str],
    left_metrics: list[str],
    right_metric: str | None,
    cols: int = 3,
    title: str = "Data • Last 3 KVKs",
):
    """
    Returns (filename, BytesIO) for a small PNG table.
    Orientation matches the chart: KVK numbers as columns.
    Rows are "<Account> – <Metric>" for each selected metric.
    """
    from io import BytesIO

    try:
        df = df.copy()
    except Exception:
        if df is None:
            df = pd.DataFrame()

    # Sanitize overlay once
    overlay_safe: dict[int, str] = {gid: _safe_text(lbl) for gid, lbl in (overlay or {}).items()}

    if df.empty or "KVK_NO" not in df.columns:
        kvks = []
    else:
        df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")
        kvks = sorted(x for x in df["KVK_NO"].dropna().unique())[-cols:]

    row_defs = []  # (row_label, series_dict)
    metrics = [m for m in left_metrics[:2] if m in LEFT_METRICS]
    if right_metric and right_metric in RIGHT_METRICS:
        metrics.append(right_metric)

    for gid, label in overlay_safe.items():
        for m in metrics:
            if m in LEFT_METRICS:
                col = LEFT_METRICS[m]
                fmt = lambda v: fmt_short(v)
            else:
                col = RIGHT_METRICS[m]
                fmt = lambda v: f"{float(v):.1f}%"

            row_label = _safe_text(f"{label} – {m}")
            series = {}
            for kvk in kvks:
                gdf = df[(df["Gov_ID"] == gid) & (df["KVK_NO"] == kvk)]
                val = gdf[col].iloc[0] if (not gdf.empty and col in gdf.columns) else 0
                series[int(kvk)] = fmt(val)
            row_defs.append((row_label, series))

    # Render
    if not kvks or not row_defs:
        fig, ax = plt.subplots(figsize=(6.5, 0.9), dpi=200)
        ax.axis("off")
        ax.text(0.5, 0.5, "No data to show.", ha="center", va="center", fontsize=11)
    else:
        # Build a DataFrame with KVKs as columns
        data = {lbl: [row.get(k, "") for k in kvks] for lbl, row in row_defs}
        table_df = pd.DataFrame(data, index=[int(k) for k in kvks]).T
        table_df.columns = [f"KVK {int(c)}" for c in table_df.columns]
        table_df.index.name = ""

        # Figure size adapts to content
        fig_w = max(6.5, 5.0 + 0.6 * len(kvks))
        fig_h = max(1.1, 1.0 + 0.38 * len(row_defs))
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
        ax.set_title(_safe_text(title), fontsize=12, pad=8)
        ax.axis("off")
        tbl = ax.table(
            cellText=table_df.values,
            colLabels=list(table_df.columns),
            rowLabels=list(table_df.index),
            loc="center",
            cellLoc="center",
            rowLoc="center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(11)
        tbl.scale(1.02, 1.18)

    buf = BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return "kvk_table.png", buf


def build_history_csv(df: pd.DataFrame, filename: str) -> tuple[str, bytes]:
    """
    Builds a CSV for the current dataset (only the columns users care about).
    Returns (filename, bytes).
    Defensive: if df is empty or missing columns, return header-only CSV.
    """
    cols = [
        "Gov_ID",
        "Governor_Name",
        "KVK_NO",
        "T4_KILLS",
        "T5_KILLS",
        "T4T5_Kills",
        "KillPct",
        "Deads",
        "DeadPct",
        "DKP_SCORE",
        "DKPPct",
        "P4_Kills",
        "P6_Kills",
        "P7_Kills",
        "P8_Kills",
        "P4_Deads",
        "P6_Deads",
        "P7_Deads",
        "P8_Deads",
    ]
    try:
        if df is None or df.empty:
            out = pd.DataFrame(columns=cols)
        else:
            missing = [c for c in cols if c not in df.columns]
            if missing:
                out = pd.DataFrame(columns=cols)
            else:
                out = df[cols].sort_values(["Gov_ID", "KVK_NO"]).copy()
    except Exception:
        out = pd.DataFrame(columns=cols)

    data = out.to_csv(index=False).encode("utf-8")
    return filename, data
