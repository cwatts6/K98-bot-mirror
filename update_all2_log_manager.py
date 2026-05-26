"""
Update ALL2 Log Management Module
==================================
Thin wrapper that integrates existing log_health and log_backup modules
to provide intelligent log backup coordination for UPDATE_ALL2 stored procedure.

This module leverages:
- log_health.preflight_from_env_sync() for headroom checks
- log_backup.trigger_log_backup_sync() for backup triggering
- file_utils.get_conn_with_retries() for robust DB connections
- file_utils.emit_telemetry_event() for operational visibility
- New LogBackupTriggerQueue table for SP->Python coordination

Usage in bot:
    from update_all2_log_manager import execute_update_all2_with_log_management

    result = execute_update_all2_with_log_management(
        cursor=db_cursor,
        param1=kingdom_rank,
        param2=kingdom_seed
    )
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Centralized imports
try:
    from file_utils import cursor_row_to_dict, emit_telemetry_event, get_conn_with_retries
except ImportError:
    logger.error("file_utils not available - core functionality will be limited")
    get_conn_with_retries = None
    emit_telemetry_event = None
    cursor_row_to_dict = None

try:
    from constants import DATABASE, ODBC_DRIVER, PASSWORD, SERVER, USERNAME
except ImportError:
    logger.warning("constants module not available - using fallback defaults")
    SERVER = None
    DATABASE = "ROK_TRACKER"
    USERNAME = None
    PASSWORD = None
    ODBC_DRIVER = "ODBC Driver 17 for SQL Server"

# Reuse existing modules
try:
    from log_backup import trigger_log_backup_sync
except ImportError:
    logger.warning("log_backup module not available - backup triggering disabled")
    trigger_log_backup_sync = None

try:
    from log_health import LogHeadroomError, preflight_from_env_sync
except ImportError:
    logger.warning("log_health module not available - preflight checks disabled")
    preflight_from_env_sync = None
    LogHeadroomError = RuntimeError


def _safe_emit_telemetry(payload: dict) -> None:
    """Safe wrapper for telemetry emission that won't crash on failure."""
    try:
        if emit_telemetry_event:
            emit_telemetry_event(payload)
    except Exception:
        logger.debug("Telemetry emission failed (non-fatal)", exc_info=True)


def get_log_space_usage(cursor) -> float | None:
    """
    Query current transaction log usage percentage.
    Reuses logic from log_health._get_log_used_pct but simplified for cursor use.

    Args:
        cursor: Active database cursor

    Returns:
        Log usage percentage (0-100) or None if unavailable
    """
    try:
        cursor.execute("""
            SELECT CAST(used_log_space_in_percent AS DECIMAL(5,2))
            FROM sys.dm_db_log_space_usage
        """)
        row = cursor.fetchone()
        if row and row[0] is not None:
            usage = float(row[0])
            _safe_emit_telemetry(
                {"event": "log_space_usage_query", "method": "dmv", "usage_pct": usage}
            )
            return usage
    except Exception as e:
        logger.debug("DMV log space query failed: %s", e)

    # Fallback to DBCC SQLPERF
    try:
        cursor.execute("DBCC SQLPERF(LOGSPACE)")
        rows = cursor.fetchall()
        cursor.execute("SELECT DB_NAME()")
        current_db = cursor.fetchone()[0].upper()

        for row in rows:
            try:
                db_name = str(row[0]).strip().upper()
                if db_name == current_db:
                    usage = float(row[2])
                    _safe_emit_telemetry(
                        {"event": "log_space_usage_query", "method": "dbcc", "usage_pct": usage}
                    )
                    return usage
            except Exception:
                continue
    except Exception as e:
        logger.debug("DBCC SQLPERF fallback failed: %s", e)

    _safe_emit_telemetry({"event": "log_space_usage_query", "method": "failed", "usage_pct": None})
    return None


