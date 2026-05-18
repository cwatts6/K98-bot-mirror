# stats_alerts/kvk_meta.py
import logging
from typing import Any

import numpy as np
import pandas as pd

from constants import (
    KVK_SHEET_ID,
)
import gsheet_module as gm
from kvk_state import get_kvk_context_today, get_latest_kvk_details, is_scan_within_open_window

# Fixed import: parse_mixed_dates exists as that name in formatters.py
from stats_alerts.formatters import parse_mixed_dates as _parse_mixed_dates
from utils import date_to_utc_start, utcnow

logger = logging.getLogger(__name__)


def get_latest_kvk_metadata_sql() -> dict[str, Any] | None:
    try:
        details = get_latest_kvk_details()
        if not details:
            return None
        return dict(details)
    except Exception:
        logger.exception("[KVK SQL META] Failed to read KVK_Details")
        return None


def get_latest_kvk_metadata() -> dict[str, Any] | None:
    """Sheets fallback for *display only* (name/dates/banner)."""
    try:
        # Use centralized gsheet wrapper for consistent retry/telemetry.
        rows = gm.get_sheet_values(KVK_SHEET_ID, "KVK_Details!A1:Z")
        # gm.get_sheet_values returns None on error, [] for empty ranges
        if not rows:
            return None

        headers = rows[0]
        df = pd.DataFrame(rows[1:], columns=headers)

        df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")
        # Use the imported robust parser from formatters
        df["KVK_START_DATE"] = _parse_mixed_dates(df["KVK_START_DATE"])
        df["KVK_END_DATE"] = _parse_mixed_dates(df["KVK_END_DATE"])
        df["MATCHMAKING_SCAN"] = pd.to_numeric(df.get("MATCHMAKING_SCAN"), errors="coerce")
        df["KVK_END_SCAN"] = pd.to_numeric(df.get("KVK_END_SCAN"), errors="coerce")

        if "MATCHMAKING_SCAN" in df.columns:
            df.loc[
                df["MATCHMAKING_SCAN"].isna() | (df["MATCHMAKING_SCAN"] <= 0), "MATCHMAKING_SCAN"
            ] = np.nan
        if "KVK_END_SCAN" in df.columns:
            df.loc[df["KVK_END_SCAN"].isna() | (df["KVK_END_SCAN"] <= 0), "KVK_END_SCAN"] = np.nan

        df = df.dropna(
            subset=[
                "KVK_NO",
                "KVK_NAME",
                "KVK_START_DATE",
                "KVK_END_DATE",
                "MATCHMAKING_SCAN",
                "KVK_END_SCAN",
            ]
        )
        latest_row = df.sort_values("KVK_NO", ascending=False).iloc[0]

        return {
            "kvk_no": int(latest_row["KVK_NO"]),
            "kvk_name": latest_row["KVK_NAME"],
            "start_date": latest_row["KVK_START_DATE"],
            "end_date": latest_row["KVK_END_DATE"],
            "matchmaking_scan": int(latest_row["MATCHMAKING_SCAN"]),
            "kvk_end_scan": int(latest_row["KVK_END_SCAN"]),
        }
    except Exception:
        logger.exception("[KVK META] Failed to load KVK metadata")
        return None


def get_kvk_window_from_sql() -> dict[str, int | None] | None:
    try:
        details = get_latest_kvk_details()
        if not details:
            return None
        return {
            "kvk_no": details["kvk_no"],
            "matchmaking_scan": details["matchmaking_scan"],
            "kvk_end_scan": details["kvk_end_scan"],
            "pass4_start_scan": details["pass4_start_scan"],
        }
    except Exception:
        logger.exception("[KVK SQL] Failed to read KVK window")
        return None


def is_currently_kvk(*_args: Any, **_kwargs: Any) -> bool:
    try:
        ctx = get_kvk_context_today()
        if not ctx:
            return False
        return is_scan_within_open_window(
            ctx.get("matchmaking_scan"),
            ctx.get("kvk_end_scan"),
            ctx.get("max_scan_order"),
        )
    except Exception:
        logger.exception("[KVK CHECK] Unexpected failure in KVK detection logic")
        return False


def is_kvk_fighting_open() -> bool:
    try:
        ctx = get_kvk_context_today()
        return bool(ctx and ctx.get("state") == "ACTIVE")
    except Exception:
        logger.exception("[KVK CHECK] Unexpected failure in Pass4 gate")
        return False


def days_until(date_obj) -> int | None:
    if not date_obj:
        return None
    try:
        target_utc = date_to_utc_start(date_obj)
        if not target_utc:
            return None
        return (target_utc.date() - utcnow().date()).days
    except Exception:
        return None
