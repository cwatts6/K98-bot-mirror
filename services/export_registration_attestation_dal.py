"""Append-only independent activation witnesses under the existing account lock."""

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _mutex, identity


class RegistrationAttestationDAL:
    def __init__(self, connect, account):
        self.connect, self.account = connect, account

    def latest(self, activation_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP(1) * FROM dbo.ExportRegistrationAttestation WHERE AccountKey=? AND ActivationID=? "
                "ORDER BY CreatedUTC DESC,ActionID DESC",
                self.account,
                identity(activation_id),
            )
            row = one(cursor)
            if row is None:
                return None
            result = _wire(row)
            for key in ("ActionID", "ActivationID", "OriginalReference", "ReceiptReference"):
                result[key] = identity(row[key])
            return result

    def save(self, expected, proof, *, action_id, token, receipt, actor, reason):
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + self.account)
            cursor.execute(
                "SELECT a.*,c.OutputOperationID FROM dbo.ExportReplacementActivation a WITH(UPDLOCK,HOLDLOCK) "
                "JOIN dbo.ExportReplacementPlan p ON p.ReplacementID=a.ReplacementID "
                "JOIN dbo.ExportTargetContainment c ON c.ContainmentID=p.ContainmentID AND c.AccountKey=a.AccountKey "
                "WHERE a.AccountKey=? AND a.ActivationID=?",
                self.account,
                expected["ActivationID"],
            )
            found = rows(cursor)
            if len(found) != 1 or _wire(found[0]) != expected:
                raise SourceConflict("Exact activation binding changed during attestation.")
            cursor.execute(
                "INSERT dbo.ExportRegistrationAttestation(ActionID,ActivationID,AccountKey,OriginalReference,OriginalHash,"
                "ReviewHash,ProjectionHash,ReceiptReference,ReceiptHash,Actor,Reason) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                action_id,
                expected["ActivationID"],
                self.account,
                expected["ReceiptReference"],
                bytes.fromhex(expected["ReceiptHash"]),
                bytes.fromhex(token),
                digest(proof),
                receipt["reference"],
                bytes.fromhex(receipt["sha256"]),
                actor,
                reason,
            )