def check_pending_log_backup_triggers(cursor, max_age_minutes: int = 5) -> list:
    """
    Check for pending log backup triggers in LogBackupTriggerQueue.

    Args:
        cursor: Active database cursor
        max_age_minutes: Maximum age of triggers to consider (default: 5)

    Returns:
        List of pending trigger records (dicts)
    """
    try:
        cursor.execute(
            """
            SELECT ID,
                TriggerTime,
                ProcedureName,
                Reason,
                LogUsedPctBefore,
                DATEDIFF(SECOND, TriggerTime, SYSDATETIME()) AS AgeSeconds
            FROM dbo.LogBackupTriggerQueue
            WHERE Processed = 0
              AND TriggerTime >= DATEADD(MINUTE, -?, SYSDATETIME())
            ORDER BY TriggerTime ASC
        """,
            max_age_minutes,
        )

        rows = cursor.fetchall()
        triggers = []
        for row in rows:
            # Use centralized cursor_row_to_dict if available
            if cursor_row_to_dict:
                try:
                    trigger = cursor_row_to_dict(cursor, row)
                    # Normalize keys to match expected schema
                    triggers.append(
                        {
                            "id": trigger.get("ID"),
                            "trigger_time": trigger.get("TriggerTime"),
                            "procedure_name": trigger.get("ProcedureName"),
                            "reason": trigger.get("Reason"),
                            "log_used_pct_before": trigger.get("LogUsedPctBefore"),
                            "age_seconds": trigger.get("AgeSeconds"),
                        }
                    )
                except Exception:
                    # Fallback to manual extraction
                    triggers.append(
                        {
                            "id": row[0],
                            "trigger_time": row[1],
                            "procedure_name": row[2],
                            "reason": row[3],
                            "log_used_pct_before": row[4],
                            "age_seconds": row[5],
                        }
                    )
            else:
                triggers.append(
                    {
                        "id": row[0],
                        "trigger_time": row[1],
                        "procedure_name": row[2],
                        "reason": row[3],
                        "log_used_pct_before": row[4],
                        "age_seconds": row[5],
                    }
                )

        _safe_emit_telemetry(
            {
                "event": "check_pending_triggers",
                "triggers_found": len(triggers),
                "max_age_minutes": max_age_minutes,
            }
        )

        return triggers
    except Exception as e:
        logger.warning("Failed to check pending log backup triggers: %s", e)
        _safe_emit_telemetry(
            {"event": "check_pending_triggers", "status": "failed", "error": str(e)}
        )
        return []


def mark_trigger_processed(
    cursor,
    trigger_id: int,
    processed_by: str = "Python Bot",
    log_used_pct_after: float | None = None,
    backup_result: str | None = None,
) -> bool:
    """
    Mark a log backup trigger as processed.

    Args:
        cursor: Active database cursor
        trigger_id: ID of the trigger to mark
        processed_by: Identifier of the processing agent
        log_used_pct_after: Log usage after backup (optional)
        backup_result: Result message from backup operation (optional)

    Returns:
        True if marked successfully, False otherwise
    """
    try:
        cursor.execute(
            """
            EXEC dbo.usp_MarkLogBackupTriggerProcessed
                @TriggerID = ?,
                @ProcessedBy = ?,
                @LogUsedPctAfter = ?,
                @BackupResult = ?
        """,
            trigger_id,
            processed_by,
            log_used_pct_after,
            backup_result,
        )

        logger.info("Marked trigger ID %d as processed", trigger_id)
        _safe_emit_telemetry(
            {
                "event": "mark_trigger_processed",
                "trigger_id": trigger_id,
                "processed_by": processed_by,
                "log_used_pct_after": log_used_pct_after,
                "status": "success",
            }
        )
        return True
    except Exception as e:
        logger.warning("Failed to mark trigger %d as processed: %s", trigger_id, e)
        _safe_emit_telemetry(
            {
                "event": "mark_trigger_processed",
                "trigger_id": trigger_id,
                "status": "failed",
                "error": str(e),
            }
        )
        return False


