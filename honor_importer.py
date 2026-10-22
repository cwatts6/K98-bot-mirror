# honor_importer.py
from __future__ import annotations

import datetime as dt
import hashlib
import io
import logging

import pandas as pd

from file_utils import fetch_one_dict
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)


def _conn():
    """
    Use the centralized connection helper (get_conn_with_retries).
    """
    from file_utils import get_conn_with_retries  # type: ignore

    return get_conn_with_retries()


def _current_kvk_no(cur) -> int:
    """
    Resolve the KVK number for the current import.

    Preferred path:
      - Try to use kvk_state.get_kvk_context_today() (single source of truth).

    Fallback:
      - If kvk_state is unavailable or returns None, fall back to original DB
        logic using the provided cursor: prefer the active KVK (start<=now<=end),
        else return the latest KVK_NO.
    """
    try:
        # Lazy import to avoid circular import at module import time
        from kvk_state import get_kvk_context_today  # type: ignore

        try:
            ctx = get_kvk_context_today()
            if ctx and ctx.get("kvk_no") is not None:
                return int(ctx["kvk_no"])
        except Exception:
            # If kvk_state helper fails, we'll fall back to DB below
            logger.debug(
                "[HONOR] kvk_state.get_kvk_context_today raised; falling back to DB lookup",
                exc_info=True,
            )
    except Exception:
        # kvk_state not importable; fall back to DB lookup below
        pass

    # Fallback: original DB lookup (active KVK first, else latest)
    cur.execute("""
      SELECT TOP (1) KVK_NO
      FROM dbo.KVK_Details
      WHERE KVK_START_DATE <= SYSUTCDATETIME() AND KVK_END_DATE >= SYSUTCDATETIME()
      ORDER BY KVK_NO DESC
    """)
    row = fetch_one_dict(cur)
    if not row:
        # fallback: max KVK_NO
        cur.execute("SELECT TOP (1) KVK_NO FROM dbo.KVK_Details ORDER BY KVK_NO DESC")
        row = fetch_one_dict(cur)

    if not row:
        raise RuntimeError("No KVK_NO found in dbo.KVK_Details")

    # Prefer explicit column name, fall back to first value
    if "KVK_NO" in row:
        return int(row["KVK_NO"])
    return int(next(iter(row.values())))


def _next_scan_id(cur, kvk_no: int) -> int:
    """
    Return the next ScanID for the given KVK_NO.
    This uses a single-SELECT that returns NextScanID as a numeric column.
    If the DB returns a different column name, we fall back sensibly to the first value.
    """
    cur.execute(
        """
        SELECT ISNULL(MAX(ScanID), 0) + 1 AS NextScanID
        FROM dbo.KVK_Honor_Scan
        WHERE KVK_NO = ?
        """,
        kvk_no,
    )
    row = fetch_one_dict(cur)
    if not row:
        # No rows -> start at 1
        return 1
    if "NextScanID" in row:
        return int(row["NextScanID"])
    return int(next(iter(row.values())))


def parse_honor_xlsx(xlsx_bytes: bytes) -> pd.DataFrame:
    """
    Parse the provided bytes as an Excel workbook and return a normalized DataFrame
    with columns: GovernorID (Int64), GovernorName (str), HonorPoints (Int64).

    Supported header variants (case-sensitive variants are normalized):
     - GovernorID
     - GovernorName or Name
     - HonorPoints or "Honor Points"
    """
    # Read sheet named "honor"
    df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="honor")

    # Normalize potential column names
    cols = set(df.columns.astype(str).tolist())

    # Map of accepted source names to canonical names
    col_map = {}
    if "GovernorID" in cols:
        col_map["GovernorID"] = "GovernorID"
    if "GovernorName" in cols:
        col_map["GovernorName"] = "GovernorName"
    elif "Name" in cols:
        col_map["Name"] = "GovernorName"

    if "HonorPoints" in cols:
        col_map["HonorPoints"] = "HonorPoints"
    elif "Honor Points" in cols:
        col_map["Honor Points"] = "HonorPoints"

    required = {"GovernorID", "GovernorName", "HonorPoints"}
    found = set(col_map.values())
    if not required.issubset(found):
        # Helpful error showing found columns to ease debugging
        found_columns = ", ".join(sorted(cols))
        missing = ", ".join(sorted(required - found))
        raise ValueError(
            f"Missing required column(s) for honor import: {missing}. Found columns: {found_columns}"
        )

    # Rename then select canonical columns
    # Build rename map from actual columns to canonical
    rename_map = {}
    for src, canon in col_map.items():
        if src != canon:
            rename_map[src] = canon
    if rename_map:
        df = df.rename(columns=rename_map)

    df = df[["GovernorID", "GovernorName", "HonorPoints"]]

    # Coerce dtypes
    df["GovernorID"] = pd.to_numeric(df["GovernorID"], errors="coerce").astype("Int64")
    df["HonorPoints"] = pd.to_numeric(df["HonorPoints"], errors="coerce").fillna(0).astype("Int64")
    # Ensure name is string and NaN/None -> empty string
    df["GovernorName"] = df["GovernorName"].fillna("").astype(str).str.strip()
    # Drop empties (GovernorID required)
    df = df.dropna(subset=["GovernorID"]).copy()
    return df


