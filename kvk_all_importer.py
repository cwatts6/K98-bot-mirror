# kvk_all_importer.py
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
from io import BytesIO
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

import pandas as pd
import pyodbc

from constants import (
    CREDENTIALS_FILE,
    DATABASE,
    KVK_SHEET_NAME,
    PASSWORD,
    SERVER,
    USERNAME,
)
from gsheet_module import run_kvk_proc_exports_with_alerts
from utils import ensure_aware_utc

COLUMN_ALIASES = {
    # canonical -> acceptable variants (case/space/underscore insensitive)
    "first_updateUTC": [
        "first_updateutc",
        "first_update",
        "first update",
        "firstupdated",
        "first_updated",
    ],
    "last_updateUTC": [
        "last_updateutc",
        "last_update",
        "last update",
        "lastupdated",
        "last_updated",
    ],
    "kills_iv_diff": ["kills_iv_diff", "kills iv diff", "t4_kills", "t4 kills", "t4"],
    "kills_v_diff": ["kills_v_diff", "kills v diff", "t5_kills", "t5 kills", "t5"],
    "max_units_healed_diff": [
        "max_units_healed_diff",
        "max units healed diff",
        "healed_units_diff",
        "healed units",
    ],
    "dead_diff": ["dead_diff", "deads", "dead", "deads_diff"],
    "points_difference": [
        "points_difference",
        "kill_points_diff",
        "kill points difference",
        "kp_diff",
    ],
}

# 1) Define the exact stage order ONCE (top of file, near STAGE_INSERT_SQL)
STAGE_COL_ORDER = [
    "governor_id",
    "name",
    "kingdom",
    "campid",
    "min_points",
    "max_points",
    "points_difference",
    "min_power",
    "max_power",
    "power_difference",
    "first_updateUTC",
    "last_updateUTC",
    "latest_power",
    "kill_points_diff",
    "power_diff",
    "dead_diff",
    "troop_power_diff",
    "max_units_healed_diff",
    "healed_troops",
    "kills_iv_diff",
    "kills_v_diff",
    "subscription_level",
]


