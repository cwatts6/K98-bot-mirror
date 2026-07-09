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
import time

import pyodbc

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

from constants import DOWNLOAD_FOLDER, _conn_trusted
from file_utils import (  # run_step/run_blocking_in_thread imported dynamically later
    emit_telemetry_event,
)
from services.fallback_import_service import (
    FallbackImportPaths,
    archive_secondary_file,
    delete_import_metadata,
    load_import_metadata,
    process_fallback_source_file,
    read_source_dataframe,
    robust_move,
)
import services.import_audit_service as import_audit_service
from stats.dal.fallback_import_dal import (
    fetch_latest_fallback_snapshot,
    fetch_update_all2_last_counter,
    fetch_update_all2_status,
    record_fallback_import_control,
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

FALLBACK_AUDIT_IMPORT_KIND = "fallback"
FALLBACK_AUDIT_PHASES = {
    "excel": "fallback_file_prepare",
    "archive": "fallback_secondary_archive",
    "sql": "fallback_update_all2",
}


def _fallback_import_paths() -> FallbackImportPaths:
    return FallbackImportPaths(
        download_folder=DOWNLOAD_FOLDER,
        source_file_2=SOURCE_FILE_2,
        archive_dir_1=ARCHIVE_DIR_1,
        archive_dir_2=ARCHIVE_DIR_2,
        csv_file_path=CSV_FILE_PATH,
        import_metadata_file_path=IMPORT_METADATA_FILE_PATH,
    )


def _robust_move(src, dst):
    return robust_move(src, dst)


def _read_source_dataframe(source_filepath: str):
    return read_source_dataframe(source_filepath)


def _fetch_latest_fallback_snapshot():
    return fetch_latest_fallback_snapshot(_conn_trusted)


def _write_import_metadata(metadata: dict) -> None:
    from services.fallback_import_service import write_import_metadata

    write_import_metadata(metadata, IMPORT_METADATA_FILE_PATH)


def _load_import_metadata() -> dict:
    return load_import_metadata(IMPORT_METADATA_FILE_PATH)


def _delete_import_metadata() -> None:
    delete_import_metadata(IMPORT_METADATA_FILE_PATH)


def _record_fallback_import_control(cur, metadata: dict) -> int | None:
    return record_fallback_import_control(cur, metadata)


def _audit_timestamp_utc():
    return utcnow().replace(tzinfo=None)


def _metadata_int(metadata: dict, key: str) -> int | None:
    try:
        value = metadata.get(key)
        if value is None or value == "":
            return None
        return int(value)
    except Exception:
        return None


def _fallback_audit_source_type(source_filename: str | None) -> str:
    return "fallback_source_file" if source_filename else "fallback_sql_only"


def _fallback_audit_source_filename(source_filename: str | None) -> str | None:
    if not source_filename:
        return None
    try:
        return os.path.basename(source_filename)
    except Exception:
        return source_filename


def _fallback_control_external_id(metadata: dict) -> str | None:
    try:
        value = metadata.get("_fallback_import_control_id")
        return str(value) if value is not None and value != "" else None
    except Exception:
        return None


def _step_display_message(success: bool, stdout: str, stderr: str) -> str:
    return stdout if success else (stderr or stdout)


def _details_from_update_all2_phase(row: dict) -> dict:
    details = {
        "source": "dbo.UPDATE_ALL2",
        "sql_phase": row.get("phase_name"),
    }
    raw_details = row.get("details_json")
    if raw_details:
        try:
            details["sql_details"] = json.loads(raw_details)
        except Exception:
            details["sql_details"] = raw_details
    return details


# === Excel Processing ===
def process_excel_file(source_filepath):
    return process_fallback_source_file(
        source_filepath,
        paths=_fallback_import_paths(),
        fetch_latest_snapshot=_fetch_latest_fallback_snapshot,
        read_dataframe=_read_source_dataframe,
        move_file=_robust_move,
    )


# === Archive second file ===
def archive_second_file():
    return archive_secondary_file(paths=_fallback_import_paths(), move_file=_robust_move)


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
async def run_sql_procedure(
    rank=None, seed=None, timeout_seconds: int = 600, import_metadata: dict | None = None
):
    logger.info(f"[SQL_PROC] Received Rank: {rank}, Seed: {seed}")

    def _proc_and_get_expected_counter() -> int:
        with _conn_trusted() as conn:
            conn.autocommit = False
            cur = conn.cursor()
            try:
                cur.timeout = max(1, int(timeout_seconds) - 5)
            except Exception:
                pass

            original_counter = fetch_update_all2_last_counter(cur, TASK_NAME)
            expected_counter = original_counter + 1
            logger.info(f"[SQL_PROC] Executing procedure with expected counter: {expected_counter}")

            try:
                # ⭐ DEFENSE LAYER 1: Wrap UPDATE_ALL2 with log management ⭐
                logger.info("[SQL_PROC] Executing UPDATE_ALL2 with log management wrapper...")
                fallback_control_id = _record_fallback_import_control(cur, import_metadata or {})

                result = execute_update_all2_with_log_management(cur, param1=rank, param2=seed)

                if not result["success"]:
                    raise RuntimeError(f"UPDATE_ALL2 failed: {result.get('error', 'unknown')}")

                if isinstance(import_metadata, dict):
                    import_metadata["_update_all2_phase_results"] = (
                        result.get("phase_results") or []
                    )

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
                        "internal_phase_count": len(result.get("phase_results") or []),
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
            if fallback_control_id is not None and isinstance(import_metadata, dict):
                import_metadata["_fallback_import_control_id"] = fallback_control_id
            if import_metadata:
                _delete_import_metadata()
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
            return fetch_update_all2_status(_conn_trusted, TASK_NAME)

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
    current_import_metadata: dict = {}

    excel_included = bool(source_filename)
    audit_ref = _unwrap_offload_result(
        await _offload_callable_py(
            lambda: import_audit_service.start_batch_best_effort(
                import_kind=FALLBACK_AUDIT_IMPORT_KIND,
                source_type=_fallback_audit_source_type(source_filename),
                source_filename=_fallback_audit_source_filename(source_filename),
                details={
                    "entry_point": "run_stats_copy_archive",
                    "rank": rank,
                    "seed": seed,
                    "source_filename": source_filename,
                    "excel_included": excel_included,
                },
            ),
            name="import_audit_start",
            meta={"import_kind": FALLBACK_AUDIT_IMPORT_KIND},
        ),
    )

    async def _record_audit_phase(
        *,
        key: str | None,
        title: str,
        success: bool,
        stdout: str,
        stderr: str,
        started_at_utc,
        completed_at_utc,
        duration_ms: int,
    ) -> None:
        if not key or not audit_ref:
            return
        phase_name = FALLBACK_AUDIT_PHASES.get(key)
        if not phase_name:
            return
        rows_in = (
            _metadata_int(current_import_metadata, "rows_in_source") if key == "excel" else None
        )
        rows_out = (
            _metadata_int(current_import_metadata, "rows_written")
            if key in {"excel", "sql"}
            else None
        )
        await _offload_callable_py(
            lambda: import_audit_service.record_phase_best_effort(
                audit_ref,
                phase_name=phase_name,
                phase_status="completed" if success else "failed",
                started_at_utc=started_at_utc,
                completed_at_utc=completed_at_utc,
                rows_in=rows_in,
                rows_out=rows_out,
                duration_ms=duration_ms,
                error_type=None if success else "ImportStepFailed",
                error_text=None if success else (stderr or stdout),
                details={
                    "step": key,
                    "title": title,
                    "message": _step_display_message(success, stdout, stderr),
                    "metadata": current_import_metadata if current_import_metadata else None,
                },
                set_batch_status="staged" if key == "excel" and success else None,
            ),
            name="import_audit_phase",
            meta={"import_kind": FALLBACK_AUDIT_IMPORT_KIND, "phase": phase_name},
        )

    async def _record_update_all2_subphases() -> None:
        if not audit_ref:
            return
        phase_rows = current_import_metadata.get("_update_all2_phase_results") or []
        if not isinstance(phase_rows, list):
            return

        for row in phase_rows:
            if not isinstance(row, dict):
                continue
            phase_name = row.get("phase_name")
            if not phase_name:
                continue
            await _offload_callable_py(
                lambda row=row, phase_name=phase_name: import_audit_service.record_phase_best_effort(
                    audit_ref,
                    phase_name=str(phase_name),
                    phase_status=str(row.get("phase_status") or "completed"),
                    started_at_utc=row.get("started_at_utc"),
                    completed_at_utc=row.get("completed_at_utc"),
                    rows_in=row.get("rows_in"),
                    rows_out=row.get("rows_out"),
                    duration_ms=row.get("duration_ms"),
                    error_type=row.get("error_type"),
                    error_text=row.get("error_text"),
                    details=_details_from_update_all2_phase(row),
                ),
                name="import_audit_update_all2_phase",
                meta={"import_kind": FALLBACK_AUDIT_IMPORT_KIND, "phase": phase_name},
            )

    if source_filename:
        source_filename_for_import = source_filename

        def _resolve_source_path() -> str:
            return (
                source_filename_for_import
                if os.path.isabs(source_filename_for_import)
                else os.path.join(DOWNLOAD_FOLDER, source_filename_for_import)
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
        (
            sql_title,
            lambda: run_sql_procedure(
                rank, seed, timeout_seconds=600, import_metadata=current_import_metadata
            ),
        ),
    ]

    all_success = True
    combined_log_parts = []
    step_results = {}

    async def _fail_audit_batch_for_exit(
        *,
        status: str,
        error_type: str,
        error_text: str,
    ) -> None:
        fallback_control_id = _fallback_control_external_id(current_import_metadata)
        await _offload_callable_py(
            lambda: import_audit_service.fail_batch_best_effort(
                audit_ref,
                status=status,
                error_type=error_type,
                error_text=error_text,
                rows_in_source=_metadata_int(current_import_metadata, "rows_in_source"),
                external_batch_table=(
                    "dbo.FallbackImportBatchControl" if fallback_control_id else None
                ),
                external_batch_id=fallback_control_id,
                details={
                    "steps": dict(step_results),
                    "metadata": current_import_metadata if current_import_metadata else None,
                },
            ),
            name="import_audit_exit",
            meta={"import_kind": FALLBACK_AUDIT_IMPORT_KIND, "status": status},
        )

    try:
        for title, func in steps:
            if send_step_embed:
                await send_step_embed(title, "⏳ Running...")

            step_started_at_utc = _audit_timestamp_utc()
            step_started_monotonic = time.monotonic()
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

            step_completed_at_utc = _audit_timestamp_utc()
            duration_ms = int((time.monotonic() - step_started_monotonic) * 1000)
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
                if key == "excel" and success:
                    current_import_metadata = _load_import_metadata()

            await _record_audit_phase(
                key=key,
                title=title,
                success=success,
                stdout=stdout,
                stderr=stderr,
                started_at_utc=step_started_at_utc,
                completed_at_utc=step_completed_at_utc,
                duration_ms=duration_ms,
            )
            if key == "sql":
                await _record_update_all2_subphases()

            status_icon = "✅" if success else "❌"
            message = _step_display_message(success, stdout, stderr)
            combined_log_parts.append(f"{status_icon} **{title}**\n{message}")

            if send_step_embed:
                await send_step_embed(title, f"{status_icon} {message}")

            if not success:
                all_success = False

            await asyncio.sleep(0.01)

        combined_log = "\n\n".join(combined_log_parts)
        rows_written = _metadata_int(current_import_metadata, "rows_written")
        rows_in_source = _metadata_int(current_import_metadata, "rows_in_source")
        fallback_control_id = _fallback_control_external_id(current_import_metadata)
        completion_details = {
            "steps": dict(step_results),
            "metadata": current_import_metadata if current_import_metadata else None,
        }
        if all_success:
            await _offload_callable_py(
                lambda: import_audit_service.complete_batch_best_effort(
                    audit_ref,
                    rows_in_source=rows_in_source,
                    rows_staged=rows_written,
                    rows_written=rows_written,
                    external_batch_table=(
                        "dbo.FallbackImportBatchControl" if fallback_control_id else None
                    ),
                    external_batch_id=fallback_control_id,
                    details=completion_details,
                ),
                name="import_audit_complete",
                meta={"import_kind": FALLBACK_AUDIT_IMPORT_KIND},
            )
        else:
            await _offload_callable_py(
                lambda: import_audit_service.fail_batch_best_effort(
                    audit_ref,
                    error_type="FallbackImportFailed",
                    error_text=combined_log,
                    rows_in_source=rows_in_source,
                    rows_staged=rows_written,
                    rows_written=rows_written,
                    rows_skipped=(
                        rows_in_source - rows_written
                        if rows_in_source is not None and rows_written is not None
                        else None
                    ),
                    external_batch_table=(
                        "dbo.FallbackImportBatchControl" if fallback_control_id else None
                    ),
                    external_batch_id=fallback_control_id,
                    details=completion_details,
                ),
                name="import_audit_fail",
                meta={"import_kind": FALLBACK_AUDIT_IMPORT_KIND},
            )
    except asyncio.CancelledError:
        await _fail_audit_batch_for_exit(
            status="cancelled",
            error_type="FallbackImportCancelled",
            error_text="Fallback import was cancelled before completion.",
        )
        raise
    except Exception as e:
        await _fail_audit_batch_for_exit(
            status="failed",
            error_type=type(e).__name__,
            error_text=str(e),
        )
        raise
    return (
        bool(all_success),
        str(combined_log or ""),
        {
            "excel": bool(step_results.get("excel")),
            "archive": bool(step_results.get("archive")),
            "sql": bool(step_results.get("sql")),
        },
    )
