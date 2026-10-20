"""Admin-guided report settlement, capture, queueing and acknowledgement recovery."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.all_kvk_capture_recovery_service import AllKvkCaptureRecoveryAdapter
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL
from services.import_capture_recovery_service import ImportCaptureRecovery
from services.legacy_export_snapshot_service import SnapshotUnavailable, configuration_digest
from services.player_report_recovery_dal import PlayerReportRecoveryDAL


class PlayerReportCaptureRecovery(ImportCaptureRecovery):
    request_dal = PlayerReportRecoveryDAL
    procedure = "dbo.SP_Stats_for_Upload"

    def __init__(self, runtime, outcomes):
        super().__init__(runtime, outcomes)
        self.dal = ImportCaptureRecoveryDAL(outcomes, stats_execution=False)

    def no_export(self, prep):
        producer = self.request_dal.request(prep)["request"]["producer"]
        return producer.get("export_disposition") in {"cache_only_v1", "configuration_only_v1"}

    def after_capture(self, preparation_id):
        prep = self.outcomes.inspect(preparation_id)["preparation"]
        if self.no_export(prep):
            self.runtime.verified_snapshot(preparation_id)
            return None
        return super().after_capture(preparation_id)

    def verify_queued(self, source_id):
        preview = self.outcomes.inspect(source_id)
        if not self.no_export(preview["preparation"]):
            return super().verify_queued(source_id)
        self.generation(preview["preparation"], preview["execution"])
        row, _, _ = self.runtime.verified_snapshot(source_id)
        return bool(preview["captured"] and not row["JobID"] and row["State"] == "captured")

    def queue(self, source_id, token):
        if self.no_export(self.outcomes.inspect(source_id)["preparation"]):
            raise SourceConflict("The original no-export intent cannot queue spreadsheet work.")
        return super().queue(source_id, token)

    def generation(self, prep, execution=None):
        request = self.request_dal.request(prep)
        scope = json.loads(self.runtime.configuration)[self.consumer]
        generation = json.loads(prep["GenerationJson"] or "{}")
        if (
            execution
            or request["request"].get("config") != scope
            or generation.get("completion") != "committed"
            or generation.get("commit_identity") != str(prep["PreparationID"]).lower()
            or generation.get("registration_sha256") != configuration_digest(scope)
            or generation.get("producer") != dict(procedure=self.procedure, atomic_checkpoint=1)
            or generation.get("capture") not in {"pending", "complete"}
        ):
            raise SourceConflict(
                "The atomic report checkpoint or registered output could not be verified."
            )
        return generation


class PlayerReportRecoveryAdapter(AllKvkCaptureRecoveryAdapter):
    automatic_action = "complete_cache_only"
    automatic_reason = "Original cache-only intent and committed retained output verified"
    cancel_action = "cancel_report"
    closure_key = "report_cancelled"
    open_outcome = "report_not_committed"
    close_label = "Close failed report & release"
    kind = "player_report"
    title = "Player-stat report recovery"
    output_name = "player-stat report"
    no_export_outcome = "cache_only_completed"
    no_export_label = "Verify cache-only completion"
    no_export_pending = (
        "This cache-only refresh needs no export decision. Automatic verification is pending."
    )
    no_export_explanation = (
        "This invocation requested a local cache refresh, not a spreadsheet export. "
        "Its committed SQL output and captured evidence are preserved; "
        "the recorded no-export disposition is verified. Cache freshness and "
        "spreadsheet delivery are separate checks."
    )

    def _no_export(self, preview):
        if self.kind != "player_report":
            return False
        request = self.dal.request(preview["preparation"])
        return request["request"]["producer"].get("export_disposition") == "cache_only_v1"

    def _verify_no_export(self, source_id, preview):
        prep = preview["preparation"]
        if (
            not self._no_export(preview)
            or preview["action"] != "queue_capture"
            or preview.get("resources")
            or not preview["captured"]
            or prep["JobID"]
        ):
            raise SourceConflict("Exact unqueued no-export output is required.")
        self.capture_recovery.generation(prep, preview["execution"])
        self.capture_recovery.runtime.verified_snapshot(source_id)

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        if preview["action"] not in {self.cancel_action, "cancelled"}:
            evidence, token, resolved = super().inspect(source_id)
            try:
                cache_only = self._no_export(preview)
                if cache_only and resolved and evidence["outcome"] == "export_skipped":
                    evidence["outcome"] = self.no_export_outcome
                    evidence["explanation"] = self.no_export_explanation
                    evidence["failure_context"]["summary"] = evidence["explanation"]
                elif cache_only and not resolved:
                    if preview["action"] == "resume_capture":
                        evidence["actions"].pop("queue_capture", None)
                        evidence["actions"]["resume_capture"].update(
                            check="Confirm that the committed output should be captured without rerunning the producer.",
                            effect="Preserve and verify the exact committed output. The original no-export intent remains binding: no spreadsheet job is queued. Its no-export completion is checked separately.",
                        )
                        evidence["explanation"] = (
                            "The SQL result committed, but its retained capture needs recovery. "
                            "This invocation requested no spreadsheet export."
                        )
                        return evidence, token, resolved
                    self._verify_no_export(source_id, preview)
                    evidence["actions"] = {
                        self.automatic_action: dict(
                            label=self.no_export_label,
                            check="The original request explicitly required no spreadsheet export. Verify and close this retained capture.",
                            effect="Recheck original intent, committed output, exact ownership and absence of provider execution; preserve SQL and captured bytes, record and verify no-export completion. No report or provider write is replayed.",
                        )
                    }
                    evidence["explanation"] = self.no_export_pending
                    evidence["failure_context"].update(
                        summary=evidence["explanation"],
                        current_blocker=f"{self.no_export_outcome.removesuffix('_completed')}_verification_pending",
                    )
            except (
                SourceConflict,
                SnapshotUnavailable,
                ValueError,
                KeyError,
                TypeError,
                OSError,
            ) as exc:
                # Missing or changed evidence keeps the existing guided actions;
                # never infer a cache-only decision for historical requests.
                evidence["failure_context"]["automatic_completion_check"] = type(exc).__name__
            return evidence, token, resolved
        closed = preview["action"] == "cancelled"
        return (
            dict(
                title=self.title,
                outcome=self.closure_key if closed else self.open_outcome,
                explanation=(
                    "The failed report attempt is closed and its exact reservation is released. Existing imported data is preserved. This does not claim the report or cache is current."
                    if closed
                    else "The atomic report contract and SQL locks show this attempt has no committed report. Existing imports and previous reports are preserved."
                ),
                actions=(
                    {}
                    if closed
                    else {
                        self.cancel_action: dict(
                            label=self.close_label,
                            check="Confirm you want to close this uncommitted report attempt. Existing imported data is retained; this action does not refresh reports or the cache.",
                            effect="Exclude live report execution, verify the atomic checkpoint is absent, fence the old attempt, release only its exact reservation, then verify the durable closure. No import is replayed.",
                        )
                    }
                ),
            ),
            preview["token"],
            closed,
        )

    def execute(self, source_id, action, token, actor, reason):
        if action == self.automatic_action:
            preview = self.dal.inspect(source_id)
            if preview["token"] != token:
                raise SourceConflict("No-export evidence changed; recheck the incident.")
            self._verify_no_export(source_id, preview)
            return self.capture_recovery.abandon(source_id, token, actor, reason)
        if action == self.cancel_action:
            return self.dal.cancel(source_id, token, actor, reason)
        return super().execute(source_id, action, token, actor, reason)

    def reconcile(self, source_id, action):
        if action["ActionKind"] == self.automatic_action:
            preview = self.dal.inspect(source_id)
            if not self._no_export(preview):
                return "not_applied"
            if preview["token"] == action["EvidenceHash"]:
                self.execute(
                    source_id,
                    self.automatic_action,
                    action["EvidenceHash"],
                    f"recovery:{action['ActionID']}",
                    action["Reason"],
                )
            # Reuse the durable exact-action abandonment receipt for lost replies.
            return super().reconcile(source_id, dict(action, ActionKind="abandon_capture"))
        if action["ActionKind"] != self.cancel_action:
            return super().reconcile(source_id, action)
        preview = self.dal.inspect(source_id)
        marker = dict(
            token=action["EvidenceHash"],
            actor=f"recovery:{action['ActionID']}",
            reason=action["Reason"],
        )
        if preview["token"] == action["EvidenceHash"]:
            self.dal.cancel(source_id, marker["token"], marker["actor"], marker["reason"])
            # A lost approval acknowledgement can leave dispatch to this pass.
            # Verify its durable marker before refresh closes the incident and
            # removes it from subsequent open-incident discovery.
            preview = self.dal.inspect(source_id)
        if (
            preview["action"] == "cancelled"
            and json.loads(preview["preparation"]["GenerationJson"])[self.closure_key] == marker
        ):
            return "verified"
        if preview["token"] != action["EvidenceHash"]:
            return "not_applied"
        return None
