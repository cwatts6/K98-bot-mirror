# stats_alert_utils.py
import asyncio
from datetime import datetime, timedelta  # ensure timedelta & time are imported
import json
import logging
import os
from typing import Any

import discord
from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np
import pandas as pd
import pyodbc

from bot_config import OFFSEASON_STATS_CHANNEL_ID, STATS_ALERT_CHANNEL_ID
from constants import (
    CREDENTIALS_FILE,
    CUSTOM_AVATAR_URL,
    KVK_BANNER_MAP,
    KVK_SHEET_ID,
    OUR_KINGDOM,
    STATS_ALERT_LOG,
    STATS_SHEET_ID,
    TARGETS_SHEET_ID,
    TIMELINE_SHEET_ID,
)
from embed_offseason_stats import send_offseason_stats_embed_v2
from embed_utils import LocalTimeToggleView, fmt_short, format_event_time
from event_cache import get_all_upcoming_events

# file_utils now provides connection helper + atomic file helpers and lock
from file_utils import (
    acquire_lock,
    atomic_write_csv,
    atomic_write_json,
    get_conn_with_retries,
    read_csv_rows_safe,
    resolve_path,
)
from stats_helpers import fetch_all_dicts
from utils import date_to_utc_start, ensure_aware_utc, parse_isoformat_utc, utcnow

logger = logging.getLogger(__name__)

# --- Single-source absolute path for the CSV log ---
# Use resolve_path from file_utils (accepts env var or explicit path)
LOG_PATH = str(resolve_path(STATS_ALERT_LOG))
HEADER = ["date", "time_utc", "kind"]

# ---------------------------------------------------------------------------
# Send-limit helpers (per "kind") — atomic claim using a lock file
# ---------------------------------------------------------------------------

KIND_KVK = "kvk"
KIND_OFFSEASON_DAILY = "offseason_daily"
KIND_OFFSEASON_WEEKLY = "offseason_weekly"
KIND_PREKVK_DAILY = "prekvk_daily"

# Feature toggle: show Pre-KVK embed (before Pass 4) instead of Off-season
ENABLE_PREKVK = True


def _ensure_log_exists() -> None:
    """
    Ensure the CSV log exists and is in headered 3-col format.
    - If file missing -> write header.
    - If header missing or legacy 2-col rows present -> migrate to header + 3-cols.
    Uses file_utils.read_csv_rows_safe and atomic_write_csv for atomic writes.
    """
    try:
        rows = read_csv_rows_safe(LOG_PATH)
        if not rows:
            # create with header
            atomic_write_csv(LOG_PATH, HEADER, [])
            logger.info("[STATS_ALERT] created log at %s", LOG_PATH)
            return

        # Detect header
        first = rows[0] if rows else None
        has_header = False
        if first and len(first) >= 1 and isinstance(first[0], str) and first[0].lower() == "date":
            has_header = True

        data_rows = rows[1:] if has_header else rows

        upgraded = []
        changed = False
        for ln in data_rows:
            if not any(cell.strip() for cell in ln):
                continue
            parts = [p.strip() for p in ln if p is not None]
            if len(parts) == 2:
                date_str, time_str = parts
                upgraded.append([date_str, time_str, KIND_OFFSEASON_DAILY])
                changed = True
            elif len(parts) >= 3:
                upgraded.append(parts[:3])
            else:
                # corrupt -> skip
                changed = True
                continue

        # If header missing, or any changes detected, write header + upgraded
        if (not has_header) or changed:
            atomic_write_csv(LOG_PATH, HEADER, upgraded)
            logger.info("[STATS_ALERT] migrated log to headered 3-col format at %s", LOG_PATH)
    except Exception:
        logger.exception("[STATS_ALERT] failed to ensure/migrate stats alert log")


def _norm_event_type(t: str | None) -> str:
    raw = (t or "").strip().lower()
    return {
        "next ruins": "ruins",
        "ruins": "ruins",
        "next altar fight": "altars",
        "altar": "altars",
        "altars": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }.get(raw, raw)


def _to_aware_utc(dt):
    """Coerce a datetime to timezone-aware UTC (returns None if not a datetime)."""
    if not isinstance(dt, datetime):
        return None
    return ensure_aware_utc(dt)


def _abbr(n: int | float | None) -> str:
    # Use the shared formatter for consistency across embeds and charts
    if n is None:
        return "0"
    try:
        return fmt_short(n)
    except Exception:
        try:
            return str(int(n))
        except Exception:
            return "0"


def _fmt_dkp(v: Any, base_dp: int = 2, max_dp: int = 10) -> str:
    """Show DKP with 2dp normally; if that would be 0.00 for a non-zero value,
    increase precision until a non-zero decimal digit appears (up to max_dp)."""
    if v is None:
        return "0.00"
    try:
        val = float(v)
    except Exception:
        return "0.00"

    if val == 0.0:
        return "0.00"

    dp = base_dp
    while dp <= max_dp:
        s = f"{val:.{dp}f}"
        # if any decimal digit is non-zero, keep this precision
        if "." in s and any(ch != "0" for ch in s.split(".", 1)[1]):
            return s
        dp += 1

    # last resort: max precision trimmed nicely
    s = f"{val:.{max_dp}f}".rstrip("0").rstrip(".")
    return s if s else "0.00"


def _fmt_top(
    rows, name_key: str, val_key: str, extra_key: str | None = None, *, val_fmt=None, extra_fmt=None
) -> str:
    """Render 1–3 rows -> numbered list monospaced, with optional per-field formatters."""
    if not rows:
        return "—"
    if val_fmt is None:
        val_fmt = _abbr
    if extra_key and extra_fmt is None:
        extra_fmt = _abbr

    medals = ["🥇", "🥈", "🥉"]
    out = []
    for i, r in enumerate(rows[:3]):
        left = f"{medals[i]} {r[name_key]}"
        right = val_fmt(r.get(val_key))
        if extra_key:
            right += f" | {extra_fmt(r.get(extra_key))}"
        out.append(f"{left} — `{right}`")
    return "\n".join(out)


def _fmt_top_dkp(rows, name_key: str, dkp_key: str = "dkp") -> str:
    if not rows:
        return "—"
    medals = ["🥇", "🥈", "🥉"]
    out = []
    for i, r in enumerate(rows[:3]):
        try:
            val = float(r.get(dkp_key, 0))
        except Exception:
            val = 0.0
        out.append(f"{medals[i]} {r[name_key]} — `{val:.2f}`")
    return "\n".join(out)


def _normalize_row(row_list):
    parts = [p.strip() for p in row_list if p is not None]
    if len(parts) == 2:
        d, t = parts
        k = KIND_OFFSEASON_DAILY
    elif len(parts) >= 3:
        d, t, k = parts[0], parts[1], parts[2]
    else:
        return None
    # Basic validation
    if len(d) != 10 or d[4] != "-" or d[7] != "-":  # crude ISO date check
        return None
    return {"date": d, "time_utc": t, "kind": k}


def _iter_log_rows():
    """
    Schema-agnostic iterator yielding dicts with keys: date, time_utc, kind.
    Handles header/no-header and 2-col legacy rows.
    """
    _ensure_log_exists()
    try:
        rows = read_csv_rows_safe(LOG_PATH)
        if not rows:
            return
        first = rows[0]
        # Skip header if present
        idx = 0
        if first and isinstance(first, list) and first and first[0].lower() == "date":
            idx = 1
        # process rows from idx onwards
        for row in rows[idx:]:
            if not row:
                continue
            nr = _normalize_row(row)
            if nr:
                yield nr
    except Exception:
        logger.exception("[STATS_ALERT] Failed iterating log rows")
        return


