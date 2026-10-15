"""Continue capture of an existing SQL commit; never invoke the import or provider."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    configuration_digest,
    output_digest,
)


class ImportCaptureRecovery:
    def __init__(self, runtime, outcomes):
        self.runtime = runtime
        self.outcomes = outcomes
        self.dal = ImportCaptureRecoveryDAL(outcomes)

    def generation(self, prep, execution):
        scope = json.loads(self.runtime.configuration)["scan_data"]
        request = json.loads(prep["RequestJson"])
        if (
            request.get("consumer") != "scan_data"
            or request.get("storage_owner") != self.runtime.store.storage_owner
            or request.get("request", {}).get("kind") != "scan_data"
            or request.get("request", {}).get("config") != scope
        ):
            raise SourceConflict("The retained import registration differs from this runtime.")
        expected = dict(
            completion="committed",
            commit_identity=str(prep["PreparationID"]).lower(),
            registration_sha256=configuration_digest(scope),
            producer=dict(
                procedure="dbo.UPDATE_ALL2",
                completed_filename=execution["CompletedFileName"],
                execution_preparation_id=str(prep["PreparationID"]).lower(),
                scan_order=execution["ScanOrder"],
                last_run_counter=execution["LastRunCounter"],
            ),
        )
        if not prep["GenerationJson"]:
            return dict(expected, capture="pending")
        generation = json.loads(prep["GenerationJson"])
        if generation.get("capture") not in {"pending", "complete"} or any(
            generation.get(key) != value for key, value in expected.items()
        ):
            raise SourceConflict(
                "Retained generation or output registration differs. Preserve the evidence."
            )
        return generation

    def run(self, preparation_id, token, actor):
        preview = self.outcomes.inspect(preparation_id)
        if preview["captured"]:
            marker = json.loads(preview["preparation"]["GenerationJson"]).get("capture_recovery")
            if marker != dict(token=token, actor=actor):
                raise SourceConflict("Captured output belongs to a different recovery action.")
        else:
            with self.dal.session(preparation_id) as connection:
                claim, generation = self.dal.adopt(
                    connection, preparation_id, token, actor, self.generation
                )
                cursor = connection.cursor()
                try:
                    self.runtime.dal.verify_producer_cursor(claim, cursor)
                finally:
                    cursor.close()
                scope = json.loads(self.runtime.configuration)["scan_data"]
                sections, planned = self.runtime.capture(connection, scope)
                if generation["capture"] == "pending":
                    generation = dict(
                        generation,
                        capture="complete",
                        output_sha256=output_digest(sections),
                        config_sha256=configuration_digest(planned),
                    )
                    claim = self.runtime.dal.transition(
                        claim, expected="committed", state="committed", generation=generation
                    )
                # Existing complete proof is immutable. Capture verifies exact hashes
                # before writing another immutable spool after a lost acknowledgement.
                snapshot = LegacySnapshot.capture(
                    consumer="scan_data",
                    preparation_id=claim.preparation_id,
                    generation=generation,
                    config=planned,
                    provenance=dict(owner=claim.owner, fence=claim.fence),
                    sections=sections,
                )
                receipt = snapshot.persist(self.runtime.store)
                self.runtime.dal.captured(claim, receipt)
        # This is an idempotent queue admission of the retained snapshot, not export
        # dispatch. Its acknowledgement must also be reconciled before resolution.
        return self.runtime.enqueue_snapshot(preparation_id)
