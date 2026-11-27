"""One acknowledged backup request; never fall back after uncertain dispatch."""

import os
from types import SimpleNamespace

from core.sql_connection_custody import require_sql_admission, retain_connection

try:
    import pyodbc
except ImportError:
    pyodbc = None

# Execute this fixed metadata query in msdb even when the equivalent pre-admission
# caller supplied a cursor whose current database is master. OBJECT_ID alone
# cannot distinguish a missing wrapper from metadata hidden from this principal.
# Database VIEW DEFINITION is insufficient: an object-level DENY can hide the
# wrapper while that database permission still reports 1. Only the existing dbo
# context can prove absence here; never grant broader rights to satisfy this check.
BACKUP_ROUTE_METADATA = """SET NOCOUNT ON;
SELECT OBJECT_ID(N'dbo.usp_start_rok_tracker_log_backup',N'P') AS wrapper_id,
       CASE WHEN DATABASE_PRINCIPAL_ID()=1 THEN 1 ELSE 0 END AS can_prove_absence,
       HAS_PERMS_BY_NAME(N'dbo.usp_start_rok_tracker_log_backup',N'OBJECT',N'EXECUTE') AS can_execute_wrapper;
"""
BACKUP_ROUTE_QUERY = (
    "EXEC msdb.sys.sp_executesql N'" + BACKUP_ROUTE_METADATA.replace("'", "''") + "';"
)


def trigger_log_backup_sync(job_name: str = "ROK_TRACKER - LOG Backup") -> dict:
    """Request the existing job once. Acknowledgement is not backup completion.

    Choose the installed route before dispatch. Lost responses never authorize
    another job request or an ad-hoc BACKUP LOG. No schedule is changed.
    """
    require_sql_admission()
    server = os.getenv("SQL_MONITOR_SERVER") or os.getenv("SQL_SERVER")
    username = (
        os.getenv("SQL_MONITOR_USERNAME")
        or os.getenv("IMPORT_USERNAME")
        or os.getenv("SQL_USERNAME")
    )
    password = (
        os.getenv("SQL_MONITOR_PASSWORD")
        or os.getenv("IMPORT_PASSWORD")
        or os.getenv("SQL_PASSWORD")
    )
    result = {"ok": False, "outcome": "not_attempted", "backup_completed": None}
    if not (server and username and password):
        return dict(result, error="missing_db_credentials")
    if pyodbc is None:
        return dict(result, error="pyodbc_missing")
    connection = cursor = None
    attempted = False
    failure = None
    try:
        connection = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=msdb;UID={username};PWD={password};",
            autocommit=True,
            timeout=5,
        )
        connection.timeout = 300
        cursor = connection.cursor()
        result = request_once(cursor, job_name=job_name, job_id=os.getenv("SQL_MONITOR_JOB_ID"))
        attempted = result["outcome"] != "not_attempted"
    except Exception as error:
        failure = error
        result.update(
            outcome="unknown" if attempted else "not_attempted",
            error="dispatch_unknown" if attempted else "route_unavailable",
        )
    finally:
        for handle in (cursor, connection):
            if handle is None:
                continue
            try:
                handle.close()
            except BaseException as cleanup:
                retain_connection(
                    SimpleNamespace(connection=connection, cursor=cursor),
                    effect="unknown" if attempted else "not_attempted",
                    first_failure=failure or cleanup,
                    cleanup_error=cleanup,
                )
                result["cleanup"] = "unconfirmed"
                break
    return result


def request_once(cursor, *, job_name="ROK_TRACKER - LOG Backup", job_id=None):
    """Shared pre-admission/background dispatch rule; no fallback after attempt."""
    result = {"ok": False, "outcome": "not_attempted", "backup_completed": None}
    attempted = False
    try:
        cursor.execute(BACKUP_ROUTE_QUERY)
        rows = cursor.fetchmany(2)
        if len(rows) != 1 or len(rows[0]) != 3:
            raise RuntimeError("Backup route inspection was not acknowledged.")
        wrapper_id, can_prove_absence, can_execute_wrapper = rows[0]
        if cursor.nextset():
            raise RuntimeError("Unexpected backup route inspection result.")
        wrapper = wrapper_id is not None
        if wrapper and can_execute_wrapper != 1:
            raise RuntimeError("The visible backup wrapper is not executable.")
        if not wrapper and can_prove_absence != 1:
            raise RuntimeError("Backup wrapper absence is not established.")
        method = "wrapper" if wrapper else "job_id" if job_id else "job_name"
        result["used_method"] = method
        # Every failure after this boundary is outcome-unknown.
        attempted = True
        if wrapper:
            cursor.execute("EXEC msdb.dbo.usp_start_rok_tracker_log_backup;")
        elif job_id:
            cursor.execute("EXEC msdb.dbo.sp_start_job @job_id=?", job_id)
        else:
            cursor.execute("EXEC msdb.dbo.sp_start_job @job_name=?", job_name)
        while cursor.nextset():
            pass
        result.update(ok=True, outcome="requested")
    except Exception:
        result.update(
            outcome="unknown" if attempted else "not_attempted",
            error="dispatch_unknown" if attempted else "route_unavailable",
        )
    return result
