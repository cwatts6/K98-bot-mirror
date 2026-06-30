"""Data-access workflow for KVK_ALL Full Data imports."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
import time
from typing import Any
import uuid

import pandas as pd
import pyodbc

from file_utils import fetch_one_dict
from kvk.schemas.kvk_all_schema import FULL_DATA_NUMERIC_COLUMN_MAP, SCHEMA_VERSION
from kvk.services.kvk_all_import_service import KvkAllPreparedImport
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)

STAGE_COL_ORDER = [
    "governor_id",
    "name",
    "kingdom",
    "campid",
    "rank",
    "min_kill_points",
    "max_kill_points",
    "min_power_raw",
    "max_power_raw",
    "min_dead",
    "max_dead",
    "min_troop_power",
    "max_troop_power",
    "min_units_healed",
    "max_units_healed",
    "min_kills_iv",
    "max_kills_iv",
    "min_kills_v",
    "max_kills_v",
    "min_max_contribute",
    "max_max_contribute",
    "min_cur_contribute",
    "max_cur_contribute",
    "max_contribute_diff",
    "cur_contribute_diff",
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
    "schema_version",
    "source_sheet_name",
    "source_column_hash",
    "source_column_count",
    "source_row_count",
]

STAGE_PHASE2_REQUIRED_COLUMNS = (
    *FULL_DATA_NUMERIC_COLUMN_MAP.values(),
    "schema_version",
    "source_sheet_name",
    "source_column_hash",
    "source_column_count",
    "source_row_count",
)

STAGE_SCHEMA_COLUMNS_SQL = """
 SELECT c.name
 FROM sys.columns AS c
 WHERE c.object_id = OBJECT_ID(N'KVK.KVK_AllPlayers_Stage')
 """

STAGE_INSERT_COLUMNS = ["IngestToken", *STAGE_COL_ORDER]

STAGE_INSERT_SQL = f"""
 INSERT INTO KVK.KVK_AllPlayers_Stage (
   {", ".join(f"[{column}]" for column in STAGE_INSERT_COLUMNS)}
 ) VALUES ({",".join("?" for _ in STAGE_INSERT_COLUMNS)})
 """

CALL_INGEST_SQL = """
 DECLARE @kvk INT, @scan INT, @rows INT;
 EXEC KVK.sp_KVK_AllPlayers_Ingest
   @IngestToken=?,
   @ScanTimestampUTC=?,
   @SourceFileName=?,
   @FileHash=?,
   @UploaderDiscordID=?,
   @SchemaVersion=?,
   @SourceSheetName=?,
   @SourceColumnHash=?,
   @SourceColumnCount=?,
   @SourceRowCount=?,
   @OutKVK_NO=@kvk OUTPUT,
   @OutScanID=@scan OUTPUT,
   @OutRowCount=@rows OUTPUT;
 SELECT @kvk AS KVK_NO, @scan AS ScanID, @rows AS RowImported;
 """

RECOMPUTE_SQL = "EXEC KVK.sp_KVK_Recompute_Windows @KVK_NO=?;"
NEGATIVE_COUNT_SQL = "SELECT COUNT(*) FROM KVK.KVK_Ingest_Negatives WHERE KVK_NO=? AND ScanID=?;"
DELETE_STAGED_TOKEN_SQL = "DELETE FROM KVK.KVK_AllPlayers_Stage WHERE IngestToken=?;"
INSERT_INGEST_DIAGNOSTIC_SQL = """
 INSERT INTO KVK.KVK_Ingest_Diagnostics
 (
   DiagnosticStatus, DiagnosticType, IngestToken, KVK_NO, ScanID,
   SourceFileName, FileHashSha256, UploaderDiscordID,
   SchemaVersion, SourceSheetName, SourceColumnHash,
   SourceColumnCount, SourceRowCount, StagedRowCount,
   ErrorText, ContextJson
 )
 OUTPUT INSERTED.DiagnosticID
 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
 """


def connect_sql_server(
    *, server: str, database: str, username: str, password: str
) -> pyodbc.Connection:
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )


def enable_fast_executemany(cur: Any) -> bool:
    try:
        cur.fast_executemany = True
        return bool(getattr(cur, "fast_executemany", False))
    except Exception:
        return False


def rows_for_stage(token: str, df: pd.DataFrame) -> list[tuple[Any, ...]]:
    df2 = df.reindex(columns=STAGE_COL_ORDER)
    logger.info("[KVK] DF staged col order: %s", list(df2.columns))

    def _noneify(value: Any) -> Any:
        try:
            import numpy as np

            if isinstance(value, np.floating) and np.isnan(value):
                return None
        except Exception:
            pass
        return None if pd.isna(value) else value

    return [
        (token, *(tuple(_noneify(value) for value in row)))
        for row in df2.itertuples(index=False, name=None)
    ]


def missing_stage_columns(cur: Any, required_columns: tuple[str, ...]) -> list[str]:
    cur.execute(STAGE_SCHEMA_COLUMNS_SQL)
    available_columns = {row[0] for row in cur.fetchall() if row and row[0]}
    return [column for column in required_columns if column not in available_columns]


def write_ingest_diag(token: str, note: str, context: dict[str, Any]) -> str | None:
    try:
        diag_dir = os.path.join(os.getcwd(), "data", "ingest_diagnostics")
        os.makedirs(diag_dir, exist_ok=True)
        filename = os.path.join(diag_dir, f"kvk_ingest_diag_{token}.json")
        payload = {
            "timestamp": dt.datetime.utcnow().isoformat(),
            "note": note,
            "context": context,
        }
        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
        return filename
    except Exception:
        logger.exception("Failed to write ingest diagnostic file")
        return None


def record_ingest_diagnostic(
    con: pyodbc.Connection,
    *,
    status: str,
    diagnostic_type: str,
    ingest_token: str | None = None,
    kvk_no: int | None = None,
    scan_id: int | None = None,
    source_filename: str | None = None,
    file_hash_hex: str | None = None,
    uploader_id: int | None = None,
    schema_metadata: dict[str, Any] | None = None,
    sheet_name: str | None = None,
    staged_rows: int | None = None,
    error_text: str | None = None,
    context: dict[str, Any] | None = None,
) -> int | None:
    """Best-effort durable KVK ingest diagnostic write.

    Phase 8 SQL may not be deployed everywhere at the same time as Python, so
    diagnostic write failures are intentionally logged and suppressed.
    """
    metadata = schema_metadata or {}
    context_payload = json.dumps(context or {}, ensure_ascii=False, default=str)
    try:
        cur = con.cursor()
        cur.execute(
            INSERT_INGEST_DIAGNOSTIC_SQL,
            (
                status,
                diagnostic_type[:64],
                ingest_token,
                kvk_no,
                scan_id,
                source_filename[:255] if source_filename else None,
                file_hash_hex[:64] if file_hash_hex else None,
                int(uploader_id) if uploader_id is not None else None,
                str(metadata.get("schema_version") or SCHEMA_VERSION)[:64],
                str(sheet_name or metadata.get("sheet_name") or "")[:128] or None,
                str(metadata.get("column_hash") or "")[:64] or None,
                metadata.get("column_count"),
                metadata.get("row_count") or metadata.get("source_row_count") or staged_rows,
                staged_rows,
                str(error_text or "")[:1000] or None,
                context_payload,
            ),
        )
        row = cur.fetchone()
        diagnostic_id = int(row[0]) if row and row[0] is not None else None
        logger.info(
            "[KVK] ingest diagnostic recorded id=%s status=%s type=%s token=%s file=%s",
            diagnostic_id,
            status,
            diagnostic_type,
            ingest_token,
            source_filename,
        )
        return diagnostic_id
    except Exception:
        logger.exception(
            "[KVK] failed to record ingest diagnostic status=%s type=%s token=%s file=%s",
            status,
            diagnostic_type,
            ingest_token,
            source_filename,
        )
        return None


def scan_ts_within_kvk_details(con: pyodbc.Connection, scan_ts_naive: dt.datetime) -> bool:
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT TOP(1) 1
            FROM dbo.KVK_Details AS d WITH (READCOMMITTEDLOCK)
            WHERE ? >= d.KVK_REGISTRATION_DATE
              AND ? <= d.KVK_END_DATE
            """,
            (scan_ts_naive, scan_ts_naive),
        )
        return bool(cur.fetchone())
    except Exception:
        logger.exception("[KVK] Pre-check using KVK_Details failed (allowing ingest).")
        return True


