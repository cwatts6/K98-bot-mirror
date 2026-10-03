"""Required read-only headroom gate for dedicated coordinated SQL work."""

from kvk.dal.new_source_import_dal import SourceConflict

HEADROOM_SQL = """SELECT DB_NAME() AS DatabaseName, USER_NAME() AS Principal,
    l.total_log_size_in_bytes AS TotalBytes, l.used_log_space_in_bytes AS UsedBytes,
    d.recovery_model_desc AS RecoveryModel, d.log_reuse_wait_desc AS ReuseWait
    FROM sys.dm_db_log_space_usage l
    JOIN sys.databases d ON d.database_id=DB_ID()"""


def verify_headroom(cursor, configuration):
    """No DBCC, backup/job request, sleep, transaction or permission mutation."""
    cursor.execute(HEADROOM_SQL)
    row = cursor.fetchone()
    if row is None or cursor.fetchone() is not None:
        raise SourceConflict("Exact target log headroom is unavailable.")
    database, principal, total, used, recovery, reuse = row
    if (
        database != configuration["database"]
        or principal != configuration["username"]
        or type(total) is not int
        or type(used) is not int
        or total <= 0
        or not 0 <= used <= total
        or recovery != "FULL"
        or reuse not in {"NOTHING", "ACTIVE_TRANSACTION", "LOG_BACKUP"}
    ):
        raise SourceConflict(
            "SQL target, log measurement or reuse state requires operator reconciliation."
        )
    policy = configuration["headroom"]
    free = total - used
    percent = used * 100.0 / total
    if free < policy["min_free_bytes"] or percent >= policy["max_used_percent"]:
        raise SourceConflict("SQL log headroom is below the reviewed workload reserve.")
    return {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "used_percent": percent,
        "reuse_wait": reuse,
    }


def preflight():
    from core.export_sql_connection import connect, settings
    from log_health import LogHeadroomError

    connection = None
    try:
        configuration = settings()
        connection = connect(server=configuration["server"], database=configuration["database"])
        connection.autocommit = True
        cursor = connection.cursor()
        try:
            return verify_headroom(cursor, configuration)
        finally:
            cursor.close()
    except Exception:
        raise LogHeadroomError(
            "Required S11 SQL headroom check failed; no work admitted."
        ) from None
    finally:
        if connection is not None:
            connection.close()
