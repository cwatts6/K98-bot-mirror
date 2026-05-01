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
        # Core metrics
        "PowerEnd": snapv("Power"),
        "TroopPowerEnd": snapv("TroopPower"),
        "KillPointsEnd": snapv("KillPoints"),
        "DeadsEnd": snapv("Deads"),
        "RSSGatheredEnd": snapv("RSS_Gathered"),
        "RSSAssistEnd": snapv("RSSAssist"),
        "HelpsEnd": snapv("Helps"),
        "PowerDelta": colsum("PowerDelta"),
        "TroopPowerDelta": colsum("TroopPowerDelta"),
        "KillPointsDelta": colsum("KillPointsDelta"),
        "DeadsDelta": colsum("DeadsDelta"),
        "RSS_GatheredDelta": colsum("RSS_GatheredDelta"),
        "RSSAssistDelta": colsum("RSSAssistDelta"),
        "HelpsDelta": colsum("HelpsDelta"),
        "TechDonationsSum": colsum("TechDonations"),
        # Forts (ADDED - was missing!)
        "FortsTotalEnd": snapv("FortsTotal"),
        "FortsLaunchedSum": colsum("FortsLaunched"),
        "FortsJoinedSum": colsum("FortsJoined"),
        # AOO
        "AOOJoinedEnd": snapv("AOOJoined"),
        "AOOWonEnd": snapv("AOOWon"),
        "AOOAvgKillEnd": snapv("AOOAvgKill"),
        "AOOAvgDeadEnd": snapv("AOOAvgDead"),
        "AOOAvgHealEnd": snapv("AOOAvgHeal"),
        # Detailed metrics
        "T4_KillsEnd": snapv("T4_Kills"),
        "T5_KillsEnd": snapv("T5_Kills"),
        "T4T5_KillsEnd": snapv("T4T5_Kills"),
        "HealedTroopsEnd": snapv("HealedTroops"),
        "RangedPointsEnd": snapv("RangedPoints"),
        "HighestAcclaimEnd": snapv("HighestAcclaim"),
        "AutarchTimesEnd": snapv("AutarchTimes"),
        "T4_KillsDelta": colsum("T4_KillsDelta"),
        "T5_KillsDelta": colsum("T5_KillsDelta"),
        "T4T5_KillsDelta": colsum("T4T5_KillsDelta"),
        "HealedTroopsDelta": colsum("HealedTroopsDelta"),
        "RangedPointsDelta": colsum("RangedPointsDelta"),
    }


_FORBIDDEN_SHEET_CHARS = set(r"[]:*?/\\")


def _safe_sheet_name(base: str, fallback: str, max_len: int = 31) -> str:
    s = (base or "").strip().strip("'")
    s = "".join(ch for ch in s if ch not in _FORBIDDEN_SHEET_CHARS)
    s = s or fallback
    return s[:max_len]


