"""
Extended log health & telemetry utilities.

Adds JSON telemetry lines for preflight_from_env_sync and writes them to:
- logs/telemetry_log.jsonl (rotating via central logging_setup)
Also still emits human-readable [LOG WAIT] and [LOG DIAG] lines.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import datetime as _dt
import json
import logging
import time as _time

try:
    # Central logging already initialized; import path constant (optional use)
    from logging_setup import TELEMETRY_LOG_PATH
except Exception:
    TELEMETRY_LOG_PATH = None  # type: ignore

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")  # dedicated namespace for JSON events

try:
    import pyodbc  # type: ignore
except Exception:
    pyodbc = None  # type: ignore

# Prefer the centralized emit_telemetry_event helper when available; fall back gracefully.
try:
    from file_utils import emit_telemetry_event  # type: ignore
except Exception:

    def emit_telemetry_event(payload: dict, *, max_snippet: int = 2000) -> None:
        """
        Fallback telemetry emitter: best-effort JSON line through telemetry logger.
        Kept as a thin compatibility shim if file_utils is not importable in a particular test env.
        """
        try:
            telemetry_logger.info(json.dumps(payload, default=str))
        except Exception:
            try:
                telemetry_logger.info(str(payload))
            except Exception:
                # Last-resort no-op to avoid raising from telemetry emission
                pass


@dataclass
class LogHealth:
    used_percent: float
    reuse_wait_desc: str


class LogHeadroomError(RuntimeError):
    """Raised when the database log headroom is insufficient for heavy work."""


DEFAULT_DB = "ROK_TRACKER"
DEFAULT_WARN_THRESHOLD = 85.0


def _query_single_value(cur, sql: str, params: tuple = ()):
    cur.execute(sql, *params)
    row = cur.fetchone()
    return None if not row else row[0]


def _is_permission_error(exc: Exception) -> bool:
    try:
        text = str(exc).lower()
        if "permission" in text and ("denied" in text or "was denied" in text):
            return True
        if "view server state" in text or "view server performance state" in text:
            return True
        if "(297)" in text or "(300)" in text:
            return True
    except Exception:
        pass
    return False


def _log_session_identity_safe(cur):
    try:
        cur.execute("SELECT SUSER_SNAME(), ORIGINAL_LOGIN()")
        who = cur.fetchone()
        logger.warning("Session identity for DB connection: %r", who)
    except Exception:
        logger.debug("Unable to read SUSER_SNAME() for diagnostic", exc_info=True)


def get_log_health(cnxn, *, dbname: str = DEFAULT_DB) -> LogHealth:
    if cnxn is None:
        raise RuntimeError("No DB connection provided to get_log_health.")
    used_percent: float | None = None
    reuse_wait_desc: str | None = None
    with cnxn.cursor() as cur:
        try:
            _log_session_identity_safe(cur)
        except Exception:
            logger.debug("Session identity diagnostic failed", exc_info=True)

        dmv_sql_templates = [
            "SELECT CAST(used_log_space_percent AS float) AS used_percent FROM sys.dm_db_log_space_usage WHERE DB_NAME(database_id) = ?;",
            "SELECT CAST(used_log_space_in_percent AS float) AS used_percent FROM sys.dm_db_log_space_usage WHERE DB_NAME(database_id) = ?;",
        ]
        for sql in dmv_sql_templates:
            try:
                val = _query_single_value(cur, sql, (dbname,))
                if val is None:
                    raise RuntimeError("sys.dm_db_log_space_usage returned no rows")
                used_percent = float(val)
                logger.debug("DMV used_percent retrieved using SQL: %s", sql)
                break
            except Exception as exc:
                if _is_permission_error(exc):
                    logger.warning("Insufficient permissions to query server DMVs: %s", exc)
                    try:
                        _log_session_identity_safe(cur)
                    except Exception:
                        pass
                    raise PermissionError("Insufficient permission to query server DMVs") from exc
                logger.debug("DMV attempt failed: %s", exc, exc_info=True)

        if used_percent is None:
            try:
                cur.execute("DBCC SQLPERF(LOGSPACE)")
                rows = cur.fetchall()
                if not rows:
                    raise RuntimeError("DBCC SQLPERF(LOGSPACE) returned no rows")
                for r in rows:
                    if str(r[0]).strip().lower() == dbname.lower():
                        used_percent = float(r[2])
                        break
                if used_percent is None:
                    raise RuntimeError("DBCC SQLPERF(LOGSPACE) entry not found for DB")
            except Exception as exc2:
                if _is_permission_error(exc2):
                    logger.warning("Insufficient permissions for DBCC SQLPERF(LOGSPACE): %s", exc2)
                    try:
                        _log_session_identity_safe(cur)
                    except Exception:
                        pass
                    raise PermissionError(
                        "Insufficient permission to query log space via DBCC"
                    ) from exc2
                logger.debug("DBCC fallback failed: %s", exc2, exc_info=True)
                raise RuntimeError("Unable to determine log usage (DMV+DBCC failed)") from exc2

        try:
            cur.execute("SELECT log_reuse_wait_desc FROM sys.databases WHERE name = ?", dbname)
            row2 = cur.fetchone()
            if not row2:
                raise RuntimeError("sys.databases lookup failed")
            reuse_wait_desc = str(row2[0])
        except Exception as exc3:
            if _is_permission_error(exc3):
                logger.warning("Insufficient permission reading sys.databases: %s", exc3)
                try:
                    _log_session_identity_safe(cur)
                except Exception:
                    pass
                raise PermissionError("Insufficient permission to read sys.databases") from exc3
            logger.debug("sys.databases reuse_wait read failed: %s", exc3, exc_info=True)
            raise RuntimeError("Unable to read log_reuse_wait_desc") from exc3

    return LogHealth(used_percent=used_percent, reuse_wait_desc=reuse_wait_desc)


def preflight_or_raise(
    cnxn, *, dbname: str = DEFAULT_DB, warn_threshold: float = DEFAULT_WARN_THRESHOLD
):
    try:
        health = get_log_health(cnxn, dbname=dbname)
    except PermissionError as pe:
        logger.warning("SQL log health check unavailable (permissions): %s", pe)
        logger.debug("Permission error details:", exc_info=True)
        return None
    except Exception as exc:
        logger.warning("SQL log health check unavailable (continuing): %s", exc)
        logger.debug("Health check failure details:", exc_info=True)
        return None

    msg = f"SQL log {health.used_percent:.1f}% used for {dbname} (reuse wait: {health.reuse_wait_desc})"

    if health.used_percent >= warn_threshold:
        logger.warning("Log headroom warning: %s", msg)
        raise LogHeadroomError(
            f"{msg}. Abort heavy work. Run FULL+LOG backups and ensure backup drive has space."
        )

    if health.reuse_wait_desc and str(health.reuse_wait_desc).upper() == "LOG_BACKUP":
        extra = (
            "SQL indicates LOG_BACKUP reuse wait. "
            "Take a FULL backup, then a LOG backup to establish the chain before heavy procedures."
        )
        logger.warning("Log reuse wait: %s: %s", health.reuse_wait_desc, extra)
        raise LogHeadroomError(extra)

    logger.debug("Log health OK: %s", msg)
    return health


# ---------- helpers for auto-trigger + bounded wait ----------


def _get_last_log_backup_finish(cur, dbname: str):
    cur.execute(
        """
        SELECT TOP (1) backup_finish_date
        FROM msdb.dbo.backupset
        WHERE database_name = ? AND type = 'L'
        ORDER BY backup_finish_date DESC
        """,
        dbname,
    )
    row = cur.fetchone()
    return row[0] if row and row[0] else None


def _get_last_full_backup_finish(cur, dbname: str):
    cur.execute(
        """
        SELECT TOP (1) backup_finish_date
        FROM msdb.dbo.backupset
        WHERE database_name = ? AND type = 'D'
        ORDER BY backup_finish_date DESC
        """,
        dbname,
    )
    row = cur.fetchone()
    return row[0] if row and row[0] else None


def _get_log_reuse_wait_and_model(cur, dbname: str):
    cur.execute(
        "SELECT recovery_model_desc, log_reuse_wait_desc FROM sys.databases WHERE name = ?",
        dbname,
    )
    row = cur.fetchone()
    if not row:
        return None, None
    return str(row[0] or ""), str(row[1] or "")


def _get_log_used_pct(cur, dbname: str) -> float | None:
    try:
        cur.execute("SELECT DB_NAME()")
        current_db = (cur.fetchone() or [""])[0]
        if current_db != dbname:
            cur.execute(f"USE [{dbname}]")
        cur.execute("""
            SELECT used_log_space_pct =
                   (used_log_space_in_bytes * 100.0 / NULLIF(total_log_size_in_bytes, 0))
            FROM sys.dm_db_log_space_usage
            """)
        row = cur.fetchone()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        pass
    try:
        cur.execute("DBCC SQLPERF(LOGSPACE)")
        cols = [d[0].lower() for d in cur.description]
        rows = cur.fetchall()
        try:
            name_ix = cols.index("database name")
            used_ix = cols.index("log space used (%)")
        except ValueError:
            return None
        for r in rows or []:
            if str(r[name_ix]).strip().lower() == dbname.lower():
                return float(r[used_ix])
    except Exception:
        pass
    return None


def _get_opentrans_summary(cur, dbname: str) -> str | None:
    """
    Run DBCC OPENTRAN(db) and return a short textual summary:
      - "No active open transactions." if none
      - Or a brief single-line message containing the open transaction info.
    Returns None if the check cannot be performed.
    """
    try:
        # DBCC OPENTRAN returns either a message row or a resultset describing the oldest open transaction.
        # Use the DBCC command and collect any rows/messages.
        sql = f"DBCC OPENTRAN('{dbname}')"
        cur.execute(sql)
        rows = cur.fetchall()
        if not rows:
            # Some SQL Server versions return no rows but emit messages; try to read description-based output
            return None
        # Consolidate into a short string
        try:
            # If the first column is a message string (common), return it truncated
            first_row = rows[0]
            # join non-null columns into a single message
            parts = [str(c) for c in first_row if c is not None]
            summary = " | ".join(parts)
            return summary[:1000]
        except Exception:
            return None
    except Exception:
        # permission errors or other failures should not crash preflight
        return None


def _get_job_last_run_status(cur, job_name: str = "ROK_TRACKER - LOG Backup") -> dict | None:
    """
    Query msdb for the latest job-run entry (step_id = 0) for job with given name.
    Returns a dict { run_datetime: datetime, run_status: int, message: str, run_date: int, run_time: int }
    or None if not found / cannot query.
    """
    try:
        # Find job_id
        cur.execute("SELECT job_id FROM msdb.dbo.sysjobs WHERE name = ?", job_name)
        row = cur.fetchone()
        if not row:
            return None
        job_id = row[0]
        # Latest job history entry for the job (step_id = 0 indicates job outcome)
        cur.execute(
            """
            SELECT TOP 1 run_date, run_time, run_status, message
            FROM msdb.dbo.sysjobhistory
            WHERE job_id = ? AND step_id = 0
            ORDER BY run_date DESC, run_time DESC
            """,
            job_id,
        )
        h = cur.fetchone()
        if not h:
            return None
        run_date = int(h[0]) if h[0] is not None else None
        run_time = int(h[1]) if h[1] is not None else None
        run_status = int(h[2]) if h[2] is not None else None
        message = str(h[3]) if h[3] is not None else None

        run_dt = None
        try:
            if run_date and run_time is not None:
                date_s = str(run_date).zfill(8)
                time_s = str(run_time).zfill(6)
                run_dt = _dt.datetime.strptime(date_s + time_s, "%Y%m%d%H%M%S")
        except Exception:
            run_dt = None

        return {
            "run_datetime": run_dt,
            "run_status": run_status,  # 1 = succeeded
            "message": message,
            "run_date": run_date,
            "run_time": run_time,
        }
    except Exception:
        logger.debug("Failed to query job history for %s", job_name, exc_info=True)
        return None


def _trigger_log_backup(cur) -> bool:
    try:
        cur.execute("EXEC msdb.dbo.usp_start_rok_tracker_log_backup;")
        logger.info("Requested msdb.dbo.usp_start_rok_tracker_log_backup (wrapper) successfully.")
        return True
    except Exception as e:
        logger.info("Wrapper unavailable/failed: %s", e)
    try:
        cur.execute("EXEC msdb.dbo.sp_start_job @job_name = ?", "ROK_TRACKER - LOG Backup")
        logger.info("Requested SQL Agent job 'ROK_TRACKER - LOG Backup'.")
        return True
    except Exception as e:
        logger.warning("sp_start_job fallback failed: %s", e)
        return False


def _emit_json_telemetry(event: str, data: dict):
    """
    Emit a single-line JSON log through the telemetry logger.
    """
    try:
        payload = {"event": event, **data}
        emit_telemetry_event(payload)
    except Exception:
        # Fallback: ensure we don't raise on telemetry emit
        try:
            telemetry_logger.info(json.dumps({"event": event, **data}, default=str))
        except Exception:
            logger.debug("Failed to emit telemetry JSON", exc_info=True)


def preflight_from_env_sync(
    server: str,
    database: str,
    username: str,
    password: str,
    *,
    driver: str = "ODBC Driver 17 for SQL Server",
    warn_threshold: float = DEFAULT_WARN_THRESHOLD,
    abort_threshold: float = 97.5,
    wait_on_log_backup: bool = True,
    max_wait_seconds: int = 360,
    poll_interval_seconds: float = 60.0,
):
    if pyodbc is None:
        raise RuntimeError("pyodbc is not available in this environment.")

    conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE=master;UID={username};PWD={password}"
    logger.info("Running preflight_from_env_sync using SQL user: %s on DB: %s", username, database)
    conn = None
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cur = conn.cursor()

        recovery_model_initial, reuse_wait_initial = _get_log_reuse_wait_and_model(cur, database)
        logger.warning("Session identity for DB connection: (%r, %r)", username, username)
        logger.warning(
            "[LOG DIAG] db=%s recovery_model=%s reuse_wait=%s",
            database,
            recovery_model_initial,
            reuse_wait_initial,
        )

        initial_used = _get_log_used_pct(cur, database)
        last_log_backup_before = _get_last_log_backup_finish(cur, database)
        last_full_backup_before = _get_last_full_backup_finish(cur, database)

        wait_elapsed = 0.0
        wait_reason = "immediate"
        observed_new_backup = False
        triggered_backup = False
        final_used = initial_used
        last_log_backup_after = last_log_backup_before

        # Attempt to gather an OPENTRAN summary in case it's useful diagnostics (non-fatal)
        opentran_summary = None
        try:
            opentran_summary = _get_opentrans_summary(cur, database)
        except Exception:
            opentran_summary = None

        # Attempt to gather wrapper job last-run status (non-fatal)
        wrapper_job_last_run = None
        try:
            wrapper_job_last_run = _get_job_last_run_status(cur, "ROK_TRACKER - LOG Backup")
        except Exception:
            wrapper_job_last_run = None

        if (reuse_wait_initial or "").upper() == "LOG_BACKUP" and wait_on_log_backup:
            logger.warning("Log reuse wait LOG_BACKUP detected; initiating wait cycle.")
            triggered_backup = _trigger_log_backup(cur)

            t0 = _time.time()
            deadline = t0 + max_wait_seconds
            while _time.time() < deadline:
                _time.sleep(poll_interval_seconds)
                candidate = _get_last_log_backup_finish(cur, database)
                if candidate and (
                    (not last_log_backup_before) or candidate > last_log_backup_before
                ):
                    observed_new_backup = True
                    last_log_backup_after = candidate
                    wait_reason = "new_backup"
                    break
                now_used = _get_log_used_pct(cur, database)
                final_used = now_used if now_used is not None else final_used
                if now_used is not None and now_used < warn_threshold:
                    wait_reason = "used_pct_drop"
                    break

            wait_elapsed = _time.time() - t0
            recovery_model_final, reuse_wait_final = _get_log_reuse_wait_and_model(cur, database)
            final_used = _get_log_used_pct(cur, database) or final_used
            if wait_reason == "immediate" and (reuse_wait_final or "").upper() == "LOG_BACKUP":
                wait_reason = "timeout"

            logger.info(
                "[LOG WAIT] db=%s reason=%s elapsed=%.2fs observed_new_backup=%s "
                "initial_used=%s final_used=%s last_log_backup_before=%s last_log_backup_after=%s",
                database,
                wait_reason,
                wait_elapsed,
                observed_new_backup,
                f"{initial_used:.2f}%" if initial_used is not None else "unknown",
                f"{final_used:.2f}%" if final_used is not None else "unknown",
                last_log_backup_before,
                last_log_backup_after,
            )

            telemetry_payload = {
                "db": database,
                "user": username,
                "reuse_wait_initial": reuse_wait_initial,
                "reuse_wait_final": reuse_wait_final,
                "initial_used_pct": initial_used,
                "final_used_pct": final_used,
                "wait_reason": wait_reason,
                "elapsed_seconds": round(wait_elapsed, 3),
                "observed_new_backup": observed_new_backup,
                "triggered_backup": triggered_backup,
                "last_full_backup": last_full_backup_before,
                "last_log_backup_before": last_log_backup_before,
                "last_log_backup_after": last_log_backup_after,
                "opentran_summary": opentran_summary,
                "wrapper_job_last_run": wrapper_job_last_run,
                "warn_threshold": warn_threshold,
                "abort_threshold": abort_threshold,
            }

            _emit_json_telemetry("log_wait", telemetry_payload)

            if (reuse_wait_final or "").upper() == "LOG_BACKUP":
                _emit_json_telemetry(
                    "log_wait_error",
                    {
                        "db": database,
                        "user": username,
                        "error": "LOG_BACKUP_persisted",
                        "final_used_pct": final_used,
                        "elapsed_seconds": round(wait_elapsed, 3),
                        "wait_reason": wait_reason,
                        "last_full_backup": last_full_backup_before,
                        "opentran_summary": opentran_summary,
                        "wrapper_job_last_run": wrapper_job_last_run,
                    },
                )
                raise LogHeadroomError(
                    "SQL indicates LOG_BACKUP reuse wait persists. Take a FULL and then LOG backup "
                    "to establish the chain. Aborting heavy operation."
                )

            if final_used is not None and final_used >= abort_threshold:
                _emit_json_telemetry(
                    "log_wait_error",
                    {
                        "db": database,
                        "user": username,
                        "error": "final_used_pct_above_abort_threshold",
                        "final_used_pct": final_used,
                        "abort_threshold": abort_threshold,
                        "elapsed_seconds": round(wait_elapsed, 3),
                        "wait_reason": wait_reason,
                        "last_full_backup": last_full_backup_before,
                        "opentran_summary": opentran_summary,
                        "wrapper_job_last_run": wrapper_job_last_run,
                    },
                )
                raise LogHeadroomError(
                    f"Transaction log usage remains high ({final_used:.1f}%). "
                    f"Aborting to avoid excessive log growth."
                )
        else:
            # Immediate path
            logger.info(
                "[LOG WAIT] db=%s reason=immediate elapsed=0.00s observed_new_backup=False "
                "initial_used=%s final_used=%s last_log_backup_before=%s last_log_backup_after=%s",
                database,
                f"{initial_used:.2f}%" if initial_used is not None else "unknown",
                f"{initial_used:.2f}%" if initial_used is not None else "unknown",
                last_log_backup_before,
                last_log_backup_before,
            )

            telemetry_payload = {
                "db": database,
                "user": username,
                "reuse_wait_initial": reuse_wait_initial,
                "reuse_wait_final": reuse_wait_initial,
                "initial_used_pct": initial_used,
                "final_used_pct": initial_used,
                "wait_reason": "immediate",
                "elapsed_seconds": 0.0,
                "observed_new_backup": False,
                "triggered_backup": False,
                "last_full_backup": last_full_backup_before,
                "last_log_backup_before": last_log_backup_before,
                "last_log_backup_after": last_log_backup_before,
                "opentran_summary": opentran_summary,
                "wrapper_job_last_run": wrapper_job_last_run,
                "warn_threshold": warn_threshold,
                "abort_threshold": abort_threshold,
            }

            _emit_json_telemetry("log_wait", telemetry_payload)

            if (reuse_wait_initial or "").upper() == "LOG_BACKUP":
                _emit_json_telemetry(
                    "log_wait_error",
                    {
                        "db": database,
                        "user": username,
                        "error": "LOG_BACKUP_immediate_abort",
                        "initial_used_pct": initial_used,
                        "last_full_backup": last_full_backup_before,
                        "opentran_summary": opentran_summary,
                        "wrapper_job_last_run": wrapper_job_last_run,
                    },
                )
                raise LogHeadroomError(
                    "SQL indicates LOG_BACKUP reuse wait. Take FULL then LOG backup before heavy work."
                )

            if initial_used is not None and initial_used >= abort_threshold:
                _emit_json_telemetry(
                    "log_wait_error",
                    {
                        "db": database,
                        "user": username,
                        "error": "initial_used_pct_above_abort_threshold",
                        "initial_used_pct": initial_used,
                        "abort_threshold": abort_threshold,
                        "last_full_backup": last_full_backup_before,
                        "opentran_summary": opentran_summary,
                        "wrapper_job_last_run": wrapper_job_last_run,
                    },
                )
                raise LogHeadroomError(
                    f"Transaction log usage is {initial_used:.1f}% (>= {abort_threshold:.1f}%). Aborting."
                )

            if initial_used is not None and initial_used >= warn_threshold:
                logger.warning(
                    "Transaction log usage elevated: %.1f%% (>= %.1f%%). Proceeding with caution.",
                    initial_used,
                    warn_threshold,
                )

        return None

    except LogHeadroomError:
        raise
    except Exception as e:
        _emit_json_telemetry(
            "log_wait_error",
            {
                "db": database,
                "user": username,
                "error": f"unexpected_exception:{type(e).__name__}",
                "message": str(e),
            },
        )
        raise LogHeadroomError(f"Failed preflight headroom check: {type(e).__name__}: {e}") from e
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# ---------- RESTORED diagnostic helper ----------


def log_backup_context(cur, dbname: str):
    cur.execute(
        "SELECT recovery_model_desc, log_reuse_wait_desc FROM sys.databases WHERE name = ?",
        dbname,
    )
    row = cur.fetchone()
    rm = row[0] if row else None
    reuse = row[1] if row else None

    cur.execute(
        """
        SELECT TOP (1) backup_finish_date
        FROM msdb.dbo.backupset
        WHERE database_name = ? AND type = 'D'
        ORDER BY backup_finish_date DESC
        """,
        dbname,
    )
    row = cur.fetchone()
    last_full = row[0] if row else None

    cur.execute(
        """
        SELECT TOP (1) backup_finish_date
        FROM msdb.dbo.backupset
        WHERE database_name = ? AND type = 'L'
        ORDER BY backup_finish_date DESC
        """,
        dbname,
    )
    row = cur.fetchone()
    last_log = row[0] if row else None

    used_percent = None
    try:
        cur.execute(
            """
            SELECT CAST(used_log_space_percent AS float)
            FROM sys.dm_db_log_space_usage
            WHERE DB_NAME(database_id) = ?
            """,
            dbname,
        )
        row = cur.fetchone()
        used_percent = float(row[0]) if row else None
    except Exception:
        try:
            cur.execute(
                """
                SELECT CAST(used_log_space_in_percent AS float)
                FROM sys.dm_db_log_space_usage
                WHERE DB_NAME(database_id) = ?
                """,
                dbname,
            )
            row = cur.fetchone()
            used_percent = float(row[0]) if row else None
        except Exception:
            try:
                cur.execute("DBCC SQLPERF(LOGSPACE)")
                rows = cur.fetchall()
                for r in rows or []:
                    if str(r[0]).strip().lower() == dbname.lower():
                        used_percent = float(r[2])
                        break
            except Exception:
                logger.debug(
                    "dm_db_log_space_usage/DBCC not available or permission denied", exc_info=True
                )

    logger.warning(
        "[LOG DIAG] db=%s recovery_model=%s reuse_wait=%s used_log_space_percent=%s last_full=%s last_log=%s",
        dbname,
        rm,
        reuse,
        used_percent,
        last_full,
        last_log,
    )


# ---------- Optional trigger context ----------


def _trigger_log_backup_with_cursor_or_creds(
    cur_or_conn=None,
    *,
    server: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> bool:
    if pyodbc is None:
        return False
    if cur_or_conn is not None:
        try:
            cur = getattr(cur_or_conn, "cursor", None)
            if cur is None:
                cur = cur_or_conn
            else:
                cur = cur()
            return _trigger_log_backup(cur)
        except Exception:
            logger.debug(
                "Failed to trigger log backup with provided cursor/connection.", exc_info=True
            )
            return False
    if server and username and password:
        conn = None
        try:
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};DATABASE=msdb;UID={username};PWD={password}",
                autocommit=True,
            )
            cur = conn.cursor()
            return _trigger_log_backup(cur)
        except Exception:
            logger.debug("Failed to trigger log backup with credentials.", exc_info=True)
            return False
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
    return False


@contextmanager
def log_backup_trigger_context(
    cur_or_conn=None,
    *,
    server: str | None = None,
    username: str | None = None,
    password: str | None = None,
    trigger_before: bool = False,
    trigger_after: bool = True,
):
    try:
        if trigger_before:
            _trigger_log_backup_with_cursor_or_creds(
                cur_or_conn, server=server, username=username, password=password
            )
        yield
    finally:
        if trigger_after:
            _trigger_log_backup_with_cursor_or_creds(
                cur_or_conn, server=server, username=username, password=password
            )
