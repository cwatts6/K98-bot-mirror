"""Locked legacy closeout snapshots and authority-only SQL settlement."""

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import identity
from services.export_target_containment_dal import ExportTargetContainmentDAL


def _receipt_wire(row):
    """Match SQL uniqueidentifier values to canonical private receipt identities.

    ODBC can return uppercase GUID strings. Normalize only typed receipt IDs;
    signed historical bodies and case-sensitive provider file IDs stay intact.
    """
    if row is None:
        return None
    value = _wire(row)
    for column in ("ActionID", "ContainmentID", "ReceiptReference"):
        if value.get(column) is not None:
            value[column] = identity(value[column])
    return value


class LegacyExportCloseoutDAL:
    def __init__(self, connect, *, account, storage_owner):
        self.connect, self.account, self.storage_owner = connect, account, storage_owner

    def receipt_exists(self, job_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT c.ActionID FROM dbo.ExportLegacyCloseout c JOIN dbo.ExportJob j "
                "ON j.JobID=c.JobID WHERE j.JobID=? AND j.AccountKey=? AND j.StorageOwner=? "
                "AND j.ConsumerKind IN ('scan_data','all_kvk')",
                identity(job_id),
                self.account,
                self.storage_owner,
            )
            return one(cursor) is not None

    def _snapshot(self, cursor, job_id):
        state = ExportTargetContainmentDAL._snapshot(cursor, job_id, self.account, None)
        state["receipt"] = _receipt_wire(state["receipt"])
        job = state["job"]
        # Later jobs may legitimately own this account after closeout. Their
        # execution must block a new decision without reopening old history.
        state["foreign_streams"] = [s for s in state["streams"] if s["JobID"] != job_id]
        state["streams"] = [s for s in state["streams"] if s["JobID"] == job_id]
        if job["StorageOwner"] != self.storage_owner or job["ConsumerKind"] not in {
            "scan_data",
            "all_kvk",
        }:
            raise SourceConflict("Legacy export is outside registered custody.")
        cursor.execute("SELECT * FROM dbo.ExportAttempt WHERE JobID=? ORDER BY AttemptID", job_id)
        state["attempts"] = _wire(rows(cursor))
        cursor.execute("SELECT * FROM dbo.ExportLegacyCloseout WHERE JobID=?", job_id)
        receipt = one(cursor)
        state["closeout"] = _receipt_wire(receipt)
        cursor.execute(
            "SELECT ReplacementID FROM dbo.ExportReplacementPlan WHERE ContainmentID IN "
            "(SELECT ContainmentID FROM dbo.ExportTargetContainment WHERE JobID=?) ORDER BY ReplacementID",
            job_id,
        )
        state["replacements"] = _wire(rows(cursor))
        cursor.execute(
            "SELECT FileID,ContainmentID FROM dbo.ExportContainedTarget WHERE ContainmentID IN "
            "(SELECT ContainmentID FROM dbo.ExportTargetContainment WHERE JobID=?) ORDER BY FileID",
            job_id,
        )
        state["contained_targets"] = _wire(rows(cursor))
        return state

    def snapshot(self, job_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, identity(job_id))

    def settle(self, expected, *, action_id, token, marker, actor, reason):
        with transaction(self.connect) as cursor:
            job = expected["job"]
            if self._snapshot(cursor, job["JobID"]) != expected:
                raise SourceConflict("Export evidence changed; no restriction was lifted.")
            cursor.execute(
                "EXEC dbo.usp_ExportLegacyCloseout @ActionID=?,@JobID=?,@AccountKey=?,"
                "@StorageOwner=?,@ExpectedVersion=?,@OwnerID=?,@Fence=?,@SnapshotHash=?,"
                "@ReceiptHash=?,@ReceiptReference=?,@Actor=?,@Reason=?",
                identity(action_id),
                job["JobID"],
                self.account,
                self.storage_owner,
                job["Version"],
                job["OwnerID"],
                job["Fence"],
                bytes.fromhex(token),
                bytes.fromhex(marker["sha256"]),
                marker["reference"],
                actor,
                reason,
            )
            if one(cursor) is None:
                raise SourceConflict(
                    "Closeout acknowledgement missing; reconcile the saved action."
                )
