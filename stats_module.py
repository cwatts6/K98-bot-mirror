# stats_module.py
"""
stats_module.py

Provides routines to:
 - process an optional Excel stats file,
 - archive helper files,
 - run the main DB stored procedure and wait for completion.

Important contract (STANDARDIZED):
  async def run_stats_copy_archive(rank=None, seed=None, source_filename=None, send_step_embed=None)
  MUST return a tuple with the exact schema:

    (success: bool, combined_log: str, steps: dict[str, bool])

  Where:
    - success: True if all required steps succeeded (caller may still inspect steps).
    - combined_log: human-readable combined output/log for the run (string).
    - steps: mapping of step name (canonical keys: "excel", "archive", "sql") -> bool success.

This stable contract allows callers (e.g., processing_pipeline.execute_processing_pipeline)
to rely on a single return signature and avoid defensive normalization logic.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

import json
import os
import shutil

import pandas as pd
import pyodbc

from constants import DOWNLOAD_FOLDER, _conn_trusted
from file_utils import fetch_one_dict
from utils import utcnow

SOURCE_FILE_2 = os.path.join(DOWNLOAD_FOLDER, "stats.xlsx")
ARCHIVE_DIR_1 = os.path.join(DOWNLOAD_FOLDER, "Databook_Archive")
ARCHIVE_DIR_2 = os.path.join(DOWNLOAD_FOLDER, "Import_Archive")
CSV_FILE_PATH = os.path.join(DOWNLOAD_FOLDER, "stats.csv")

TASK_NAME = "UPDATE_ALL2"
WAIT_SECONDS = 15
MAX_RETRIES = 10


try:
    import openpyxl  # noqa: F401
except Exception as e:
    logger.critical("[DEPENDENCY] openpyxl not available: %s", e)


def _robust_move(src, dst):
    try:
        shutil.move(src, dst)
    except Exception:
        shutil.copy2(src, dst)
        try:
            os.remove(src)
        except Exception:
            pass


# === Excel Processing ===
def process_excel_file(source_filepath):
    if not os.path.isfile(source_filepath):
        logger.error(f"[EXCEL] Source file does not exist: {source_filepath}")
        return False, f"[ERROR] Source file not found: {source_filepath}", None

    try:
        logger.info(f"[EXCEL] Processing {source_filepath}")
        with pd.ExcelFile(source_filepath, engine="openpyxl") as xf:
            latest_sheet = xf.sheet_names[-1]
            df = pd.read_excel(xf, sheet_name=latest_sheet, engine="openpyxl")

        if "updated_on" not in df.columns:
            timestamp = utcnow().strftime("%d%b%y-%Hh%Mm")
            df["updated_on"] = timestamp

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
        return False, f"[ERROR] Archiving second file failed: {e}", None


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

            # Read current counter (by name)
            cur.execute(
                "SELECT ISNULL(MAX(LastRunCounter), 0) AS LastRunCounter "
                "FROM SP_TaskStatus WHERE TaskName = ?",
                TASK_NAME,
            )
            row = fetch_one_dict(cur)
            original_counter = int(row.get("LastRunCounter", 0) if row else 0) or 0
            expected_counter = original_counter + 1
            logger.info(f"[SQL_PROC] Executing procedure with expected counter: {expected_counter}")

            # Call the proc
            try:
                cur.execute("EXEC dbo.UPDATE_ALL2 @param1 = ?, @param2 = ?", rank, seed)
            except pyodbc.ProgrammingError as e:
                msg = str(e).lower()
                if "bulk load" in msg or "4834" in msg:
                    raise PermissionError(
                        "SQL login does not have permission to perform bulk load operations (error 4834). "
                        "Grant ADMINISTER BULK OPERATIONS or add the login to the 'bulkadmin' server role."
                    ) from e
                raise

            # Drain resultsets/messages so the batch fully completes serverside
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

    try:
        # Local import to avoid circular import at module import time
        from file_utils import run_blocking_in_thread
    except Exception:
        run_blocking_in_thread = None

    try:
        if run_blocking_in_thread is not None:
            expected_counter = await asyncio.wait_for(
                run_blocking_in_thread(
                    _proc_and_get_expected_counter, name="sql_proc_exec", meta={"task": TASK_NAME}
                ),
                timeout=timeout_seconds,
            )
        else:
            expected_counter = await asyncio.wait_for(
                asyncio.to_thread(_proc_and_get_expected_counter), timeout=timeout_seconds
            )
    except TimeoutError:
        logger.exception("[SQL_PROC] Procedure step timed out after %ss", timeout_seconds)
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "sql_proc",
                    "status": "timeout",
                    "task_name": TASK_NAME,
                    "orphaned_offload_possible": True,
                }
            )
        )
        return False, f"[TIMEOUT] Procedure step exceeded {timeout_seconds}s.", None
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception("SQL procedure execution failed")
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "sql_proc",
                    "status": "failed",
                    "task_name": TASK_NAME,
                    "orphaned_offload_possible": False,
                }
            )
        )
        return False, f"[ERROR] SQL execution failed: {e}", None

    # Counter poll loop (read by name; alias columns)
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
            if run_blocking_in_thread is not None:
                # Provide task context in meta so telemetry includes it
                row = await run_blocking_in_thread(
                    _read_status, name="sql_read_status", meta={"task": TASK_NAME}
                )
            else:
                row = await asyncio.to_thread(_read_status)
        except Exception:
            row = None

        current_counter = int(row.get("LastRunCounter", 0)) if isinstance(row, dict) else 0
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
    """
    Orchestrate the steps:
      - optional Excel processing (process_excel_file)
      - optional secondary archive (archive_second_file)
      - SQL procedure (run_sql_procedure)

    Return (success, combined_log, steps) where steps is a dict with keys:
      - "excel": bool
      - "archive": bool
      - "sql": bool

    The function is async and may offload blocking work to file_utils.run_blocking_in_thread.
    """

    async def run_sql_step():
        return await run_sql_procedure(rank, seed, timeout_seconds=600)

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
            try:
                from file_utils import run_blocking_in_thread
            except Exception:
                run_blocking_in_thread = None

            if run_blocking_in_thread is not None:
                return await run_blocking_in_thread(
                    process_excel_file,
                    _resolve_source_path(),
                    name="process_excel_file",
                    meta={"source": _resolve_source_path()},
                )
            else:
                return await asyncio.to_thread(process_excel_file, _resolve_source_path())

        steps.append((excel_title, _run_excel_async))

    async def _archive2_guard_async():
        if not excel_included:
            return True, "[INFO] Skipped secondary archive (Excel step not run).", None
        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        if run_blocking_in_thread is not None:
            # include the source path in telemetry meta
            return await run_blocking_in_thread(
                archive_second_file, name="archive_second_file", meta={"source": SOURCE_FILE_2}
            )
        return await asyncio.to_thread(archive_second_file)

    steps += [
        (archive2_title, _archive2_guard_async),
        (sql_title, run_sql_step),
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
                success, stdout, stderr = await result
            else:
                success, stdout, stderr = result
        except asyncio.CancelledError:
            raise
        except Exception as e:
            success, stdout, stderr = False, "", str(e)

        logger.info("[STEP] %s -> %s", title, "SUCCESS" if success else "FAIL")
        # Map our well-known titles to canonical keys
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
    # Ensure canonical return shape
    return (
        bool(all_success),
        str(combined_log or ""),
        {
            "excel": bool(step_results.get("excel")),
            "archive": bool(step_results.get("archive")),
            "sql": bool(step_results.get("sql")),
        },
    )