def ingest_honor_snapshot(
    xlsx_bytes: bytes, *, source_filename: str, scan_ts_utc: dt.datetime | None = None
) -> tuple[int, int]:
    """
    Returns: (kvk_no, scan_id)

    Behavior:
    - Performs a scan header insert and a bulk insert of player rows within a single transaction.
    - On error, attempts an explicit rollback and re-raises the exception.
    - Emits telemetry events via file_utils.emit_telemetry_event if available (best-effort).
    """
    scan_ts_utc = scan_ts_utc or utcnow()
    # Normalize to aware UTC internally, but strip tzinfo for DB call if the DB expects naive UTC
    scan_ts_param = ensure_aware_utc(scan_ts_utc).replace(tzinfo=None)

    df = parse_honor_xlsx(xlsx_bytes)

    # compute short hash for telemetry
    try:
        file_hash = hashlib.sha256(xlsx_bytes).hexdigest()[:8]
    except Exception:
        file_hash = None

    # telemetry helper (best-effort)
    try:
        from file_utils import emit_telemetry_event  # type: ignore
    except Exception:

        def emit_telemetry_event(payload: dict, **kw):
            return None

    # Start telemetry / structured log
    try:
        emit_telemetry_event(
            {
                "event": "honor_import_start",
                "file": source_filename,
                "rows": len(df),
                "hash": file_hash,
            }
        )
    except Exception:
        pass

    cn = None
    try:
        cn = _conn()
        cur = cn.cursor()
        kvk_no = _current_kvk_no(cur)
        scan_id = _next_scan_id(cur, kvk_no)

        try:
            # Insert scan header
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
                        (
                            kvk_no,
                            scan_id,
                            int(r.GovernorID),
                            r.GovernorName,
                            int(r.HonorPoints or 0),
                        )
                        for r in df.itertuples(index=False)
                    ],
                )

            cn.commit()

        except Exception as db_exc:
            # Attempt an explicit rollback; log any rollback failure but prefer original error for caller
            try:
                cn.rollback()
            except Exception as rb_exc:
                logger.exception("[HONOR] Rollback failed after error: %s", rb_exc)
            logger.exception("[HONOR] Failed to ingest honor snapshot: %s", db_exc)
            try:
                emit_telemetry_event(
                    {
                        "event": "honor_import_fail",
                        "file": source_filename,
                        "error": str(type(db_exc).__name__) + ": " + str(db_exc),
                        "kvk_no": kvk_no,
                        "scan_id": scan_id,
                        "rows": len(df),
                        "hash": file_hash,
                    }
                )
            except Exception:
                pass
            # Re-raise so callers can observe the failure
            raise

    finally:
        try:
            if cn:
                try:
                    cn.close()
                except Exception:
                    pass
        except Exception:
            pass

    logger.info(
        "[HONOR] Ingested KVK_NO=%s ScanID=%s rows=%s from %s hash=%s",
        kvk_no,
        scan_id,
        len(df),
        source_filename,
        file_hash,
    )
    try:
        emit_telemetry_event(
            {
                "event": "honor_import_success",
                "kvk_no": kvk_no,
                "scan_id": scan_id,
                "rows": len(df),
                "file": source_filename,
                "hash": file_hash,
            }
        )
    except Exception:
        pass

    return kvk_no, scan_id
