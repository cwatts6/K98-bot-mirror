"""Atomic export disposition for captured history without SQL execution receipts."""

import json
from uuid import UUID

from kvk.dal.new_source_import_dal import SourceConflict, digest, rows, transaction
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL


class HistoricalImportRecoveryDAL:
    def __init__(self, outcomes):
        self.outcomes = outcomes

    def _snapshot(self, cursor, source_id):
        prep, execution, resources = self.outcomes._snapshot(cursor, source_id)
        self.outcomes._scope(prep)
        cursor.execute(
            "SELECT StreamID,State,Version FROM dbo.ExportExecutionStream WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=? ORDER BY StreamID",
            source_id,
        )
        streams = rows(cursor)
        token = digest(
            dict(
                outcome=self.outcomes.token(prep, execution, resources),
                streams=[{k: str(v) for k, v in row.items()} for row in streams],
            )
        ).hex()
        return dict(
            preparation=prep, execution=execution, resources=resources, streams=streams, token=token
        )

    def inspect(self, source_id):
        source_id = identity(source_id)
        with transaction(self.outcomes.connect) as cursor:
            self.outcomes._idle(cursor, source_id)
            return self._snapshot(cursor, source_id)

    def retire(self, source_id, token, actor, reason, verify, evidence_token):
        if (
            not isinstance(actor, str)
            or not 1 <= len(actor) <= 128
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise ValueError("Bounded admin identity and decision reason required.")
        if not actor.startswith("recovery:") or str(UUID(actor[9:])) != actor[9:]:
            raise ValueError("A durable guided recovery action identity is required.")
        source_id = identity(source_id)
        expected = dict(token=token, actor=actor, reason=reason, sql_outcome="unproven")
        # Same producer guards and account mutex as capture/admission. No locks
        # are released, no execution receipt is invented, and no SQL is replayed.
        with ImportCaptureRecoveryDAL(self.outcomes).session(source_id) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                _mutex(cursor, "account:" + self.outcomes.account)
                state = self._snapshot(cursor, source_id)
                closed = verify(state)
                prep = state["preparation"]
                generation = json.loads(prep["GenerationJson"])
                if closed:
                    if generation["historical_disposition"] != expected:
                        raise SourceConflict("Another historical decision is already recorded.")
                else:
                    if evidence_token(state) != token:
                        raise SourceConflict(
                            "Historical evidence changed. Review this incident again."
                        )
                    generation["historical_disposition"] = expected
                    _cas(
                        cursor,
                        "UPDATE dbo.ExportPreparation SET State='unavailable',GenerationJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                        "OUTPUT inserted.Version WHERE PreparationID=? AND Version=? AND OwnerID=? AND Fence=? AND State='captured' AND JobID IS NULL",
                        bounded_json(generation),
                        source_id,
                        prep["Version"],
                        prep["OwnerID"],
                        prep["Fence"],
                    )
                cursor.execute("COMMIT TRANSACTION")
            except BaseException:
                try:
                    cursor.execute("IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
                except Exception:
                    pass  # Lost commit acknowledgement is reconciled from the saved marker.
                raise
            finally:
                cursor.close()