def _first_scalar(cursor: Any) -> Any:
    row = fetch_one_dict(cursor)
    if not row:
        return None
    return next(iter(row.values()))


def ingest_prepared_import(
    *,
    con: pyodbc.Connection,
    prepared: KvkAllPreparedImport,
    content: bytes,
    source_filename: str,
    uploader_id: int,
    scan_ts_utc: dt.datetime,
) -> dict[str, Any]:
    df = prepared.dataframe
    staged_rows = prepared.staged_rows
    sheet_name = prepared.sheet_name
    schema_metadata = prepared.schema_metadata

    cur = con.cursor()
    enable_fast_executemany(cur)

    try:
        missing_columns = missing_stage_columns(cur, STAGE_PHASE2_REQUIRED_COLUMNS)
    except Exception:
        logger.exception("[KVK] Stage schema preflight failed; continuing with staged insert.")
    else:
        if missing_columns:
            migration_file = "sql/kvk_all_phase2_full_data_capacity.sql"
            message = (
                "KVK.KVK_AllPlayers_Stage is missing required phase-2 columns: "
                f"{', '.join(missing_columns)}. Apply {migration_file} before "
                "deploying this importer."
            )
            logger.warning("[KVK] %s", message)
            return {
                "success": False,
                "error": message,
                "sheet": sheet_name,
                "schema_version": SCHEMA_VERSION,
                "schema": schema_metadata,
                "missing_stage_columns": missing_columns,
                "required_sql_migration": migration_file,
            }

    token = str(uuid.uuid4())
    stage_rows_started = time.perf_counter()
    stage_rows = rows_for_stage(token, df)
    stage_rows_ms = (time.perf_counter() - stage_rows_started) * 1000.0
    stage_insert_started = time.perf_counter()
    cur.executemany(STAGE_INSERT_SQL, stage_rows)
    con.commit()
    stage_insert_ms = (time.perf_counter() - stage_insert_started) * 1000.0

    logger.info("[KVK] Final stage col order: %s", STAGE_COL_ORDER)
    logger.info("[KVK] DF col order now: %s", list(df.columns))

    file_hash_obj = hashlib.sha256(content)
    file_hash = file_hash_obj.digest()
    file_hash_hex = file_hash_obj.hexdigest()
    scan_ts_utc = ensure_aware_utc(scan_ts_utc)
    scan_ts_naive = scan_ts_utc.replace(tzinfo=None)

    precheck_started = time.perf_counter()
    if not scan_ts_within_kvk_details(con, scan_ts_naive):
        precheck_ms = (time.perf_counter() - precheck_started) * 1000.0
        cleanup_failed = False
        cleanup_error: str | None = None
        try:
            cur.execute(DELETE_STAGED_TOKEN_SQL, token)
            con.commit()
        except Exception as exc:
            cleanup_failed = True
            cleanup_error = f"token={token} {type(exc).__name__}: {exc}"
            logger.exception(
                "[KVK] Failed to clean staged rows for token %s after pre-check failure.", token
            )
        context: dict[str, Any] = {
            "scan_ts_naive": str(scan_ts_naive),
            "source_filename": source_filename,
            "staged_rows": staged_rows,
            "stage_rows_ms": stage_rows_ms,
            "stage_insert_ms": stage_insert_ms,
            "precheck_ms": precheck_ms,
            "schema": schema_metadata,
            "sample_row": {},
            "cleanup_failed": cleanup_failed,
        }
        if cleanup_error:
            context["cleanup_error"] = cleanup_error
        try:
            sample = df.iloc[0].to_dict()
            context["sample_row"] = {key: str(value) for key, value in sample.items()}
        except Exception:
            pass
        diag = write_ingest_diag(token, "scan timestamp outside KVK_Details ranges", context)
        diagnostic_id = record_ingest_diagnostic(
            con,
            status="rejected",
            diagnostic_type="scan_timestamp_outside_kvk_details",
            ingest_token=token,
            source_filename=source_filename,
            file_hash_hex=file_hash_hex,
            uploader_id=uploader_id,
            schema_metadata=schema_metadata,
            sheet_name=sheet_name,
            staged_rows=staged_rows,
            error_text="Scan timestamp outside KVK_Details ranges.",
            context=context,
        )
        if diagnostic_id is not None:
            try:
                con.commit()
            except Exception:
                logger.exception(
                    "[KVK] Failed to commit ingest diagnostic id=%s for pre-check rejection.",
                    diagnostic_id,
                )
        message = (
            f"Scan timestamp {scan_ts_naive!s} does not fall within any configured "
            f"KVK_Details range. Diagnostic: {diag}"
        )
        logger.info("[KVK] Pre-check FAILED for %s: %s", source_filename, message)
        return {
            "success": False,
            "error": message,
            "sheet": sheet_name,
            "offending_scan_ts": str(scan_ts_naive),
            "cleanup_failed": cleanup_failed,
            "cleanup_error": cleanup_error,
            "diagnostic_id": diagnostic_id,
            "staged_rows": staged_rows,
            "stage_rows_ms": stage_rows_ms,
            "stage_insert_ms": stage_insert_ms,
            "precheck_ms": precheck_ms,
        }
    precheck_ms = (time.perf_counter() - precheck_started) * 1000.0

    cur = con.cursor()
    ingest_started = time.perf_counter()
    try:
        cur.execute(
            CALL_INGEST_SQL,
            (
                token,
                scan_ts_naive,
                source_filename,
                file_hash,
                int(uploader_id),
                schema_metadata.get("schema_version") or SCHEMA_VERSION,
                sheet_name,
                schema_metadata.get("column_hash"),
                schema_metadata.get("column_count"),
                staged_rows,
            ),
        )
        rows = cur.fetchall()
        ingest_ms = (time.perf_counter() - ingest_started) * 1000.0
        if not rows:
            raise RuntimeError("Ingest returned no outputs.")
    except Exception as exc:
        ingest_ms = (time.perf_counter() - ingest_started) * 1000.0
        context = {
            "scan_ts_naive": str(scan_ts_naive),
            "source_filename": source_filename,
            "staged_rows": staged_rows,
            "stage_rows_ms": stage_rows_ms,
            "stage_insert_ms": stage_insert_ms,
            "precheck_ms": precheck_ms,
            "ingest_ms": ingest_ms,
            "schema": schema_metadata,
            "stage_retention": "staged rows are retained for inspection until Phase 8 cleanup",
        }
        diagnostic_id = record_ingest_diagnostic(
            con,
            status="failed",
            diagnostic_type="ingest_procedure_failed",
            ingest_token=token,
            source_filename=source_filename,
            file_hash_hex=file_hash_hex,
            uploader_id=uploader_id,
            schema_metadata=schema_metadata,
            sheet_name=sheet_name,
            staged_rows=staged_rows,
            error_text=f"{type(exc).__name__}: {exc}",
            context=context,
        )
        if diagnostic_id is not None:
            try:
                con.commit()
            except Exception:
                logger.exception(
                    "[KVK] Failed to commit ingest diagnostic id=%s after ingest failure.",
                    diagnostic_id,
                )
        try:
            setattr(exc, "kvk_diagnostic_id", diagnostic_id)
            setattr(exc, "kvk_staged_rows", staged_rows)
        except Exception:
            pass
        raise
    kvk_no, scan_id, row_count = rows[0]
    con.commit()

    cur = con.cursor()
    recompute_started = time.perf_counter()
    cur.execute(RECOMPUTE_SQL, kvk_no)
    con.commit()
    recompute_ms = (time.perf_counter() - recompute_started) * 1000.0

    cur = con.cursor()
    negative_count_started = time.perf_counter()
    cur.execute(NEGATIVE_COUNT_SQL, (kvk_no, scan_id))
    negative_value = _first_scalar(cur)
    negative_count_ms = (time.perf_counter() - negative_count_started) * 1000.0
    negatives = int(negative_value) if negative_value is not None else 0

    return {
        "kvk_no": int(kvk_no),
        "scan_id": int(scan_id),
        "row_count": int(row_count),
        "negatives": negatives,
        "staged_rows": staged_rows,
        "stage_rows_ms": stage_rows_ms,
        "stage_insert_ms": stage_insert_ms,
        "precheck_ms": precheck_ms,
        "ingest_ms": ingest_ms,
        "recompute_ms": recompute_ms,
        "negative_count_ms": negative_count_ms,
        "proc_ms": ingest_ms,
        "sheet": sheet_name,
        "schema_version": SCHEMA_VERSION,
        "schema": schema_metadata,
        "success": True,
    }
