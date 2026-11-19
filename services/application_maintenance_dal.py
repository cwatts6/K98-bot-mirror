"""Consistent, bounded application catalogue/maintenance observation.

The caller owns the connection and transaction. Only a session schema lock is
borrowed; no commit, rollback, maintenance or receipt mutation is performed.
"""

from contextlib import contextmanager
import json
from types import SimpleNamespace

from core.sql_connection_custody import SqlCleanupUnknown, retain_connection
from kvk.dal.new_source_import_dal import SourceConflict
from services.application_maintenance_contract import POLICY, RESOURCE, policy_objects

SCHEMA_ACQUIRE_SQL = (
    "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,"
    "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r"
)
SCHEMA_RELEASE_SQL = (
    "DECLARE @r int; EXEC @r=sys.sp_releaseapplock @Resource=?,"
    "@LockOwner='Session'; SELECT @r,APPLOCK_MODE('public',?,'Session')"
)


class SchemaObservationRefused(SourceConflict):
    """An acknowledged refusal owns no schema lock and proves no schema drift.

    Preserve SourceConflict compatibility for business callers. Only the separate
    verification-only entry point classifies -1 as pending, with no retry.
    """

    def __init__(self, result):
        self.result = result
        super().__init__("Application schema observation is busy or refused; no retry performed.")


@contextmanager
def schema_observation(cursor):
    """Exclude both publishers and maintenance without taking a second writer lock.

    The actual business cursor can be on a different connection from the outer
    writer admission owner. Reacquiring its global writer lock would self-block.
    P02 publishers take Shared transaction schema ownership; maintenance takes
    Exclusive session ownership. A zero-wait Exclusive observation excludes both.
    Never upgrade/release an existing caller-owned lock or change isolation.
    """
    from core.sql_connection_custody import require_sql_admission

    require_sql_admission()
    cursor.execute(
        # Transaction-owned APPLOCK_MODE raises SQL3918 without a user
        # transaction. Branch in SQL on actual session state, not the driver's
        # autocommit flag (manual mode need not have started a transaction yet).
        # IF keeps the function out of the no-transaction execution path.
        "DECLARE @transaction_mode nvarchar(32)=N'NoLock'; "
        "IF @@TRANCOUNT>0 "
        "SET @transaction_mode=APPLOCK_MODE('public',?,'Transaction'); "
        "SELECT APPLOCK_MODE('public',?,'Session'),"
        "@transaction_mode,transaction_isolation_level "
        "FROM sys.dm_exec_sessions WHERE session_id=@@SPID",
        RESOURCE,
        RESOURCE,
    )
    row = cursor.fetchone()
    if row is None or row[0] != "NoLock" or row[1] != "NoLock" or row[2] != 2:
        raise SourceConflict(
            "Application schema observation requires an unowned READ COMMITTED cursor."
        )
    attempted = False
    acquired = False
    failed = None
    try:
        attempted = True
        cursor.execute(SCHEMA_ACQUIRE_SQL, RESOURCE)
        result = cursor.fetchone()
        if result is None or type(result[0]) is not int:
            raise SqlCleanupUnknown("Application schema observation acquisition is unconfirmed.")
        if result[0] in {-1, -2, -3, -999}:
            # A negative acknowledged return owns no lock. Do not retry.
            attempted = False
            raise SchemaObservationRefused(result[0])
        if result[0] not in {0, 1}:
            raise SqlCleanupUnknown("Application schema observation acquisition result is unknown.")
        acquired = True
        yield
    except BaseException as error:
        failed = error
        raise
    finally:
        if attempted:
            try:
                # If acquisition acknowledgement was lost, ownership is unknown.
                # Do not guess whether release or connection close is safe.
                if not acquired:
                    raise SqlCleanupUnknown("Application schema ownership was not acknowledged.")
                # A bounded observer may have exhausted admission for new reads.
                # Only its explicit, single-use cleanup operation bypasses that
                # admission budget. Ordinary runtime cursors retain this SQL path.
                release = getattr(type(cursor), "release_schema_observation", None)
                if release is None:
                    cursor.execute(SCHEMA_RELEASE_SQL, RESOURCE, RESOURCE)
                    result = cursor.fetchone()
                else:
                    result = release(cursor, RESOURCE)
                if result is None or result[0] != 0 or result[1] != "NoLock":
                    raise SqlCleanupUnknown(
                        "Application schema observation release is unconfirmed."
                    )
            except BaseException as cleanup:
                retain_connection(
                    SimpleNamespace(connection=cursor.connection, cursor=cursor),
                    effect="not_applicable",
                    first_failure=failed or cleanup,
                    cleanup_error=cleanup,
                )
                raise SqlCleanupUnknown(
                    "Application schema observation retained for cleanup review."
                ) from (failed or cleanup)


def maintenance_snapshot(cursor, approved, read_metadata):
    """Read metadata and durable publication binding under one schema exclusion."""
    objects = policy_objects(approved)
    with schema_observation(cursor):
        result = read_metadata()
        cursor.execute(
            "SELECT j.ObjectName,o.object_id AS ObjectID,"
            "CONVERT(nvarchar(30),o.create_date,126) AS ObjectCreated,"
            "h.Revision AS HeaderRevision,h.State AS HeaderState,w.KVKNo,"
            "w.DueGeneration,w.CompletedGeneration,w.DueObjectID,"
            "CONVERT(nvarchar(30),w.DueObjectCreateDate,126) AS DueObjectCreated,"
            "w.DueHeaderRevision,w.State,w.ClaimedGeneration,"
            "a.DueGeneration AS AggregateDue,a.CompletedGeneration AS AggregateCompleted,"
            "a.State AS AggregateState "
            "FROM OPENJSON(?) WITH(ObjectName nvarchar(128),KVKNo int) j "
            "LEFT JOIN sys.tables o ON o.object_id=OBJECT_ID(j.ObjectName,'U') "
            "LEFT JOIN dbo.KVKFinalReportHeader h ON h.KVK_NO=j.KVKNo "
            "LEFT JOIN dbo.MaintenanceKvkWork w ON w.KVKNo=j.KVKNo "
            "LEFT JOIN dbo.MaintenanceWork a ON a.Kind='kvk_output' "
            "ORDER BY j.ObjectName COLLATE Latin1_General_100_BIN2",
            json.dumps([{"ObjectName": name, "KVKNo": season} for name, season in objects]),
        )
        from services.export_execution_dal import rows

        result["maintenance_lifecycle"] = {
            "policy": POLICY,
            "guard": "exclusive_schema_observation",
            "outputs": rows(cursor),
        }
        return result