def _read_counts_for(kind: str, date_iso: str) -> int:
    c = 0
    for row in _iter_log_rows():
        if not row:
            continue
        if row["date"] == date_iso and row["kind"] == kind:
            c += 1
    return c


STATE_PATH = f"{LOG_PATH}.state.json"


def _load_state() -> dict:
    try:
        if not os.path.exists(STATE_PATH):
            return {}
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("[STATS_ALERT] Failed to load state")
        return {}


def _save_state(d: dict) -> None:
    try:
        atomic_write_json(STATE_PATH, d)
    except Exception:
        logger.exception("[STATS_ALERT] Failed to persist state")


def _fetch_all_dicts(cur) -> list[dict]:
    # Delegates to shared helper (consistent cursor -> dict behaviour)
    return fetch_all_dicts(cur)


def _load_prekvk_top3(kvk_no: int, sql_conn_str: str) -> dict[str, list[dict]]:
    """
    Returns:
      {
        'overall': [{'Name': str, 'Points': int}, ... up to 3],
        'p1':      [{'Name': str, 'Points': int}, ...],
        'p2':      [{'Name': str, 'Points': int}, ...],
        'p3':      [{'Name': str, 'Points': int}, ...],
      }
    Uses TVFs: fn_PreKvkLatestOverall, fn_PreKvkPhaseDelta
    """
    out = {"overall": [], "p1": [], "p2": [], "p3": []}
    try:
        # allow external connection string if provided (keeps previous behaviour)
        if sql_conn_str:
            conn = pyodbc.connect(sql_conn_str)
        else:
            conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()

            # Overall (latest snapshot)
            cur.execute(
                """
                SELECT TOP 3 Name, Points
                FROM (
                    SELECT GovernorName AS Name, Points
                    FROM dbo.fn_PreKvkLatestOverall(?)
                ) x
                ORDER BY Points DESC, Name;
            """,
                (kvk_no,),
            )
            out["overall"] = _fetch_all_dicts(cur)

            # Phase helper
            def _phase_top3(phase: int) -> list[dict]:
                cur.execute(
                    """
                    SELECT TOP 3 Name, Points
                    FROM (
                        SELECT COALESCE(n.GovernorName, CONVERT(varchar(20), p.GovernorID)) AS Name,
                               p.DeltaPoints AS Points
                        FROM dbo.fn_PreKvkPhaseDelta(?, ?) p
                        LEFT JOIN dbo.fn_PreKvkLatestOverall(?) n
                          ON n.GovernorID = p.GovernorID
                    ) x
                    ORDER BY Points DESC, Name;
                """,
                    (kvk_no, phase, kvk_no),
                )
                return _fetch_all_dicts(cur)

            out["p1"] = _phase_top3(1)
            out["p2"] = _phase_top3(2)
            out["p3"] = _phase_top3(3)

    except Exception:
        logger.exception("[PREKVK] Failed to load Pre-KVK Top-3")
    return out


# --- Honour helpers ---------------------------------------------------------

# get_conn_with_retries = _conn


def get_latest_honor_top(n: int = 3) -> list[dict]:
    """
    Returns latest overall honour Top-N for the most recent scan of the latest KVK,
    or [] if none or top==0.
    """
    sql = """
    ;WITH latest_kvk AS (
        SELECT MAX(KVK_NO) AS KVK_NO
        FROM dbo.KVK_Honor_Scan
    ),
    last_scan AS (
        SELECT s.KVK_NO, MAX(s.ScanID) AS ScanID
        FROM dbo.KVK_Honor_Scan s
        JOIN latest_kvk k ON k.KVK_NO = s.KVK_NO
        GROUP BY s.KVK_NO
    )
    SELECT TOP (?) a.GovernorName, a.GovernorID, a.HonorPoints
    FROM dbo.KVK_Honor_AllPlayers_Raw a
    JOIN last_scan l ON l.KVK_NO = a.KVK_NO AND l.ScanID = a.ScanID
    ORDER BY a.HonorPoints DESC, a.GovernorID ASC;
    """
    try:
        with get_conn_with_retries() as cn:
            cur = cn.cursor()
            cur.execute(sql, n)
            rows = [
                {"GovernorName": r[0], "GovernorID": int(r[1]), "HonorPoints": int(r[2])}
                for r in cur.fetchall()
            ]
        if not rows or rows[0]["HonorPoints"] <= 0:
            return []
        return rows
    except Exception:
        logger.exception("[HONOUR] Failed loading latest Top-%s", n)
        return []


def purge_latest_honor_scan() -> int:
    """
    Deletes the most recent honour scan (header + rows) for the latest KVK.
    Returns number of rows deleted from KVK_Honor_AllPlayers_Raw.
    Useful after test uploads.
    """
    try:
        with get_conn_with_retries() as cn:
            cur = cn.cursor()
            # find latest kvk + scan
            cur.execute("SELECT MAX(KVK_NO) FROM dbo.KVK_Honor_Scan")
            kvk = cur.fetchone()[0]
            if kvk is None:
                return 0
            cur.execute("SELECT MAX(ScanID) FROM dbo.KVK_Honor_Scan WHERE KVK_NO=?", kvk)
            sid = cur.fetchone()[0]
            if sid is None:
                return 0
            # delete children then header
            cur.execute(
                "SELECT COUNT(*) FROM dbo.KVK_Honor_AllPlayers_Raw WHERE KVK_NO=? AND ScanID=?",
                kvk,
                sid,
            )
            cnt = int(cur.fetchone()[0] or 0)
            cur.execute(
                "DELETE FROM dbo.KVK_Honor_AllPlayers_Raw WHERE KVK_NO=? AND ScanID=?", kvk, sid
            )
            cur.execute("DELETE FROM dbo.KVK_Honor_Scan WHERE KVK_NO=? AND ScanID=?", kvk, sid)
            cn.commit()
            logger.info("[HONOUR] Purged latest scan KVK=%s ScanID=%s (rows=%s)", kvk, sid, cnt)
            return cnt
    except Exception:
        logger.exception("[HONOUR] Purge latest scan failed")
        return 0


def _fmt_honor(rows: list[dict]) -> str:
    if not rows:
        return "—"
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, r in enumerate(rows[:3]):
        name = r.get("GovernorName") or "Unknown"
        pts = int(r.get("HonorPoints") or 0)
        lines.append(f"{medals[i]} {name} — `{pts:,}`")
    return "\n".join(lines)


def _today_iso() -> str:
    return utcnow().date().isoformat()


def _lock_path() -> str:
    return f"{LOG_PATH}.lock"


