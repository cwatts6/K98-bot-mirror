"""Durable read attempts, scoped observations and exact SQL settlement."""

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.config_read_containment import stream_wire
from services.export_coordination_dal import identity


class ReplacementVerificationDAL:
    def __init__(self, connect):
        self.connect = connect

    def snapshot(self, verification_id, *, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT v.* FROM dbo.ExportReplacementVerification v "
                "JOIN dbo.ExportReplacementPlan p ON p.ReplacementID=v.ReplacementID "
                "WHERE v.VerificationID=? AND p.AccountKey=?",
                identity(verification_id),
                account,
            )
            attempt = one(cursor)
            if attempt is None:
                return None
            attempt = _wire(attempt)
            for key in (
                "VerificationID",
                "ReplacementID",
                "PreparationID",
                "SessionID",
                "ReceiptReference",
            ):
                if attempt[key] is not None:
                    attempt[key] = identity(attempt[key])
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE PreparationID=? AND AccountKey=?",
                attempt["PreparationID"],
                account,
            )
            preparation = one(cursor)
            if preparation is None:
                raise SourceConflict("Replacement verification preparation is missing.")
            cursor.execute(
                "SELECT r.* FROM dbo.ExportPreparationResource m JOIN dbo.ExportResource r "
                "ON r.ResourceKey=m.ResourceKey WHERE m.PreparationID=? ORDER BY r.ResourceKey",
                attempt["PreparationID"],
            )
            resources = rows(cursor)
            cursor.execute(
                "SELECT * FROM dbo.ExportExecutionStream WHERE PreparationID=? ORDER BY StreamID",
                attempt["PreparationID"],
            )
            return dict(
                attempt=attempt,
                preparation=_wire(preparation),
                resources=[_wire(r) for r in resources],
                streams=[stream_wire(s) for s in rows(cursor)],
            )

    def list_for_plan(self, replacement_id, *, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT v.VerificationID FROM dbo.ExportReplacementVerification v "
                "JOIN dbo.ExportReplacementPlan p ON p.ReplacementID=v.ReplacementID "
                "WHERE p.ReplacementID=? AND p.AccountKey=? ORDER BY v.CreatedUTC,v.VerificationID",
                identity(replacement_id),
                account,
            )
            return [identity(r["VerificationID"]) for r in rows(cursor)]

    def transition(
        self,
        *,
        verification_id,
        replacement_id,
        session_id,
        account,
        action,
        plan=None,
        actor=None,
        reason=None,
        receipt=None,
        stream=None,
        ledger=None,
    ):
        receipt, stream, ledger = receipt or {}, stream or {}, ledger or {}
        with transaction(self.connect) as cursor:
            cursor.execute(
                "EXEC dbo.usp_ExportReplacementVerificationTransition @VerificationID=?,@ReplacementID=?,"
                "@SessionID=?,@AccountKey=?,@Action=?,@PlanJson=?,@Actor=?,@Reason=?,@ReceiptHash=?,"
                "@ReceiptReference=?,@ExpectedVersion=?,@StreamID=?,@StreamVersion=?,@LastSequence=?,@EventDigest=?",
                identity(verification_id),
                identity(replacement_id),
                identity(session_id),
                account,
                action,
                plan.sql_json if plan is not None else None,
                actor,
                reason,
                bytes.fromhex(receipt["sha256"]) if receipt else None,
                identity(receipt["reference"]) if receipt else None,
                0 if action == "begin" else 1,
                identity(stream["StreamID"]) if stream else None,
                stream.get("Version"),
                ledger.get("last_sequence"),
                bytes.fromhex(ledger["event_digest"]) if ledger else None,
            )
            if one(cursor) is None:
                raise SourceConflict(
                    "Verification acknowledgement is missing; inspect its retained attempt."
                )
