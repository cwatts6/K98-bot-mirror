"""Account-scoped private-evidence inventory from existing authoritative bindings.

No schema writes or caller-selected SQL. JSON paths are the exact private
bindings authored by child birth, read containment and queued replacement.
"""

from kvk.dal.new_source_import_dal import SourceConflict, rows, transaction
from services.export_coordination_dal import identity


def _select(reference, sha, source, label, account="x.AccountKey"):
    return (
        f"SELECT {reference} AS Reference,{sha} AS ExpectedHash,'{label}' AS EvidenceKind "
        f"FROM {source} WHERE {account}=?"
    )


CATALOG = " UNION ALL ".join(
    (
        _select(
            "x.ClosureReference", "x.ClosureHash", "dbo.ExportExecutionStream x", "stream closure"
        ),
        _select(
            "TRY_CONVERT(uniqueidentifier,JSON_VALUE(x.ScopeJson,'$.host_birth.reference'))",
            "TRY_CONVERT(binary(32),JSON_VALUE(x.ScopeJson,'$.host_birth.sha256'),2)",
            "dbo.ExportExecutionStream x",
            "child identity",
        ),
        _select(
            "x.PayloadReference",
            "x.PayloadHash",
            "dbo.ExportProviderRequest x JOIN dbo.ExportExecutionStream s ON s.StreamID=x.StreamID",
            "request payload",
            "s.AccountKey",
        ),
        _select(
            "x.EvidenceReference",
            "x.EvidenceHash",
            "dbo.ExportProviderRequestEvent x JOIN dbo.ExportProviderRequest r ON r.RequestID=x.RequestID "
            "JOIN dbo.ExportExecutionStream s ON s.StreamID=r.StreamID",
            "request event",
            "s.AccountKey",
        ),
        *(
            _select(
                f"x.{field}Reference",
                f"x.{field}Hash",
                f"dbo.{table} x JOIN dbo.ExportPreparation p ON p.PreparationID=x.PreparationID",
                label,
                "p.AccountKey",
            )
            for table, field, label in (
                ("ExportManagedFileOrigin", "Origin", "managed file origin"),
                ("ExportManagedFileOrigin", "Eligibility", "managed file verification"),
                ("ExportManualFileOrigin", "Eligibility", "manual file verification"),
            )
        ),
        *(
            _select("x.ReceiptReference", "x.ReceiptHash", f"dbo.{table} x", label)
            for table, label in (
                ("ExportTargetContainment", "target isolation"),
                ("ExportContainmentAttestation", "present isolation attestation"),
                ("ExportRegistrationAttestation", "registration dependency attestation"),
                ("ExportReplacementPlan", "replacement proposal"),
                ("ExportReplacementActivation", "replacement activation"),
            )
        ),
        _select(
            "x.ReceiptReference",
            "x.ReceiptHash",
            "dbo.ExportReplacementVerification x JOIN dbo.ExportReplacementPlan p "
            "ON p.ReplacementID=x.ReplacementID",
            "replacement verification",
            "p.AccountKey",
        ),
        _select(
            "TRY_CONVERT(uniqueidentifier,JSON_VALUE(x.GenerationJson,'$.receipt.reference'))",
            "TRY_CONVERT(binary(32),JSON_VALUE(x.GenerationJson,'$.receipt.sha256'),2)",
            "dbo.ExportPreparation x",
            "read isolation",
        ),
        _select(
            "TRY_CONVERT(uniqueidentifier,JSON_VALUE(x.ProvenanceJson,'$.replacement.input_evidence.reference'))",
            "TRY_CONVERT(binary(32),JSON_VALUE(x.ProvenanceJson,'$.replacement.input_evidence.sha256'),2)",
            "dbo.ExportJob x",
            "queued input decision",
        ),
        _select(
            "TRY_CONVERT(uniqueidentifier,JSON_VALUE(x.ProvenanceJson,'$.failed_export_retired.reference'))",
            "TRY_CONVERT(binary(32),JSON_VALUE(x.ProvenanceJson,'$.failed_export_retired.sha256'),2)",
            "dbo.ExportJob x",
            "failed export retirement",
        ),
        _select(
            "x.ReceiptReference",
            "x.ReceiptHash",
            "dbo.ExportLegacyCloseout x",
            "legacy export closeout",
        ),
        _select(
            "TRY_CONVERT(uniqueidentifier,CASE WHEN LEN(JSON_VALUE(x.EvidenceJson,'$.evidence_id'))=32 "
            "THEN STUFF(STUFF(STUFF(STUFF(JSON_VALUE(x.EvidenceJson,'$.evidence_id'),"
            "21,0,'-'),17,0,'-'),13,0,'-'),9,0,'-') "
            "ELSE JSON_VALUE(x.EvidenceJson,'$.evidence_id') END)",
            "TRY_CONVERT(binary(32),JSON_VALUE(x.EvidenceJson,'$.evidence_hash'),2)",
            "dbo.ExportReconciliationProof x",
            "reconciliation audit",
        ),
    )
)


