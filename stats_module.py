# stats_module.py
"""
Stats processing orchestration (updated offload usage).

This version fixes incorrect usage of the maintenance/process offload helpers.
Key rules:
 - file_utils.run_maintenance_with_isolation and start_callable_offload are for
   running maintenance commands or subprocesses (they expect command/module/function
   identifiers, not direct Python callables).
 - For direct Python callables (functions defined in this process), prefer:
     1) file_utils.run_step(...) (async wrapper that delegates to run_blocking_in_thread)
     2) file_utils.run_blocking_in_thread(...)
     3) asyncio.to_thread(...)
 - Keep the normalization helpers so callers always see a canonical (success, stdout, stderr)
   result regardless of which offload helper returned the value or returned (value, meta).

Apply this file in place of the existing stats_module.py.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil

import pandas as pd
import pyodbc

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

from constants import DOWNLOAD_FOLDER, _conn_trusted
from file_utils import (  # run_step/run_blocking_in_thread imported dynamically later
    emit_telemetry_event,
    fetch_one_dict,
)
from services.fallback_import_schema import (
    INTERIM_AUTO_PARTIAL_SNAPSHOT,
    detect_fallback_source_type,
    normalize_fallback_dataframe,
)
from update_all2_log_manager import execute_update_all2_with_log_management
from utils import utcnow

SOURCE_FILE_2 = os.path.join(DOWNLOAD_FOLDER, "stats.xlsx")
ARCHIVE_DIR_1 = os.path.join(DOWNLOAD_FOLDER, "Databook_Archive")
ARCHIVE_DIR_2 = os.path.join(DOWNLOAD_FOLDER, "Import_Archive")
CSV_FILE_PATH = os.path.join(DOWNLOAD_FOLDER, "stats.csv")
IMPORT_METADATA_FILE_PATH = os.path.join(DOWNLOAD_FOLDER, "stats_import_metadata.json")

TASK_NAME = "UPDATE_ALL2"
WAIT_SECONDS = 15
MAX_RETRIES = 10


def _robust_move(src, dst):
    try:
        shutil.move(src, dst)
    except Exception:
        shutil.copy2(src, dst)
        try:
            os.remove(src)
        except Exception:
            pass


def _read_source_dataframe(source_filepath: str) -> pd.DataFrame:
    ext = os.path.splitext(source_filepath)[1].lower()
    if ext == ".csv":
        return pd.read_csv(source_filepath, encoding="utf-8-sig")

    with pd.ExcelFile(source_filepath, engine="openpyxl") as xf:
        sheet_name = "Data" if "Data" in xf.sheet_names else xf.sheet_names[-1]
        return pd.read_excel(xf, sheet_name=sheet_name, engine="openpyxl")


def _fetch_latest_fallback_snapshot() -> pd.DataFrame:
    """Read the latest full stats snapshot so interim partial imports can overlay safely."""
    query = """
        SELECT
            GovernorID AS [Governor ID],
            GovernorName AS [Name],
            [Power],
            Alliance,
            T1_Kills AS [T1-Kills],
            T2_Kills AS [T2-Kills],
            T3_Kills AS [T3-Kills],
            T4_Kills AS [T4-Kills],
            T5_Kills AS [T5-Kills],
            KillPoints AS [Total Kill Points],
            Deads AS [Dead Troops],
            HealedTroops AS [Healed Troops],
            RSSASSISTANCE AS [Rss Assistance],
            Helps AS [Alliance Helps],
            Rss_Gathered AS [Rss Gathered],
            [City Hall],
            [Troops Power],
            [Tech Power],
            [Building Power],
            [Commander Power],
            Civilization,
            AutarchTimes AS [Autarch Times],
            RangedPoints AS [Ranged Points],
            KvKPlayed AS [KvK Played],
            MostKvKKill AS [Most KvK Kill],
            MostKvKDead AS [Most KvK Dead],
            MostKvKHeal AS [Most KvK Heal],
            Acclaim,
            HighestAcclaim AS [Highest Acclaim],
            AOOJoined AS [AOO Joined],
            AOOWon AS [AOO Won],
            AOOAvgKill AS [AOO Avg Kill],
            AOOAvgDead AS [AOO Avg Dead],
            AOOAvgHeal AS [AOO Avg Heal],
            Conduct AS [Credit]
        FROM dbo.KingdomScanData4 WITH (NOLOCK)
        WHERE SCANORDER = (
            SELECT TOP (1) SCANORDER
            FROM dbo.KingdomScanData4 WITH (NOLOCK)
            ORDER BY SCANORDER DESC
        );
    """
    with _conn_trusted() as conn:
        cur = conn.cursor()
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame.from_records(cur.fetchall(), columns=cols)


def _write_import_metadata(metadata: dict) -> None:
    os.makedirs(os.path.dirname(IMPORT_METADATA_FILE_PATH), exist_ok=True)
    with open(IMPORT_METADATA_FILE_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)


def _load_import_metadata() -> dict:
    try:
        with open(IMPORT_METADATA_FILE_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        logger.debug("[EXCEL] Failed to read import metadata sidecar", exc_info=True)
        return {}


def _record_fallback_import_control(cur, metadata: dict) -> None:
    if not metadata:
        return

    source_type = str(metadata.get("source_type") or "")
    cur.execute("SELECT OBJECT_ID(N'dbo.FallbackImportBatchControl', N'U') AS ObjectId;")
    row = fetch_one_dict(cur)
    if not row or row.get("ObjectId") is None:
        if source_type == INTERIM_AUTO_PARTIAL_SNAPSHOT:
            raise RuntimeError(
                "dbo.FallbackImportBatchControl is required before interim partial imports."
            )
        logger.warning(
            "[EXCEL] FallbackImportBatchControl missing; continuing without SQL metadata."
        )
        return

    cur.execute(
        """
        INSERT INTO dbo.FallbackImportBatchControl
            (SourceType, SourceFilename, ScoreHeader, ColumnsPresentJson, RowsInSource, RowsWritten)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        source_type or None,
        metadata.get("source_filename"),
        metadata.get("score_header"),
        json.dumps(metadata.get("columns_present") or [], ensure_ascii=False),
        int(metadata.get("rows_in_source") or 0),
        int(metadata.get("rows_written") or 0),
    )


