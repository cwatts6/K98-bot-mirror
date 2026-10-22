"""Resume only transactionally receipted reports; never call the import entry point."""

import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from services.export_coordination_dal import _cas, _mutex, identity
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL


class StatsReportContinuationDAL:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.guards = ImportCaptureRecoveryDAL(outcomes)

    def pending_recovery(self, *, after=None):
        with transaction(self.outcomes.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) c.PreparationID FROM dbo.StatsImportReportContinuation c "
                "JOIN dbo.StatsImportExecution e ON e.PreparationID=c.PreparationID "
                "JOIN dbo.ExportPreparation p ON p.PreparationID=c.PreparationID "
                "WHERE p.AccountKey=? AND p.StorageOwner=? AND p.ConsumerKind='scan_data' "
                "AND e.Resolution IS NULL AND c.CompletedStage<3 "
                "AND e.State IN ('import_committed','partial') "
                "ORDER BY CASE WHEN c.PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,c.PreparationID",
                self.outcomes.account,
                self.outcomes.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["PreparationID"]) for row in rows(cursor)]

    def _snapshot(self, cursor, source_id):
        prep, execution, resources = self.outcomes._snapshot(cursor, identity(source_id))
        self.outcomes._scope(prep)
        cursor.execute(
            "SELECT * FROM dbo.StatsImportReportContinuation WITH (UPDLOCK,HOLDLOCK) "
            "WHERE PreparationID=?",
            identity(source_id),
        )
        receipt = one(cursor)
        if not receipt or not execution or receipt["ContractVersion"] != 1:
            raise SourceConflict(
                "No transactional reporting contract survives. Historical partial reports "
                "need an independent successor decision; they cannot be replayed."
            )
        if receipt["ScanOrder"] != execution["ScanOrder"] or execution["Resolution"]:
            raise SourceConflict("The committed import identity or disposition changed.")
        complete = receipt["CompletedStage"] == 3 and execution["State"] == "completed"
        explanation = None
        if not complete:
            try:
                cursor.execute(
                    "EXEC dbo.usp_S11ValidateStatsReportStage @PreparationID=?,@CompletedFileName=?",
                    identity(source_id),
                    execution["CompletedFileName"],
                )
                while cursor.nextset():
                    pass
            except Exception:
                # Do not hide a database failure or try to commit a doomed transaction.
                raise SourceConflict(
                    "Reporting inputs, configuration, ownership or writer exclusion no longer "
                    "verify. Preserve the existing stage receipts and review the blocker."
                ) from None
        document = [prep, execution, resources, receipt]
        token = hashlib.sha256(
            json.dumps(document, sort_keys=True, default=str).encode()
        ).hexdigest()
        return dict(
            preparation=prep,
            execution=execution,
            receipt=receipt,
            token=token,
            complete=complete,
            explanation=explanation,
        )

    def inspect(self, source_id):
        with self.guards.session(source_id) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                result = self._snapshot(cursor, source_id)
                cursor.execute("COMMIT TRANSACTION")
                return result
            finally:
                cursor.execute("IF @@TRANCOUNT>0 ROLLBACK")
                cursor.close()

    def run(self, source_id, token, action_id):
        """Commit the exact intent, then skip every already committed stage.

        A repeated action is safe only under both session guards and its saved
        marker. A known failed attempt needs a fresh confirmation. A lost reply
        is reconciled from the same transaction checkpoints, never a timer.
        """
        source_id, action_id = identity(source_id), identity(action_id)
        with self.guards.session(source_id) as connection:
            cursor = connection.cursor()
            dispatched = False
            try:
                cursor.execute("BEGIN TRANSACTION")
                _mutex(cursor, "account:" + self.outcomes.account)
                snapshot = self._snapshot(cursor, source_id)
                receipt = snapshot["receipt"]
                same = (
                    receipt["RecoveryActionID"] is not None
                    and identity(receipt["RecoveryActionID"]) == action_id
                    and receipt["RecoveryEvidenceHash"] == token
                )
                if same and snapshot["complete"]:
                    cursor.execute("COMMIT TRANSACTION")
                    return
                if snapshot["complete"] or (same and receipt["RecoveryState"] == "failed"):
                    raise SourceConflict(
                        "This attempt ended; review the current reporting outcome."
                    )
                if not same:
                    if snapshot["token"] != token or receipt["RecoveryState"] == "running":
                        raise SourceConflict(
                            "Reporting evidence changed or an accepted repair is unresolved."
                        )
                    _cas(
                        cursor,
                        "UPDATE dbo.StatsImportReportContinuation SET RecoveryActionID=?,"
                        "RecoveryEvidenceHash=?,RecoveryState='running',Version=Version+1 "
                        "OUTPUT inserted.Version WHERE PreparationID=? AND Version=?",
                        action_id,
                        token,
                        source_id,
                        receipt["Version"],
                    )
                cursor.execute("COMMIT TRANSACTION")
                # A lost marker-commit reply exits before dispatch. Reconciliation
                # subsequently obtains these same guards and verifies that marker.
                dispatched = True
                cursor.execute(
                    "EXEC dbo.usp_S11CompleteStatsReports @CompletedFileName=?,@ExportPreparationID=?",
                    snapshot["execution"]["CompletedFileName"],
                    source_id,
                )
                while cursor.nextset():
                    pass
            except BaseException:
                try:
                    cursor.execute("IF @@TRANCOUNT>0 ROLLBACK")
                    if dispatched:
                        # Only on the original guarded session, after its failed
                        # statement ended. Never turn a committed final receipt
                        # into failure because its response was lost.
                        cursor.execute(
                            "UPDATE dbo.StatsImportReportContinuation SET RecoveryState='failed',"
                            "Version=Version+1 WHERE PreparationID=? AND RecoveryActionID=? "
                            "AND RecoveryEvidenceHash=? AND RecoveryState='running' AND CompletedStage<3",
                            source_id,
                            action_id,
                            token,
                        )
                except Exception:
                    pass
                raise
            finally:
                cursor.close()
