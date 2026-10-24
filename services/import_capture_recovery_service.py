"""Continue capture of an existing SQL commit; never invoke the import or provider."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    SnapshotUnavailable,
    configuration_digest,
    output_digest,
)


class ImportCaptureRecovery:
    consumer = "scan_data"

    def __init__(self, runtime, outcomes):
        self.runtime = runtime
        self.outcomes = outcomes
        self.dal = ImportCaptureRecoveryDAL(outcomes)
        self.pipeline_handoff = None

    def handoff_evidence(self, preview):
        if self.pipeline_handoff is None or not preview.get("captured"):
            return None
        link = self.pipeline_handoff.inspect(preview["preparation"])
        if link is None:
            return None
        self.generation(preview["preparation"], preview["execution"])
        self.runtime.verified_snapshot(preview["preparation"]["PreparationID"])
        links = [
            dict(
                label="Review pipeline handoff",
                kind="processing_pipeline",
                source_id=link["pipeline_id"],
            )
        ]
        if link["job_id"]:
            links.insert(
                0, dict(label="Review existing export", kind="export_job", source_id=link["job_id"])
            )
        return (
            dict(
                title="Pipeline capture handoff",
                outcome=(
                    "pipeline_export_queued" if link["job_id"] else "pipeline_export_unconfirmed"
                ),
                explanation=(
                    "This pipeline queued its final captured output. The earlier SQL result and capture remain preserved. Follow the existing export job; queue admission does not confirm spreadsheet delivery."
                    if link["job_id"]
                    else "This capture belongs to a pipeline whose export handoff is unconfirmed. Review that pipeline before any queue decision; the committed result and capture remain preserved."
                ),
                actions={},
                recovery_links=links,
            ),
            preview["token"],
            bool(link["job_id"]),
        )

    def _assert_independent_capture(self, preview):
        if (
            self.pipeline_handoff is not None
            and self.pipeline_handoff.inspect(preview["preparation"]) is not None
        ):
            raise SourceConflict(
                "This pipeline owns the export handoff; review its existing job before any capture decision."
            )

    def generation(self, prep, execution):
        scope = json.loads(self.runtime.configuration)["scan_data"]
        request = json.loads(prep["RequestJson"])
        if (
            not isinstance(request, dict)
            or not isinstance(request.get("request"), dict)
            or request.get("consumer") != "scan_data"
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
        if not isinstance(generation, dict):
            raise SourceConflict("The retained generation document is malformed.")
        producer = generation.get("producer")
        # Normal completion predates the timeout-recovery producer shape. Both
        # refer to this exact preparation and the independently completed SQL
        # receipt; phase prose is never used as proof of completion.
        normal_producer = (
            isinstance(producer, dict)
            and set(producer) == {"procedure", "completed_filename", "phases"}
            and producer.get("procedure") == "dbo.UPDATE_ALL2"
            and producer.get("completed_filename") == execution["CompletedFileName"]
            and isinstance(producer.get("phases"), list)
            and execution.get("State") == "completed"
            and execution.get("Resolution") is None
        )
        if (
            generation.get("capture") not in {"pending", "complete"}
            or any(
                generation.get(key) != value for key, value in expected.items() if key != "producer"
            )
            or not (producer == expected["producer"] or normal_producer)
        ):
            raise SourceConflict(
                "Retained generation or output registration differs. Preserve the evidence."
            )
        return generation

    def run(self, preparation_id, token, actor):
        preview = self.outcomes.inspect(preparation_id)
        self._assert_not_closed(preview["preparation"])
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
                scope = json.loads(self.runtime.configuration)[self.consumer]
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
                    consumer=self.consumer,
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
        return self.after_capture(preparation_id)

    def after_capture(self, preparation_id):
        if self.pipeline_handoff is not None:
            self._assert_independent_capture(self.outcomes.inspect(preparation_id))
        return self.runtime.enqueue_snapshot(preparation_id)

    def verify_queued(self, source_id):
        preview = self.outcomes.inspect(source_id)
        self.generation(preview["preparation"], preview["execution"])
        row, _, _ = self.runtime.verified_snapshot(source_id)
        return bool(preview["captured"] and row["JobID"] and row["State"] == "materialized")

    def queue(self, source_id, token):
        preview = self.outcomes.inspect(source_id)
        self._assert_independent_capture(preview)
        self._assert_not_closed(preview["preparation"])
        self.generation(preview["preparation"], preview["execution"])
        if not preview["captured"]:
            raise SourceConflict("A retained immutable capture is required.")
        if not preview["preparation"]["JobID"] and preview["token"] != token:
            raise SourceConflict("Capture evidence changed. Review the current incident.")
        # Only called after a durable confirmed action. The coordinator atomically
        # links this immutable preparation to its single job.
        return self.runtime.enqueue_snapshot(source_id)

    @staticmethod
    def _assert_not_closed(prep):
        generation = json.loads(prep["GenerationJson"] or "{}")
        if generation.get("capture_failure") or generation.get("capture_abandoned"):
            raise SourceConflict("Capture needs an admin decision; its prior repair cannot resume.")

    def abandonment(self, preview):
        """Read-only presentation; consuming DAL repeats every scope/ownership check."""
        prep, execution = preview["preparation"], preview["execution"]
        generation = self.generation(prep, execution)
        if prep["JobID"]:
            return None
        if self.dal.stats_execution and (
            not execution
            or execution["State"] != "completed"
            or execution["Resolution"] is not None
        ):
            return None
        if (
            generation.get("capture_abandoned")
            and prep["State"] == "unavailable"
            and not preview.get("resources")
        ):
            return "abandoned"
        if preview["action"] in {"resume_capture", "queue_capture"} or preview["captured"]:
            return "failed" if generation.get("capture_failure") else "available"
        return None

    def abandon(self, source_id, token, actor, reason):
        self._assert_independent_capture(self.outcomes.inspect(source_id))
        self.dal.conclude(source_id, token, actor, reason, self.generation, abandon=True)

    def reconcile_capture(self, source_id, action):
        """Classify deterministic output failure only after producer exclusion and fencing."""
        preview = self.outcomes.inspect(source_id)
        prep = preview["preparation"]
        generation = self.generation(prep, preview["execution"])
        actor, token = f"recovery:{action['ActionID']}", action["EvidenceHash"]
        failure = generation.get("capture_failure", {})
        if failure.get("actor") == actor and failure.get("token") == token:
            return "not_applied"
        if generation.get("capture_abandoned"):
            return "not_applied"
        # Pipeline ownership/lineage refusal is not damaged output. Keep it
        # outside the deterministic capture-failure classifier below.
        self._assert_independent_capture(preview)
        try:
            if action["ActionKind"] == "queue_capture":
                if not prep["JobID"] and preview["token"] != token:
                    return "not_applied"
                self.queue(source_id, token)
            else:
                marker = generation.get("capture_recovery")
                if marker != dict(token=token, actor=actor) and preview["token"] != token:
                    return "not_applied"
                self.run(source_id, token, actor)
            return "verified" if self.verify_queued(source_id) else None
        except (SnapshotUnavailable, FileNotFoundError, ValueError):
            # SQL/transport timeouts are not evidence of non-dispatch. This path
            # accepts only deterministic local output/format failure, and the DAL
            # proves no queue job exists while excluding all producer/capture work.
            self.dal.conclude(
                source_id,
                token,
                actor,
                "Output unavailable or failed verification",
                self.generation,
                abandon=False,
            )
            return "not_applied"


ABANDON_CAPTURE_ACTION = {
    "label": "Keep SQL; skip this export",
    "check": "Confirm you accept no spreadsheet export for this completed import. Committed SQL data stays in place; any older spreadsheet may remain out of date.",
    "effect": "Exclude active SQL producers, preserve the checkpoint and any retained files, close only this unqueued capture and release its exact snapshot reservation. No import, recompute or provider write is rerun. Later eligible work can continue.",
}
