"""Guided SQL import settlement using the existing exact receipt and lock checks."""


class ImportRecoveryAdapter:
    kind = "stats_import"

    def __init__(self, dal):
        self.dal = dal

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        execution = preview["execution"] or {}
        decision = preview["action"]
        actions = {}
        if decision == "release_failure":
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
            "explanation": preview.get("explanation")
            or (
                "The reservation has been settled. This is not proof that reports completed."
                if decision == "resolved"
                else "Review the verified SQL outcome and choose the appropriate recovery."
            ),
            "actions": actions,
        }
        return evidence, preview["token"], decision == "resolved"

    def execute(self, source_id, action, token, actor, reason):
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
        if receipt.get("Resolution") == action["ActionKind"]:
            # Settlement is atomic with release in the existing DAL. An equivalent
            # settlement by the automatic observer also establishes this postcondition.
            return "verified"
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
