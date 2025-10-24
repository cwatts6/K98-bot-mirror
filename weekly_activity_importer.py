# weekly_activity_importer.py
from datetime import datetime, timedelta
import hashlib
import io
import logging

import pandas as pd
import pyodbc

from utils import ensure_aware_utc

log = logging.getLogger(__name__)

# ---- Helpers ---------------------------------------------------------------


def _week_start_utc(ts: datetime) -> datetime:
    """
    Return an aware UTC datetime (tzinfo=UTC) clamped to the Monday 00:00:00 of the week
    that contains `ts`. Accepts naive or aware datetimes.
    """
    t = ensure_aware_utc(ts)  # now guaranteed tzinfo=UTC
    dow = t.weekday()  # Monday = 0
    monday = (t - timedelta(days=dow)).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday  # aware UTC


def _sha1(b: bytes) -> bytes:
    # 20 bytes; use VARBINARY(20) in SQL
    return hashlib.sha1(b).digest()


REQUIRED_COLS = {
    "GovernorID": "GovernorID",
    "Name": "GovernorName",
    "Alliance": "AllianceTag",
    "Power": "Power",
    "Kill Points": "KillPoints",
    "Help Times": "HelpTimes",
    "Rss Trading": "RssTrading",
    "Building": "BuildingTotal",
    "Tech Donation": "TechDonationTotal",
}


def _normalize_col_name(x: object) -> str:
    """
    Normalise a header name for tolerant matching:
    - cast to str, strip whitespace, collapse NBSP -> space, lower-case
    """
    if x is None:
        return ""
    return str(x).strip().replace("\u00a0", " ").lower()


def _select_sheet_with_required_columns(xl: pd.ExcelFile) -> str:
    """
    Select the first worksheet containing the required columns, robust to minor header variations.
    Falls back to the first sheet if none match (the caller will error later with a clear message).
    """
    required_norms = {k: _normalize_col_name(k) for k in REQUIRED_COLS.keys()}
    for name in xl.sheet_names:
        try:
            df_head = xl.parse(name, nrows=2)
        except Exception:
            # skip sheets that can't be parsed
            continue
        cols_norm = {_normalize_col_name(c): c for c in df_head.columns}
        if all(rn in cols_norm for rn in required_norms.values()):
            return name
    # Fallback to first sheet; we'll error later if required cols are missing
    return xl.sheet_names[0]


