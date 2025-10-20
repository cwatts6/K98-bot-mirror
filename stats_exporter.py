# stats_exporter.py
from __future__ import annotations

import os

import numpy as np
import pandas as pd

try:
    import xlsxwriter  # noqa: F401

    _EXCEL_ENGINE = "xlsxwriter"
except Exception:
    try:
        import openpyxl  # noqa: F401

        _EXCEL_ENGINE = "openpyxl"
    except Exception as e:
        raise RuntimeError(
            "No Excel writer installed. Please `pip install XlsxWriter` "
            "(preferred) or `pip install openpyxl`."
        ) from e


def _coalesce_cols(df: pd.DataFrame, cols: list[str], fill=0) -> pd.Series:
    for c in cols:
        if c in df.columns:
            return df[c].fillna(fill)
    return pd.Series([fill] * len(df))


def _write_safe(ws, r: int, c: int, v, num_fmt):
    """Write numbers safely: blanks for NaN/Inf, strings for non-numbers."""
    # Treat pandas/NumPy numbers uniformly
    if isinstance(v, (int, float, np.integer, np.floating)):
        if isinstance(v, (np.floating, float)):
            if np.isnan(v) or np.isinf(v):
                ws.write_blank(r, c, None)
                return
        ws.write_number(r, c, float(v), num_fmt)
    else:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            ws.write_blank(r, c, None)
        else:
            ws.write(r, c, v)


def _clean_text(s: str | None) -> str:
    if s is None:
        return ""
    return " ".join(str(s).split())