# === Excel Processing ===
def process_excel_file(source_filepath):
    if not os.path.isfile(source_filepath):
        logger.error(f"[EXCEL] Source file does not exist: {source_filepath}")
        return False, f"[ERROR] Source file not found: {source_filepath}", None

    try:
        logger.info(f"[EXCEL] Processing {source_filepath}")
        source_df = _read_source_dataframe(source_filepath)
        source_type = detect_fallback_source_type(source_df)
        latest_rows = (
            _fetch_latest_fallback_snapshot()
            if source_type == INTERIM_AUTO_PARTIAL_SNAPSHOT
            else None
        )
        normalized = normalize_fallback_dataframe(
            source_df,
            source_filename=os.path.basename(source_filepath),
            latest_rows=latest_rows,
        )
        df = normalized.dataframe
        metadata = normalized.metadata.as_json_dict()
        _write_import_metadata(metadata)

        credit_non_null = int(pd.to_numeric(df["Credit"], errors="coerce").notna().sum())
        logger.info(
            "[EXCEL] Fallback import source_type=%s score_header=%s rows_in_source=%d rows_written=%d credit_non_null=%d",
            normalized.metadata.source_type,
            normalized.metadata.score_header,
            normalized.metadata.rows_in_source,
            normalized.metadata.rows_written,
            credit_non_null,
        )

        output_path = os.path.join(DOWNLOAD_FOLDER, "stats.xlsx")
        df.to_excel(output_path, index=False, engine="openpyxl")
        if not os.path.isfile(output_path):
            logger.error(f"[EXCEL] to_excel reported no error but file missing: {output_path}")
            return False, f"[ERROR] Failed to write Excel to {output_path}", None
        else:
            logger.info(f"[EXCEL] Wrote Excel -> {output_path}")

        os.makedirs(ARCHIVE_DIR_1, exist_ok=True)
        base_name, ext = os.path.splitext(os.path.basename(source_filepath))
        timestamp_str = utcnow().strftime("%Y-%m-%d_%H%M")
        archive_path = os.path.join(ARCHIVE_DIR_1, f"{base_name}_{timestamp_str}{ext}")
        _robust_move(source_filepath, archive_path)
        logger.info(f"[EXCEL] Archived original -> {archive_path}")

        df.to_csv(CSV_FILE_PATH, index=False, encoding="utf-8-sig")
        if not os.path.isfile(CSV_FILE_PATH):
            logger.error(f"[EXCEL] Failed to write CSV to {CSV_FILE_PATH}")
            return False, f"[ERROR] Failed to write CSV to {CSV_FILE_PATH}", None
        else:
            logger.info(f"[EXCEL] Wrote CSV -> {CSV_FILE_PATH}")

        return True, "[INFO] Excel processed successfully.", None

    except Exception as e:
        logger.exception(f"[EXCEL] Excel processing failed for {source_filepath}: {e}")
        return False, f"[ERROR] Excel processing failed: {e}", None


