"""Raw personal Stats history CSV builder."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from player_self_service.account_data_export_contract import (
    filter_history_window,
    spreadsheet_safe_text,
)
from stats.dal.stats_export_dal import EXPORT_COLUMNS

RAW_HISTORY_COLUMNS = tuple(EXPORT_COLUMNS)
_TEXT_COLUMNS = frozenset({"GovernorName", "Alliance"})
_DATE_COLUMNS = frozenset({"AsOfDate"})


def _prepare_history_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy(deep=True)
    for column in RAW_HISTORY_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = pd.NA
    prepared = prepared.loc[:, RAW_HISTORY_COLUMNS].copy()
    if not prepared.empty:
        prepared["GovernorID"] = pd.to_numeric(prepared["GovernorID"], errors="coerce")
        prepared["AsOfDate"] = pd.to_datetime(prepared["AsOfDate"], errors="coerce")
        prepared = prepared.sort_values(
            ["GovernorID", "AsOfDate"], ascending=[True, False], kind="mergesort"
        ).reset_index(drop=True)
    return prepared


def _csv_value(column: str, value: Any) -> Any:
    if value is None or pd.isna(value):
        return ""
    if column in _TEXT_COLUMNS:
        return spreadsheet_safe_text(value)
    if column in _DATE_COLUMNS:
        timestamp = pd.Timestamp(value)
        return "" if pd.isna(timestamp) else timestamp.date().isoformat()
    if column == "GovernorID":
        return int(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            return ""
        return int(number) if number.is_integer() else number
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number) or not math.isfinite(float(number)):
        return ""
    numeric = float(number)
    return int(numeric) if numeric.is_integer() else numeric


def build_account_data_history_csv(frame: pd.DataFrame, *, out_path: str | Path) -> str:
    """Write already-authorised, already-filtered history in the locked raw contract."""
    prepared = _prepare_history_frame(frame)
    target = Path(out_path)
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(RAW_HISTORY_COLUMNS)
        for row in prepared.itertuples(index=False, name=None):
            writer.writerow(
                _csv_value(column, value)
                for column, value in zip(RAW_HISTORY_COLUMNS, row, strict=True)
            )
    return str(target)


def build_user_stats_csv(
    df_daily: pd.DataFrame,
    _df_targets: pd.DataFrame | None,
    *,
    out_path: str = "user_stats.csv",
    days_for_daily_table: int = 180,
) -> str:
    """Compatibility wrapper using the canonical Phase 5G window helper."""
    window = filter_history_window(df_daily, days_for_daily_table)
    return build_account_data_history_csv(window.frame, out_path=out_path)
