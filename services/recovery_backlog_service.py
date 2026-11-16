"""Group approval and progress, with the existing per-incident proof boundary."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.recovery_backlog_dal import RecoveryBacklogDAL


class EvidenceBatchAdapter:
    kind = "evidence_batch"
    # Discovery returns existing open groups only. Persist their terminal state
    # immediately instead of waiting behind the general incident backlog.
    observe_healthy = True

    def __init__(self, store):
        self.dal = RecoveryBacklogDAL(store)

    def pending_recovery(self, *, after=None):
        return self.dal.pending_groups()

    def inspect(self, source_id):
        row, counts = self.dal.group_progress(source_id)
        approved = row["evidence"]["approved_count"]
        pending = counts.get("dispatched", 0) + counts.get("unknown", 0)
        verified = counts.get("verified", 0)
        changed = counts.get("not_applied", 0)
        complete = sum(counts.values()) == approved and pending == 0
        evidence = dict(
            title="Grouped evidence repairs",
            actions={},
            group_id=str(source_id),
            approved_count=approved,
            verified_count=verified,
            changed_count=changed,
            pending_count=pending,
            outcome=(
                ("verified" if verified == approved else "completed_with_exceptions")
                if complete
                else "running"
            ),
            explanation=(
                f"{verified} of {approved} approved evidence repairs verified; {pending} awaiting verification; "
                f"{changed} changed or no longer applicable. Progress survives restart. "
                "Changed or unavailable incidents retain their individual diagnosis. This group never releases queue ownership or replays a write."
            ),
        )
        return evidence, digest(evidence).hex(), complete


def review_group(service, actor):
    service.authorize(actor)
    _require_adapter(service)
    return RecoveryBacklogDAL(service.store).preview()


def approve_group(service, actor, preview):
    service.authorize(actor)
    _require_adapter(service)
    group = RecoveryBacklogDAL(service.store).approve(preview, f"discord:{actor.user_id}")
    return service.review(actor, group)


def _require_adapter(service):
    from services.recovery_release_policy import P0A_ACTIONS

    if (
        "private_evidence" not in service.adapters
        or not {"protect_evidence", "restore_evidence"} <= P0A_ACTIONS["private_evidence"]
    ):
        raise SourceConflict("Verified evidence-copy repair is unavailable in this recovery scope.")
