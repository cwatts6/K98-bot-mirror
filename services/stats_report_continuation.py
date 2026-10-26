"""Guided remaining-report decisions, separate from cache and export acceptance."""

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity


class StatsReportContinuation:
    kind = "stats_report_continuation"

    def __init__(self, dal):
        self.dal = dal

    def pending_recovery(self, *, after=None):
        return self.dal.pending_recovery(after=after)

    def inspect(self, source_id):
        state = self.dal.inspect(source_id)
        receipt = state["receipt"]
        complete = state["complete"]
        actions = {}
        if not complete and receipt["RecoveryState"] != "running":
            actions["continue_reports"] = dict(
                label="Finish remaining reports",
                check="Confirm the bot should finish the unfinished reports for this committed scan.",
                effect="Recheck the exact input, unchanged configuration and writer guards; skip committed reporting stages and complete only the remainder. Cache, configuration and export outcomes remain separate.",
            )
        return (
            dict(
                title="Unfinished scan reports",
                outcome="reports_completed" if complete else "reports_partial",
                scan=receipt["ScanOrder"],
                completed_reporting_stages=receipt["CompletedStage"],
                explanation=(
                    "All three reporting transactions have durable receipts. Continue to output capture; this does not prove cache freshness or spreadsheet delivery."
                    if complete
                    else "The import is committed. Reporting receipts identify the remaining transactions; the import will not run again."
                ),
                actions=actions,
                recovery_links=[
                    dict(
                        label="Review import and capture", kind="stats_import", source_id=source_id
                    )
                ],
            ),
            state["token"],
            complete,
        )

    def execute(self, source_id, action, token, actor, reason):
        if action != "continue_reports" or not actor.startswith("recovery:"):
            raise SourceConflict("A confirmed reporting continuation action is required.")
        self.dal.run(source_id, token, identity(actor.removeprefix("recovery:")))

    def reconcile(self, source_id, action):
        if action["ActionKind"] != "continue_reports":
            raise SourceConflict("Unsupported reporting continuation action.")
        state = self.dal.inspect(source_id)
        receipt = state["receipt"]
        same = (
            receipt["RecoveryActionID"] is not None
            and identity(receipt["RecoveryActionID"]) == identity(action["ActionID"])
            and receipt["RecoveryEvidenceHash"] == action["EvidenceHash"]
        )
        if same and state["complete"] and receipt["RecoveryState"] == "completed":
            return "verified"
        if same and receipt["RecoveryState"] == "failed":
            return "not_applied"
        if not same and state["token"] != action["EvidenceHash"]:
            return "not_applied"
        self.dal.run(source_id, action["EvidenceHash"], action["ActionID"])
        # Independent readback on a new guarded connection, including the original
        # import's completed receipt. Never resolve from the call's return alone.
        verified = self.dal.inspect(source_id)
        return "verified" if verified["complete"] else None