def _claim_send(kind: str, *, max_per_day: int = 1) -> bool:
    """
    Claim a send slot by appending a row to the CSV log.
    Uses file_utils.acquire_lock to get cross-process exclusive access.
    Writes atomically via atomic_write_csv after reading existing rows.
    """
    _ensure_log_exists()
    today = _today_iso()
    lock_path = _lock_path()
    try:
        with acquire_lock(lock_path, timeout=5):
            sends_today = _read_counts_for(kind, today)  # <- use robust reader
            if sends_today >= max_per_day:
                logger.info(
                    "[SEND GUARD] '%s' already sent %d/%d for %s — skipping.",
                    kind,
                    sends_today,
                    max_per_day,
                    today,
                )
                return False

            # Read existing rows, preserve header if present
            rows = read_csv_rows_safe(LOG_PATH)
            header = []
            data_rows = rows
            if rows and rows[0] and rows[0][0].lower() == "date":
                header = rows[0]
                data_rows = rows[1:]

            time_str = utcnow().strftime("%H:%M:%S")
            data_rows.append([today, time_str, kind])

            # Write header + data rows atomically
            if not header:
                header = HEADER
            atomic_write_csv(LOG_PATH, header, data_rows)

            logger.info(
                "[SEND GUARD] Claimed slot %d/%d for '%s' on %s (log=%s).",
                sends_today + 1,
                max_per_day,
                kind,
                today,
                LOG_PATH,
            )
            return True
    except TimeoutError:
        logger.exception("[SEND GUARD] Failed to acquire lock to claim send")
        return False
    except Exception:
        logger.exception("[SEND GUARD] Failed to claim send")
        return False


def _last_send_dt_utc(kind: str) -> datetime | None:
    _ensure_log_exists()
    last = None
    for row in _iter_log_rows():
        if not row or row["kind"] != kind:
            continue
        try:
            # Parse using robust parser -> aware UTC
            dt = parse_isoformat_utc(f"{row['date']} {row['time_utc']}")
            if (last is None) or (dt > last):
                last = dt
        except Exception:
            continue
    return last


def _cooldown_ok(kind: str, hours: int) -> bool:
    last = _last_send_dt_utc(kind)
    if not last:
        return True
    now = utcnow()
    delta_h = (now - last).total_seconds() / 3600.0
    if delta_h < hours:
        logger.info(
            "[SEND GUARD] Cooldown active for '%s': %.1fh elapsed (< %dh).", kind, delta_h, hours
        )
        return False
    return True


def _sent_today(kind: str) -> bool:
    today = _today_iso()
    return _read_counts_for(kind, today) > 0


def _sent_today_any(kinds: list[str]) -> bool:
    today = _today_iso()
    kinds_set = set(kinds)
    for row in _iter_log_rows():
        if not row:
            continue
        if row["date"] == today and row["kind"] in kinds_set:
            return True
    return False


# ---------------------------------------------------------------------------
# Robust date parsing (Sheets fallback)
# ---------------------------------------------------------------------------


def _parse_mixed_dates(s: pd.Series) -> pd.Series:
    """Warning-free parsing for mixed inputs (ISO, UK dd/mm/yyyy, Excel serials)."""
    s = s.astype("object").map(lambda x: x.strip() if isinstance(x, str) else x)
    s = s.replace({"": np.nan, "NULL": np.nan, "NaN": np.nan})

    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

    # Excel serials
    is_num = s.map(lambda x: isinstance(x, (int, float)) and not pd.isna(x))
    if is_num.any():
        serials = s[is_num].astype(float)
        out.loc[is_num] = pd.to_datetime("1899-12-30") + pd.to_timedelta(serials, unit="D")

    # Strings
    str_mask = s.map(lambda x: isinstance(x, str))
    if str_mask.any():
        s_str = s[str_mask]
        supports_mixed = tuple(map(int, pd.__version__.split(".")[:2])) >= (2, 0)
        if supports_mixed:
            parsed = pd.to_datetime(s_str, format="mixed", errors="coerce", utc=False)
        else:
            parsed = pd.Series(pd.NaT, index=s_str.index, dtype="datetime64[ns]")
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
                mask = parsed.isna()
                if not mask.any():
                    break
                parsed.loc[mask] = pd.to_datetime(s_str[mask], format=fmt, errors="coerce")
            still = parsed.isna()
            if still.any():
                parsed.loc[still] = pd.to_datetime(s_str[still], errors="coerce", dayfirst=True)
        out.loc[str_mask] = parsed

    return out  # keep as datetime; format on output as needed


# ---------------------------------------------------------------------------
# KVK metadata (SQL for display + logic; Sheets is cosmetic fallback)
# ---------------------------------------------------------------------------