def _find_and_rename_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find columns in df that match the required names tolerantly and rename them to canonical names
    from REQUIRED_COLS values. Raises ValueError if any required column cannot be matched.
    """
    cols_map = {_normalize_col_name(c): c for c in df.columns}
    found = {}
    missing = []
    for req_key, canonical in REQUIRED_COLS.items():
        norm_req = _normalize_col_name(req_key)
        if norm_req in cols_map:
            found[cols_map[norm_req]] = canonical
        else:
            missing.append(req_key)
    if missing:
        raise ValueError(f"Expected columns missing: {', '.join(missing)}.")
    return df.rename(columns=found)


def parse_activity_excel(content: bytes) -> pd.DataFrame:
    try:
        xl = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Unable to open Excel content: {type(e).__name__}: {e}")

    sheet = _select_sheet_with_required_columns(xl)
    df = xl.parse(sheet)

    try:
        df = _find_and_rename_required_columns(df)
    except ValueError as e:
        # Provide the sheet name and available columns for easier debugging
        raise ValueError(
            f"Expected columns missing in '{sheet}': {e}. Found: {', '.join(map(str, df.columns))}"
        )

    # Remove thousands separators if present and trim strings
    for c in [
        "Power",
        "KillPoints",
        "HelpTimes",
        "RssTrading",
        "BuildingTotal",
        "TechDonationTotal",
    ]:
        if c in df.columns:
            # Explicit regex=False to avoid pandas future warnings and improve perf
            df[c] = df[c].astype(str).str.replace(",", "", regex=False).str.strip()

    # Types
    # GovernorID: coerce -> drop rows without valid ID -> convert to plain int
    df["GovernorID"] = pd.to_numeric(df["GovernorID"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["GovernorID"]).copy()
    # Now safe to convert to plain int for subsequent use
    df["GovernorID"] = df["GovernorID"].astype(int)

    # Building/Tech totals: coerce NaN -> 0 and ensure int
    df["BuildingTotal"] = pd.to_numeric(df["BuildingTotal"], errors="coerce").fillna(0).astype(int)
    df["TechDonationTotal"] = (
        pd.to_numeric(df["TechDonationTotal"], errors="coerce").fillna(0).astype(int)
    )

    # Optional numerics retained as nullable floats (become NaN if missing).
    # Consumers cast to int conditionally when inserting.
    for opt in ["Power", "KillPoints", "HelpTimes", "RssTrading"]:
        if opt in df.columns:
            df[opt] = pd.to_numeric(df[opt], errors="coerce")

    # GovernorName / AllianceTag: avoid converting missing to literal "nan".
    # - Preserve None (-> SQL NULL) where empty after trimming.
    if "GovernorName" in df.columns:
        df["GovernorName"] = df["GovernorName"].where(df["GovernorName"].notna(), "")
        df["GovernorName"] = df["GovernorName"].astype(str).str.strip().str[:64]
        df["GovernorName"] = df["GovernorName"].replace({"": None})
    if "AllianceTag" in df.columns:
        df["AllianceTag"] = df["AllianceTag"].where(df["AllianceTag"].notna(), "")
        df["AllianceTag"] = df["AllianceTag"].astype(str).str.strip().str[:16]
        df["AllianceTag"] = df["AllianceTag"].replace({"": None})

    return df


# ---- SQL I/O ---------------------------------------------------------------


def _cxn(server=None, database=None, username=None, password=None):
    """
    Return a pyodbc connection.
    - If server/database/username/password are provided, build a connection from them.
    - Otherwise reuse the central _conn() from constants.py (preferred).
    Keeps autocommit=False for transactional safety.
    """
    try:
        # Import the project-level helper if available
        from constants import _conn as _default_conn  # lazy import to avoid hard dependency
    except Exception:
        _default_conn = None

    # If any explicit params were supplied, build a custom connection using them.
    if server or database or username or password:
        import pyodbc  # lazy

        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        # explicit timeout kept minimal; constants._conn uses timeout=5 so we could mirror that
        return pyodbc.connect(conn_str, autocommit=False, timeout=5)

    # Prefer the shared helper if available, else fall back to building from env/constants
    if _default_conn is not None:
        return _default_conn()
    # Last-resort: build from the driver with no credentials (will likely fail)
    import pyodbc

    return pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};", autocommit=False, timeout=5)


def _get_prev_snapshot_id_excluding(
    cur, week_start_utc: datetime, current_snapshot_id: int
) -> int | None:
    """
    Return the most recent snapshot for the given week that is NOT the current snapshot.
    Accepts aware or naive week_start_utc; converts to naive UTC for SQL comparison.
    """
    wk_naive = ensure_aware_utc(week_start_utc).replace(tzinfo=None)
    cur.execute(
        """
        SELECT TOP (1) SnapshotId
        FROM dbo.AllianceActivitySnapshotHeader
        WHERE WeekStartUtc = ? AND SnapshotId <> ?
        ORDER BY SnapshotTsUtc DESC
    """,
        wk_naive,
        current_snapshot_id,
    )
    row = cur.fetchone()
    return row[0] if row else None


def _load_prev_totals(cur, prev_snapshot_id: int | None) -> dict[int, tuple[int, int]]:
    """
    Return {GovernorID: (BuildingTotal, TechDonationTotal)} from previous snapshot.
    """
    if not prev_snapshot_id:
        return {}
    cur.execute(
        """
        SELECT GovernorID, BuildingTotal, TechDonationTotal
        FROM dbo.AllianceActivitySnapshotRow
        WHERE SnapshotId = ?
    """,
        prev_snapshot_id,
    )
    out: dict[int, tuple[int, int]] = {}
    for gov, b, t in cur.fetchall():
        out[int(gov)] = (int(b or 0), int(t or 0))
    return out


# ---- NEW: Week rebuilder (cumulative -> daily deltas) ----------------------


def _rebuild_daily_activity_for_week(cur, week_start: datetime) -> int:
    """
    Recompute daily activity deltas for the whole week [Mon..Sun] for all governors
    from cumulative snapshot rows, and upsert into dbo.AllianceActivityDaily.

    Accepts aware or naive week_start; converts to naive UTC for SQL usage.
    Returns number of daily rows written.
    """
    wk_naive = ensure_aware_utc(week_start).replace(tzinfo=None)

    # 1) Load all snapshot rows for this week (join header -> rows)
    cur.execute(
        """
        SELECT r.GovernorID,
               CAST(h.SnapshotTsUtc AS DATE) AS AsOfDate,
               r.BuildingTotal,
               r.TechDonationTotal
        FROM dbo.AllianceActivitySnapshotRow AS r
        JOIN dbo.AllianceActivitySnapshotHeader AS h
          ON h.SnapshotId = r.SnapshotId
        WHERE h.WeekStartUtc = ?
    """,
        wk_naive,
    )
    rows = cur.fetchall()
    if not rows:
        return 0

    # Build a dict: {gov: {date: (build_cum, tech_cum)}}
    from collections import defaultdict
    import datetime as _dt

    gmap = defaultdict(dict)
    for gov, as_of_date, b_cum, t_cum in rows:
        d = as_of_date  # DATE
        # take the MAX cumulative per day if multiple imports
        prev = gmap[gov].get(d)
        if prev is None:
            gmap[gov][d] = (int(b_cum or 0), int(t_cum or 0))
        else:
            gmap[gov][d] = (max(prev[0], int(b_cum or 0)), max(prev[1], int(t_cum or 0)))

    # Week calendar (mon is a date)
    mon = ensure_aware_utc(week_start).date()
    days = [mon + _dt.timedelta(days=i) for i in range(7)]

    # 2) For each governor, generate a non-decreasing cumulative series over the week
    #    - missing days carry forward previous cumulative (or 0 on Monday)
    #    - any negative movement is clamped out by monotonic carry-forward
    to_upsert = []  # (GovernorID, AsOfDate, WeekStartUtc, BuildDonations, TechDonations)
    for gov, per_day in gmap.items():
        prev_cum_b = 0  # Monday baseline
        prev_cum_t = 0
        for d in days:
            b_cum, t_cum = per_day.get(d, (prev_cum_b, prev_cum_t))
            # clamp to previous to enforce monotonic non-decreasing within the week
            if b_cum < prev_cum_b:
                b_cum = prev_cum_b
            if t_cum < prev_cum_t:
                t_cum = prev_cum_t

            b_delta = b_cum - prev_cum_b
            t_delta = t_cum - prev_cum_t

            # WeekStartUtc stored in SQL as naive UTC (precomputed)
            to_upsert.append((int(gov), d, wk_naive, int(b_delta), int(t_delta)))

            prev_cum_b, prev_cum_t = b_cum, t_cum

    # 3) Replace the week in one shot (simple & fast)
    cur.execute("DELETE FROM dbo.AllianceActivityDaily WHERE WeekStartUtc = ?", wk_naive)
    if to_upsert:
        cur.fast_executemany = True
        cur.executemany(
            """
            INSERT INTO dbo.AllianceActivityDaily
                (GovernorID, AsOfDate, WeekStartUtc, BuildDonations, TechDonations)
            VALUES (?, ?, ?, ?, ?)
        """,
            to_upsert,
        )

    return len(to_upsert)


# ---- Ingest ---------------------------------------------------------------


def ingest_weekly_activity_excel(
    *,
    content: bytes,
    snapshot_ts_utc: datetime,
    message_id: int | None,
    channel_id: int | None,
    server: str,
    database: str,
    username: str,
    password: str,
    source_filename: str = "1198_alliance_activity.xlsx",
) -> tuple[int, int]:
    """
    Ingests the weekly activity Excel into header/row tables and writes per-governor deltas
    vs the *prior* snapshot of the same week (not the current one).

    Returns:
        (snapshot_id, delta_row_count)
        (0, 0) if duplicate file for the same week (by SHA-1).
    """
    # Ensure snapshot_ts_utc is aware UTC (in-memory arithmetic uses aware datetimes)
    snapshot_ts_utc = ensure_aware_utc(snapshot_ts_utc)
    week_start = _week_start_utc(snapshot_ts_utc)  # aware UTC
    df = parse_activity_excel(content)
    file_sha1 = _sha1(content)

    with _cxn(server, database, username, password) as cxn:
        cur = cxn.cursor()
        try:
            # SQL expects naive WeekStartUtc; convert here once
            week_start_naive = week_start.replace(tzinfo=None)

            # Deduplicate by (WeekStartUtc, SourceFileSha1)
            cur.execute(
                """
                SELECT COUNT(1)
                FROM dbo.AllianceActivitySnapshotHeader
                WHERE WeekStartUtc = ? AND SourceFileSha1 = ?
            """,
                week_start_naive,
                pyodbc.Binary(file_sha1),
            )
            if cur.fetchone()[0]:
                log.info("Duplicate upload for this week detected; skipping ingest.")
                cxn.rollback()
                return (0, 0)

            # Insert header
            cur.execute(
                """
                INSERT INTO dbo.AllianceActivitySnapshotHeader
                    (SnapshotTsUtc, WeekStartUtc, SourceMessageId, SourceChannelId,
                     SourceFileName, SourceFileSha1, Row_Count)
                OUTPUT INSERTED.SnapshotId
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                snapshot_ts_utc.replace(tzinfo=None),  # legacy proc/header expects naive UTC
                week_start_naive,
                message_id,
                channel_id,
                source_filename,
                pyodbc.Binary(file_sha1),
                int(df.shape[0]),
            )
            snapshot_id = cur.fetchone()[0]
            log.info(
                "Inserted SnapshotId=%s for week %s (rows=%d)",
                snapshot_id,
                week_start.date(),
                df.shape[0],
            )

            # Insert rows (fast_executemany for speed)
            cur.fast_executemany = True
            rows = []
            for row in df.itertuples(index=False):
                rows.append(
                    (
                        snapshot_id,
                        int(row.GovernorID),
                        row.GovernorName,
                        row.AllianceTag,
                        int(row.Power) if pd.notna(row.Power) else None,
                        int(row.KillPoints) if pd.notna(row.KillPoints) else None,
                        int(row.HelpTimes) if pd.notna(row.HelpTimes) else None,
                        int(row.RssTrading) if pd.notna(row.RssTrading) else None,
                        int(row.BuildingTotal),
                        int(row.TechDonationTotal),
                    )
                )
            if rows:
                cur.executemany(
                    """
                    INSERT INTO dbo.AllianceActivitySnapshotRow
                        (SnapshotId, GovernorID, GovernorName, AllianceTag,
                         Power, KillPoints, HelpTimes, RssTrading,
                         BuildingTotal, TechDonationTotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    rows,
                )
            log.debug("Inserted %d snapshot rows for SnapshotId=%s", len(rows), snapshot_id)

            # Compute deltas vs the previous snapshot (EXCLUDING the current)
            prev_snapshot_id = _get_prev_snapshot_id_excluding(cur, week_start, snapshot_id)
            prev_totals = _load_prev_totals(cur, prev_snapshot_id)

            # Current totals (from the just-inserted rows)
            cur.execute(
                """
                SELECT GovernorID, BuildingTotal, TechDonationTotal
                FROM dbo.AllianceActivitySnapshotRow
                WHERE SnapshotId = ?
            """,
                snapshot_id,
            )
            current_totals = {int(g): (int(b or 0), int(t or 0)) for g, b, t in cur.fetchall()}

            delta_rows = []
            for gov_id, (b_now, t_now) in current_totals.items():
                b_prev, t_prev = prev_totals.get(gov_id, (0, 0))
                note = None
                if gov_id not in prev_totals:
                    note = "new_governor"
                b_delta = b_now - b_prev
                t_delta = t_now - t_prev
                if b_delta < 0 or t_delta < 0:
                    # Guard for counter resets / data cleanup
                    b_delta = max(b_delta, 0)
                    t_delta = max(t_delta, 0)
                    note = f"{note};counter_reset" if note else "counter_reset"
                # NOTE: zero-delta rows are intentionally kept for auditing/history.
                delta_rows.append((snapshot_id, prev_snapshot_id, gov_id, b_delta, t_delta, note))

            if delta_rows:
                cur.fast_executemany = True
                cur.executemany(
                    """
                    INSERT INTO dbo.AllianceActivityDelta
                        (SnapshotId, PrevSnapshotId, GovernorID, BuildingDelta, TechDonationDelta, Note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    delta_rows,
                )
            log.info(
                "Wrote %d delta rows for SnapshotId=%s (prev_snapshot=%s)",
                len(delta_rows),
                snapshot_id,
                prev_snapshot_id,
            )

            # ... after writing AllianceActivityDelta ...
            # Rebuild daily activity table for the whole week
            rebuilt = _rebuild_daily_activity_for_week(cur, week_start)
            log.info(
                "[ACTIVITY DAILY] Rebuilt %s daily rows for week %s", rebuilt, week_start.date()
            )

            cxn.commit()
            return (snapshot_id, len(delta_rows))
        except Exception:
            log.exception("Failed ingesting weekly activity; rolling back transaction")
            try:
                cxn.rollback()
            except Exception:
                log.exception("Rollback failed")
            raise