# === Archive second file ===
def archive_second_file():
    if not os.path.isfile(SOURCE_FILE_2):
        return False, f"[ERROR] Second source file not found: {SOURCE_FILE_2}", None

    try:
        os.makedirs(ARCHIVE_DIR_2, exist_ok=True)
        base_name, ext = os.path.splitext(os.path.basename(SOURCE_FILE_2))
        timestamp_str = utcnow().strftime("%Y-%m-%d_%H%M")
        archive_path = os.path.join(ARCHIVE_DIR_2, f"{base_name}_{timestamp_str}{ext}")
        _robust_move(SOURCE_FILE_2, archive_path)
        return True, "[INFO] Second file archived.", None
    except Exception as e:
        logger.exception("Archiving second file failed: %s", e)
        return False, f"[ERROR] Archiving second file failed: {e}", None


# ---- Helpers to handle offload return shapes ---------------------------------
def _unwrap_offload_result(res):
    """
    Offload helpers sometimes return (value, meta). Normalize by returning value.
    If res is a 2-tuple where the second element is a dict (meta), return the first element.
    Else return res as-is.
    """
    try:
        if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
            return res[0]
    except Exception:
        pass
    return res


def _normalize_step_result(raw) -> tuple[bool, str, str]:
    """
    Normalize a step result into (success: bool, stdout: str, stderr: str).
    """
    try:
        r = _unwrap_offload_result(raw)
        if isinstance(r, (tuple, list)):
            if len(r) == 3:
                success, stdout, stderr = r
                return bool(success), str(stdout or ""), str(stderr or "")
            if len(r) == 2:
                success, stdout = r
                return bool(success), str(stdout or ""), ""
            if len(r) == 1:
                return bool(r[0]), "", ""
        if isinstance(r, (bool, int)):
            return bool(r), "", ""
        if isinstance(r, dict):
            s = bool(r.get("success", True))
            message = r.get("message") or r.get("stdout") or r.get("log") or ""
            err = r.get("error") or r.get("stderr") or ""
            return s, str(message), str(err)
        return False, str(r or ""), ""
    except Exception:
        return False, "", "NormalizationError"


# === Helper: offload callables properly ===
async def _offload_callable_py(fn, *args, name: str | None = None, meta: dict | None = None):
    """
    Offload a direct Python callable using run_step -> run_blocking_in_thread -> asyncio.to_thread.
    Returns the callable result (not metadata).
    """
    try:
        from file_utils import run_blocking_in_thread, run_step  # type: ignore
    except Exception:
        run_step = None
        run_blocking_in_thread = None

    meta = meta or {}
    if run_step is not None:
        try:
            return await run_step(fn, *args, name=name, meta=meta)
        except Exception:
            # fall through to thread fallback
            pass

    if run_blocking_in_thread is not None:
        try:
            return await run_blocking_in_thread(fn, *args, name=name, meta=meta)
        except Exception:
            pass

    # final fallback
    return await asyncio.to_thread(fn, *args)


