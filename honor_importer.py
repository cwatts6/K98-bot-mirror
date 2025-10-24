# honor_importer.py
from __future__ import annotations

import datetime as dt
import io
import logging

import pandas as pd
import pyodbc

from constants import DATABASE, PASSWORD, SERVER, USERNAME
from utils import ensure_aware_utc, utcnow

log = logging.getLogger(__name__)


def _conn():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}",
        autocommit=False,
    )


def _current_kvk_no(cur) -> int:
    # Reuse your KVK_Details model; pick the active KVK
    # If you prefer latest row instead, adjust
    cur.execute(
        """
      SELECT TOP (1) KVK_NO
      FROM dbo.KVK_Details
      WHERE KVK_START_DATE <= SYSUTCDATETIME() AND KVK_END_DATE >= SYSUTCDATETIME()
      ORDER BY KVK_NO DESC
    """
    )
    row = cur.fetchone()
    if not row:
        # fallback: max KVK_NO
        cur.execute("SELECT TOP (1) KVK_NO FROM dbo.KVK_Details ORDER BY KVK_NO DESC")
        row = cur.fetchone()
    return int(row[0])


def _next_scan_id(cur, kvk_no: int) -> int:
    cur.execute("SELECT ISNULL(MAX(ScanID),0) FROM dbo.KVK_Honor_Scan WHERE KVK_NO=?", kvk_no)
    return int(cur.fetchone()[0]) + 1


def parse_honor_xlsx(xlsx_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="honor")
    # Normalize columns
    df = df.rename(
        columns={"GovernorID": "GovernorID", "Name": "GovernorName", "Honor Points": "HonorPoints"}
    )[["GovernorID", "GovernorName", "HonorPoints"]]
    # Coerce dtypes
    df["GovernorID"] = pd.to_numeric(df["GovernorID"], errors="coerce").astype("Int64")
    df["HonorPoints"] = pd.to_numeric(df["HonorPoints"], errors="coerce").fillna(0).astype("Int64")
    df["GovernorName"] = df["GovernorName"].fillna("").astype(str).str.strip()
    # Drop empties
    df = df.dropna(subset=["GovernorID"]).copy()
    return df


def ingest_honor_snapshot(
    xlsx_bytes: bytes, *, source_filename: str, scan_ts_utc: dt.datetime | None = None
) -> tuple[int, int]:
    """
    Returns: (kvk_no, scan_id)
    """
    scan_ts_utc = scan_ts_utc or utcnow()
    # Normalize to aware UTC internally, but strip tzinfo for DB call if the DB expects naive UTC
    scan_ts_param = ensure_aware_utc(scan_ts_utc).replace(tzinfo=None)

    df = parse_honor_xlsx(xlsx_bytes)

    with _conn() as cn:
        cur = cn.cursor()
        kvk_no = _current_kvk_no(cur)
        scan_id = _next_scan_id(cur, kvk_no)

        # Insert scan row
        cur.execute(
            """
            INSERT INTO dbo.KVK_Honor_Scan (KVK_NO, ScanID, ScanTimestampUTC, SourceFileName, ImportedAtUTC, row_count)
            VALUES (?,?,?,?,SYSUTCDATETIME(),?)
        """,
            kvk_no,
            scan_id,
            scan_ts_param,
            source_filename,
            len(df),
        )

        if len(df) > 0:
            # Fast executemany
            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.KVK_Honor_AllPlayers_Raw (KVK_NO, ScanID, GovernorID, GovernorName, HonorPoints)
                VALUES (?,?,?,?,?)
            """,
                [
                    (kvk_no, scan_id, int(r.GovernorID), r.GovernorName, int(r.HonorPoints or 0))
                    for r in df.itertuples(index=False)
                ],
            )

        cn.commit()

    log.info(
        "[HONOR] Ingested KVK_NO=%s ScanID=%s rows=%s from %s",
        kvk_no,
        scan_id,
        len(df),
        source_filename,
    )
    return kvk_no, scan_id
