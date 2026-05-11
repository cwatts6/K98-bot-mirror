# stats_alerts/kvk_meta.py
import logging
from typing import Any

import numpy as np
import pandas as pd

from constants import (
    KVK_SHEET_ID,
)
from file_utils import fetch_one_dict, get_conn_with_retries
import gsheet_module as gm

# Fixed import: parse_mixed_dates exists as that name in formatters.py
from stats_alerts.formatters import parse_mixed_dates as _parse_mixed_dates
from utils import date_to_utc_start, utcnow

logger = logging.getLogger(__name__)


def get_latest_kvk_metadata_sql() -> dict[str, Any] | None:
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT TOP (1)
                       KVK_NO, KVK_NAME,
                       KVK_REGISTRATION_DATE, KVK_START_DATE, KVK_END_DATE,
                       MATCHMAKING_SCAN, KVK_END_SCAN, NEXT_KVK_NO,
                       MATCHMAKING_START_DATE, FIGHTING_START_DATE, PASS4_START_SCAN
                FROM dbo.KVK_Details
                WHERE KVK_NO IS NOT NULL
                ORDER BY KVK_NO DESC
            """)
            row = cur.fetchone()
            if not row:
                return None

            kvk_no = int(row.KVK_NO)
            kvk_name = row.KVK_NAME or "KVK"
            registration = row.KVK_REGISTRATION_DATE
            start_date = row.KVK_START_DATE
            end_date = row.KVK_END_DATE
            match_scan = int(row.MATCHMAKING_SCAN) if row.MATCHMAKING_SCAN is not None else None
            end_scan = int(row.KVK_END_SCAN) if row.KVK_END_SCAN is not None else None
            next_kvk_no = int(row.NEXT_KVK_NO) if row.NEXT_KVK_NO is not None else None
            mm_start = row.MATCHMAKING_START_DATE
            fight_start = row.FIGHTING_START_DATE
            pass4_scan = int(row.PASS4_START_SCAN) if row.PASS4_START_SCAN is not None else None

            if (
                (not isinstance(match_scan, int))
                or (not isinstance(end_scan, int))
                or match_scan <= 0
                or end_scan <= 0
                or end_scan < match_scan
            ):
                logger.warning(
                    "[KVK SQL META] Invalid scan window in KVK_Details: KVK=%s, MM=%r, END=%r",
                    kvk_no,
                    match_scan,
                    end_scan,
                )
                return {
                    "kvk_no": kvk_no,
                    "kvk_name": kvk_name,
                    "registration": registration,
                    "start_date": start_date,
                    "end_date": end_date,
                    "matchmaking_scan": None,
                    "kvk_end_scan": None,
                    "matchmaking_start_date": mm_start,
                    "fighting_start_date": fight_start,
                    "pass4_start_scan": pass4_scan,
                    "next_kvk_no": next_kvk_no,
                }

            return {
                "kvk_no": kvk_no,
                "kvk_name": kvk_name,
                "registration": registration,
                "start_date": start_date,
                "end_date": end_date,
                "matchmaking_scan": match_scan,
                "kvk_end_scan": end_scan,
                "matchmaking_start_date": mm_start,
                "fighting_start_date": fight_start,
                "pass4_start_scan": pass4_scan,
                "next_kvk_no": next_kvk_no,
            }
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


def get_kvk_window_from_sql() -> dict[str, int] | None:
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            # Prefer dbo.KVK_Details (latest)
            cur.execute("""
                SELECT TOP (1) KVK_NO, MATCHMAKING_SCAN, KVK_END_SCAN, PASS4_START_SCAN
                FROM dbo.KVK_Details
                WHERE KVK_NO IS NOT NULL
                ORDER BY KVK_NO DESC
                """)
            r = fetch_one_dict(cur)
            if r:
                # prefer explicit column names; otherwise fall back to first returned value
                def _val(dct, *names):
                    for n in names:
                        if n in dct:
                            return dct[n]
                    return next(iter(dct.values())) if dct else None

                kvk_no = int(_val(r, "KVK_NO"))
                mm_raw = _val(r, "MATCHMAKING_SCAN")
                ke_raw = _val(r, "KVK_END_SCAN")
                p4_raw = _val(r, "PASS4_START_SCAN")
                mm = int(mm_raw) if mm_raw is not None else None
                ke = int(ke_raw) if ke_raw is not None else None
                p4 = int(p4_raw) if p4_raw is not None else None
                if isinstance(mm, int) and isinstance(ke, int) and mm > 0 and ke > 0 and ke >= mm:
                    return {
                        "kvk_no": kvk_no,
                        "matchmaking_scan": mm,
                        "kvk_end_scan": ke,
                        "pass4_start_scan": p4,
                    }
                else:
                    logger.warning(
                        "[KVK SQL] KVK_Details has invalid window for KVK=%s (MM=%r, END=%r)",
                        kvk_no,
                        mm,
                        ke,
                    )

            # ProcConfig fallback
            cur.execute("""
                SELECT MAX(TRY_CAST(ConfigValue AS int)) AS CurrentKVK
                FROM dbo.ProcConfig
                WHERE ConfigKey = 'CURRENTKVK3'
                """)
            rowd = fetch_one_dict(cur)
            if not rowd or rowd.get("CurrentKVK") is None:
                logger.warning("[KVK SQL] No CURRENTKVK3 found in ProcConfig.")
                return None
            current_kvk = int(rowd["CurrentKVK"])

            cur.execute(
                """
                SELECT ConfigKey, ConfigValue
                FROM dbo.ProcConfig
                WHERE KVKVersion = ? AND ConfigKey IN ('MATCHMAKING_SCAN','KVK_END_SCAN')
                """,
                (current_kvk,),
            )
            kv_map = {x.ConfigKey: x.ConfigValue for x in cur.fetchall()}
            mm = kv_map.get("MATCHMAKING_SCAN")
            ke = kv_map.get("KVK_END_SCAN")
            try:
                match_scan = int(mm) if mm is not None else None
                end_scan = int(ke) if ke is not None else None
            except Exception:
                match_scan, end_scan = None, None

            if (
                not match_scan
                or not end_scan
                or match_scan <= 0
                or end_scan <= 0
                or end_scan < match_scan
            ):
                logger.warning(
                    "[KVK SQL] Invalid window. MATCHMAKING_SCAN=%r, KVK_END_SCAN=%r for KVK=%s",
                    mm,
                    ke,
                    current_kvk,
                )
                return None

            return {"kvk_no": current_kvk, "matchmaking_scan": match_scan, "kvk_end_scan": end_scan}
    except Exception:
        logger.exception("[KVK SQL] Failed to read KVK window")
        return None


def is_currently_kvk() -> bool:
    try:
        win = get_kvk_window_from_sql()
        if not win:
            return False
        match_scan = win["matchmaking_scan"]
        end_scan = win["kvk_end_scan"]

        conn = get_conn_with_retries()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(ScanOrder) FROM ROK_TRACKER.dbo.kingdomscandata4")
        r = fetch_one_dict(cursor)
        # extract first (and only) column value using next(iter(...))
        max_scan_order = next(iter(r.values())) if r else None
        conn.close()

        if max_scan_order is None:
            logger.warning("[KVK CHECK] No ScanOrder found \u2014 treating as off-season.")
            return False

        return match_scan <= max_scan_order <= end_scan
    except Exception:
        logger.exception("[KVK CHECK] Unexpected failure in KVK detection logic")
        return False


def is_kvk_fighting_open() -> bool:
    try:
        win = get_kvk_window_from_sql()
        if not win:
            return False
        end_scan = win.get("kvk_end_scan")
        pass4_scan = win.get("pass4_start_scan")
        if not isinstance(end_scan, int) or not isinstance(pass4_scan, int):
            return False
        if end_scan <= 0 or pass4_scan <= 0 or end_scan < pass4_scan:
            return False

        conn = get_conn_with_retries()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(ScanOrder) FROM ROK_TRACKER.dbo.kingdomscandata4")
        max_scan_order = cursor.fetchone()[0]
        conn.close()

        if max_scan_order is None:
            logger.warning("[KVK CHECK] No ScanOrder found \u2014 treating as not fighting.")
            return False

        return pass4_scan <= max_scan_order <= end_scan
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