def process_log_backup_triggers(cursor, max_triggers: int = 5) -> dict[str, Any]:
    """
    Process any pending log backup triggers from the queue.
    Uses existing log_backup.trigger_log_backup_sync() for actual backup triggering.

    Args:
        cursor: Active database cursor
        max_triggers: Maximum number of triggers to process in one call

    Returns:
        Dictionary with processing results
    """
    results = {"triggers_found": 0, "triggers_processed": 0, "backups_triggered": 0, "errors": []}

    pending = check_pending_log_backup_triggers(cursor, max_age_minutes=10)
    results["triggers_found"] = len(pending)

    if not pending:
        logger.debug("No pending log backup triggers found")
        return results

    logger.info("Found %d pending log backup trigger(s)", len(pending))

    for trigger in pending[:max_triggers]:
        trigger_id = trigger["id"]
        procedure_name = trigger["procedure_name"]
        reason = trigger["reason"]

        logger.info(
            "Processing trigger ID %d from %s (reason: %s, age: %ds)",
            trigger_id,
            procedure_name,
            reason,
            trigger["age_seconds"],
        )

        # Get log usage before backup
        _log_before = get_log_space_usage(cursor)

        # Trigger log backup using existing module
        backup_success = False
        backup_msg = "not_attempted"

        if trigger_log_backup_sync:
            try:
                result = trigger_log_backup_sync()
                backup_success = result.get("ok", False)
                backup_msg = f"method={result.get('used_method', 'unknown')}, ok={backup_success}"

                if backup_success:
                    results["backups_triggered"] += 1
                    logger.info("Log backup triggered successfully for trigger ID %d", trigger_id)
                    _safe_emit_telemetry(
                        {
                            "event": "log_backup_triggered",
                            "trigger_id": trigger_id,
                            "method": result.get("used_method"),
                            "status": "success",
                        }
                    )
                else:
                    error_detail = result.get("error", "unknown")
                    backup_msg += f", error={error_detail}"
                    logger.warning(
                        "Log backup trigger failed for ID %d: %s", trigger_id, error_detail
                    )
                    results["errors"].append(f"Trigger {trigger_id}: {error_detail}")
                    _safe_emit_telemetry(
                        {
                            "event": "log_backup_triggered",
                            "trigger_id": trigger_id,
                            "status": "failed",
                            "error": error_detail,
                        }
                    )
            except Exception as e:
                backup_msg = f"exception:{type(e).__name__}:{str(e)[:100]}"
                logger.exception("Exception triggering log backup for trigger ID %d", trigger_id)
                results["errors"].append(f"Trigger {trigger_id}: {e!s}")
                _safe_emit_telemetry(
                    {
                        "event": "log_backup_triggered",
                        "trigger_id": trigger_id,
                        "status": "exception",
                        "error_type": type(e).__name__,
                        "error": str(e)[:200],
                    }
                )
        else:
            backup_msg = "trigger_log_backup_sync_unavailable"
            logger.warning(
                "trigger_log_backup_sync not available, cannot process trigger %d", trigger_id
            )
            _safe_emit_telemetry(
                {"event": "log_backup_triggered", "trigger_id": trigger_id, "status": "unavailable"}
            )

        # Wait briefly for backup to start
        if backup_success:
            time.sleep(2)

        log_after = get_log_space_usage(cursor)

        # Mark as processed
        if mark_trigger_processed(
            cursor,
            trigger_id,
            processed_by="Python Bot (update_all2_log_manager)",
            log_used_pct_after=log_after,
            backup_result=backup_msg[:4000],
        ):
            results["triggers_processed"] += 1

    _safe_emit_telemetry({"event": "process_log_backup_triggers_complete", **results})

    return results