class EvidenceCatalogDAL:
    def __init__(self, connect, account):
        self.connect, self.account = connect, account

    def _parameters(self):
        return [self.account] * CATALOG.count("?")

    @staticmethod
    def _replacement_owner(row):
        job, operation = row.pop("JobID"), row.pop("OutputOperationID")
        if (job is None) == (operation is None):
            raise SourceConflict("One exact replacement owner is required.")
        result = {key: identity(value) for key, value in row.items()}
        # Preserve the existing job wire contract. Rollover identifiers use an
        # explicit discriminator so the recovery UI cannot open a job by mistake.
        result["JobID"] = identity(job if job is not None else operation)
        if operation is not None:
            result["owner_kind"] = "rollover"
        return result

    def replacement_check(self, reference):
        """Locate a check from its terminal receipt or private read journal."""
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT DISTINCT v.VerificationID,c.JobID,c.OutputOperationID FROM dbo.ExportReplacementVerification v "
                "JOIN dbo.ExportReplacementPlan p ON p.ReplacementID=v.ReplacementID "
                "JOIN dbo.ExportTargetContainment c ON c.ContainmentID=p.ContainmentID "
                "AND c.AccountKey=p.AccountKey "
                "LEFT JOIN dbo.ExportExecutionStream s ON s.PreparationID=v.PreparationID "
                "AND s.AccountKey=p.AccountKey WHERE p.AccountKey=? AND (v.ReceiptReference=? "
                "OR s.ClosureReference=? "
                "OR EXISTS(SELECT 1 FROM dbo.ExportProviderRequest r WHERE r.StreamID=s.StreamID "
                "AND (r.PayloadReference=? OR EXISTS(SELECT 1 FROM dbo.ExportProviderRequestEvent e "
                "WHERE e.RequestID=r.RequestID AND e.EvidenceReference=?))))",
                self.account,
                *([identity(reference)] * 4),
            )
            found = rows(cursor)
        if len(found) != 1:
            raise SourceConflict("One exact replacement check is required for fresh verification.")
        return self._replacement_owner(found[0])

    def replacement_proposal(self, reference):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT p.ReplacementID,c.JobID,c.OutputOperationID FROM dbo.ExportReplacementPlan p "
                "JOIN dbo.ExportTargetContainment c ON c.ContainmentID=p.ContainmentID "
                "AND c.AccountKey=p.AccountKey WHERE p.AccountKey=? AND p.ReceiptReference=?",
                self.account,
                identity(reference),
            )
            found = rows(cursor)
        if len(found) != 1:
            raise SourceConflict("One exact replacement proposal is required for recovery.")
        return self._replacement_owner(found[0])

    def page(self, after=None):
        after = identity(after) if after is not None else None
        with transaction(self.connect) as cursor:
            cursor.execute(
                "WITH refs AS (" + CATALOG + ") "
                "SELECT DISTINCT TOP (100) Reference FROM refs "
                "WHERE Reference IS NOT NULL AND (? IS NULL OR Reference>CONVERT(uniqueidentifier,?)) "
                "ORDER BY Reference",
                *self._parameters(),
                after,
                after,
            )
            return [identity(r["Reference"]) for r in rows(cursor)]

    def get(self, reference):
        reference = identity(reference)
        with transaction(self.connect) as cursor:
            cursor.execute(
                "WITH refs AS (" + CATALOG + ") "
                "SELECT DISTINCT ExpectedHash,EvidenceKind FROM refs WHERE Reference=?",
                *self._parameters(),
                reference,
            )
            found = rows(cursor)
        if not found:
            raise SourceConflict("This evidence is outside the registered recovery account.")
        hashes = {
            bytes(r["ExpectedHash"]).hex() if r["ExpectedHash"] is not None else None for r in found
        }
        if len(hashes) != 1 or None in hashes:
            raise SourceConflict(
                "The retained evidence bindings disagree; restoration is not authorised."
            )
        return dict(
            reference=reference,
            sha256=hashes.pop(),
            kinds=sorted({r["EvidenceKind"] for r in found}),
        )