def _apply_aliases(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    # Trim and build lookup (lower, no spaces/underscores)
    def norm(s: str) -> str:
        return "".join(str(s).strip().lower().replace("_", " ").split())

    lookup = {norm(c): c for c in df.columns}
    renames = {}
    for canonical, variants in COLUMN_ALIASES.items():
        if canonical in df.columns:
            continue
        for v in variants:
            key = norm(v)
            if key in lookup:
                renames[lookup[key]] = canonical
                break
    if renames:
        df = df.rename(columns=renames)
        try:
            logger.info("[KVK] Header aliases applied: %s", renames)
        except Exception:
            pass
    return df


def _get_negatives_count(cn, kvk_no: int, scan_id: int) -> int:
    with cn.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)
            FROM KVK.KVK_Ingest_Negatives
            WHERE KVK_NO = ? AND ScanID = ?
        """,
            (kvk_no, scan_id),
        )
        row = c.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


STAGE_INSERT_SQL = """
 INSERT INTO KVK.KVK_AllPlayers_Stage (
   IngestToken, governor_id, name, kingdom, campid,
   min_points, max_points, points_difference, min_power, max_power, power_difference,
   first_updateUTC, last_updateUTC,
   latest_power, kill_points_diff, power_diff, dead_diff, troop_power_diff,
   max_units_healed_diff, healed_troops, kills_iv_diff, kills_v_diff, subscription_level
 ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
 """

CALL_INGEST_SQL = """
 DECLARE @kvk INT, @scan INT, @rows INT;
 EXEC KVK.sp_KVK_AllPlayers_Ingest
   @IngestToken=?,
   @ScanTimestampUTC=?,
   @SourceFileName=?,
   @FileHash=?,
   @UploaderDiscordID=?,
   @OutKVK_NO=@kvk OUTPUT,
   @OutScanID=@scan OUTPUT,
   @OutRowCount=@rows OUTPUT;
 SELECT @kvk AS KVK_NO, @scan AS ScanID, @rows AS RowImported;
 """

RECOMPUTE_SQL = "EXEC KVK.sp_KVK_Recompute_Windows @KVK_NO=?;"
NEGATIVE_COUNT_SQL = "SELECT COUNT(*) FROM KVK.KVK_Ingest_Negatives WHERE KVK_NO=? AND ScanID=?;"

REQUIRED_MIN_COLS = [
    "governor_id",
    "kingdom",
    "max_power",  # needed to fix Baseline starting_power
    "points_difference",  # KP source-of-truth (will be aliased if file uses kill_points_diff)
    "kills_iv_diff",  # T4
    "kills_v_diff",  # T5
    "dead_diff",
    "max_units_healed_diff",
]


def _enable_fast_executemany(cur) -> bool:
    try:
        cur.fast_executemany = True
        return bool(getattr(cur, "fast_executemany", False))
    except Exception:
        return False


def _read_excel(content: bytes) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(content))
    df.columns = [str(c).strip() for c in df.columns]
    df = _apply_aliases(df)
    return df


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    # Validate minimal set
    missing = [c for c in REQUIRED_MIN_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    def as_int(x):
        try:
            return int(x)
        except Exception:
            return None

    def as_str(x):
        return None if pd.isna(x) else str(x)[:64]

    def as_dt(x):
        if pd.isna(x):
            return None
        try:
            # produce timezone-aware UTC datetimes in memory for consistent arithmetic
            if isinstance(x, pd.Timestamp):
                return ensure_aware_utc(x.to_pydatetime())
            return ensure_aware_utc(pd.to_datetime(x, errors="coerce").to_pydatetime())
        except Exception:
            return None

    out = pd.DataFrame()
    # Common fields
    out["governor_id"] = df["governor_id"].map(as_int)
    out["name"] = df["name"].map(as_str) if "name" in df.columns else None
    out["kingdom"] = df["kingdom"].map(as_int)
    out["campid"] = df.get("campid").map(as_int) if "campid" in df.columns else None

    # Numerics (optional if missing)
    for c in [
        "min_points",
        "max_points",
        "points_difference",
        "min_power",
        "max_power",
        "power_difference",
        "latest_power",
        "kill_points_diff",
        "power_diff",
        "dead_diff",
        "troop_power_diff",
        "max_units_healed_diff",
        "healed_troops",
        "kills_iv_diff",
        "kills_v_diff",
        "subscription_level",
    ]:
        if c in df.columns:
            out[c] = df[c].map(as_int)
        else:
            out[c] = None

    # Optional datetimes (support either first_updateUTC/last_updateUTC or absent)
    out["first_updateUTC"] = df.get("first_updateUTC", pd.Series([None] * len(df))).map(as_dt)
    out["last_updateUTC"] = df.get("last_updateUTC", pd.Series([None] * len(df))).map(as_dt)

    # Final sanity: at least governor_id + kingdom present
    if out["governor_id"].isna().any() or out["kingdom"].isna().any():
        raise ValueError("One or more rows missing governor_id or kingdom after coercion.")
    return out


# 2) Replace _rows_for_stage with an order-safe version
def _rows_for_stage(token: str, df: pd.DataFrame) -> list[tuple]:
    df2 = df.reindex(columns=STAGE_COL_ORDER)
    try:
        logger.info("[KVK] DF staged col order: %s", list(df2.columns))
    except Exception:
        pass

    # Convert pandas NA/NaT to None row-by-row (so pyodbc is happy)
    def _noneify(x):
        # also handle numpy types cleanly
        try:
            import numpy as np

            if isinstance(x, (np.floating,)) and (np.isnan(x)):
                return None
        except Exception:
            pass
        return None if pd.isna(x) else x

    rows = []
    for row in df2.itertuples(index=False, name=None):
        cleaned = tuple(_noneify(v) for v in row)
        rows.append((token, *cleaned))
    return rows


def ingest_kvk_all_excel(
    *,
    content: bytes,
    source_filename: str,
    uploader_id: int,
    scan_ts_utc: dt.datetime,
    server: str,
    database: str,
    username: str,
    password: str,
) -> dict[str, Any]:
    """
    Returns:
      {
        "kvk_no": int,
        "scan_id": int,
        "row_count": int,
        "negatives": int,
        "duration_s": float,
        # NEW
        "staged_rows": int,
        "ingest_ms": float,
        "recompute_ms": float,
        "proc_ms": float,          # alias of ingest_ms for backward compat
      }
    Raises on validation/SQL errors (bubbled to caller).
    """
    t0 = time.perf_counter()
    df_raw = _read_excel(content)
    df = _coerce(df_raw)

    if df.empty:
        raise ValueError("No rows found in uploaded file.")

    staged_rows = int(
        df.shape[0]
    )  # <= count AFTER coercion/cleanup; reliable even if executemany.rowcount varies

    con = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )
    try:
        cur = con.cursor()
        _enable_fast_executemany(cur)

        import uuid

        token = str(uuid.uuid4())

        # Stage rows
        cur.executemany(STAGE_INSERT_SQL, _rows_for_stage(token, df))
        con.commit()

        logger.info("[KVK] Final stage col order: %s", STAGE_COL_ORDER)
        logger.info("[KVK] DF col order now: %s", list(df.columns))

        # Hash
        file_hash = hashlib.sha256(content).digest()

        # Normalize scan_ts_utc to aware UTC internally, then strip tzinfo for the legacy proc
        scan_ts_utc = ensure_aware_utc(scan_ts_utc)
        scan_ts_naive = scan_ts_utc.replace(tzinfo=None)

        # Commit ingest (TIMED)
        cur = con.cursor()
        t_ingest0 = time.perf_counter()
        cur.execute(
            CALL_INGEST_SQL, (token, scan_ts_naive, source_filename, file_hash, int(uploader_id))
        )
        res = cur.fetchall()
        ingest_ms = (time.perf_counter() - t_ingest0) * 1000.0
        if not res:
            raise RuntimeError("Ingest returned no outputs.")
        kvk_no, scan_id, row_count = res[0]
        con.commit()

        # Recompute windows (current KVK only) — TIMED
        cur = con.cursor()
        t_recompute0 = time.perf_counter()
        cur.execute(RECOMPUTE_SQL, kvk_no)
        con.commit()
        recompute_ms = (time.perf_counter() - t_recompute0) * 1000.0

        # Negative corrections count for this scan
        cur = con.cursor()
        cur.execute(NEGATIVE_COUNT_SQL, (kvk_no, scan_id))
        negatives = int(cur.fetchone()[0])

        duration_s = round(time.perf_counter() - t0, 2)

        return {
            "kvk_no": int(kvk_no),
            "scan_id": int(scan_id),
            "row_count": int(row_count),
            "negatives": negatives,
            "duration_s": duration_s,
            # NEW health metrics
            "staged_rows": staged_rows,
            "ingest_ms": ingest_ms,
            "recompute_ms": recompute_ms,
            "proc_ms": ingest_ms,  # alias to keep existing callers happy
        }
    finally:
        try:
            con.close()
        except Exception:
            pass


async def _auto_export_kvk(kvk_no: int, notify_channel, bot_loop):
    try:
        # Run the (blocking) export in a worker thread
        ok = await asyncio.to_thread(
            run_kvk_proc_exports_with_alerts,
            SERVER,
            DATABASE,
            USERNAME,
            PASSWORD,
            kvk_no,
            KVK_SHEET_NAME,
            CREDENTIALS_FILE,
            notify_channel,
            bot_loop,
        )
        if ok and notify_channel:
            await notify_channel.send(f"📤 Export complete: **KVK {kvk_no} → {KVK_SHEET_NAME}**")
    except Exception as e:
        logger.exception("[KVK_EXPORT] Auto-export crashed")
        if notify_channel:
            await notify_channel.send(
                f"⚠️ Export failed for **KVK {kvk_no}**: `{type(e).__name__}: {e}`"
            )
