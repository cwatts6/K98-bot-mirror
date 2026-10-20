"""Guided SQL import settlement using the existing exact receipt and lock checks."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.capture_recovery_context import add_capture_context, capture_review, capture_summary
from services.historical_import_recovery_service import ACTION, HistoricalImportRecovery
from services.stats_import_outcome_dal import StatsImportOutcomeDAL


class ImportRecoveryAdapter:
    kind = "stats_import"

    def __init__(self, dal, capture_recovery=None):
        self.dal = dal
        self.capture_recovery = capture_recovery
        self.historical = (
            HistoricalImportRecovery(dal, capture_recovery.runtime)
            if capture_recovery and isinstance(dal, StatsImportOutcomeDAL)
            else None
        )

    def review_details(self, source_id, action, token):
        if action == ACTION and self.historical:
            return self.historical.review_details(source_id, action, token)
        return capture_review(self, source_id, action, token)

    def review_summary(self, source_id, action, token):
        if action == ACTION and self.historical:
            return self.historical.review_summary(source_id, action, token)
        return capture_summary(self, source_id, action, token)

    def pending_recovery(self, *, after=None):
        return self.dal.pending_recovery(after=after)

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        execution = preview["execution"] or {}
        decision = preview["action"]
        captured = preview.get("captured", False)
        prep = preview.get("preparation") or {}
        if not execution and self.historical and prep.get("SpoolKey"):
            return self.historical.inspect(source_id)
        capture_pending_queue = captured and not prep.get("JobID")
        if capture_pending_queue:
            captured = False
        elif captured and self.capture_recovery:
            try:
                captured = self.capture_recovery.verify_queued(source_id)
            except (SourceConflict, ValueError, KeyError, TypeError):
                captured = False
                preview["explanation"] = (
                    "The queued capture could not be verified. The incident remains open."
                )
        actions = {}
        capture_blocked = False
        if capture_pending_queue and self.capture_recovery:
            try:
                self.capture_recovery.generation(prep, execution)
            except (SourceConflict, ValueError, KeyError, TypeError):
                capture_blocked = True
                preview["explanation"] = (
                    "The retained capture registration or completion record does not verify. Review the failure details; no queue or release is authorised."
                )
            else:
                actions["queue_capture"] = {
                    "label": "Queue verified capture",
                    "check": "Confirm this completed stats output should continue to its registered export destination.",
                    "effect": "Verify the retained capture and original registration, then queue it once. The import is not rerun.",
                }
        elif decision == "resume_capture" and self.capture_recovery:
            # Validate registered output and producer identity before offering a button.
            try:
                self.capture_recovery.generation(prep, execution)
            except (SourceConflict, ValueError, KeyError, TypeError):
                preview["explanation"] = (
                    "SQL completed, but the retained capture evidence or registered output does not match. "
                    "The incident and reservation are retained for investigation."
                )
            else:
                actions[decision] = {
                    "label": "Finish capture & queue export",
                    "check": "SQL confirms the import and reports completed. Confirm that the bot should retain this output and continue its export.",
                    "effect": "Verify both execution locks and the completion receipt, finish the retained output capture, release its exact snapshot reservation, and queue that snapshot once. The import is not rerun.",
                }
        elif decision == "release_failure":
            actions[decision] = {
                "label": "Release failed import",
                "check": "Confirm you want to close this failed attempt. SQL records no committed import for this attempt.",
                "effect": "Recheck both execution and producer locks, then release this attempt's exact snapshot reservation. Input is retained. No import is rerun.",
            }
        elif decision == "supersede_partial":
            actions[decision] = {
                "label": "Accept partial & release",
                "check": "The import committed but its reports did not finish. Confirm you accept leaving those reports unfinished and will provide a corrected scan.",
                "effect": "Preserve committed data and the original input; close only this unfinished attempt and release its exact reservation. This does not complete reports or rerun the import.",
            }
        evidence = {
            "title": "Stats import recovery",
            "outcome": execution.get("State", "unproven"),
            "scan": execution.get("ScanOrder"),
            "resolution": execution.get("Resolution"),
            "explanation": (
                "Output capture is verified; recovery is still checking its export queue admission."
                if capture_pending_queue and not capture_blocked
                else (
                    "SQL processing completed and its output was captured; the snapshot reservation is released. Export delivery is a separate outcome."
                    if captured
                    else preview.get("explanation")
                )
            )
            or (
                "The reservation has been settled. This is not proof that reports completed."
                if decision == "resolved"
                else "Review the verified SQL outcome and choose the appropriate recovery."
            ),
            "actions": actions,
        }
        if not execution:
            # Missing receipts can also be typed admissions interrupted before
            # SQL registration. Link to that adapter's stronger proof checks;
            # never infer a rollback or release from receipt absence alone.
            document = json.loads(prep.get("RequestJson") or "{}")
            producer = document.get("request", {}).get("producer", {})
            held = preview.get("resources", [])
            evidence["receipt_diagnostics"] = dict(
                receipt_present=False,
                preparation_state=prep.get("State"),
                preparation_version=prep.get("Version"),
                producer_kind=producer.get("kind"),
                held_resources=[
                    dict(
                        category=str(r["ResourceKey"]).split(":", 1)[0],
                        fence=r.get("Fence"),
                        version=r.get("Version"),
                        blocked=bool(r.get("BlockedReason")),
                    )
                    for r in held
                ],
                captured=bool(prep.get("SpoolKey")),
                export_job_id=str(prep["JobID"]) if prep.get("JobID") else None,
            )
            if producer.get("kind") == "stats_import":
                evidence["recovery_links"] = [
                    dict(
                        label="Review interrupted admission",
                        kind="producer_refusal",
                        source_id=producer.get("parent") or source_id,
                    )
                ]
                evidence["explanation"] = (
                    "No SQL execution receipt is recorded. The saved request identifies a stats "
                    "admission: use Review interrupted admission to check whether it stopped before "
                    "execution and offer its guided cancellation or continuation. This incident "
                    "does not authorize a release or replay."
                )
        if self.capture_recovery:
            try:
                disposition = self.capture_recovery.abandonment(preview)
            except (SourceConflict, ValueError, KeyError, TypeError):
                disposition = None
            if disposition == "abandoned":
                evidence.update(
                    actions={},
                    outcome="export_skipped",
                    explanation="The committed SQL result is preserved. Admin chose to skip this export; the capture reservation is released. This does not claim the spreadsheet is current.",
                )
                add_capture_context(evidence, prep, execution, self.capture_recovery, resolved=True)
                return evidence, preview["token"], True
            if disposition in {"available", "failed"}:
                from services.import_capture_recovery_service import ABANDON_CAPTURE_ACTION

                if disposition == "failed":
                    actions.clear()
                    evidence["explanation"] = (
                        "The capture repair could not verify its output. SQL data and retained evidence are preserved. Review the option to skip this export and unblock later work."
                    )
                actions["abandon_capture"] = ABANDON_CAPTURE_ACTION
            # Do not mutate the shared action definition while adding review UI.
            evidence["actions"] = {key: dict(value) for key, value in actions.items()}
            add_capture_context(
                evidence,
                prep,
                execution,
                self.capture_recovery,
                resolved=decision == "resolved" or captured,
            )
        return evidence, preview["token"], decision == "resolved" or captured

    def execute(self, source_id, action, token, actor, reason):
        if action == ACTION and self.historical:
            return self.historical.execute(source_id, token, actor, reason)
        if action == "abandon_capture" and self.capture_recovery:
            return self.capture_recovery.abandon(source_id, token, actor, reason)
        if action == "queue_capture" and self.capture_recovery:
            return self.capture_recovery.queue(source_id, token)
        if action == "resume_capture" and self.capture_recovery:
            return self.capture_recovery.run(source_id, token, actor)
        if action not in {"release_failure", "supersede_partial"}:
            raise ValueError("Unsupported import repair.")
        self.dal.settle(
            source_id,
            token=token,
            actor=actor,
            reason=reason,
            allow_partial=action == "supersede_partial",
        )

    def reconcile(self, source_id, action):
        if action["ActionKind"] == ACTION and self.historical:
            return self.historical.reconcile(source_id, action)
        if action["ActionKind"] in {"resume_capture", "queue_capture"} and self.capture_recovery:
            return self.capture_recovery.reconcile_capture(source_id, action)
        if action["ActionKind"] == "abandon_capture" and self.capture_recovery:
            preview = self.dal.inspect(source_id)
            prep = preview["preparation"]
            marker = json.loads(prep["GenerationJson"] or "{}").get("capture_abandoned")
            expected = dict(
                token=action["EvidenceHash"],
                actor=f"recovery:{action['ActionID']}",
                reason=action["Reason"],
            )
            if marker == expected and self.capture_recovery.abandonment(preview) == "abandoned":
                return "verified"
            if preview["token"] != action["EvidenceHash"]:
                return "not_applied"
            self.execute(
                source_id,
                "abandon_capture",
                action["EvidenceHash"],
                expected["actor"],
                action["Reason"],
            )
            return None
        # inspect checks exact account/storage and obtains the SQL execution lock.
        preview = self.dal.inspect(source_id)
        receipt = preview["execution"] or {}
        if receipt.get("Resolution") == action["ActionKind"]:
            # Settlement is atomic with release in the existing DAL. An equivalent
            # settlement by the automatic observer also establishes this postcondition.
            return "verified"
        if preview["token"] != action["EvidenceHash"]:
            # inspect() locks the exact receipt/preparation/resource rows. A changed
            # version-bound token with no matching atomic settlement proves this
            # old intent cannot now apply: settle() will reject its original token.
            # An in-flight settlement holds those same row locks until its commit.
            return "not_applied"
        # This one adapter can safely resume the SAME SQL settlement: settle()
        # locks and compares the original evidence, and writes its resolution and
        # resource release atomically. It cannot replay the business import.
        # Never generalise this to provider writes without an equivalent contract.
        if preview["token"] == action["EvidenceHash"] and preview["action"] == action["ActionKind"]:
            try:
                self.execute(
                    source_id,
                    action["ActionKind"],
                    action["EvidenceHash"],
                    f"recovery:{action['ActionID']}",
                    action["Reason"],
                )
            except Exception:
                return None
            receipt = self.dal.inspect(source_id)["execution"] or {}
            if receipt.get("Resolution") == action["ActionKind"]:
                return "verified"
        return None