def execute_update_all2_with_log_management(
    cursor,
    param1: float | None = None,
    param2: str | None = None,
    *,
    post_trigger_wait: float = 2.0,
    max_post_trigger_wait: float = 30.0,
) -> dict[str, Any]:
    """
    Execute UPDATE_ALL2 with intelligent log backup management.

    This function:
    1. Executes UPDATE_ALL2 stored procedure
    2. Monitors for log backup triggers in LogBackupTriggerQueue
    3. Processes pending triggers and initiates backups
    4. Waits for backup to reduce log pressure

    Note: Preflight checks are handled separately by processing_pipeline.py

    Args:
        cursor: Active database cursor (must support execute)
        param1: KINGDOM_RANK parameter (optional)
        param2: KINGDOM_SEED parameter (optional)
        post_trigger_wait: Initial wait after triggering backup (seconds)
        max_post_trigger_wait: Maximum total wait for log backup (seconds)

    Returns:
        Dictionary containing:
            - success: bool
            - sp_result: Result from UPDATE_ALL2
            - log_before: Log usage before execution
            - log_after: Log usage after execution
            - trigger_results: Results from trigger processing
            - error: Error message if failed

    Raises:
        Exception: Any unhandled exceptions from stored procedure
    """
    result = {
        "success": False,
        "sp_result": None,
        "log_before": None,
        "log_after": None,
        "trigger_results": None,
        "error": None,
    }

    start_time = time.time()

    try:
        # Capture log usage before
        result["log_before"] = get_log_space_usage(cursor)
        if result["log_before"] is not None:
            logger.info("Log usage before UPDATE_ALL2: %.2f%%", result["log_before"])

        # Execute UPDATE_ALL2
        logger.info("Executing UPDATE_ALL2 (param1=%s, param2=%s)", param1, param2)
        _safe_emit_telemetry(
            {
                "event": "update_all2_execute_start",
                "param1": param1,
                "param2": param2,
                "log_before": result["log_before"],
            }
        )

        if param1 is not None and param2 is not None:
            cursor.execute("EXEC dbo.UPDATE_ALL2 @param1 = ?, @param2 = ?", param1, param2)
        elif param1 is not None:
            cursor.execute("EXEC dbo.UPDATE_ALL2 @param1 = ?", param1)
        elif param2 is not None:
            cursor.execute("EXEC dbo.UPDATE_ALL2 @param2 = ?", param2)
        else:
            cursor.execute("EXEC dbo.UPDATE_ALL2")

        # Consume ALL result sets (UPDATE_ALL2 returns 4 result sets)
        # 1. xp_cmdshell output ("1 file(s) moved.")
        # 2. Index maintenance log (table variable)
        # 3. Phase A summary (5 columns)
        # 4. Phase B final (8 columns) ← This is what we want
        try:
            all_results = []
            result_count = 0

            # Loop through all result sets
            while True:
                try:
                    rows = cursor.fetchall()
                    result_count += 1
                    if rows:
                        all_results.append(rows)
                        logger.debug(
                            f"Result set #{result_count}: {len(rows)} row(s), "
                            f"{len(rows[0]) if rows else 0} column(s)"
                        )
                except Exception as fetch_err:
                    logger.debug(f"Fetch on result set #{result_count} failed: {fetch_err}")

                # Try to advance to next result set
                try:
                    if not cursor.nextset():
                        break
                except Exception:
                    break

            logger.info(
                f"UPDATE_ALL2 returned {result_count} result set(s), {len(all_results)} non-empty"
            )

            # The LAST result set should be Phase B final (8 columns)
            if all_results:
                final_result_set = all_results[-1]
                if final_result_set and len(final_result_set) > 0:
                    sp_result_row = final_result_set[-1]  # Last row of final result set

                    # Expected: 8 columns
                    if len(sp_result_row) >= 8:
                        result["sp_result"] = {
                            "rows_inserted_ks5": sp_result_row[0],
                            "rows_inserted_ks4": sp_result_row[1],
                            "duration_seconds": sp_result_row[2],
                            "phase_b_duration_ms": sp_result_row[3],
                            "log_used_pct_before": sp_result_row[4],
                            "log_used_pct_after": sp_result_row[5],
                            "log_backup_triggered": sp_result_row[6],
                            "status": sp_result_row[7],
                        }
                        logger.info("UPDATE_ALL2 Phase B result: %s", result["sp_result"])
                    elif len(sp_result_row) == 5:
                        logger.warning("Got Phase A summary instead of Phase B (5 columns)")
                        result["sp_result"] = {
                            "ks5_max_scanorder": sp_result_row[0],
                            "ks5_rows_inserted": sp_result_row[1],
                            "ks4_rows_inserted": sp_result_row[2],
                            "import_staging_rows": sp_result_row[3],
                            "ks4_rows_in_latest": sp_result_row[4],
                        }
                    else:
                        logger.warning(
                            f"Unexpected final result row length: {len(sp_result_row)} "
                            f"(expected 8 or 5)"
                        )
                        result["sp_result"] = {
                            "raw": str(sp_result_row)[:200],
                            "column_count": len(sp_result_row),
                        }
                else:
                    logger.warning("Final result set is empty")
            else:
                logger.warning("UPDATE_ALL2 returned no non-empty result sets")

        except Exception as e:
            logger.exception("Error parsing UPDATE_ALL2 results")
            result["sp_result"] = {"error": str(e)[:200]}

        # Capture log usage after
        result["log_after"] = get_log_space_usage(cursor)
        if result["log_after"] is not None:
            logger.info("Log usage after UPDATE_ALL2: %.2f%%", result["log_after"])

        # Process any pending log backup triggers
        logger.info("Checking for pending log backup triggers...")
        trigger_results = process_log_backup_triggers(cursor, max_triggers=5)
        result["trigger_results"] = trigger_results

        if trigger_results["backups_triggered"] > 0:
            logger.info(
                "Log backup(s) triggered (%d), waiting %.1fs for backup to start...",
                trigger_results["backups_triggered"],
                post_trigger_wait,
            )
            time.sleep(post_trigger_wait)

            # Optional: Wait for log usage to drop
            wait_start = time.time()
            while time.time() - wait_start < max_post_trigger_wait:
                current_usage = get_log_space_usage(cursor)
                if current_usage is None:
                    break

                if result["log_after"] and current_usage < result["log_after"] - 5.0:
                    logger.info(
                        "Log usage reduced from %.2f%% to %.2f%% (waited %.1fs)",
                        result["log_after"],
                        current_usage,
                        time.time() - wait_start,
                    )
                    result["log_after"] = current_usage
                    break

                time.sleep(5)
            else:
                logger.info("Max wait time reached, continuing...")

        result["success"] = True
        elapsed = time.time() - start_time
        logger.info(
            "UPDATE_ALL2 execution with log management completed successfully (%.2fs)", elapsed
        )

        _safe_emit_telemetry(
            {
                "event": "update_all2_execute_complete",
                "status": "success",
                "duration_seconds": elapsed,
                "log_before": result["log_before"],
                "log_after": result["log_after"],
                "backups_triggered": trigger_results.get("backups_triggered", 0),
                "triggers_processed": trigger_results.get("triggers_processed", 0),
            }
        )

    except Exception as e:
        result["error"] = str(e)
        elapsed = time.time() - start_time
        logger.exception("UPDATE_ALL2 execution with log management failed")
        _safe_emit_telemetry(
            {
                "event": "update_all2_execute_complete",
                "status": "failed",
                "duration_seconds": elapsed,
                "error_type": type(e).__name__,
                "error": str(e)[:500],
            }
        )
        raise

    return result


