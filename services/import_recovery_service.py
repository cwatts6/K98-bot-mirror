"""Guided SQL import settlement using the existing exact receipt and lock checks."""

import json

from kvk.dal.new_source_import_dal import SourceConflict


class ImportRecoveryAdapter:
    kind = "stats_import"

    def __init__(self, dal, capture_recovery=None):
        self.dal = dal
        self.capture_recovery = capture_recovery

    def pending_recovery(self, *, after=None):
        return self.dal.pending_recovery(after=after)

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        execution = preview["execution"] or {}
        decision = preview["action"]
        captured = preview.get("captured", False)
        prep = preview.get("preparation") or {}
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
        if capture_pending_queue and self.capture_recovery:
            try:
                self.capture_recovery.generation(prep, execution)
            except (SourceConflict, ValueError, KeyError, TypeError):
                preview["explanation"] = "The retained capture registration does not verify."
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
                if capture_pending_queue
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
        return evidence, preview["token"], decision == "resolved" or captured

    def execute(self, source_id, action, token, actor, reason):
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
        # inspect checks exact account/storage and obtains the SQL execution lock.
        preview = self.dal.inspect(source_id)
        receipt = preview["execution"] or {}
        if action["ActionKind"] == "queue_capture" and self.capture_recovery:
            if not preview["preparation"]["JobID"] and preview["token"] != action["EvidenceHash"]:
                return "not_applied"
            self.capture_recovery.queue(source_id, action["EvidenceHash"])
            return "verified" if self.capture_recovery.verify_queued(source_id) else None
        if action["ActionKind"] == "resume_capture" and self.capture_recovery:
            prep = preview["preparation"]
            marker = json.loads(prep["GenerationJson"] or "{}").get("capture_recovery")
            expected = dict(token=action["EvidenceHash"], actor=f"recovery:{action['ActionID']}")
            if marker == expected and preview["captured"] and prep["JobID"]:
                # Re-read and hash-check the retained spool through idempotent queue
                # admission, including after a lost enqueue commit acknowledgement.
                self.capture_recovery.run(source_id, expected["token"], expected["actor"])
                return "verified"
            if marker != expected and preview["token"] != action["EvidenceHash"]:
                return "not_applied"
            self.capture_recovery.run(source_id, expected["token"], expected["actor"])
            verified = self.dal.inspect(source_id)
            if verified["captured"] and verified["preparation"]["JobID"]:
                return "verified"
            return None
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
