"""Admin-guided report settlement, capture, queueing and acknowledgement recovery."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.all_kvk_capture_recovery_service import AllKvkCaptureRecoveryAdapter
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL
from services.import_capture_recovery_service import ImportCaptureRecovery
from services.legacy_export_snapshot_service import configuration_digest
from services.player_report_recovery_dal import PlayerReportRecoveryDAL


class PlayerReportCaptureRecovery(ImportCaptureRecovery):
    request_dal = PlayerReportRecoveryDAL
    procedure = "dbo.SP_Stats_for_Upload"

    def __init__(self, runtime, outcomes):
        super().__init__(runtime, outcomes)
        self.dal = ImportCaptureRecoveryDAL(outcomes, stats_execution=False)

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
    cancel_action = "cancel_report"
    closure_key = "report_cancelled"
    open_outcome = "report_not_committed"
    close_label = "Close failed report & release"
    kind = "player_report"
    title = "Player-stat report recovery"
    output_name = "player-stat report"

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        if preview["action"] not in {self.cancel_action, "cancelled"}:
            return super().inspect(source_id)
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
        if action == self.cancel_action:
            return self.dal.cancel(source_id, token, actor, reason)
        return super().execute(source_id, action, token, actor, reason)

    def reconcile(self, source_id, action):
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