# Convenience alias for backward compatibility
run_update_all2_with_log_management = execute_update_all2_with_log_management


if __name__ == "__main__":
    # Test/demo code
    import os

    logger.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=" * 60)
    print("UPDATE_ALL2 Log Manager - Test Mode")
    print("=" * 60)

    if not get_conn_with_retries:
        print("ERROR: file_utils.get_conn_with_retries not available")
        exit(1)

    server = SERVER or os.environ.get("SQL_SERVER")
    database = DATABASE or os.environ.get("SQL_DATABASE", "ROK_TRACKER")
    username = USERNAME or os.environ.get("SQL_USERNAME")
    password = PASSWORD or os.environ.get("SQL_PASSWORD")
    driver = ODBC_DRIVER

    if not all([server, username, password]):
        print("ERROR: Missing SQL credentials")
        print("Required: SQL_SERVER, SQL_USERNAME, SQL_PASSWORD")
        print(f"Current: server={server}, database={database}, user={username}")
        exit(1)

    print(f"\nConnecting to: {server}/{database}")
    print(f"Using driver: {driver}")

    try:
        # Use centralized connection helper
        conn = get_conn_with_retries()

        if not conn:
            print("ERROR: get_conn_with_retries returned None")
            exit(1)

        with conn:
            cursor = conn.cursor()

            # Test 1: Check pending triggers
            print("\n" + "=" * 60)
            print("Test 1: Checking for pending triggers")
            print("=" * 60)
            pending = check_pending_log_backup_triggers(cursor)
            print(f"Found {len(pending)} pending trigger(s)")
            for trigger in pending:
                print(f"  - ID {trigger['id']}: {trigger['procedure_name']} ({trigger['reason']})")

            # Test 2: Get log space usage
            print("\n" + "=" * 60)
            print("Test 2: Checking log space usage")
            print("=" * 60)
            usage = get_log_space_usage(cursor)
            if usage is not None:
                print(f"Log space used: {usage:.2f}%")
            else:
                print("Could not determine log space usage")

            # Test 3: Process triggers (dry run)
            if pending:
                print("\n" + "=" * 60)
                print("Test 3: Processing triggers (max 1 for test)")
                print("=" * 60)
                results = process_log_backup_triggers(cursor, max_triggers=1)
                print(f"Results: {results}")

            print("\n" + "=" * 60)
            print("Tests completed successfully!")
            print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
