"""Short, consistent metadata observations; never grant recovery authority.

The database must explicitly allow SNAPSHOT isolation. There is no locking-read
fallback and this module never enables a database setting. Recovery mutations
retain their independent session guards, current-row locks and evidence CAS.
"""

from contextlib import contextmanager
import re

from core.sql_connection_custody import require_sql_admission, retain_connection
from core.sql_observation import ObservationBusy, lock_contention, observation
from core.sql_operation_policy import RECOVERY_STATEMENT_SECONDS
from kvk.dal.source_sql_diagnostics import diagnostic_call, diagnostic_cursor

STATEMENT_TIMEOUT_SECONDS = RECOVERY_STATEMENT_SECONDS
# Microsoft ODBC Driver 18 SDK, msodbcsql.h. SNAPSHOT is a SQL Server-specific
# connection attribute; a SET statement is too late with ODBC automatic BEGIN.
SQL_COPT_SS_TXN_ISOLATION = 1227
SQL_TXN_SS_SNAPSHOT = 0x20
SQL_TXN_READ_COMMITTED = 0x02


class RecoveryObservationCleanupUnknown(RuntimeError):
    """The read failed to acknowledge cleanup; do not classify it as ordinary busy."""


def require_recovery_snapshot_isolation(cursor):
    """Additional startup prerequisite, independent of the three source contracts."""
    cursor.execute("SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID()")
    row = cursor.fetchone()
    if row is None or row[0] != 1:
        raise RuntimeError(
            "Recovery observations require reviewed SNAPSHOT isolation enabled on this database."
        )


@contextmanager
def recovery_snapshot(connect):
    """Own one dedicated read transaction through physical rollback and close.

    No business commit, retry or producer admission lock is performed here.
    A shared transaction guard excludes optional schema maintenance only.
    A snapshot is a preview: it does not prove that a producer has physically ended.
    """
    require_sql_admission()
    connection = diagnostic_call("connect", connect)
    cursor = None
    failure = None
    cleanup_failed = False
    retain_open = False
    try:
        require_sql_admission()
        if connection.autocommit:
            raise ValueError("Recovery observation requires a dedicated transactional connection.")
        # Set before creating the cursor; LOCK_TIMEOUT is a different budget.
        connection.timeout = STATEMENT_TIMEOUT_SECONDS
        # This is a newly owned factory connection, never a borrowed producer.
        # End factory setup, then select isolation BEFORE entering manual-commit
        # mode. ODBC's automatic BEGIN otherwise starts at the old isolation.
        diagnostic_call("snapshot_begin", connection.rollback)
        connection.autocommit = True
        diagnostic_call(
            "isolation", connection.set_attr, SQL_COPT_SS_TXN_ISOLATION, SQL_TXN_SS_SNAPSHOT
        )
        connection.autocommit = False
        cursor = diagnostic_cursor(diagnostic_call("cursor", connection.cursor))
        with observation():
            cursor.execute(
                "SET LOCK_TIMEOUT 0; SET XACT_ABORT ON; SET NOCOUNT ON; "
                "DECLARE @r int; EXEC @r=sys.sp_getapplock "
                "@Resource='K98:maintenance-schema:v1',@LockMode='Shared',"
                "@LockOwner='Transaction',@LockTimeout=0; "
                "IF @r=-1 THROW 51966,'Observation schema maintenance busy.',1; "
                "ELSE IF @r<0 THROW 51967,'Observation schema guard not acquired.',1;"
            )
            yield cursor
    except BaseException as error:
        failure = error
    finally:
        # Attempt every cleanup step and preserve the first failure. Never return
        # a successful/busy observation if physical cleanup was not acknowledged.
        for phase, action in (
            ("rollback", connection.rollback),
            (
                "isolation_restore",
                lambda: connection.set_attr(SQL_COPT_SS_TXN_ISOLATION, SQL_TXN_READ_COMMITTED),
            ),
            ("cursor_close", cursor.close if cursor is not None else None),
            ("close", connection.close),
        ):
            if action is None or retain_open:
                continue
            try:
                diagnostic_call(phase, action)
            except BaseException as error:
                cleanup_failed = True
                if failure is None:
                    failure = error
                else:
                    failure.add_note(f"Recovery observation {phase} failed: {type(error).__name__}")
                if phase in {"rollback", "close"}:
                    # A failed rollback may still own the shared transaction
                    # guard. Never return it to a pool or change its isolation.
                    retain_open = True
                    retain_connection(
                        connection,
                        effect="not_applicable",
                        first_failure=failure,
                        cleanup_error=error,
                    )
    if failure is not None:
        if cleanup_failed:
            raise RecoveryObservationCleanupUnknown(
                "Recovery observation cleanup was not acknowledged; retain its first failure."
            ) from failure
        args = getattr(failure, "args", ())
        schema_busy = bool(
            args
            and args[0] == "42000"
            and any(isinstance(v, str) and re.search(r"\(51966\)", v[:8192]) for v in args[1:5])
        )
        if (lock_contention(failure) or schema_busy) and not cleanup_failed:
            raise ObservationBusy(
                "Recovery metadata is busy; retain the previous observation."
            ) from failure
        raise failure
