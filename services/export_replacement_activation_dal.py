"""Append-only registration activation with scoped chain reads."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import identity


def origin_rows(cursor, account, targets):
    cursor.execute(
        "SELECT t.NewFileID AS FileID,a.ActivationID,a.ReplacementID,a.VerificationID,a.NewPoolID,"
        "a.ReceiptHash,a.ReceiptReference,a.RegistrationHash,a.RegistrationJson,"
        "v.PlanHash,v.ReceiptHash AS VerificationReceiptHash,v.ReceiptReference AS VerificationReceiptReference,"
        "p.RequestJson,p.RequestHash,p.State AS PreparationState,s.StreamID,s.SessionID "
        "FROM dbo.ExportReplacementActivation a JOIN dbo.ExportReplacementTarget t ON t.ReplacementID=a.ReplacementID "
        "JOIN dbo.ExportReplacementVerification v ON v.VerificationID=a.VerificationID AND v.ReplacementID=a.ReplacementID "
        "JOIN dbo.ExportPreparation p ON p.PreparationID=v.PreparationID "
        "JOIN dbo.ExportExecutionStream s ON s.PreparationID=v.PreparationID "
        "JOIN OPENJSON(?) WITH(FileID varchar(128) '$') requested ON requested.FileID=t.NewFileID "
        "WHERE a.AccountKey=? AND p.AccountKey=a.AccountKey AND a.NewPoolID IS NOT NULL "
        "AND v.State='verified' AND v.Version=2 AND p.State='completed' AND p.RequestHash=v.PlanHash "
        "AND s.State='closed' AND s.ActiveAccountKey IS NULL ORDER BY t.NewFileID",
        json.dumps(targets),
        account,
    )
    return rows(cursor)


class ReplacementActivationDAL:
    def __init__(self, connect):
        self.connect = connect

    def chain(self, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportReplacementActivation WHERE AccountKey=? ORDER BY CreatedUTC,ActivationID",
                account,
            )
            return [_wire(r) for r in rows(cursor)]

    def activate(
        self, *, activation_id, proposal, verification_id, account, receipt, actor, reason, old_pool
    ):
        pool = proposal["pool_registration"]
        with transaction(self.connect) as cursor:
            cursor.execute(
                "EXEC dbo.usp_ExportReplacementActivate @ActivationID=?,@ReplacementID=?,@VerificationID=?,"
                "@AccountKey=?,@BaseRegistrationHash=?,@RegistrationHash=?,@RegistrationJson=?,@ReceiptHash=?,@ReceiptReference=?,"
                "@Actor=?,@Reason=?,@OldPoolID=?,@OldPoolVersion=?,@PoolRegistrationJson=?,@PoolRegistrationHash=?",
                identity(activation_id),
                identity(proposal["replacement_id"]),
                identity(verification_id),
                account,
                bytes.fromhex(proposal["base_registration_sha256"]),
                bytes.fromhex(proposal["registration_sha256"]),
                json.dumps(proposal["registration"], sort_keys=True, separators=(",", ":")),
                bytes.fromhex(receipt["sha256"]),
                identity(receipt["reference"]),
                actor,
                reason,
                old_pool["PoolID"] if old_pool else None,
                old_pool["Version"] if old_pool else None,
                json.dumps(pool, sort_keys=True, separators=(",", ":")) if pool else None,
                digest(pool) if pool else None,
            )
            if one(cursor) is None:
                raise SourceConflict("Activation reply is missing; verify the original receipt.")
