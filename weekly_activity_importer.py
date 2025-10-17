# weekly_activity_importer.py
from datetime import UTC, datetime, timedelta
import hashlib
import io
import logging

import pandas as pd
import pyodbc

log = logging.getLogger(__name__)

# ---- Helpers ---------------------------------------------------------------


def _week_start_utc(ts: datetime) -> datetime:
    """
    Convert an aware/naive datetime to naive UTC, then clamp to Monday 00:00 (UTC).
    Stored in SQL as naive UTC (DATETIME2).
    """
    ts = ts.astimezone(UTC).replace(tzinfo=None)
    dow = ts.weekday()  # Monday = 0
    monday = (ts - timedelta(days=dow)).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday


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


def _select_sheet_with_required_columns(xl: pd.ExcelFile) -> str:
    for name in xl.sheet_names:
        df_head = xl.parse(name, nrows=2)
        if all(col in df_head.columns for col in REQUIRED_COLS.keys()):
            return name
    # Fallback to first sheet; we'll error later if required cols are missing
    return xl.sheet_names[0]


def parse_activity_excel(content: bytes) -> pd.DataFrame:
    try:
        xl = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Unable to open Excel content: {type(e).__name__}: {e}")

    sheet = _select_sheet_with_required_columns(xl)
    df = xl.parse(sheet)

    # Validate/rename required columns
    missing = [col for col in REQUIRED_COLS.keys() if col not in df.columns]
    if missing:
        raise ValueError(
            f"Expected columns missing in '{sheet}': {', '.join(missing)}. "
            f"Found: {', '.join(map(str, df.columns))}"
        )

    df = df.rename(columns=REQUIRED_COLS)[list(REQUIRED_COLS.values())]

    # Remove thousands separators if present and trim strings
    for c in [
        "Power",
        "KillPoints",
        "HelpTimes",
        "RssTrading",
        "BuildingTotal",
        "TechDonationTotal",
    ]:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.replace(",", "").str.strip()

    # Types
    df["GovernorID"] = pd.to_numeric(df["GovernorID"], errors="coerce").astype("Int64")
    df["BuildingTotal"] = pd.to_numeric(df["BuildingTotal"], errors="coerce").fillna(0).astype(int)
    df["TechDonationTotal"] = (
        pd.to_numeric(df["TechDonationTotal"], errors="coerce").fillna(0).astype(int)
    )

    # Optional numerics retained as nullable ints (become NULL if NaN)
    for opt in ["Power", "KillPoints", "HelpTimes", "RssTrading"]:
        df[opt] = pd.to_numeric(df[opt], errors="coerce")

    df["GovernorName"] = df["GovernorName"].astype(str).str.strip().str[:64]
    df["AllianceTag"] = df["AllianceTag"].astype(str).str.strip().str[:16]

    df = df.dropna(subset=["GovernorID"]).copy()
    return df


# ---- SQL I/O ---------------------------------------------------------------


def _cxn(server, database, username, password):
    # Use your existing connection style from other importers
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={database};UID={username};PWD={password}",
        autocommit=False,
    )


def _get_prev_snapshot_id_excluding(
    cur, week_start_utc: datetime, current_snapshot_id: int
) -> int | None:
    """
    Return the most recent snapshot for the given week that is NOT the current snapshot.
    This is the critical fix to avoid 'now - now = 0' deltas.
    """
    cur.execute(
        """
        SELECT TOP (1) SnapshotId
        FROM dbo.AllianceActivitySnapshotHeader
        WHERE WeekStartUtc = ? AND SnapshotId <> ?
        ORDER BY SnapshotTsUtc DESC
    """,
        week_start_utc,
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

    Returns number of daily rows written.
    """
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
        week_start,
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

    # Week calendar
    mon = week_start.date()
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

            to_upsert.append((int(gov), d, week_start, int(b_delta), int(t_delta)))

            prev_cum_b, prev_cum_t = b_cum, t_cum

    # 3) Replace the week in one shot (simple & fast)
    cur.execute("DELETE FROM dbo.AllianceActivityDaily WHERE WeekStartUtc = ?", week_start)
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
    snapshot_ts_utc = snapshot_ts_utc.astimezone(UTC).replace(tzinfo=None)
    week_start = _week_start_utc(snapshot_ts_utc)
    df = parse_activity_excel(content)
    file_sha1 = _sha1(content)

    with _cxn(server, database, username, password) as cxn:
        cur = cxn.cursor()

        # Deduplicate by (WeekStartUtc, SourceFileSha1)
        cur.execute(
            """
            SELECT COUNT(1)
            FROM dbo.AllianceActivitySnapshotHeader
            WHERE WeekStartUtc = ? AND SourceFileSha1 = ?
        """,
            week_start,
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
            snapshot_ts_utc,
            week_start,
            message_id,
            channel_id,
            source_filename,
            pyodbc.Binary(file_sha1),
            int(df.shape[0]),
        )
        snapshot_id = cur.fetchone()[0]

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

        # ... after writing AllianceActivityDelta ...
        # Rebuild daily activity table for the whole week
        rebuilt = _rebuild_daily_activity_for_week(cur, week_start)
        log.info("[ACTIVITY DAILY] Rebuilt %s daily rows for week %s", rebuilt, week_start.date())

        cxn.commit()
        return (snapshot_id, len(delta_rows))