def get_latest_kvk_metadata_sql() -> dict[str, Any] | None:
    """
    Preferred source for KVK display metadata + window.
    Reads the latest KVK (highest KVK_NO) from dbo.KVK_Details.
    Enforces valid window (>0, end >= start). Returns dict or None.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TOP (1)
                       KVK_NO, KVK_NAME,
                       KVK_REGISTRATION_DATE, KVK_START_DATE, KVK_END_DATE,
                       MATCHMAKING_SCAN, KVK_END_SCAN, NEXT_KVK_NO,
                       MATCHMAKING_START_DATE, FIGHTING_START_DATE, PASS4_START_SCAN
                FROM dbo.KVK_Details
                WHERE KVK_NO IS NOT NULL
                ORDER BY KVK_NO DESC
            """
            )
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
            mm_start = row.MATCHMAKING_START_DATE  # DATE or None
            fight_start = row.FIGHTING_START_DATE  # DATE or None
            pass4_scan = int(row.PASS4_START_SCAN) if row.PASS4_START_SCAN is not None else None

            # Enforce early validity for window (still return display even if invalid)
            if (
                (not isinstance(match_scan, int))
                or (not isinstance(end_scan, int))
                or match_scan <= 0
                or end_scan <= 0
                or end_scan < match_scan
            ):
                logger.warning(
                    "[KVK SQL META] Invalid scan window in KVK_Details: " "KVK=%s, MM=%r, END=%r",
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
    """
    Sheets fallback for *display only* (name/dates/banner). Not used for season logic.
    """
    try:
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        service = build("sheets", "v4", credentials=creds)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=KVK_SHEET_ID, range="KVK_Details!A1:Z")
            .execute()
        )

        values = result.get("values", [])
        headers = values[0]
        df = pd.DataFrame(values[1:], columns=headers)

        df["KVK_NO"] = pd.to_numeric(df["KVK_NO"], errors="coerce")
        df["KVK_START_DATE"] = _parse_mixed_dates(df["KVK_START_DATE"])
        df["KVK_END_DATE"] = _parse_mixed_dates(df["KVK_END_DATE"])
        df["MATCHMAKING_SCAN"] = pd.to_numeric(df.get("MATCHMAKING_SCAN"), errors="coerce")
        df["KVK_END_SCAN"] = pd.to_numeric(df.get("KVK_END_SCAN"), errors="coerce")

        # Treat non-positive as invalid
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
    """
    Pull the authoritative KVK scan window from SQL, preferring dbo.KVK_Details.
    Fallback to dbo.ProcConfig if needed.
    - Enforces: both positive integers and end >= start.
    Returns: {"kvk_no": int, "matchmaking_scan": int, "kvk_end_scan": int} or None if not valid.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()

            # 1) Prefer dbo.KVK_Details (latest KVK_NO)
            cur.execute(
                """
                SELECT TOP (1) KVK_NO, MATCHMAKING_SCAN, KVK_END_SCAN, PASS4_START_SCAN
                FROM dbo.KVK_Details
                WHERE KVK_NO IS NOT NULL
                ORDER BY KVK_NO DESC
            """
            )
            r = cur.fetchone()
            if r:
                kvk_no = int(r.KVK_NO)
                mm = int(r.MATCHMAKING_SCAN) if r.MATCHMAKING_SCAN is not None else None
                ke = int(r.KVK_END_SCAN) if r.KVK_END_SCAN is not None else None
                p4 = int(r.PASS4_START_SCAN) if r.PASS4_START_SCAN is not None else None
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

            # 2) Fallback: dbo.ProcConfig (CURRENTKVK3 → window keys)
            cur.execute(
                """
                SELECT MAX(TRY_CAST(ConfigValue AS int)) AS CurrentKVK
                FROM dbo.ProcConfig
                WHERE ConfigKey = 'CURRENTKVK3'
            """
            )
            row = cur.fetchone()
            if not row or row.CurrentKVK is None:
                logger.warning("[KVK SQL] No CURRENTKVK3 found in ProcConfig.")
                return None
            current_kvk = int(row.CurrentKVK)

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

            return {
                "kvk_no": current_kvk,
                "matchmaking_scan": match_scan,
                "kvk_end_scan": end_scan,
                # No PASS4 in ProcConfig fallback (optional to add later)
            }
    except Exception:
        logger.exception("[KVK SQL] Failed to read KVK window")
        return None


def is_currently_kvk(
    _server: str | None = None,
    _database: str | None = None,
    _username: str | None = None,
    _password: str | None = None,
) -> bool:
    try:
        # Authoritative window from SQL (KVK_Details preferred, ProcConfig fallback)
        win = get_kvk_window_from_sql()
        if not win:
            return False
        match_scan = win["matchmaking_scan"]
        end_scan = win["kvk_end_scan"]

        conn = get_conn_with_retries()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(ScanOrder) FROM ROK_TRACKER.dbo.kingdomscandata4")
        max_scan_order = cursor.fetchone()[0]
        conn.close()

        if max_scan_order is None:
            logger.warning("[KVK CHECK] No ScanOrder found — treating as off-season.")
            return False

        return match_scan <= max_scan_order <= end_scan

    except Exception:
        logger.exception("[KVK CHECK] Unexpected failure in KVK detection logic")
        return False


def is_kvk_fighting_open() -> bool:
    """
    True only once Pass 4 has opened (PASS4_START_SCAN reached) and before KVK_END_SCAN.
    Uses dbo.KVK_Details; if PASS4_START_SCAN is null/invalid, returns False.
    """
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
            logger.warning("[KVK CHECK] No ScanOrder found — treating as not fighting.")
            return False

        return pass4_scan <= max_scan_order <= end_scan
    except Exception:
        logger.exception("[KVK CHECK] Unexpected failure in Pass4 gate")
        return False


def _days_until(date_obj) -> int | None:
    """date_obj: Python date or datetime. Returns integer days until (UTC), or None."""
    if not date_obj:
        return None
    try:
        # Convert to an aware UTC datetime at midnight for accuracy, then compare dates in UTC
        target_utc = date_to_utc_start(date_obj)
        if not target_utc:
            return None
        return (target_utc.date() - utcnow().date()).days
    except Exception:
        return None


async def _send_prekvk_embed(
    bot,
    channel: discord.abc.Messageable,
    timestamp: str,
    sql_conn_str: str,
    *,
    is_test: bool,
):
    """
    Lightweight, no-stats embed shown between matchmaking and Pass 4.
    Adds a timeline, countdowns, and 'what's next' notes.
    Returns: "edited" (silent edit) or "sent" (new message).
    """
    meta_sql = await asyncio.to_thread(get_latest_kvk_metadata_sql)
    kvk_no = meta_sql["kvk_no"] if meta_sql else "?"
    kvk_name = meta_sql["kvk_name"] if meta_sql else "KVK"
    reg_dt = meta_sql.get("registration") if meta_sql else None
    start_dt = meta_sql.get("start_date") if meta_sql else None
    end_dt = meta_sql.get("end_date") if meta_sql else None
    mm_start = meta_sql.get("matchmaking_start_date") if meta_sql else None
    fight_start = meta_sql.get("fighting_start_date") if meta_sql else None
    pass4_scan = meta_sql.get("pass4_start_scan") if meta_sql else None

    # Date range (best-effort)
    try:
        kvk_date_range = (
            f"{start_dt.strftime('%d %b')} – {end_dt.strftime('%d %b')}"
            if start_dt and end_dt
            else ""
        )
    except Exception:
        kvk_date_range = ""

    # Countdowns (days)
    _d_mm = _days_until(mm_start)
    d_fight = _days_until(fight_start)

    def _fmt_dd(n):
        if n is None:
            return "—"
        if n < 0:
            return f"{abs(n)}d ago"
        if n == 0:
            return "today"
        return f"in {n}d"

    # Build embed
    embed = discord.Embed(
        title=f"🧭 Pre-KVK — {kvk_name} (KVK {kvk_no})",
        description=(f"**{kvk_date_range}**\n" if kvk_date_range else "")
        + f"Prep update **{timestamp}**\n\n"
        "Fighting hasn’t started yet. Here’s what’s ahead 👇",
        color=discord.Color.blurple(),
    )
    thumb = (CUSTOM_AVATAR_URL or "").strip()
    if thumb and thumb.lower().startswith(("http://", "https://")):
        try:
            embed.set_thumbnail(url=thumb)
        except Exception:
            pass

    banner_url = KVK_BANNER_MAP.get((kvk_name or "KVK").lower(), None)
    if banner_url:
        embed.set_image(url=banner_url)

    def _fmt_date(d):
        try:
            return d.strftime("%d %b %Y") if d else "TBD"
        except Exception:
            return "TBD"

    tl_lines = []
    if reg_dt:
        tl_lines.append(f"📜 Registration: **{_fmt_date(reg_dt)}**")
    if start_dt:
        tl_lines.append(f"🗺 **KVK Map opens** : **{_fmt_date(start_dt)}**")
    if fight_start:
        try:
            tl_lines.append(f"⚔️ Fighting starts: **{fight_start:%d %b %Y}** ({_fmt_dd(d_fight)})")
        except Exception:
            tl_lines.append(f"⚔️ Fighting starts: **{_fmt_date(fight_start)}** ({_fmt_dd(d_fight)})")
    embed.add_field(
        name="Season timeline", value=("\n".join(tl_lines) if tl_lines else "—"), inline=False
    )

    # Pre-KVK Top-3 (overall + phases)
    try:
        tops = await asyncio.to_thread(
            _load_prekvk_top3, int(kvk_no) if str(kvk_no).isdigit() else 13, sql_conn_str
        )
    except Exception:
        tops = {"overall": [], "p1": [], "p2": [], "p3": []}

    def _fmt_top_simple(rows: list[dict], units: str = "pts") -> str:
        if not rows:
            return "—"
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, r in enumerate(rows[:3]):
            name = r.get("Name") or "Unknown"
            pts = int(r.get("Points") or 0)
            lines.append(f"{medals[i]} {name} — `{pts:,} {units}`")
        return "\n".join(lines)

    embed.add_field(
        name="🏆 Overall Pre-KVK Rankings:",
        value=_fmt_top_simple(tops["overall"], "pts"),
        inline=False,
    )
    embed.add_field(
        name="🗡️ Phase 1 — Marauders", value=_fmt_top_simple(tops["p1"], "pts"), inline=True
    )
    embed.add_field(
        name="🏗️ Phase 2 — Training", value=_fmt_top_simple(tops["p2"], "pts"), inline=True
    )
    embed.add_field(
        name="🏕️ Phase 3 — Encampments", value=_fmt_top_simple(tops["p3"], "pts"), inline=True
    )

    # Honor Rankings section
    # Show placeholder only if no honor data yet. If we have data, show Top 3 and skip the placeholder.
    try:
        honor_top = await asyncio.to_thread(get_latest_honor_top, 3)
    except Exception:
        logger.exception("[PREKVK] Honor block failed")
        honor_top = []

    if honor_top:
        # We have honor data — show Top 3 only.
        embed.add_field(
            name="🏅 Honor Rankings (Top 3):", value=_fmt_honor(honor_top), inline=False
        )
    else:
        # No honor data yet — show the placeholder line (only if PASS4 scan is defined).
        next_lines = []
        if isinstance(pass4_scan, int):
            next_lines.append("📌 Honor Rankings will appear here as soon as available.")
        embed.add_field(
            name="🏅 Honor Rankings (Top 3):",
            value="\n".join(next_lines) if next_lines else "—",
            inline=False,
        )

    # Upcoming week (chronicle / major only)
    try:
        upcoming = get_all_upcoming_events() or []
    except Exception:
        upcoming = []

    now_utc = utcnow()
    week_ahead = now_utc + timedelta(days=7)

    _filtered = []
    for e in upcoming:
        st = _to_aware_utc(e.get("start_time"))
        if not st:
            continue
        if (now_utc - timedelta(hours=1)) <= st <= week_ahead:
            if _norm_event_type(e.get("type")) in ("chronicle", "major"):
                _filtered.append({**e, "start_time": st})
    week_events = sorted(_filtered, key=lambda ev: ev["start_time"])

    def _event_line(e):
        name = (e.get("name") or e.get("title") or "Event").strip()
        ts = int(e["start_time"].timestamp())
        return f"• **{name}** — starts <t:{ts}:R>\n  {format_event_time(e['start_time'])}"

    if week_events:
        upcoming_text = "\n".join(_event_line(e) for e in week_events[:12])
        embed.add_field(name="🗓️ Next 7 days:", value=upcoming_text, inline=False)

    embed.add_field(
        name="📎 Get ready",
        value="Use **/mykvktargets** (targets are now LIVE) • **/subscribe** receive event reminders",
        inline=False,
    )

    timeline_link = (
        f"https://docs.google.com/spreadsheets/d/{TIMELINE_SHEET_ID}" if TIMELINE_SHEET_ID else None
    )
    targets_link = (
        f"https://docs.google.com/spreadsheets/d/{TARGETS_SHEET_ID}" if TARGETS_SHEET_ID else None
    )
    link_parts = []
    if timeline_link:
        link_parts.append(f"[Timeline]({timeline_link})")
    if targets_link:
        link_parts.append(f"[Targets]({targets_link})")
    if link_parts:
        embed.add_field(name="🔗 Links", value=" • ".join(link_parts), inline=False)

    embed.set_footer(text="KD98 Discord Bot")

    view = (
        LocalTimeToggleView(week_events, prefix="prekvk_week", timeout=None)
        if week_events
        else None
    )

    # Load state and decide edit vs send
    state = _load_state()
    msg_id = state.get("prekvk_msg_id")
    message = None
    # 🛠 Define today's UTC date (was previously used but not defined)
    today_utc = utcnow().date()
    if msg_id:
        try:
            message = await channel.fetch_message(int(msg_id))
            # If saved message is from a previous UTC day, force a fresh send
            if message and getattr(message, "created_at", None):
                try:
                    msg_created = ensure_aware_utc(message.created_at)
                except Exception:
                    msg_created = None
                if msg_created is None or msg_created.date() != today_utc:
                    message = None
                    # 🔧 Clear stale id (new day)
                    state.pop("prekvk_msg_id", None)
                    _save_state(state)
        except Exception:
            # Couldn’t fetch (deleted/perm changes/etc.) → treat as fresh send
            message = None
            # 🔧 Clear bad id (no such message anymore)
            if state.pop("prekvk_msg_id", None) is not None:
                _save_state(state)

    # Try silent edit
    if message:
        try:
            await message.edit(embed=embed, view=view)
            logger.info(
                "[PREKVK] Edited existing message id=%s in channel=%s",
                getattr(message, "id", "?"),
                getattr(channel, "id", "?"),
            )
            return "edited"
        except Exception:
            logger.exception("[PREKVK] Edit failed; will send a fresh message.")
            # 🔧 Clear id on failed edit, so next run won’t keep trying
            if state.pop("prekvk_msg_id", None) is not None:
                _save_state(state)

    # Fresh send; ping only if we've never stored a message id before
    first_send_ping = not bool(state.get("prekvk_msg_id"))

    sent = await channel.send(
        embed=embed,
        content="@everyone" if first_send_ping else None,
        view=view,
        allowed_mentions=discord.AllowedMentions(everyone=first_send_ping),
    )
    logger.info(
        "[PREKVK] Sent new message id=%s in channel=%s",
        getattr(sent, "id", "?"),
        getattr(channel, "id", "?"),
    )

    # Remember id for future silent edits
    try:
        state["prekvk_msg_id"] = sent.id
        _save_state(state)
    except Exception:
        logger.exception("[PREKVK] Failed to persist message id")

    return "sent"


# ---------------------------------------------------------------------------
# Public entry — choose which embed to send (KVK vs Off-season)
# ---------------------------------------------------------------------------


async def send_stats_update_embed(
    bot,
    timestamp: str,
    is_kvk: bool,
    sql_conn_str: str,
    is_test: bool = False,
):
    """
    When is_kvk = True  -> post the classic KVK embed to STATS_ALERT_CHANNEL_ID (≤3/day).
    When is_kvk = False -> post the off-season daily dashboard to OFFSEASON_STATS_CHANNEL_ID (1/day + 12h cooldown),
                           plus an optional weekly Monday dashboard (1/Monday, no ping).
    """
    # Guard: KVK embed allowed only once Pass 4 has actually started.
    # If KVK but not fighting yet, optionally show Pre-KVK instead of Off-season.
    try:
        fighting_open = await asyncio.to_thread(is_kvk_fighting_open)
    except Exception:
        fighting_open = False

    effective_is_kvk = bool(is_kvk and fighting_open)

    # If fighting is open now, forget any remembered Pre-KVK message id
    if effective_is_kvk:
        try:
            state = _load_state()
            if state.pop("prekvk_msg_id", None) is not None:
                _save_state(state)
                logger.info("[PREKVK] Fighting opened — cleared stored prekvk_msg_id.")
        except Exception:
            logger.exception("[PREKVK] Failed to clear prekvk_msg_id on fighting-open.")

    # Choose channel based on final path
    if effective_is_kvk:
        channel_id = STATS_ALERT_CHANNEL_ID
    elif is_kvk and ENABLE_PREKVK:
        channel_id = STATS_ALERT_CHANNEL_ID  # keep KVK alerts in same place
    else:
        channel_id = OFFSEASON_STATS_CHANNEL_ID
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.warning("⚠️ Could not find channel id %s.", channel_id)
        return

    if effective_is_kvk:
        # Mutual exclusivity — if any off-season (daily/weekly) already posted today, skip KVK.
        if not is_test and _sent_today_any([KIND_OFFSEASON_DAILY, KIND_OFFSEASON_WEEKLY]):
            logger.info("[STATS EMBED] Off-season already posted today; skipping KVK.")
            return

        # Respect daily cap (no log yet)
        if not is_test and _read_counts_for(KIND_KVK, _today_iso()) >= 3:
            logger.info("[STATS EMBED] KVK daily limit reached, skipping broadcast.")
            return

        try:
            await _send_kvk_embed(bot, channel, timestamp, sql_conn_str, is_test=is_test)
            # Log AFTER success
            if not is_test:
                _claim_send(KIND_KVK, max_per_day=3)
        except Exception:
            logger.exception("[STATS EMBED] KVK send failed.")
        return

    # --- Pre-KVK path (KVK but before Pass 4) ---
    if is_kvk and ENABLE_PREKVK:
        # Mutual exclusivity — if we already posted Off-season (daily/weekly) today, skip Pre-KVK.
        if not is_test and _sent_today_any([KIND_OFFSEASON_DAILY, KIND_OFFSEASON_WEEKLY]):
            logger.info("[STATS EMBED] Off-season already posted today; skipping Pre-KVK.")
            return

        # If we already have a message id, do a SILENT EDIT regardless of daily limit
        state = _load_state()
        if state.get("prekvk_msg_id"):
            try:
                action = await _send_prekvk_embed(
                    bot, channel, timestamp, sql_conn_str, is_test=is_test
                )
                # 🚫 Do NOT write to CSV on silent edits
                if action == "sent" and not is_test and not _sent_today(KIND_PREKVK_DAILY):
                    _claim_send(KIND_PREKVK_DAILY, max_per_day=1)
                return
            except Exception:
                # If the edit failed (message deleted / perms / etc.), fall back to a fresh send
                logger.exception(
                    "[STATS EMBED] Silent Pre-KVK edit failed; falling back to fresh send."
                )

        # No existing message -> this is the FIRST send today. Enforce daily limit.
        # Gate by daily cap without logging yet
        if not is_test and _sent_today(KIND_PREKVK_DAILY):
            logger.info("[STATS EMBED] Pre-KVK already sent today; skipping.")
            return

        try:
            action = await _send_prekvk_embed(
                bot, channel, timestamp, sql_conn_str, is_test=is_test
            )
            # Log AFTER success, only for a fresh send
            if action == "sent" and not is_test and not _sent_today(KIND_PREKVK_DAILY):
                _claim_send(KIND_PREKVK_DAILY, max_per_day=1)
        except Exception:
            logger.exception("[STATS EMBED] Pre-KVK send failed.")
        return

    # --- Off-season (or Pre-KVK) path ---
    # 1) Daily post — strictly once per day + 12h cooldown
    # Mutual exclusivity — if KVK already posted today, suppress off-season (daily).
    if not is_test and _sent_today(KIND_KVK):
        logger.info("[STATS EMBED] KVK already posted today; skipping off-season daily.")
    elif is_test or _cooldown_ok(KIND_OFFSEASON_DAILY, hours=12):
        try:
            await send_offseason_stats_embed_v2(
                bot,
                channel=channel,
                is_weekly=False,
                mention_everyone=(not is_test),
            )
            # Log AFTER success
            if not is_test and not _sent_today(KIND_OFFSEASON_DAILY):
                _claim_send(KIND_OFFSEASON_DAILY, max_per_day=1)
        except Exception:
            logger.exception("[STATS EMBED] Off-season daily send failed.")
    else:
        logger.info("[STATS EMBED] Off-season daily cooldown active; skipping.")

    # 2) Optional weekly post — only on Mondays, at most once on that Monday, no ping
    try:
        if utcnow().weekday() == 0:  # Monday
            # Mutual exclusivity — if KVK already posted today, suppress off-season (weekly).
            if not is_test and _sent_today(KIND_KVK):
                logger.info("[STATS EMBED] KVK already posted today; skipping off-season weekly.")
            elif is_test or not _sent_today(KIND_OFFSEASON_WEEKLY):
                try:
                    await send_offseason_stats_embed_v2(
                        bot,
                        channel=channel,
                        is_weekly=True,
                        mention_everyone=False,
                    )
                    # Log AFTER success
                    if not is_test and not _sent_today(KIND_OFFSEASON_WEEKLY):
                        _claim_send(KIND_OFFSEASON_WEEKLY, max_per_day=1)
                except Exception:
                    logger.exception("[STATS EMBED] Off-season weekly send failed.")
            else:
                logger.info("[STATS EMBED] Off-season weekly already sent this Monday; skipping.")

    except Exception:
        logger.exception("[STATS EMBED] Weekly off-season dashboard failed")


# ---------------------------------------------------------------------------
# ALL_KINGDOM_KVK_DATA
# ---------------------------------------------------------------------------


def _load_allkingdom_blocks(kvk_no: int) -> dict[str, list[dict]]:
    """
    Returns aggregated top-3 blocks using database TVFs to centralize aggregation.

    Expects the following TVFs to exist in the DB:
      dbo.fn_KVK_Player_Aggregated(@kvk_no)
      dbo.fn_KVK_Kingdom_Aggregated(@kvk_no)
      dbo.fn_KVK_Camp_Aggregated(@kvk_no)

    Each TVF returns aggregated t4,t5,deads and denominators (sp/denom). We then
    CROSS APPLY to select the latest DKP Weights and compute DKP inline, ordering
    by the desired metric.
    """
    conn = get_conn_with_retries()
    with conn:
        c = conn.cursor()

        # Helper to run a simple 2-param query (kvk_no passed twice where weights TVF also needs it).
        def _run_top3(query: str, params: tuple) -> list[dict]:
            c.execute(query, params)
            cols = [d[0] for d in c.description]
            rows = [dict(zip(cols, row, strict=False)) for row in c.fetchall()]
            return rows

        # Players: use aggregated TVF and compute DKP using latest weights
        player_q = """
        SELECT TOP 3 p.name, p.kingdom, p.campid,
               (p.t4 + p.t5) AS kills_gain,
               p.deads,
               CAST(((p.t4*w.X + p.t5*w.Y + p.deads*w.Z) / NULLIF(p.sp,0)) AS float) AS dkp
        FROM dbo.fn_KVK_Player_Aggregated(?) p
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        p_kills = _run_top3(player_q, (kvk_no, kvk_no))

        player_q_deads = player_q.replace("ORDER BY kills_gain DESC", "ORDER BY p.deads DESC")
        p_deads = _run_top3(player_q_deads, (kvk_no, kvk_no))

        player_q_dkp = player_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        p_dkp = _run_top3(player_q_dkp, (kvk_no, kvk_no))

        # Our top 3 players in our kingdom (keeps previous logic)
        c.execute(
            """
        WITH W AS (
          SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL
        ), Agg AS (
          SELECT p.governor_id,
                 MAX(p.name)    AS name,
                 MAX(p.kingdom) AS kingdom,
                 SUM(ISNULL(p.t4_kills,0) + ISNULL(p.t5_kills,0)) AS kills_gain
          FROM KVK.KVK_Player_Windowed p
          JOIN W ON W.WindowName = p.WindowName
          WHERE p.KVK_NO = ? AND p.kingdom = ?
          GROUP BY p.governor_id
        )
        SELECT TOP 3 name, kills_gain
        FROM Agg
        ORDER BY kills_gain DESC;
        """,
            (kvk_no, kvk_no, OUR_KINGDOM),
        )
        our_players_top3 = [
            dict(zip([d[0] for d in c.description], row, strict=False)) for row in c.fetchall()
        ]

        # Kingdoms: aggregated TVF returns denom; compute DKP using latest weights
        kingdoms_q = """
        SELECT TOP 3 a.kingdom,
               (a.t4 + a.t5) AS kills_gain,
               a.deads,
               CAST(((a.t4*w.X + a.t5*w.Y + a.deads*w.Z) / NULLIF(a.denom,0)) AS float) AS dkp
        FROM dbo.fn_KVK_Kingdom_Aggregated(?) a
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        k_kills = _run_top3(kingdoms_q, (kvk_no, kvk_no))

        kingdoms_q_deads = kingdoms_q.replace("ORDER BY kills_gain DESC", "ORDER BY a.deads DESC")
        k_deads = _run_top3(kingdoms_q_deads, (kvk_no, kvk_no))

        kingdoms_q_dkp = kingdoms_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        k_dkp = _run_top3(kingdoms_q_dkp, (kvk_no, kvk_no))

        # Our kingdom line (unchanged)
        c.execute(
            """
        WITH W AS (SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL),
             Agg AS (
               SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads
               FROM KVK.KVK_Kingdom_Windowed kw
               JOIN W ON W.WindowName = kw.WindowName
               WHERE kw.KVK_NO=? AND kw.kingdom=?
             ),
             Den AS (
               SELECT SUM(sp) AS denom
               FROM (
                 SELECT p.governor_id, MAX(ISNULL(p.starting_power,0)) AS sp
                 FROM KVK.KVK_Player_Windowed p
                 WHERE p.KVK_NO=? AND p.kingdom=?
                 GROUP BY p.governor_id
               ) d
             ),
             Wt AS (
               SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
               FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
             )
        SELECT (a.t4+a.t5) AS kills_gain, a.deads,
               CAST(((a.t4*X + a.t5*Y + a.deads*Z)/NULLIF(d.denom,0)) AS float) AS dkp
        FROM Agg a CROSS JOIN Den d CROSS JOIN Wt;
        """,
            (kvk_no, kvk_no, OUR_KINGDOM, kvk_no, OUR_KINGDOM, kvk_no),
        )
        our_kingdom = [
            dict(zip([d[0] for d in c.description], row, strict=False)) for row in c.fetchall()
        ]

        # Camps: aggregated TVF returns denom; compute DKP using latest weights
        camps_q = """
        SELECT TOP 3 a.campid, a.camp_name,
               (a.t4 + a.t5) AS kills_gain, a.deads,
               CAST(((a.t4*w.X + a.t5*w.Y + a.deads*w.Z)/NULLIF(a.denom,0)) AS float) AS dkp
        FROM dbo.fn_KVK_Camp_Aggregated(?) a
        CROSS APPLY (
            SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
            FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
        ) w
        ORDER BY kills_gain DESC;
        """
        c_kills = _run_top3(camps_q, (kvk_no, kvk_no))

        camps_q_deads = camps_q.replace("ORDER BY kills_gain DESC", "ORDER BY a.deads DESC")
        c_deads = _run_top3(camps_q_deads, (kvk_no, kvk_no))

        camps_q_dkp = camps_q.replace("ORDER BY kills_gain DESC", "ORDER BY dkp DESC")
        c_dkp = _run_top3(camps_q_dkp, (kvk_no, kvk_no))

        # Our camp line (unchanged)
        c.execute(
            "SELECT TOP 1 CampID, CampName FROM KVK.KVK_CampMap WHERE KVK_NO=? AND Kingdom=?",
            (kvk_no, OUR_KINGDOM),
        )
        row = c.fetchone()
        our_camp_id = int(row.CampID) if row else None
        our_camp_name = str(row.CampName) if row else "Our Camp"

        if our_camp_id is not None:
            c.execute(
                """
            WITH W AS (SELECT WindowName FROM KVK.KVK_Windows WHERE KVK_NO=? AND StartScanID IS NOT NULL),
                 Agg AS (
                   SELECT SUM(ISNULL(t4_kills,0)) AS t4, SUM(ISNULL(t5_kills,0)) AS t5, SUM(ISNULL(deads,0)) AS deads
                   FROM KVK.KVK_Camp_Windowed cw
                   JOIN W ON W.WindowName = cw.WindowName
                   WHERE cw.KVK_NO=? AND cw.campid=?
                 ),
                 Den AS (
                   SELECT SUM(sp) AS denom
                   FROM (
                     SELECT p.governor_id, MAX(ISNULL(p.starting_power,0)) AS sp
                     FROM KVK.KVK_Player_Windowed p
                     WHERE p.KVK_NO=? AND p.campid=?
                     GROUP BY p.governor_id
                   ) d
                 ),
                 Wt AS (
                   SELECT TOP 1 WeightT4X AS X, WeightT5Y AS Y, WeightDeadsZ AS Z
                   FROM KVK.KVK_DKPWeights WHERE KVK_NO=? ORDER BY EffectiveFromUTC DESC
                 )
            SELECT (a.t4+a.t5) AS kills_gain, a.deads,
                   CAST(((a.t4*X + a.t5*Y + a.deads*Z)/NULLIF(d.denom,0)) AS float) AS dkp
            FROM Agg a CROSS JOIN Den d CROSS JOIN Wt;
            """,
                (kvk_no, kvk_no, our_camp_id, kvk_no, our_camp_id, kvk_no),
            )
            our_camp = [
                dict(zip([d[0] for d in c.description], row, strict=False)) for row in c.fetchall()
            ]
        else:
            our_camp = []

    return {
        "players_by_kills": p_kills,
        "players_by_deads": p_deads,
        "players_by_dkp": p_dkp,
        "kingdoms_by_kills": k_kills,
        "kingdoms_by_deads": k_deads,
        "kingdoms_by_dkp": k_dkp,
        "camps_by_kills": c_kills,
        "camps_by_deads": c_deads,
        "camps_by_dkp": c_dkp,
        "our_top_players": our_players_top3,
        "our_kingdom": our_kingdom,
        "our_camp": [{"camp_name": our_camp_name, **our_camp[0]}] if our_camp else [],
    }


# ---------------------------------------------------------------------------
# KVK embed
# ---------------------------------------------------------------------------


async def _send_kvk_embed(
    bot,
    channel: discord.abc.Messageable,
    timestamp: str,
    sql_conn_str: str,
    *,
    is_test: bool,
):
    # Prefer SQL metadata for display; fallback to Sheets only if needed.
    meta_sql = await asyncio.to_thread(get_latest_kvk_metadata_sql)
    if meta_sql and meta_sql.get("start_date") and meta_sql.get("end_date"):
        kvk_no = meta_sql["kvk_no"]
        kvk_name = meta_sql["kvk_name"]
        start_dt, end_dt = meta_sql["start_date"], meta_sql["end_date"]
        try:
            kvk_date_range = f"{start_dt.strftime('%d %b')} – {end_dt.strftime('%d %b')}"
        except Exception:
            kvk_date_range = ""
        banner_url = KVK_BANNER_MAP.get((kvk_name or "KVK").lower(), None)
    else:
        # Fallback to Sheets (best-effort for names/dates if SQL lacked them)
        meta = await asyncio.to_thread(get_latest_kvk_metadata)
        if meta:
            kvk_no = meta["kvk_no"]
            kvk_name = meta["kvk_name"]
            kvk_date_range = (
                f"{meta['start_date'].strftime('%d %b')} – {meta['end_date'].strftime('%d %b')}"
            )
            banner_url = KVK_BANNER_MAP.get(kvk_name.lower(), None)
        else:
            kvk_no = "?"
            kvk_name = "KVK"
            kvk_date_range = ""
            banner_url = None

    # --- All-kingdom fighting windows Top-3s ---
    blocks = await asyncio.to_thread(_load_allkingdom_blocks, kvk_no)

    # Build sections
    players_kills = _fmt_top(blocks["players_by_kills"], "name", "kills_gain")
    _players_deads = _fmt_top(blocks["players_by_deads"], "name", "deads")
    _players_dkp = _fmt_top(blocks["players_by_dkp"], "name", "dkp", val_fmt=_fmt_dkp)

    kingdoms_kills = _fmt_top(blocks["kingdoms_by_kills"], "kingdom", "kills_gain")
    _kingdoms_deads = _fmt_top(blocks["kingdoms_by_deads"], "kingdom", "deads")
    _kingdoms_dkp = _fmt_top(blocks["kingdoms_by_dkp"], "kingdom", "dkp", val_fmt=_fmt_dkp)

    camps_kills = _fmt_top(blocks["camps_by_kills"], "camp_name", "kills_gain")
    _camps_deads = _fmt_top(blocks["camps_by_deads"], "camp_name", "deads")
    _camps_dkp = _fmt_top(blocks["camps_by_dkp"], "camp_name", "dkp", val_fmt=_fmt_dkp)

    # Our lines (now with top-3 inside 1198)
    our_king = blocks["our_kingdom"][0] if blocks["our_kingdom"] else None
    our_camp = blocks["our_camp"][0] if blocks["our_camp"] else None
    our_topk = blocks.get("our_top_players", []) or []

    topk_lines = []
    for i, r in enumerate(our_topk[:3]):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        topk_lines.append(f"{medal} {r['name']} — `{_abbr(r['kills_gain'])}`")

    our_lines = []
    if topk_lines:
        our_lines.append("**1198 Top 3 (Kills):**\n" + "\n".join(topk_lines))
    if our_king:
        our_lines.append(
            f"👑 **Kingdom {OUR_KINGDOM}:** "
            f"kills `{_abbr(our_king['kills_gain'])}` | "
            f"deads `{_abbr(our_king['deads'])}` | "
            f"dkp `{_fmt_dkp(our_king['dkp'])}`"
        )
    if our_camp:
        our_lines.append(
            f"🏕️ **{our_camp['camp_name']}:** "
            f"kills `{_abbr(our_camp['kills_gain'])}` | "
            f"deads `{_abbr(our_camp['deads'])}` | "
            f"dkp `{_fmt_dkp(our_camp['dkp'])}`"
        )
    our_block = "\n".join(our_lines) if our_lines else "—"

    # Quick visibility into what we’re rendering
    logger.info(
        "[KVK EMBED] Rows -> players(kills=%d, deads=%d, dkp=%d) | "
        "kingdoms(kills=%d, deads=%d, dkp=%d) | "
        "camps(kills=%d, deads=%d, dkp=%d) | our(player=%d, kingdom=%d, camp=%d)",
        len(blocks.get("players_by_kills", [])),
        len(blocks.get("players_by_deads", [])),
        len(blocks.get("players_by_dkp", [])),
        len(blocks.get("kingdoms_by_kills", [])),
        len(blocks.get("kingdoms_by_deads", [])),
        len(blocks.get("kingdoms_by_dkp", [])),
        len(blocks.get("camps_by_kills", [])),
        len(blocks.get("camps_by_deads", [])),
        len(blocks.get("camps_by_dkp", [])),
        1 if blocks.get("our_top_players") else 0,
        1 if blocks.get("our_kingdom") else 0,
        1 if blocks.get("our_camp") else 0,
    )

    # Links (prefer ID if present)
    sheet_link = (
        f"https://docs.google.com/spreadsheets/d/{STATS_SHEET_ID}"
        if STATS_SHEET_ID
        else "https://docs.google.com"
    )
    embed = discord.Embed(
        title=f"🔥 {kvk_name} (KVK {kvk_no})",
        description=(
            (f"**{kvk_date_range}**\n" if kvk_date_range else "")
            + f"Stats updated **{timestamp}**\n\n"
        ),
        color=discord.Color.orange(),
    )
    # Thumbnail (keep embeds consistent with the rest of the bot)
    thumb = (CUSTOM_AVATAR_URL or "").strip()
    if thumb and thumb.lower().startswith(("http://", "https://")):
        try:
            embed.set_thumbnail(url=thumb)
        except Exception:
            logger.exception("[KVK EMBED] Failed to set thumbnail")

    if banner_url:
        embed.set_image(url=banner_url)

    # Our lines
    embed.add_field(name="⭐ Our Highlights", value=our_block, inline=False)

    # Honour Top-3 (KVK embed is already gated by fighting-open)
    try:
        honor_top = await asyncio.to_thread(get_latest_honor_top, 3)
        if honor_top:
            embed.add_field(
                name="🏅 Honor Rankings (Top 3)", value=_fmt_honor(honor_top), inline=False
            )
    except Exception:
        logger.exception("[KVK EMBED] Honor block failed")

    # Section: Players
    embed.add_field(name="\u200b", value="\u200b", inline=False)  # spacer
    embed.add_field(name="👥 All Players — Top Kills", value=players_kills, inline=False)
    # embed.add_field(name="👥 All Players — Top Deads", value=players_deads, inline=True)
    # embed.add_field(name="👥 All Players — Top DKP", value=players_dkp, inline=True)

    # Section: Kingdoms
    # embed.add_field(name="\u200b", value="\u200b", inline=False)  # spacer
    embed.add_field(name="🏰 Kingdoms — Top Kills", value=kingdoms_kills, inline=False)
    # embed.add_field(name="🏰 Kingdoms — Top Deads", value=kingdoms_deads, inline=True)
    # embed.add_field(name="🏰 Kingdoms — Top DKP", value=kingdoms_dkp, inline=True)

    # Section: Camps
    # embed.add_field(name="\u200b", value="\u200b", inline=False)  # spacer
    embed.add_field(name="⛺ Camps — Top Kills", value=camps_kills, inline=False)
    # embed.add_field(name="⛺ Camps — Top Deads", value=camps_deads, inline=True)
    # embed.add_field(name="⛺ Camps — Top DKP", value=camps_dkp, inline=True)

    # Quick commands
    embed.add_field(
        name="📎 Quick Commands",
        value="Use **/mykvkstats** to view your stats\nUse **/ranking** to see top players",
        inline=False,
    )

    # Links
    embed.add_field(
        name="🔗 Links",
        value=f"[Full KVK Stats]({sheet_link}) • [Dashboard](https://lookerstudio.google.com/s/usgUxj1t59U)",
        inline=False,
    )
    embed.set_footer(text="KD98 Discord Bot")

    content = "@everyone" if not is_test else None
    await channel.send(
        embed=embed, content=content, allowed_mentions=discord.AllowedMentions(everyone=True)
    )
