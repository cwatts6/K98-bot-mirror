"""One bounded observation after an exact refusal; never grant or release a lock."""

from datetime import datetime
from types import SimpleNamespace
from uuid import UUID

from core.sql_connection_custody import retain_connection

SNAPSHOT_RESOURCE = "k98-legacy-output-snapshot"
DIAGNOSTIC_TIMEOUT_SECONDS = 1

# The whole resource is visible only for this short, fixed name. Coordination
# resource names exceed SQL's 32-character plaintext prefix; never guess their
# undocumented internal hash or attribute a holder from that prefix alone.
_QUERY = """
SET NOCOUNT ON;
IF COALESCE(HAS_PERMS_BY_NAME(NULL,NULL,
 CASE WHEN CONVERT(int,SERVERPROPERTY('ProductMajorVersion'))>=16
 THEN 'VIEW SERVER PERFORMANCE STATE' ELSE 'VIEW SERVER STATE' END),0)<>1
BEGIN SELECT 'permission_unavailable'; RETURN; END;
SELECT TOP(3) 'observed',SYSUTCDATETIME(),@@SPID,
 rs.login_time,CONVERT(varchar(36),rc.connection_id),rc.connect_time,
 s.session_id,s.login_time,CONVERT(varchar(36),c.connection_id),c.connect_time,
 l.request_owner_type,l.request_mode
FROM sys.dm_tran_locks l
JOIN sys.dm_exec_sessions s ON s.session_id=l.request_session_id
JOIN sys.dm_exec_connections c ON c.session_id=s.session_id
JOIN sys.dm_exec_sessions rs ON rs.session_id=@@SPID
JOIN sys.dm_exec_connections rc ON rc.session_id=@@SPID
WHERE l.resource_type='APPLICATION' AND l.resource_database_id=DB_ID()
 AND l.resource_associated_entity_id=DATABASE_PRINCIPAL_ID('public')
 AND l.request_status='GRANT' AND l.request_session_id<>@@SPID
 AND LEFT(RTRIM(l.resource_description),LEN(?)) COLLATE Latin1_General_100_BIN2=?;
"""


def observe_holder(cursor, *, resource, requester, original):
    """Keep the refusal primary even if optional evidence or its cleanup fails.

    Only an ended, exactly attributed timeout refusal may call this helper. The
    caller still owns rollback/connection close; this function owns just its new
    diagnostic cursor. No second login or alternate credential profile is used.
    """
    evidence = dict(status="unavailable", reason="resource_not_supported")
    if resource != SNAPSHOT_RESOURCE:
        if isinstance(resource, str) and len(resource) > 32:
            evidence["reason"] = "resource_name_truncated"
        return evidence
    connection = diagnostic = None
    previous = None
    interruption = None
    cleanup_error = None
    try:
        connection = cursor.connection
        previous = connection.timeout
        if type(previous) is not int or previous < 0:
            return dict(status="unavailable", reason="bounded_connection_unavailable")
        connection.timeout = DIAGNOSTIC_TIMEOUT_SECONDS
        diagnostic = connection.cursor()
        # The driver copies this setting at cursor creation. Restore before any
        # diagnostic statement; no following business cursor inherits this limit.
        connection.timeout = previous
        prefix = "0:[" + SNAPSHOT_RESOURCE + "]:("
        rows = diagnostic.execute(_QUERY, prefix, prefix).fetchmany(3)
        if len(rows) == 1 and rows[0][0] == "permission_unavailable":
            evidence["reason"] = "permission_unavailable"
        elif len(rows) != 1:
            evidence["reason"] = "holder_disappeared_or_ambiguous"
        else:
            row = rows[0]
            if (
                len(row) != 12
                or row[0] != "observed"
                or type(row[2]) is not int
                or row[2] != requester
                or type(row[6]) is not int
                or not 1 <= row[6] <= 32767
                or row[6] == requester
                or any(not isinstance(row[i], datetime) for i in (1, 3, 5, 7, 9))
                or row[10] not in {"SESSION", "TRANSACTION"}
                or row[11] not in {"S", "U", "X", "IS", "IX", "SIX"}
            ):
                evidence["reason"] = "identity_unavailable"
            else:
                evidence = dict(
                    status="observed_after_refusal",
                    provenance="current_database_application_lock_dmv",
                    observed_utc=row[1].isoformat(),
                    requester=dict(
                        session_id=requester,
                        session_birth=row[3].isoformat(),
                        connection_id=str(UUID(row[4])),
                        connected_at=row[5].isoformat(),
                    ),
                    holder=dict(
                        session_id=row[6],
                        session_birth=row[7].isoformat(),
                        connection_id=str(UUID(row[8])),
                        connected_at=row[9].isoformat(),
                        owner_type=row[10],
                        lock_mode=row[11],
                    ),
                )
    except BaseException as error:
        evidence = dict(status="unavailable", reason="observation_failed")
        original.add_note("Holder observation failed: " + type(error).__name__)
        if not isinstance(error, Exception):
            interruption = error
    finally:
        for phase, action in (
            ("timeout_restore", lambda: setattr(connection, "timeout", previous)),
            ("cursor_close", diagnostic.close if diagnostic is not None else None),
        ):
            if connection is None or type(previous) is not int or action is None:
                continue
            try:
                action()
            except BaseException as error:
                evidence = dict(status="unavailable", reason="cleanup_unconfirmed")
                original.add_note("Holder " + phase + " failed: " + type(error).__name__)
                cleanup_error = cleanup_error or error
                if not isinstance(error, Exception) and interruption is None:
                    interruption = error
        if cleanup_error is not None:
            # One bundle per connection, retaining its cursor even when several
            # cleanup steps fail. Counts describe owners rather than failures.
            retain_connection(
                SimpleNamespace(connection=connection, cursor=diagnostic),
                effect="not_started",
                first_failure=original,
                cleanup_error=cleanup_error,
            )
    if interruption is not None:
        raise interruption from original
    return evidence
