"""Guided disposition of an unowned SQL block with original outcomes retained."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity


class UnownedSqlHoldRecovery:
    kind = "unowned_sql_hold"

    def __init__(self, dal):
        self.dal = dal

    def pending_recovery(self, *, after=None):
        return self.dal.pending(after)

    def inspect(self, source_id):
        state = self.dal.snapshot(source_id)
        row = state["resource"]
        resolved = not row or not row["BlockedReason"]
        actions, links = {}, []
        if self.dal.eligible(state):
            actions["clear_unowned_hold"] = dict(
                label="Clear unowned SQL blocker",
                check="Confirm this unowned SQL blocker is obsolete. Its original cause and SQL effects remain unknown; this does not verify reports, configuration or a completed import.",
                effect="Exclude current SQL producer, scan and maintenance workers. Recheck that no durable owner or open provider stream remains, preserve the exact old block in an audit record, and clear only its blocker flag. No ownership is released, no import is replayed and no output is certified.",
            )
        for owner in state["producers"]:
            if (
                owner["AccountKey"] != self.dal.account
                or owner["StorageOwner"] != self.dal.storage_owner
            ):
                continue
            kind = {
                "configuration_import": "configuration_producer",
                "player_stats_report": "player_report",
            }.get(owner["ProducerKind"], "stats_import")
            if owner["ConsumerKind"] == "all_kvk":
                kind = "all_kvk_capture"
            elif owner["ConsumerKind"] == "config":
                kind = "configuration_read"
            links.append(
                dict(
                    label="Review retained producer ownership",
                    kind=kind,
                    source_id=identity(owner["PreparationID"]),
                )
            )
        evidence = dict(
            title="Unowned SQL admission blocker",
            actions=actions,
            recovery_links=links,
            outcome=(
                "blocker_absent"
                if resolved
                else "unowned_blocker" if actions else "ownership_review_required"
            ),
            original_outcome="unknown",
            blocked_reason=row["BlockedReason"] if row else None,
            retained_producer_count=len(state["producers"]),
            active_stream_count=state["streams"],
            explanation=(
                "No unowned SQL blocker remains. This verifies admission state only; original SQL results and downstream work keep their own recovery requirements."
                if resolved
                else "Review the saved blocker and confirm its disposition only when independently unowned. Existing local or foreign owners and active workers must finish their own recovery first. No age threshold or missing reservation establishes completion."
            ),
        )
        if not resolved and not actions:
            evidence["required_evidence"] = [
                "Follow the listed producer recovery links. For a foreign-account owner or active provider stream, preserve it and have its configured operator verify settlement; this account cannot release it.",
                "If SQL worker exclusion refuses the action, allow the actual worker to settle and recheck. Do not terminate or release an owner merely to clear this blocker.",
            ]
        return evidence, digest(state).hex(), resolved

    def execute(self, source_id, action, token, actor, reason):
        if action != "clear_unowned_hold":
            raise SourceConflict("Unsupported unowned hold action.")
        self.dal.clear(source_id, token=token, actor=actor, reason=reason)

    def reconcile(self, source_id, action):
        saved = self.dal.action(action["ActionID"])
        if saved:
            return (
                "verified"
                if (
                    saved["ReviewHash"] == action["EvidenceHash"]
                    and saved["Actor"] == "recovery:" + identity(action["ActionID"])
                    and saved["Reason"] == action["Reason"]
                )
                else "not_applied"
            )
        state = self.dal.snapshot(source_id)
        if not self.dal.eligible(state) or digest(state).hex() != action["EvidenceHash"]:
            return "not_applied"
        try:
            self.execute(
                source_id,
                action["ActionKind"],
                action["EvidenceHash"],
                "recovery:" + identity(action["ActionID"]),
                action["Reason"],
            )
        except SourceConflict:
            # A live worker can retain the physical lock while metadata is
            # unchanged. Preserve this exact approved action as unconfirmed.
            return None
        return "verified" if self.dal.action(action["ActionID"]) else None
