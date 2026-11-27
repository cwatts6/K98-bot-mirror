"""Append-only present-state witnesses; no ownership or historical-receipt edits."""

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import identity


class ContainmentAttestationDAL:
    def __init__(self, connect, account):
        self.connect, self.account = connect, account

    def binding(self, reference):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportTargetContainment WHERE AccountKey=? AND ReceiptReference=?",
                self.account,
                identity(reference),
            )
            found = rows(cursor)
        if len(found) != 1:
            raise SourceConflict("One exact registered containment binding is required.")
        return _wire(found[0])

    def streams(self, containment_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT s.* FROM dbo.ExportContainedStream s JOIN dbo.ExportTargetContainment c "
                "ON c.ContainmentID=s.ContainmentID WHERE c.AccountKey=? AND c.ContainmentID=? "
                "ORDER BY CONVERT(varchar(36),s.StreamID)",
                self.account,
                identity(containment_id),
            )
            return [dict(_wire(row), StreamID=identity(row["StreamID"])) for row in rows(cursor)]

    def latest(self, containment_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) * FROM dbo.ExportContainmentAttestation WHERE AccountKey=? "
                "AND ContainmentID=? ORDER BY CreatedUTC DESC,ActionID DESC",
                self.account,
                identity(containment_id),
            )
            result = one(cursor)
            if result is None:
                return None
            normalized = _wire(result)
            for field in ("ActionID", "ContainmentID", "OriginalReference", "ReceiptReference"):
                normalized[field] = identity(result[field])
            return normalized

    def save(self, service, expected, projection, *, action_id, token, receipt, actor, reason):
        from kvk.dal.new_source_import_dal import digest

        original = expected["receipt"]
        if "operation" in expected:
            owner, pool = expected["operation"]["OperationID"], expected["pool"]["pool"]["PoolID"]
        else:
            owner = expected["job"]["JobID"]
            pool = expected["pool"]["PoolID"] if expected["pool"] else None
        with transaction(self.connect) as cursor:
            current = service.dal._snapshot(cursor, owner, self.account, pool)
            if current != expected:
                raise SourceConflict("Containment changed; no successor receipt was admitted.")
            cursor.execute(
                "INSERT dbo.ExportContainmentAttestation(ActionID,ContainmentID,AccountKey,OriginalReference,"
                "OriginalHash,ReviewHash,ProjectionHash,ReceiptReference,ReceiptHash,Actor,Reason) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                identity(action_id),
                original["ContainmentID"],
                self.account,
                original["ReceiptReference"],
                bytes.fromhex(original["ReceiptHash"]),
                bytes.fromhex(token),
                digest(projection),
                receipt["reference"],
                bytes.fromhex(receipt["sha256"]),
                actor,
                reason,
            )