# === Execute SQL Stored Procedure and Wait (NON-BLOCKING) ===
async def run_sql_procedure(rank=None, seed=None, timeout_seconds: int = 600):
    logger.info(f"[SQL_PROC] Received Rank: {rank}, Seed: {seed}")

    def _proc_and_get_expected_counter() -> int:
        with _conn_trusted() as conn:
            conn.autocommit = False
            cur = conn.cursor()
            try:
                cur.timeout = max(1, int(timeout_seconds) - 5)
            except Exception:
                pass

            cur.execute(
                "SELECT ISNULL(MAX(LastRunCounter), 0) AS LastRunCounter "
                "FROM SP_TaskStatus WHERE TaskName = ?",
                TASK_NAME,
            )
            row = fetch_one_dict(cur)
            original_counter = int(row.get("LastRunCounter", 0) if row else 0) or 0
            expected_counter = original_counter + 1
            logger.info(f"[SQL_PROC] Executing procedure with expected counter: {expected_counter}")

            try:
                # ⭐ DEFENSE LAYER 1: Wrap UPDATE_ALL2 with log management ⭐
                logger.info("[SQL_PROC] Executing UPDATE_ALL2 with log management wrapper...")
                _record_fallback_import_control(cur, _load_import_metadata())

                result = execute_update_all2_with_log_management(cur, param1=rank, param2=seed)

                if not result["success"]:
                    raise RuntimeError(f"UPDATE_ALL2 failed: {result.get('error', 'unknown')}")

                # Log telemetry
                trigger_results = result.get("trigger_results") or {}
                logger.info(
                    "[SQL_PROC] UPDATE_ALL2 completed: log_before=%.2f%%, log_after=%.2f%%, "
                    "triggers_found=%d, backups_triggered=%d",
                    result.get("log_before") or 0,
                    result.get("log_after") or 0,
                    trigger_results.get("triggers_found", 0),
                    trigger_results.get("backups_triggered", 0),
                )

                emit_telemetry_event(
                    {
                        "event": "update_all2_wrapper",
                        "status": "success",
                        "log_before": result.get("log_before"),
                        "log_after": result.get("log_after"),
                        "backups_triggered": trigger_results.get("backups_triggered", 0),
                        "triggers_processed": trigger_results.get("triggers_processed", 0),
                    }
                )

            except pyodbc.ProgrammingError as e:
                msg = str(e).lower()
                if "bulk load" in msg or "4834" in msg:
                    raise PermissionError(
                        "SQL login does not have permission to perform bulk load operations (error 4834). "
                        "Grant ADMINISTER BULK OPERATIONS or add the login to the 'bulkadmin' server role."
                    ) from e
                raise
            except Exception as e:
                logger.exception("[SQL_PROC] UPDATE_ALL2 wrapper failed")
                emit_telemetry_event(
                    {
                        "event": "update_all2_wrapper",
                        "status": "failed",
                        "error_type": type(e).__name__,
                        "error": str(e)[:500],
                    }
                )
                raise

            # Consume remaining result sets
            for _ in range(64):
                try:
                    try:
                        _ = cur.fetchall()
                    except pyodbc.ProgrammingError:
                        pass
                    more = cur.nextset()
                except pyodbc.ProgrammingError:
                    break
                if not more:
                    break

            conn.commit()
            return expected_counter

    # Offload the blocking DB work via python-callable offload helper
    try:
        expected_counter = await _offload_callable_py(
            _proc_and_get_expected_counter, name="sql_proc_exec", meta={"task": TASK_NAME}
        )
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception("SQL procedure execution failed")
        emit_telemetry_event(
            {
                "event": "sql_proc",
                "status": "failed",
                "task_name": TASK_NAME,
                "orphaned_offload_possible": False,
            }
        )
        return False, f"[ERROR] SQL execution failed: {e}", None

    # expected_counter may be wrapped by some helpers; ensure int
    try:
        expected_counter = int(_unwrap_offload_result(expected_counter))
    except Exception:
        logger.warning(
            "[SQL_PROC] Unexpected expected_counter shape; normalized to 0: %r", expected_counter
        )
        expected_counter = 0

    # Poll status loop — offload reads similarly
    for attempt in range(MAX_RETRIES):
        logger.info(f"[WAIT] Attempt {attempt + 1}: Waiting for SQL counter to increment...")
        await asyncio.sleep(WAIT_SECONDS)

        def _read_status():
            with _conn_trusted() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT "
                    "MAX(LastRunCounter) AS LastRunCounter, "
                    "MAX(LastRunTime)    AS LastRunTime, "
                    "MAX(DurationSeconds) AS DurationSeconds "
                    "FROM SP_TaskStatus WHERE TaskName = ?",
                    TASK_NAME,
                )
                return fetch_one_dict(cur)

        try:
            row = await _offload_callable_py(
                _read_status, name="sql_read_status", meta={"task": TASK_NAME}
            )
        except Exception:
            row = None

        if isinstance(row, dict):
            current_counter = int(row.get("LastRunCounter", 0))
        else:
            current_counter = 0

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "[WAIT] Observed counter=%s (expect >= %s) • last_run=%s • duration=%s",
                current_counter,
                expected_counter,
                row.get("LastRunTime") if isinstance(row, dict) else None,
                row.get("DurationSeconds") if isinstance(row, dict) else None,
            )

        if current_counter >= expected_counter:
            duration = row.get("DurationSeconds", "n/a") if isinstance(row, dict) else "n/a"
            return True, f"[SUCCESS] Counter reached {current_counter}. Duration: {duration}s", None

    return False, "[TIMEOUT] Procedure did not complete in time.", None


