"""Exact recovery CAS on existing SQL contracts; no provider operations."""

import hashlib
import threading

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, one
from services.export_contention import CoordinationLockRefused, sql_error_facts
from services.export_execution_dal import _PARAMETERS, _PROCEDURES, ExportExecutionDAL
from services.export_execution_lock import execution_account_lock
from services.export_execution_protocol import encode


class RecoveryWaiting(RuntimeError):
    """Connection was closed; next attempt must reconcile authoritative receipts."""


class RecoveryConnections:
    """Single-worker connection custody across all existing verifier/DAL calls."""

    def __init__(self, connect):
        self.factory = connect
        self._local = threading.local()

    @property
    def opened(self):
        if not hasattr(self._local, "opened"):
            self._local.opened = []
        return self._local.opened

    @opened.setter
    def opened(self, value):
        self._local.opened = value

    def connect(self):
        # Reconciliation after a lost reply may request a fresh receipt inside
        # the same checkpoint. Never open it until prior cleanup acknowledged.
        self.require_closed()
        owner = self

        class Connection:
            def __init__(self):
                self.inner = owner.factory()
                self.closed = False

            @property
            def autocommit(self):
                return self.inner.autocommit

            @autocommit.setter
            def autocommit(self, value):
                self.inner.autocommit = value

            def __getattr__(self, name):
                return getattr(self.inner, name)

            def close(self):
                self.inner.close()
                self.closed = True

        connection = Connection()
        self.opened.append(connection)
        return connection

    def require_closed(self):
        if any(not connection.closed for connection in self.opened):
            raise SourceConflict("Previous recovery connection cleanup is unconfirmed.")

    def checkpoint(self, work):
        if any(not c.closed for c in self.opened):
            raise SourceConflict("Previous recovery connection cleanup is unconfirmed.")
        self.opened = []
        try:
            result = work()
            if any(not c.closed for c in self.opened):
                raise SourceConflict("Recovery left an unclosed connection.")
            return result
        except Exception as error:
            if any(not c.closed for c in self.opened):
                raise SourceConflict("Recovery connection cleanup is unconfirmed.") from error
            facts = sql_error_facts(error)
            retryable = (
                isinstance(error, (RecoveryWaiting, UncertainCommit))
                or (isinstance(error, CoordinationLockRefused) and error.result == -1)
                or facts["sqlstate"] in {"08S01", "08001", "08003", "HYT00", "HYT01"}
                or bool(set(facts["native_errors"]) & {1205, 1222})
            )
            if retryable:
                raise RecoveryWaiting(
                    "Retained recovery is waiting for exact reconciliation."
                ) from error
            raise


def journal_digest(records):
    """Same ordered fields/encoding as ExportExecutionDAL.stream_digest."""
    hasher = hashlib.sha256()
    count = 0
    for identifier, request, events in records:
        count += 1
        if request["Sequence"] != count or str(request["RequestID"]).lower() != identifier:
            raise SourceConflict("Recovery request sequence differs.")
        if not events:
            raise SourceConflict("Recovery request has no events.")
        for index, event in enumerate(events, 1):
            if event["EventSequence"] != index or str(event["RequestID"]).lower() != identifier:
                raise SourceConflict("Recovery event sequence differs.")
            values = [
                count,
                identifier.upper(),
                request["Operation"],
                request["RequestKind"],
                request["TargetID"],
                bytes(request["PayloadHash"]).hex(),
                str(request["PayloadReference"]).upper(),
                index,
                event["State"],
                str(event["EventID"]).upper(),
                bytes(event["EvidenceHash"]).hex(),
                str(event["EvidenceReference"]).upper(),
            ]
            hasher.update(encode(values) + b"\n")
    return count, hasher.digest()


class SavedResultRecoveryDAL(ExportExecutionDAL):
    def __init__(self, closeout_dal):
        super().__init__(closeout_dal.connect)
        self.closeout_dal = closeout_dal

    def checked_transition(self, expected, kind, **values):
        """Hold account exclusion across snapshot CAS and the procedure's own txn.

        No file/protocol verification occurs here. Cleanup errors escape; callers
        must never blindly replay a transition after a failed acknowledgement.
        """
        if kind not in {"event", "stream"} or not set(values) <= set(_PARAMETERS[kind]):
            raise ValueError("Exact event or stream transition required.")
        if values["AccountKey"] != expected["job"]["AccountKey"]:
            raise SourceConflict("Recovery account differs.")
        names = [name for name in _PARAMETERS[kind] if name in values]
        connection = self.connect()
        failure = None
        admitted = False
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                with execution_account_lock(cursor, values["AccountKey"]):
                    cursor.execute("BEGIN TRANSACTION")
                    try:
                        actual = self.closeout_dal._snapshot(cursor, expected["job"]["JobID"])
                        if actual != expected:
                            raise SourceConflict("Recovery ownership or evidence changed.")
                        cursor.execute("COMMIT")
                        admitted = True
                    except BaseException:
                        cursor.execute("IF @@TRANCOUNT>0 ROLLBACK")
                        raise
                    cursor.execute(
                        "EXEC " + _PROCEDURES[kind] + " " + ",".join("@" + n + "=?" for n in names),
                        *(values[name] for name in names),
                    )
                    result = one(cursor)
                    if result is None or cursor.fetchall():
                        raise SourceConflict("Recovery acknowledgement missing or malformed.")
                    while cursor.nextset():
                        if cursor.description is not None and cursor.fetchall():
                            raise SourceConflict("Unexpected recovery acknowledgement.")
                    return result
            except SourceConflict as exc:
                if not admitted:
                    raise
                failure = exc
            except Exception as exc:
                failure = exc
            finally:
                cursor.close()
        finally:
            connection.close()
        if failure is not None:
            facts = sql_error_facts(failure)
            if isinstance(failure, CoordinationLockRefused) and failure.result != -1:
                raise failure
            if (
                facts["sqlstate"]
                and facts["sqlstate"] not in {"08S01", "08001", "08003", "HYT00", "HYT01"}
                and not set(facts["native_errors"]) & {1205, 1222}
            ):
                raise failure
            if not facts["sqlstate"] and not isinstance(
                failure, (CoordinationLockRefused, SourceConflict, OSError, RecoveryWaiting)
            ):
                raise failure
            raise RecoveryWaiting(
                "Recovery transition needs fresh receipt reconciliation."
            ) from failure
