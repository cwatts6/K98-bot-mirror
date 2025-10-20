# stats_module.py
import asyncio
import logging

logger = logging.getLogger(__name__)

import os
import shutil

import pandas as pd
import pyodbc

from constants import DOWNLOAD_FOLDER, _conn
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
        # Surface the real reason in logs, with stacktrace
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
        # Entire ODBC/proc work happens off the event loop.
        with _conn() as conn:
            conn.autocommit = False  # proc manages its own tx; we still commit.
            cur = conn.cursor()
            # Ensure the server-side call won’t run forever in the worker thread
            try:
                cur.timeout = max(1, int(timeout_seconds) - 5)  # seconds
            except Exception:
                pass

            # Read current counter
            cur.execute(
                "SELECT ISNULL(MAX(LastRunCounter), 0) FROM SP_TaskStatus WHERE TaskName = ?",
                TASK_NAME,
            )
            original_counter = cur.fetchone()[0] or 0
            expected_counter = int(original_counter) + 1
            logger.info(f"[SQL_PROC] Executing procedure with expected counter: {expected_counter}")

            # Call the proc
            cur.execute("EXEC dbo.UPDATE_ALL2 @param1 = ?, @param2 = ?", rank, seed)

            # Drain resultsets/messages so the batch fully completes serverside
            # (With SET NOCOUNT ON in the proc, this should be quick.)
            for _ in range(64):  # hard ceiling to avoid pathological churn
                try:
                    try:
                        _ = cur.fetchall()
                    except pyodbc.ProgrammingError:
                        pass  # "No results" is fine
                    more = cur.nextset()
                except pyodbc.ProgrammingError:
                    break
                if not more:
                    break

            conn.commit()
            return expected_counter

    try:
        # Run the blocking proc in a thread with an overall timeout
        expected_counter = await asyncio.wait_for(
            asyncio.to_thread(_proc_and_get_expected_counter), timeout=timeout_seconds
        )
    except TimeoutError:
        logger.exception("[SQL_PROC] Procedure step timed out after %ss", timeout_seconds)
        return False, f"[TIMEOUT] Procedure step exceeded {timeout_seconds}s.", None
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception("SQL procedure execution failed")
        return False, f"[ERROR] SQL execution failed: {e}", None

    # Counter poll loop (also offload the small ODBC hit, just to be pure async)
    for attempt in range(MAX_RETRIES):
        logger.info(f"[WAIT] Attempt {attempt + 1}: Waiting for SQL counter to increment...")
        await asyncio.sleep(WAIT_SECONDS)

        def _read_status():
            with _conn() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT MAX(LastRunCounter), MAX(LastRunTime), MAX(DurationSeconds) "
                    "FROM SP_TaskStatus WHERE TaskName = ?",
                    TASK_NAME,
                )
                return cur.fetchone()

        try:
            row = await asyncio.to_thread(_read_status)
        except Exception:
            row = None

        current_counter = int(row[0] if row and row[0] is not None else 0)
        if current_counter >= expected_counter:
            duration = row[2] if row and row[2] is not None else "n/a"
            return True, f"[SUCCESS] Counter reached {current_counter}. Duration: {duration}s", None

    return False, "[TIMEOUT] Procedure did not complete in time.", None


# === Combined Runner (make steps non-blocking) ===
async def run_stats_copy_archive(rank=None, seed=None, source_filename=None, send_step_embed=None):
    async def run_sql_step():
        # Optional: tune timeout via env/constant if desired
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
            # Offload heavy pandas/openpyxl to a worker thread
            return await asyncio.to_thread(process_excel_file, _resolve_source_path())

        steps.append((excel_title, _run_excel_async))

    async def _archive2_guard_async():
        if not excel_included:
            return True, "[INFO] Skipped secondary archive (Excel step not run).", None
        # Offload the file move/copy as well
        return await asyncio.to_thread(archive_second_file)

    steps += [
        (archive2_title, _archive2_guard_async),
        (sql_title, run_sql_step),
    ]

    all_success = True
    combined_log = []
    step_results = {}

    for title, func in steps:
        if send_step_embed:
            await send_step_embed(title, "⏳ Running...")

        try:
            result = func()
            if asyncio.iscoroutine(result):
                success, stdout, stderr = await result
            else:
                # If any step accidentally returns a tuple directly
                success, stdout, stderr = result
        except asyncio.CancelledError:
            raise
        except Exception as e:
            success, stdout, stderr = False, "", str(e)

        logger.info("[STEP] %s -> %s", title, "SUCCESS" if success else "FAIL")
        step_results[title] = success

        status_icon = "✅" if success else "❌"
        message = stdout if success else stderr
        combined_log.append(f"{status_icon} **{title}**\n{message}")

        if send_step_embed:
            await send_step_embed(title, f"{status_icon} {message}")

        if not success:
            all_success = False

        # Tiny yield between steps to keep the loop snappy
        await asyncio.sleep(0.01)

    return (
        all_success,
        "\n\n".join(combined_log),
        {
            "excel": step_results.get(excel_title),
            "archive": step_results.get(archive2_title),
            "sql": step_results.get(sql_title),
        },
    )