# === Combined Runner (make steps non-blocking) ===
async def run_stats_copy_archive(
    rank=None, seed=None, source_filename=None, send_step_embed=None
) -> tuple[bool, str, dict]:
    steps = []

    excel_title = "Processing Excel File"
    archive2_title = "Archiving Secondary File"
    sql_title = "Running SQL Procedure"

    excel_included = bool(source_filename)
    if excel_included:

        def _resolve_source_path():
            return (
                source_filename
                if os.path.isabs(source_filename)
                else os.path.join(DOWNLOAD_FOLDER, source_filename)
            )

        async def _run_excel_async():
            # Offload as a python callable (not a subprocess)
            try:
                res = await _offload_callable_py(
                    process_excel_file,
                    _resolve_source_path(),
                    name="process_excel_file",
                    meta={"source": _resolve_source_path()},
                )
                return res
            except Exception as e:
                logger.exception("process_excel_file offload failed: %s", e)
                return False, f"Exception: {e}", None

        steps.append((excel_title, _run_excel_async))

    async def _archive2_guard_async():
        if not excel_included:
            return True, "[INFO] Skipped secondary archive (Excel step not run).", None

        try:
            res = await _offload_callable_py(
                archive_second_file, name="archive_second_file", meta={"source": SOURCE_FILE_2}
            )
            return res
        except Exception as e:
            logger.exception("archive_second_file offload failed: %s", e)
            return False, f"Exception: {e}", None

    steps += [
        (archive2_title, _archive2_guard_async),
        (sql_title, lambda: run_sql_procedure(rank, seed, timeout_seconds=600)),
    ]

    all_success = True
    combined_log_parts = []
    step_results = {}

    for title, func in steps:
        if send_step_embed:
            await send_step_embed(title, "⏳ Running...")

        try:
            result = func()
            if asyncio.iscoroutine(result):
                raw = await result
            else:
                raw = result
            success, stdout, stderr = _normalize_step_result(raw)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            success, stdout, stderr = False, "", str(e)

        logger.info("[STEP] %s -> %s", title, "SUCCESS" if success else "FAIL")
        key = None
        if title == excel_title:
            key = "excel"
        elif title == archive2_title:
            key = "archive"
        elif title == sql_title:
            key = "sql"

        if key:
            step_results[key] = bool(success)

        status_icon = "✅" if success else "❌"
        message = stdout if success else stderr
        combined_log_parts.append(f"{status_icon} **{title}**\n{message}")

        if send_step_embed:
            await send_step_embed(title, f"{status_icon} {message}")

        if not success:
            all_success = False

        await asyncio.sleep(0.01)

    combined_log = "\n\n".join(combined_log_parts)
    return (
        bool(all_success),
        str(combined_log or ""),
        {
            "excel": bool(step_results.get("excel")),
            "archive": bool(step_results.get("archive")),
            "sql": bool(step_results.get("sql")),
        },
    )
