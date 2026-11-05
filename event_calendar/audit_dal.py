"""Optional EventSyncLog writes, on independent configured SQL-login sessions."""

from dataclasses import dataclass

from constants import _conn
from event_calendar.sql_lifecycle import SqlOutcome, SqlSession, error_facts
from file_utils import UnitTestLiveDbAccessError, _is_pytest_unit_mode


@dataclass
class AuditResult:
    sync_id: int | None
    sql: SqlOutcome


def _session():
    def connect():
        if _is_pytest_unit_mode():
            raise UnitTestLiveDbAccessError("Calendar audit requires an isolated SQL fixture")
        return _conn()

    return SqlSession(connect)


def _cursor(session):
    session.connection.timeout = 2
    cursor = session.cursor()
    cursor.execute("SET LOCK_TIMEOUT 250")
    return cursor


def start(started) -> AuditResult:
    session = _session()
    sync_id = None
    try:
        with session:
            cursor = _cursor(session)
            cursor.execute(
                """INSERT INTO dbo.EventSyncLog (SyncStartedUTC, SourceName, Status)
                   OUTPUT INSERTED.SyncID VALUES (?, ?, ?)""",
                started.replace(tzinfo=None),
                "google_sheets",
                "running",
            )
            candidate = int(cursor.fetchone()[0])
            session.commit()
            sync_id = candidate
    except Exception as error:
        session.outcome.error = error_facts(error)
    return AuditResult(sync_id, session.outcome)


def finish(sync_id: int, result: dict, completed) -> AuditResult:
    session = _session()
    try:
        with session:
            cursor = _cursor(session)
            cursor.execute(
                """UPDATE dbo.EventSyncLog SET SyncCompletedUTC = ?, Status = ?,
                   RowsReadRecurring = ?, RowsReadOneOff = ?, RowsReadOverrides = ?,
                   RowsUpsertedRecurring = ?, RowsUpsertedOneOff = ?, RowsUpsertedOverrides = ?,
                   InstancesGenerated = ?, ErrorMessage = ? WHERE SyncID = ?""",
                completed.replace(tzinfo=None),
                result["status"][:32],
                result.get("rows_read_recurring"),
                result.get("rows_read_oneoff"),
                result.get("rows_read_overrides"),
                result.get("rows_upserted_recurring"),
                result.get("rows_upserted_oneoff"),
                result.get("rows_upserted_overrides"),
                result.get("instances_generated"),
                result.get("error_message"),
                sync_id,
            )
            session.commit()
    except Exception as error:
        session.outcome.error = error_facts(error)
    return AuditResult(sync_id, session.outcome)