def _calc_period(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> dict:
    """
    Summarises a window:
      - *_End are snapshot values at the end of the window.
      - *_Delta are sums of the corresponding *Delta columns across the window.
      - TechDonationsSum is the sum of daily TechDonations in the window.
    """
    w = df[(df["AsOfDate"] >= start_date) & (df["AsOfDate"] <= end_date)]
    snap = df[df["AsOfDate"] <= end_date].tail(1)

    def colsum(c):
        return (
            int(pd.to_numeric(w.get(c, pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
            if c in w
            else 0
        )

    def snapv(c):
        return (
            int(snap[c].iloc[0])
            if (not snap.empty and c in snap and pd.notna(snap[c].iloc[0]))
            else 0
        )

    return {
        "PowerEnd": snapv("Power"),
        "TroopPowerEnd": snapv("TroopPower"),
        "KillPointsEnd": snapv("KillPoints"),
        "DeadsEnd": snapv("Deads"),
        "RSSGatheredEnd": snapv("RSS_Gathered"),
        "RSSAssistEnd": snapv("RSS_Assist"),
        "HelpsEnd": snapv("Helps"),
        "PowerDelta": colsum("PowerDelta"),
        "TroopPowerDelta": colsum("TroopPowerDelta"),
        "KillPointsDelta": colsum("KillPointsDelta"),
        "DeadsDelta": colsum("DeadsDelta"),
        "RSS_GatheredDelta": colsum("RSS_GatheredDelta"),
        "RSSAssistDelta": colsum("RSSAssistDelta"),
        "HelpsDelta": colsum("HelpsDelta"),
        # daily value → sum over window
        "TechDonationsSum": colsum("TechDonations"),
    }


_FORBIDDEN_SHEET_CHARS = set(r"[]:*?/\\")


def _safe_sheet_name(base: str, fallback: str, max_len: int = 31) -> str:
    s = (base or "").strip().strip("'")
    s = "".join(ch for ch in s if ch not in _FORBIDDEN_SHEET_CHARS)
    s = s or fallback
    return s[:max_len]


def _month_bounds(latest: pd.Timestamp) -> dict:
    lo_this = latest.replace(day=1)
    lo_last = (lo_this - pd.offsets.MonthBegin(1)).to_pydatetime().date()
    hi_last = (lo_this - pd.offsets.Day(1)).to_pydatetime().date()
    return {
        "mtd": (pd.Timestamp(lo_this.date()), latest),
        "last_month": (pd.Timestamp(lo_last), pd.Timestamp(hi_last)),
    }


def build_user_stats_excel(
    df_daily: pd.DataFrame,
    df_targets: pd.DataFrame | None,
    *,
    out_path: str,
    days_for_daily_table: int = 90,
) -> None:
    # Ensure folder exists first
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # ---------- CLEAN & STANDARDISE ----------
    df = df_daily.copy()
    df["AsOfDate"] = pd.to_datetime(df["AsOfDate"]).dt.normalize()
    for col in ("GovernorName", "Alliance"):
        if col in df:
            df[col] = df[col].apply(_clean_text)

    # Drop columns you don't want anywhere
    drop_cols = {"TechPower", "TechPowerDelta", "TotalRallies", "RalliesLaunched", "RalliesJoined"}
    keep = [c for c in df.columns if c not in drop_cols]
    df = df[keep]

    # ALL_DAILY column order (create if missing to keep shape stable)
    ALL_DAILY_COLS = [
        "GovernorID",
        "GovernorName",
        "Alliance",
        "AsOfDate",
        "Power",
        "PowerDelta",
        "TroopPower",
        "TroopPowerDelta",
        "KillPoints",
        "KillPointsDelta",
        "Deads",
        "DeadsDelta",
        "RSS_Gathered",
        "RSS_GatheredDelta",
        "RSSAssist",
        "RSSAssistDelta",
        "Helps",
        "HelpsDelta",
        "BuildingMinutes",
        "TechDonations",
        "FortsTotal",
        "FortsLaunched",
        "FortsJoined",
    ]
    for c in ALL_DAILY_COLS:
        if c not in df:
            df[c] = np.nan
    df_all = df[ALL_DAILY_COLS].copy()

    # Coerce GovernorID early and drop rows without an ID
    df_all["GovernorID"] = pd.to_numeric(df_all["GovernorID"], errors="coerce")
    df_all = df_all[df_all["GovernorID"].notna()].copy()
    df_all["GovernorID"] = df_all["GovernorID"].astype(int)

    # Targets (optional)
    targets = None
    if df_targets is not None and not df_targets.empty:
        t = df_targets.copy()
        # Coerce GovernorID and drop non-numeric
        t["GovernorID"] = pd.to_numeric(t["GovernorID"], errors="coerce")
        t = t[t["GovernorID"].notna()].copy()
        t["GovernorID"] = t["GovernorID"].astype(int)

        for c in ("DKP_TARGET", "DKP_SCORE"):
            if c in t:
                t[c] = pd.to_numeric(t[c], errors="coerce").fillna(0)
        targets = t.drop_duplicates("GovernorID")

    # Numeric clean (avoid inf in writer)
    num_cols = df_all.select_dtypes(include=["number"]).columns
    if len(num_cols):
        df_all[num_cols] = df_all[num_cols].replace([np.inf, -np.inf], np.nan)

    with pd.ExcelWriter(out_path, engine=_EXCEL_ENGINE) as writer:
        if _EXCEL_ENGINE == "xlsxwriter":
            # ---------- CREATE WORKSHEETS IN THE REQUIRED ORDER ----------
            wb = writer.book

            # 1) README
            ws_readme = wb.add_worksheet("README")
            writer.sheets["README"] = ws_readme  # register so we can style further
            # 2) INDEX (empty placeholder for now; filled later)
            ws_index = wb.add_worksheet("INDEX")
            writer.sheets["INDEX"] = ws_index
            # 3) ALL_DAILY (write via pandas into a pre-created sheet)
            ws_all = wb.add_worksheet("ALL_DAILY")
            writer.sheets["ALL_DAILY"] = ws_all
            df_all.to_excel(writer, index=False, sheet_name="ALL_DAILY")

            # 4) Targets (optional)
            if targets is not None and not targets.empty:
                ws_t = wb.add_worksheet("Targets")
                writer.sheets["Targets"] = ws_t
                targets.to_excel(writer, index=False, sheet_name="Targets")

            # ---------- FORMATS ----------
            f_h1 = wb.add_format({"bold": True, "font_size": 14})
            f_h2 = wb.add_format({"bold": True, "font_size": 12})
            f_hdr = wb.add_format({"bold": True, "bg_color": "#F2F2F7", "border": 1})
            f_num = wb.add_format({"num_format": "#,##0"})
            f_pct = wb.add_format({"num_format": "0%", "align": "center"})
            f_dim = wb.add_format({"font_color": "#666666"})
            f_link = wb.add_format({"font_color": "#2980B9", "underline": 1})
            f_date = wb.add_format({"num_format": "dd/mm/yyyy"})
            f_white = wb.add_format({"font_color": "#FFFFFF"})

            # ---------- README CONTENT ----------
            ws_readme.write(0, 0, "My KVK Stats Export", f_h1)
            ws_readme.write(2, 0, "This workbook shows YOUR registered accounts only.")
            ws_readme.write(3, 0, "Tab order & meaning:")
            ws_readme.write(4, 0, "• README – this page.")
            ws_readme.write(5, 0, "• INDEX – one row per account with quick links.")
            ws_readme.write(6, 0, "• ALL_DAILY – raw daily rows for the export window.")
            ws_readme.write(
                7, 0, "• <Name-ID> – KPIs, charts, and a recent daily table per account."
            )

            # ---------- STYLE ALL_DAILY ----------
            # Ensure header format and reasonable widths
            for c, name in enumerate(ALL_DAILY_COLS):
                ws_all.write(0, c, name, f_hdr)
                # width hint: longer for name/alliance/date, default otherwise
                ws_all.set_column(
                    c, c, 18 if name in ("GovernorName", "Alliance", "AsOfDate") else 14
                )
            ws_all.autofilter(0, 0, max(1, len(df_all)), max(0, len(ALL_DAILY_COLS) - 1))
            # Ensure AsOfDate column shows as a date
            asof_idx = ALL_DAILY_COLS.index("AsOfDate")
            ws_all.set_column(asof_idx, asof_idx, 18, f_date)

            # ---------- BUILD INDEX FROM LATEST SNAPSHOT ----------
            latest = (
                df_all.sort_values(["GovernorID", "AsOfDate"])
                .groupby("GovernorID", as_index=False)
                .tail(1)
            )
            # Ensure numeric IDs for the INDEX
            latest = latest[pd.to_numeric(latest["GovernorID"], errors="coerce").notna()].copy()
            latest["GovernorID"] = latest["GovernorID"].astype(int)

            # Add RSSAssist; optionally add FortsTotal (kept last so the sheet doesn’t get too wide)
            idx_cols = [
                "GovernorID",
                "GovernorName",
                "Alliance",
                "Power",
                "TroopPower",
                "KillPoints",
                "Deads",
                "RSS_Gathered",
                "RSSAssist",
                "Helps",
                "FortsTotal",  # ← optional; remove if you want a narrower index
            ]
            ws_index.write(0, 0, "Your Accounts", f_h1)
            ws_index.write_row(2, 0, idx_cols + ["DKP %", "Open"], f_hdr)

            # DKP %
            dkp_pct_map: dict[int, float] = {}
            if targets is not None and {"DKP_TARGET", "DKP_SCORE", "GovernorID"} <= set(
                targets.columns
            ):
                t = targets.copy()
                t["DKP_PCT"] = (t["DKP_SCORE"] / t["DKP_TARGET"].replace(0, pd.NA)).fillna(0.0)
                # Build an explicit mapping GovernorID -> DKP_PCT using pandas.
                # This avoids zip(...) and is explicit about the index-to-value mapping.
                # targets has already been deduplicated by GovernorID, so set_index is safe.
                dkp_pct_map = t.set_index("GovernorID")["DKP_PCT"].astype(float).to_dict()

            # Per-governor groups for later sheets & links
            by_gid = {
                int(gid): g.sort_values("AsOfDate") for gid, g in df_all.groupby("GovernorID")
            }

            # Safe sheet names: "<name>-<id>" truncated to Excel's 31 chars
            def _sheet_name(name: str, gid: int) -> str:
                base = f"{_clean_text(name)}-{gid}"
                return _safe_sheet_name(base, fallback=f"Account-{gid}")

            sheet_names = {
                gid: _sheet_name(g.iloc[-1]["GovernorName"], gid) for gid, g in by_gid.items()
            }

            start_row = 3
            for i, row in enumerate(latest[idx_cols].itertuples(index=False), start=start_row):
                vals = list(row)
                gid = int(vals[0])

                for j, v in enumerate(vals):
                    _write_safe(ws_index, i, j, v, f_num)  # ← handles NaN/Inf/None

                # DKP% is already fillna(0.0), but be defensive:
                dkp_val = float(dkp_pct_map.get(gid, 0.0))
                if np.isfinite(dkp_val):
                    ws_index.write_number(i, len(idx_cols), dkp_val, f_pct)
                else:
                    ws_index.write_blank(i, len(idx_cols), None)

                ws_index.write_url(
                    i, len(idx_cols) + 1, f"internal:'{sheet_names[gid]}'!A1", f_link, "Open"
                )

            # Widths — bump to fit the extra columns cleanly
            for c in range(len(idx_cols) + 2):
                ws_index.set_column(c, c, 16)
            # Make name wider, numeric a bit tighter
            name_col = idx_cols.index("GovernorName")
            ws_index.set_column(name_col, name_col, 22)
            for num_col in (
                idx_cols.index("Power"),
                idx_cols.index("TroopPower"),
                idx_cols.index("KillPoints"),
                idx_cols.index("Deads"),
            ):
                ws_index.set_column(num_col, num_col, 14)

            # ---------- PER-PLAYER SHEETS (KPI + 30d spark + 6m daily table + charts) ----------
            from xlsxwriter.utility import xl_col_to_name

            max_ts = pd.to_datetime(df_all["AsOfDate"]).max()
            thirty_cut = (max_ts - pd.Timedelta(days=30)).date()
            table_days = max(int(days_for_daily_table or 180), 1)
            sixm_cut = (max_ts - pd.Timedelta(days=table_days)).date()

            for gid, gdf in by_gid.items():
                gdf = gdf.copy()
                gdf["AsOfDate"] = pd.to_datetime(gdf["AsOfDate"])
                gname = _clean_text(str(gdf.iloc[-1]["GovernorName"]))
                sname = sheet_names[gid]
                ws_g = wb.add_worksheet(sname)

                # Header
                ws_g.write(0, 0, f"{gname} ({gid})", f_h1)
                ws_g.write(1, 0, f"Alliance: {gdf.iloc[-1]['Alliance']}", f_dim)

                # KPI Grid (unchanged)
                ws_g.write(3, 0, "KPIs", f_h2)
                ws_g.write_row(4, 0, ["Metric", "Latest", "MTD Δ", "Last Month Δ"], f_hdr)

                latest_snap = gdf.tail(1).to_dict("records")[0]
                month_start = gdf["AsOfDate"].max().replace(day=1)
                last_month_end = month_start - pd.Timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)

                m_mtd = _calc_period(gdf, month_start, gdf["AsOfDate"].max())
                m_last = _calc_period(gdf, last_month_start, last_month_end)

                kpi_rows = [
                    ("Power", latest_snap.get("Power"), m_mtd["PowerDelta"], m_last["PowerDelta"]),
                    (
                        "Troop Power",
                        latest_snap.get("TroopPower"),
                        m_mtd["TroopPowerDelta"],
                        m_last["TroopPowerDelta"],
                    ),
                    (
                        "Kill Points",
                        latest_snap.get("KillPoints"),
                        m_mtd["KillPointsDelta"],
                        m_last["KillPointsDelta"],
                    ),
                    ("Deads", latest_snap.get("Deads"), m_mtd["DeadsDelta"], m_last["DeadsDelta"]),
                    (
                        "RSS Gathered",
                        latest_snap.get("RSS_Gathered"),
                        m_mtd["RSS_GatheredDelta"],
                        m_last["RSS_GatheredDelta"],
                    ),
                    (
                        "RSS Assist",
                        latest_snap.get("RSSAssist"),
                        m_mtd["RSSAssistDelta"],
                        m_last["RSSAssistDelta"],
                    ),
                    ("Helps", latest_snap.get("Helps"), m_mtd["HelpsDelta"], m_last["HelpsDelta"]),
                    (
                        "Tech Donations",
                        latest_snap.get("TechDonations", 0),
                        m_mtd["TechDonationsSum"],
                        m_last["TechDonationsSum"],
                    ),
                ]
                for r, row_vals in enumerate(kpi_rows, start=5):
                    ws_g.write(r, 0, row_vals[0])
                    _write_safe(ws_g, r, 1, row_vals[1] or 0, f_num)
                    _write_safe(ws_g, r, 2, row_vals[2] or 0, f_num)
                    _write_safe(ws_g, r, 3, row_vals[3] or 0, f_num)
                ws_g.set_column(0, 3, 18)

                # 30-day Sparklines (unchanged)
                ws_g.write(13, 0, "Last 30 Days (sparklines)", f_h2)
                ws_g.write_row(14, 0, ["Metric", "Sparkline", "Min", "Max"], f_hdr)
                g30 = gdf[gdf["AsOfDate"].dt.date >= thirty_cut]
                metrics = ["Power", "TroopPower", "KillPoints", "Deads"]
                base_row = 15
                data_col = 10
                for idx_m, m in enumerate(metrics):
                    row_out = base_row + idx_m
                    ws_g.write(row_out, 0, m)
                    series = (
                        pd.to_numeric(g30.get(m, pd.Series(dtype=float)), errors="coerce")
                        .fillna(0)
                        .tolist()
                    )
                    for j, v in enumerate(series):
                        ws_g.write(row_out, data_col + j, v, f_white)
                    endc = xl_col_to_name(data_col + max(0, len(series) - 1))
                    rng = f"{xl_col_to_name(data_col)}{row_out+1}:{endc}{row_out+1}"
                    ws_g.add_sparkline(row_out, 1, {"range": f"'{sname}'!{rng}", "type": "line"})
                    _write_safe(ws_g, row_out, 2, min(series) if series else 0, f_num)
                    _write_safe(ws_g, row_out, 3, max(series) if series else 0, f_num)
                ws_g.set_column(1, 1, 22)
                ws_g.set_column(data_col, data_col + 200, None, None, {"hidden": True})

                # ===== UNIFIED SECTION =====
                # Charts first (stacked vertically), then the 6-month daily table they reference
                chart_top = 21
                ws_g.write(chart_top - 1, 0, f"Last {table_days} Days — Overview", f_h2)

                daily_cols = [
                    "AsOfDate",
                    "Power",
                    "PowerDelta",
                    "TroopPower",
                    "TroopPowerDelta",
                    "KillPoints",
                    "KillPointsDelta",
                    "Deads",
                    "DeadsDelta",
                    "RSS_Gathered",
                    "RSS_GatheredDelta",
                    "RSSAssist",
                    "RSSAssistDelta",
                    "Helps",
                    "HelpsDelta",
                    "BuildingMinutes",
                    "TechDonations",
                    "FortsTotal",
                    "FortsLaunched",
                    "FortsJoined",
                ]

                # We'll write the table AFTER the charts. Charts can point to ranges that will be populated later.
                # Define where the table will live (below the stacked charts).
                # Each chart block is ~16 rows tall with the current scaling; stack 3 → 48 rows.
                table_top = chart_top + 48
                ws_g.write(table_top, 0, f"Last {table_days} Days — Daily", f_h2)
                ws_g.write_row(table_top + 1, 0, daily_cols, f_hdr)

                # Build the 6-month dataframe now (so we know ranges for chart series)
                g6 = gdf[gdf["AsOfDate"].dt.date >= sixm_cut].copy()
                for c in daily_cols:
                    if c not in g6:
                        g6[c] = np.nan
                g6 = g6[daily_cols]

                # Coerce numerics
                for c in daily_cols:
                    if c != "AsOfDate":
                        g6[c] = pd.to_numeric(g6[c], errors="coerce").replace(
                            [np.inf, -np.inf], np.nan
                        )

                # Helper: data range resolver that points to the (future) table location
                start_data_row = table_top + 2

                def _rng(col_name: str):
                    c_idx = daily_cols.index(col_name)
                    end_row = start_data_row + max(len(g6), 0) - 1
                    return [sname, start_data_row, c_idx, end_row, c_idx]

                if len(g6) == 0:
                    # No data: write a friendly note and skip charts
                    ws_g.write(chart_top, 0, "No data available for this period.", f_dim)
                else:
                    # 1) Power vs Troop Power (line)
                    ch = wb.add_chart({"type": "line"})
                    ch.add_series(
                        {"name": "Power", "categories": _rng("AsOfDate"), "values": _rng("Power")}
                    )
                    ch.add_series(
                        {
                            "name": "TroopPower",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("TroopPower"),
                        }
                    )
                    ch.set_title({"name": "Power vs Troop Power"})
                    ch.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ch.set_y_axis({"name": "Power"})
                    ws_g.insert_chart(chart_top, 0, ch, {"x_scale": 1.15, "y_scale": 1.0})

                    # 2) Kill Points vs Deads (combo col + line on secondary axis)
                    ch2 = wb.add_chart({"type": "column"})
                    ch2.add_series(
                        {
                            "name": "KillPoints",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("KillPoints"),
                        }
                    )
                    ch2.add_series(
                        {
                            "name": "Deads",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("Deads"),
                            "type": "line",
                            "y2_axis": True,
                        }
                    )
                    ch2.set_title({"name": "Kill Points vs Deads"})
                    ch2.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ws_g.insert_chart(chart_top + 16, 0, ch2, {"x_scale": 1.15, "y_scale": 1.0})

                    # 3) RSS Gathered & Assist (columns)
                    ch3 = wb.add_chart({"type": "column"})
                    ch3.add_series(
                        {
                            "name": "RSS Gathered",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("RSS_Gathered"),
                        }
                    )
                    ch3.add_series(
                        {
                            "name": "RSS Assist",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("RSSAssist"),
                        }
                    )
                    ch3.set_title({"name": "RSS Gathered & RSS Assist"})
                    ch3.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ws_g.insert_chart(chart_top + 32, 0, ch3, {"x_scale": 1.15, "y_scale": 1.0})

                # ---- Now write the 6-month table the charts reference ----
                # Date formatting on first column
                ws_g.set_column(0, 0, 16, f_date)
                # Reasonable widths on others
                for j in range(1, len(daily_cols)):
                    ws_g.set_column(j, j, 16)

                # Write rows (dates as true datetimes)
                for i, rec in enumerate(
                    g6.itertuples(index=False, name=None), start=start_data_row
                ):
                    for j, v in enumerate(rec):
                        if daily_cols[j] == "AsOfDate":
                            dv = pd.to_datetime(v).to_pydatetime()
                            ws_g.write_datetime(i, j, dv, f_date)
                        else:
                            _write_safe(ws_g, i, j, v, f_num)

                end_row = start_data_row + len(g6) - 1
                ws_g.autofilter(table_top + 1, 0, max(table_top + 1, end_row), len(daily_cols) - 1)

                # Freeze the table header
                # ws_g.freeze_panes(table_top + 2, 0)

        else:
            # ---------- OPENPYXL PATH (no fancy formatting; still correct sheet order) ----------
            # Create README and INDEX first (as empty DataFrames) to enforce order
            pd.DataFrame(
                {
                    "Info": [
                        "My KVK Stats Export",
                        "This workbook shows YOUR registered accounts only.",
                        "Tabs: README, INDEX, ALL_DAILY, per-account sheets, Targets (optional).",
                    ]
                }
            ).to_excel(writer, index=False, sheet_name="README")
            pd.DataFrame(columns=["GovernorID", "GovernorName", "Alliance"]).to_excel(
                writer, index=False, sheet_name="INDEX"
            )
            df_all.to_excel(writer, index=False, sheet_name="ALL_DAILY")
            if targets is not None and not targets.empty:
                targets.to_excel(writer, index=False, sheet_name="Targets")

            # Per-player (basic sheets so at least structure/order is correct)
            for gid, gdf in df_all.groupby("GovernorID"):
                name = str(gdf.sort_values("AsOfDate").iloc[-1]["GovernorName"])
                sname = f"{_clean_text(name)}-{int(gid)}"[:31]
                g_basic = gdf.copy()
                g_basic.to_excel(writer, index=False, sheet_name=sname)
