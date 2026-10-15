"""Guided continuation from an atomic all-KVK commit, without producer replay."""

import json
import re

from kvk.dal.new_source_import_dal import SourceConflict
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL
from services.import_capture_recovery_service import ImportCaptureRecovery
from services.import_recovery_service import ImportRecoveryAdapter
from services.legacy_export_snapshot_service import configuration_digest


class AllKvkCaptureRecovery(ImportCaptureRecovery):
    consumer = "all_kvk"

    def __init__(self, runtime, outcomes):
        super().__init__(runtime, outcomes)
        self.dal = ImportCaptureRecoveryDAL(outcomes, stats_execution=False)

    def generation(self, prep, execution=None):
        scope = json.loads(self.runtime.configuration)[self.consumer]
        request = json.loads(prep["RequestJson"])
        if (
            request.get("consumer") != self.consumer
            or request.get("storage_owner") != self.runtime.store.storage_owner
            or request.get("kvk_no") != prep["KVK_NO"]
            or request.get("request", {}).get("kind") != self.consumer
            or request.get("request", {}).get("config") != scope
            or scope.get("kvk_no") != prep["KVK_NO"]
        ):
            raise SourceConflict("The retained all-KVK registration differs from this runtime.")
        generation = json.loads(prep["GenerationJson"] or "{}")
        if not isinstance(generation, dict):
            raise SourceConflict("The completion checkpoint is malformed.")
        producer = generation.get("producer", {})
        if not isinstance(producer, dict):
            raise SourceConflict("The producer checkpoint is malformed.")
        procedure = producer.get("procedure")
        valid_producer = (
            procedure == "KVK recompute" and set(producer) == {"procedure", "kvk_no"}
        ) or (
            procedure == "KVK ingest and recompute"
            and set(producer) == {"procedure", "kvk_no", "scan_id", "file_sha256"}
            and type(producer.get("scan_id")) is int
            and producer["scan_id"] > 0
            and isinstance(producer.get("file_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", producer["file_sha256"]) is not None
        )
        if (
            not valid_producer
            or type(producer.get("kvk_no")) is not int
            or producer["kvk_no"] != prep["KVK_NO"]
            or generation.get("completion") != "committed"
            or generation.get("commit_identity") != str(prep["PreparationID"]).lower()
            or generation.get("registration_sha256") != configuration_digest(scope)
            or generation.get("capture") not in {"pending", "complete"}
        ):
            raise SourceConflict("The atomic all-KVK completion checkpoint could not be verified.")
        return generation


class AllKvkCaptureRecoveryAdapter(ImportRecoveryAdapter):
    kind = "all_kvk_capture"

    def execute(self, source_id, action, token, actor, reason):
        if action not in {"resume_capture", "queue_capture", "abandon_capture"}:
            raise ValueError("Unsupported all-KVK capture recovery.")
        return super().execute(source_id, action, token, actor, reason)

    def reconcile(self, source_id, action):
        if action["ActionKind"] not in {"resume_capture", "queue_capture", "abandon_capture"}:
            raise ValueError("Unsupported all-KVK capture recovery.")
        return super().reconcile(source_id, action)

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        prep = preview["preparation"]
        decision = preview["action"]
        actions = {}
        explanation = preview["explanation"]
        resolved = False
        try:
            self.capture_recovery.generation(prep)
            if decision == "resolved":
                resolved = self.capture_recovery.verify_queued(source_id)
            elif decision in {"resume_capture", "queue_capture"}:
                actions[decision] = {
                    "label": (
                        "Finish capture & queue export"
                        if decision == "resume_capture"
                        else "Queue verified capture"
                    ),
                    "check": "Confirm this completed all-KVK output should continue to its registered export destination.",
                    "effect": "Verify the committed checkpoint, original registration and retained output; finish capture if needed and queue it once. The import and recompute are not rerun.",
                }
        except (SourceConflict, ValueError, KeyError, TypeError):
            explanation = "The retained checkpoint, registration or captured output does not verify. Evidence is preserved and the incident remains open."
        try:
            disposition = self.capture_recovery.abandonment(preview)
        except (SourceConflict, ValueError, KeyError, TypeError):
            disposition = None
        if disposition == "abandoned":
            actions, resolved = {}, True
            explanation = "The committed all-KVK SQL result is preserved. Admin chose to skip this export; the capture reservation is released. This does not claim the spreadsheet is current."
        elif disposition in {"available", "failed"}:
            from services.import_capture_recovery_service import ABANDON_CAPTURE_ACTION

            if disposition == "failed":
                actions.clear()
                explanation = "The capture repair could not verify its output. SQL data and retained evidence are preserved. Review the option to skip this export and unblock later work."
            actions["abandon_capture"] = ABANDON_CAPTURE_ACTION
        return (
            {
                "title": "All-KVK output recovery",
                "season": prep["KVK_NO"],
                "outcome": "export_skipped" if disposition == "abandoned" else prep["State"],
                "explanation": explanation
                or (
                    "Retained output and queue admission are verified. Export delivery is monitored separately."
                    if resolved
                    else "SQL output is retained. Review and confirm its capture or queue recovery."
                ),
                "actions": actions,
            },
            preview["token"],
            resolved,
        )
