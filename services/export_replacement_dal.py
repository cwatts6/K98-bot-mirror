"""Bounded immutable replacement proposals; no registration or provider writes."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import identity


class ExportReplacementDAL:
    def __init__(self, connect, *, owner_kind="job"):
        if owner_kind not in {"job", "rollover"}:
            raise ValueError("Explicit replacement owner kind required.")
        self.connect = connect
        self.owner_kind = owner_kind

    @property
    def owner_column(self):
        # Closed server-side choice, never caller-authored SQL. JobID remains
        # the version-one workflow wire key; no synthetic job row is created.
        return "JobID" if self.owner_kind == "job" else "OutputOperationID"

    def read(self, replacement_id, *, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                f"SELECT p.*,c.{self.owner_column} AS JobID FROM dbo.ExportReplacementPlan p "
                "JOIN dbo.ExportTargetContainment c ON c.ContainmentID=p.ContainmentID "
                f"WHERE p.ReplacementID=? AND p.AccountKey=? AND c.AccountKey=p.AccountKey AND c.{self.owner_column} IS NOT NULL",
                identity(replacement_id),
                account,
            )
            plan = one(cursor)
            if plan is None:
                return None
            plan = _wire(plan)
            for key in ("ReplacementID", "ContainmentID", "ReceiptReference", "JobID"):
                plan[key] = identity(plan[key])
            cursor.execute(
                "SELECT OldFileID,NewFileID FROM dbo.ExportReplacementTarget "
                "WHERE ReplacementID=? ORDER BY OldFileID",
                identity(replacement_id),
            )
            return dict(plan=plan, targets=rows(cursor))

    def create(self, *, proposal, containment_id, account, receipt, actor, reason):
        mapping = json.dumps(
            [dict(old=old, new=new) for old, new in sorted(proposal["mapping"].items())],
            sort_keys=True,
            separators=(",", ":"),
        )
        with transaction(self.connect) as cursor:
            cursor.execute(
                "EXEC dbo.usp_ExportReplacementPlanCreate @ReplacementID=?,@ContainmentID=?,"
                "@AccountKey=?,@BaseRegistrationHash=?,@ProjectedRegistrationHash=?,"
                "@ReceiptHash=?,@ReceiptReference=?,@MappingJson=?,@Actor=?,@Reason=?",
                identity(proposal["replacement_id"]),
                identity(containment_id),
                account,
                bytes.fromhex(proposal["base_registration_sha256"]),
                bytes.fromhex(proposal["registration_sha256"]),
                bytes.fromhex(receipt["sha256"]),
                identity(receipt["reference"]),
                mapping,
                actor,
                reason,
            )
            if one(cursor) is None:
                raise SourceConflict(
                    "Replacement proposal acknowledgement is missing; verify its original receipt."
                )

    def for_job(self, job_id, *, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT p.ReplacementID FROM dbo.ExportReplacementPlan p "
                "JOIN dbo.ExportTargetContainment c ON c.ContainmentID=p.ContainmentID "
                f"WHERE c.{self.owner_column}=? AND c.AccountKey=? AND p.AccountKey=c.AccountKey ORDER BY p.CreatedUTC,p.ReplacementID",
                identity(job_id),
                account,
            )
            return [identity(r["ReplacementID"]) for r in rows(cursor)]