def build_user_stats_excel(
    df_daily: pd.DataFrame,
    df_targets: pd.DataFrame | None,
    *,
    out_path: str,
    days_for_daily_table: int = 90,
) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    df = df_daily.copy()
    df["AsOfDate"] = pd.to_datetime(df["AsOfDate"]).dt.normalize()
    for col in ("GovernorName", "Alliance"):
        if col in df:
            df[col] = df[col].apply(_clean_text)

    # Drop deprecated columns
    drop_cols = {"TechPower", "TechPowerDelta"}
    keep = [c for c in df.columns if c not in drop_cols]
    df = df[keep]

    # ALL_DAILY column order
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
        "AOOJoined",
        "AOOJoinedDelta",
        "AOOWon",
        "AOOWonDelta",
        "AOOAvgKill",
        "AOOAvgKillDelta",
        "AOOAvgDead",
        "AOOAvgDeadDelta",
        "AOOAvgHeal",
        "AOOAvgHealDelta",
        "T4_Kills",
        "T4_KillsDelta",
        "T5_Kills",
        "T5_KillsDelta",
        "T4T5_Kills",
        "T4T5_KillsDelta",
        "HealedTroops",
        "HealedTroopsDelta",
        "RangedPoints",
        "RangedPointsDelta",
        "HighestAcclaim",
        "HighestAcclaimDelta",
        "AutarchTimes",
        "AutarchTimesDelta",
    ]
    for c in ALL_DAILY_COLS:
        if c not in df:
            df[c] = np.nan
    df_all = df[ALL_DAILY_COLS].copy()

    df_all["GovernorID"] = pd.to_numeric(df_all["GovernorID"], errors="coerce")
    df_all = df_all[df_all["GovernorID"].notna()].copy()
    df_all["GovernorID"] = df_all["GovernorID"].astype(int)

    num_cols = df_all.select_dtypes(include=["number"]).columns
    if len(num_cols):
        df_all[num_cols] = df_all[num_cols].replace([np.inf, -np.inf], np.nan)

    with pd.ExcelWriter(out_path, engine=_EXCEL_ENGINE) as writer:
        if _EXCEL_ENGINE == "xlsxwriter":
            wb = writer.book

            ws_readme = wb.add_worksheet("README")
            writer.sheets["README"] = ws_readme
            ws_index = wb.add_worksheet("INDEX")
            writer.sheets["INDEX"] = ws_index
            ws_all = wb.add_worksheet("ALL_DAILY")
            writer.sheets["ALL_DAILY"] = ws_all
            df_all.to_excel(writer, index=False, sheet_name="ALL_DAILY")

            f_h1 = wb.add_format({"bold": True, "font_size": 14})
            f_h2 = wb.add_format({"bold": True, "font_size": 12})
            f_hdr = wb.add_format({"bold": True, "bg_color": "#F2F2F7", "border": 1})
            f_num = wb.add_format({"num_format": "#,##0"})
            f_dim = wb.add_format({"font_color": "#666666"})
            f_link = wb.add_format({"font_color": "#2980B9", "underline": 1})
            f_date = wb.add_format({"num_format": "dd/mm/yyyy"})
            f_white = wb.add_format({"font_color": "#FFFFFF"})

            ws_readme.write(0, 0, "My Stats Export", f_h1)
            ws_readme.write(2, 0, "This workbook shows YOUR registered accounts only.")
            ws_readme.write(3, 0, "Tab order:")
            ws_readme.write(4, 0, "• README – this page")
            ws_readme.write(5, 0, "• INDEX – account summary with links")
            ws_readme.write(6, 0, "• ALL_DAILY – raw daily data")
            ws_readme.write(7, 0, "• <Name-ID> – KPIs, charts, and tables per account")

            for c, name in enumerate(ALL_DAILY_COLS):
                ws_all.write(0, c, name, f_hdr)
                ws_all.set_column(
                    c, c, 18 if name in ("GovernorName", "Alliance", "AsOfDate") else 14
                )
            ws_all.autofilter(0, 0, max(1, len(df_all)), max(0, len(ALL_DAILY_COLS) - 1))
            asof_idx = ALL_DAILY_COLS.index("AsOfDate")
            ws_all.set_column(asof_idx, asof_idx, 18, f_date)

            # ---------- BUILD INDEX FROM LATEST SNAPSHOT ----------
            # Get latest row per governor for snapshot metrics
            latest = (
                df_all.sort_values(["GovernorID", "AsOfDate"])
                .groupby("GovernorID", as_index=False)
                .tail(1)
            )
            latest = latest[pd.to_numeric(latest["GovernorID"], errors="coerce").notna()].copy()
            latest["GovernorID"] = latest["GovernorID"].astype(int)

            # For daily count metrics (FortsTotal, etc.), sum over a period instead of showing latest
            # Using last 180 days same as all data for summary
            max_date = pd.to_datetime(df_all["AsOfDate"]).max()
            period_start = max_date - pd.Timedelta(days=180)

            # Calculate period sums for daily metrics
            period_data = df_all[pd.to_datetime(df_all["AsOfDate"]) >= period_start].copy()

            period_sums = period_data.groupby("GovernorID", as_index=False).agg(
                {
                    "FortsTotal": lambda x: int(pd.to_numeric(x, errors="coerce").fillna(0).sum()),
                    "FortsLaunched": lambda x: int(
                        pd.to_numeric(x, errors="coerce").fillna(0).sum()
                    ),
                    "FortsJoined": lambda x: int(pd.to_numeric(x, errors="coerce").fillna(0).sum()),
                }
            )

            # Merge period sums into latest
            latest = latest.merge(
                period_sums, on="GovernorID", how="left", suffixes=("", "_period")
            )

            # Replace snapshot FortsTotal with period sum
            if "FortsTotal_period" in latest.columns:
                latest["FortsTotal"] = latest["FortsTotal_period"].fillna(0).astype(int)
                latest = latest.drop(
                    columns=["FortsTotal_period", "FortsLaunched_period", "FortsJoined_period"],
                    errors="ignore",
                )
            else:
                latest["FortsTotal"] = 0

            # Ensure AOO and T4/T5 fields exist (these are cumulative, so snapshot is correct)
            for col in ["AOOJoined", "T4_Kills", "T5_Kills"]:
                if col not in latest.columns:
                    latest[col] = 0
                else:
                    latest[col] = latest[col].fillna(0).astype(int)

            idx_cols = [
                "GovernorID",
                "GovernorName",
                "Alliance",
                "Power",
                "TroopPower",
                "KillPoints",
                "T4T5_Kills",  # Cumulative (snapshot)
                "Deads",
                "HealedTroops",
                "RSS_Gathered",
                "RSSAssist",
                "Helps",
                "FortsTotal",  # Now shows last 180 days sum
                "AOOJoined",  # Cumulative (snapshot)
                "AOOWon",  # Cumulative (snapshot) - NEW
            ]
            ws_index.write(0, 0, "Your Accounts", f_h1)
            ws_index.write_row(2, 0, idx_cols + ["Open"], f_hdr)

            by_gid = {
                int(gid): g.sort_values("AsOfDate") for gid, g in df_all.groupby("GovernorID")
            }

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
                    _write_safe(ws_index, i, j, v, f_num)

                ws_index.write_url(
                    i, len(idx_cols), f"internal:'{sheet_names[gid]}'!A1", f_link, "Open"
                )

            for c in range(len(idx_cols) + 1):
                ws_index.set_column(c, c, 16)
            name_col = idx_cols.index("GovernorName")
            ws_index.set_column(name_col, name_col, 22)

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

                ws_g.write(0, 0, f"{gname} ({gid})", f_h1)
                ws_g.write(1, 0, f"Alliance: {gdf.iloc[-1]['Alliance']}", f_dim)

                # KPI Grid
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
                    (
                        "Forts Total",
                        latest_snap.get("FortsTotal", 0),
                        m_mtd.get("FortsLaunchedSum", 0),
                        m_last.get("FortsLaunchedSum", 0),
                    ),
                    ("AOO Joined", latest_snap.get("AOOJoined", 0), 0, 0),
                    ("AOO Won", latest_snap.get("AOOWon", 0), 0, 0),
                    (
                        "T4 Kills",
                        latest_snap.get("T4_Kills", 0),
                        m_mtd["T4_KillsDelta"],
                        m_last["T4_KillsDelta"],
                    ),
                    (
                        "T5 Kills",
                        latest_snap.get("T5_Kills", 0),
                        m_mtd["T5_KillsDelta"],
                        m_last["T5_KillsDelta"],
                    ),
                ]
                for r, row_vals in enumerate(kpi_rows, start=5):
                    ws_g.write(r, 0, row_vals[0])
                    _write_safe(ws_g, r, 1, row_vals[1] or 0, f_num)
                    _write_safe(ws_g, r, 2, row_vals[2] or 0, f_num)
                    _write_safe(ws_g, r, 3, row_vals[3] or 0, f_num)
                ws_g.set_column(0, 3, 18)

                # 30-day Sparklines
                ws_g.write(18, 0, "Last 30 Days (sparklines)", f_h2)
                ws_g.write_row(19, 0, ["Metric", "Sparkline", "Min", "Max"], f_hdr)
                g30 = gdf[gdf["AsOfDate"].dt.date >= thirty_cut]
                metrics = ["Power", "TroopPower", "KillPoints", "Deads"]
                base_row = 20
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

                # ===== CHARTS + DAILY TABLE SECTION =====
                chart_top = 26
                ws_g.write(chart_top - 1, 0, f"Last {table_days} Days — Overview", f_h2)

                # ===== CHARTS + DAILY TABLE SECTION =====
                chart_top = 26
                ws_g.write(chart_top - 1, 0, f"Last {table_days} Days — Overview", f_h2)

                daily_cols = [
                    "AsOfDate",
                    "Power",
                    "PowerDelta",
                    "TroopPower",
                    "TroopPowerDelta",
                    "KillPoints",
                    "KillPointsDelta",
                    "T4_Kills",
                    "T5_Kills",
                    "T4T5_Kills",
                    "Deads",
                    "DeadsDelta",
                    "HealedTroops",
                    "HealedTroopsDelta",
                    "RSS_Gathered",
                    "RSS_GatheredDelta",
                    "RSSAssist",
                    "RSSAssistDelta",
                    "Helps",
                    "HelpsDelta",
                    "BuildingMinutes",
                    "TechDonations",
                    "FortsTotal",
                    "FortsTotal_Cumulative",
                    "FortsLaunched",
                    "FortsJoined",
                    "AOOJoined",
                    "AOOWon",
                ]

                # Daily table positioning (after charts - 5 charts × 16 rows each = 80 rows)
                table_top = chart_top + 80
                ws_g.write(table_top, 0, f"Last {table_days} Days — Daily", f_h2)
                ws_g.write_row(table_top + 1, 0, daily_cols, f_hdr)

                # Build data for charts and table
                g6 = gdf[gdf["AsOfDate"].dt.date >= sixm_cut].copy()
                for c in daily_cols:
                    if c not in g6:
                        g6[c] = np.nan
                g6 = g6[daily_cols]

                for c in daily_cols:
                    if c != "AsOfDate":
                        g6[c] = pd.to_numeric(g6[c], errors="coerce").replace(
                            [np.inf, -np.inf], np.nan
                        )

                # Calculate cumulative FortsTotal for Chart 5 (running sum)
                if "FortsTotal" in g6.columns:
                    g6["FortsTotal_Cumulative"] = g6["FortsTotal"].fillna(0).cumsum()
                    # ADD IT TO daily_cols so _rng() can find it
                    if "FortsTotal_Cumulative" not in daily_cols:
                        forts_idx = daily_cols.index("FortsTotal")
                        daily_cols.insert(forts_idx + 1, "FortsTotal_Cumulative")

                # Define data range for charts (points to future table location)
                start_data_row = table_top + 2

                def _rng(col_name: str):
                    c_idx = daily_cols.index(col_name)
                    end_row = start_data_row + max(len(g6), 0) - 1
                    return [sname, start_data_row, c_idx, end_row, c_idx]

                if len(g6) == 0:
                    ws_g.write(chart_top, 0, "No data available for this period.", f_dim)
                else:
                    # CHART 1: Power vs Troop Power
                    ch1 = wb.add_chart({"type": "line"})
                    ch1.add_series(
                        {
                            "name": "Power",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("Power"),
                            "line": {"color": "#3498DB", "width": 2},
                        }
                    )
                    ch1.add_series(
                        {
                            "name": "Troop Power",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("TroopPower"),
                            "line": {"color": "#E74C3C", "width": 2},
                        }
                    )
                    ch1.set_title({"name": "Power vs Troop Power"})
                    ch1.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ch1.set_y_axis(
                        {"name": "Power", "num_format": '[>=1000000000]###,#,,,"b";#,##0,,"m"'}
                    )
                    ch1.set_legend({"position": "bottom"})
                    ws_g.insert_chart(chart_top, 0, ch1, {"x_scale": 1.15, "y_scale": 1.0})

                    # CHART 2: Kill Points - CONDITIONAL FORMAT
                    ch2 = wb.add_chart({"type": "line"})
                    ch2.add_series(
                        {
                            "name": "Kill Points",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("KillPoints"),
                            "line": {"color": "#8E44AD", "width": 2.5},
                            "marker": {"type": "circle", "size": 4},
                        }
                    )
                    ch2.set_title({"name": "Kill Points"})
                    ch2.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ch2.set_y_axis(
                        {
                            "name": "Kill Points",
                            "num_format": '[>=1000000000]###,#,,,"b";#,##0,,"m"',
                        }
                    )
                    ch2.set_legend({"position": "bottom"})
                    ws_g.insert_chart(chart_top + 16, 0, ch2, {"x_scale": 1.15, "y_scale": 1.0})

                    # CHART 3: RSS - CONDITIONAL FORMAT
                    ch3 = wb.add_chart({"type": "line"})
                    ch3.add_series(
                        {
                            "name": "RSS Gathered",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("RSS_Gathered"),
                            "line": {"color": "#52BE80", "width": 2.5},
                            "marker": {"type": "circle", "size": 4},
                        }
                    )
                    ch3.add_series(
                        {
                            "name": "RSS Assist",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("RSSAssist"),
                            "line": {"color": "#5DADE2", "width": 2.5},
                            "marker": {"type": "square", "size": 4},
                        }
                    )
                    ch3.set_title({"name": "RSS Gathered & RSS Assist"})
                    ch3.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ch3.set_y_axis(
                        {"name": "RSS", "num_format": '[>=1000000000]###,#,,,"b";#,##0,,"m"'}
                    )
                    ch3.set_legend({"position": "bottom"})
                    ws_g.insert_chart(chart_top + 32, 0, ch3, {"x_scale": 1.15, "y_scale": 1.0})

                    # CHART 4: Combat Stats - CONDITIONAL FORMAT
                    ch4 = wb.add_chart({"type": "line"})
                    ch4.add_series(
                        {
                            "name": "T4+T5 Kills",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("T4T5_Kills"),
                            "line": {"color": "#E74C3C", "width": 2.5},
                            "marker": {"type": "circle", "size": 4},
                        }
                    )
                    if "HealedTroops" in g6.columns:
                        ch4.add_series(
                            {
                                "name": "Healed Troops",
                                "categories": _rng("AsOfDate"),
                                "values": _rng("HealedTroops"),
                                "line": {"color": "#52BE80", "width": 2.5},
                                "marker": {"type": "diamond", "size": 5},
                            }
                        )
                    ch4.add_series(
                        {
                            "name": "Deads",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("Deads"),
                            "line": {"color": "#34495E", "width": 2.5},
                            "marker": {"type": "square", "size": 5},
                            "y2_axis": True,
                        }
                    )
                    ch4.set_title({"name": "Combat Stats (T4&T5 Kills, Healed, Deads)"})
                    ch4.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ch4.set_y_axis(
                        {
                            "name": "T4&T5 Kills / Healed",
                            "num_format": '[>=1000000000]###,#,,,"b";#,##0,,"m"',
                        }
                    )
                    ch4.set_y2_axis(
                        {"name": "Deads", "num_format": '[>=1000000000]###,#,,,"b";#,##0,,"m"'}
                    )
                    ch4.set_legend({"position": "bottom"})
                    ws_g.insert_chart(chart_top + 48, 0, ch4, {"x_scale": 1.15, "y_scale": 1.0})

                    # CHART 5: Forts (no change - these are small numbers)
                    ch5 = wb.add_chart({"type": "line"})
                    ch5.add_series(
                        {
                            "name": "Forts Total (Running Sum)",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("FortsTotal_Cumulative"),
                            "line": {"color": "#95A5A6", "width": 3},
                        }
                    )
                    ch5.add_series(
                        {
                            "name": "Forts Launched",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("FortsLaunched"),
                            "type": "column",
                            "fill": {"color": "#E74C3C"},
                            "y2_axis": True,
                        }
                    )
                    ch5.add_series(
                        {
                            "name": "Forts Joined",
                            "categories": _rng("AsOfDate"),
                            "values": _rng("FortsJoined"),
                            "type": "column",
                            "fill": {"color": "#3498DB"},
                            "y2_axis": True,
                        }
                    )
                    ch5.set_title({"name": "Forts Timeline (Cumulative & Daily)"})
                    ch5.set_x_axis({"name": "Date", "date_axis": True, "num_format": "dd/mm/yyyy"})
                    ch5.set_y_axis({"name": "Total (Cumulative)", "num_format": "#,##0"})
                    ch5.set_y2_axis({"name": "Launch / Join (Daily)", "num_format": "#,##0"})
                    ch5.set_legend({"position": "bottom"})
                    ws_g.insert_chart(chart_top + 64, 0, ch5, {"x_scale": 1.15, "y_scale": 1.0})

                # Write the daily table data (that charts reference)
                ws_g.set_column(0, 0, 16, f_date)
                for j in range(1, len(daily_cols)):
                    ws_g.set_column(j, j, 14)

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

        else:
            # openpyxl fallback
            pd.DataFrame(
                {
                    "Info": [
                        "My Stats Export",
                        "This workbook shows YOUR registered accounts only.",
                        "Tabs: README, INDEX, ALL_DAILY, per-account sheets.",
                    ]
                }
            ).to_excel(writer, index=False, sheet_name="README")
            pd.DataFrame(columns=["GovernorID", "GovernorName", "Alliance"]).to_excel(
                writer, index=False, sheet_name="INDEX"
            )
            df_all.to_excel(writer, index=False, sheet_name="ALL_DAILY")

            for gid, gdf in df_all.groupby("GovernorID"):
                name = str(gdf.sort_values("AsOfDate").iloc[-1]["GovernorName"])
                sname = f"{_clean_text(name)}-{int(gid)}"[:31]
                g_basic = gdf.copy()
                g_basic.to_excel(writer, index=False, sheet_name=sname)
