# stats_exporter_csv.py
"""
CSV exporter for user stats.
Lightweight alternative to Excel format.
"""

from __future__ import annotations

import csv
import os

import numpy as np
import pandas as pd


def _clean_text(s: str | None) -> str:
    if s is None:
        return ""
    return " ".join(str(s).split())


def build_user_stats_csv(
    df_daily: pd.DataFrame,
    df_targets: pd.DataFrame | None,
    *,
    out_path: str,
    days_for_daily_table: int = 180,
) -> None:
    """
    Export user stats to CSV format.

    Creates a simple flat CSV file with all daily data.
    More compact than Excel but loses formatting/charts.

    Args:
        df_daily: Daily stats dataframe
        df_targets: Targets dataframe (currently ignored, reserved for future)
        out_path: Output file path
        days_for_daily_table: Number of days to include (default 180)
    """
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

    # Column order (same as Excel export for consistency)
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

    # Filter to requested date range
    max_date = pd.to_datetime(df_all["AsOfDate"]).max()
    cutoff_date = max_date - pd.Timedelta(days=days_for_daily_table)
    df_filtered = df_all[pd.to_datetime(df_all["AsOfDate"]) >= cutoff_date].copy()

    # Write CSV
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(ALL_DAILY_COLS)

        # Data rows
        for _, row in df_filtered.iterrows():
            row_data = []
            for col in ALL_DAILY_COLS:
                val = row[col]
                if pd.isna(val) or val is None:
                    row_data.append("")
                elif col == "AsOfDate":
                    # Format as date string
                    row_data.append(
                        pd.to_datetime(val).strftime("%Y-%m-%d") if pd.notna(val) else ""
                    )
                elif isinstance(val, (int, np.integer)):
                    row_data.append(int(val))
                elif isinstance(val, (float, np.floating)):
                    row_data.append(float(val))
                else:
                    row_data.append(str(val))
            writer.writerow(row_data)
