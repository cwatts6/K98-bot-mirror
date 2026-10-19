"""Review shared settings once; retire only explicitly selected obsolete exports."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.historical_import_recovery_service import ACTION
from services.historical_retirement_group_dal import HistoricalRetirementGroupDAL


def _adapter(service, actor):
    from services.recovery_release_policy import P0A_ACTIONS

    service.authorize(actor)
    adapter = service.adapters.get("stats_import")
    if not getattr(adapter, "historical", None) or ACTION not in P0A_ACTIONS["stats_import"]:
        raise SourceConflict("Historical retirement is unavailable in this recovery scope.")
    return adapter.historical


def configuration(row):
    context = row["evidence"]["failure_context"]
    return dict(
        original=context["original_registration_sha256"],
        current=context["current_registration_sha256"],
    )


def _member(row):
    context = row["evidence"]["failure_context"]
    return dict(
        id=row["IncidentID"],
        revision=row["Revision"],
        token=row["EvidenceHash"],
        created=context["original_created_utc"],
        input=context["input_file"],
        procedure=context["producer_procedure"],
    )


def _eligible(row):
    return (
        row["SourceKind"] == "stats_import"
        and row["State"] == "open"
        and not row.get("pending_action")
        and not row["evidence"].get("check_unavailable")
        and ACTION in row["evidence"].get("actions", {})
    )


def review_groups(service, actor, after=None):
    _adapter(service, actor)
    ids = HistoricalRetirementGroupDAL(service.store).candidates(after)
    groups = {}
    for identifier in ids:
        row = service.refresh(identifier)
        if not _eligible(row):
            continue
        config = configuration(row)
        key = digest(config).hex()
        group = groups.setdefault(key, dict(configuration=config, members=[]))
        group["members"].append(_member(row))
    return dict(groups=list(groups.values()), next_after=ids[-1] if len(ids) == 25 else None)


def verify_members(service, actor, group, selected=None):
    historical = _adapter(service, actor)
    members = group["members"]
    if not 1 <= len(members) <= 25 or len({m["id"] for m in members}) != len(members):
        raise SourceConflict("Reopen a current historical review group.")
    chosen = [m["id"] for m in members] if selected is None else selected
    if (
        not 1 <= len(chosen) <= 25
        or len(set(chosen)) != len(chosen)
        or not set(chosen) <= {m["id"] for m in members}
    ):
        raise SourceConflict("Select only distinct exports from this review group.")
    reviewed = []
    for member in members:
        if member["id"] not in chosen:
            continue
        row = service.refresh(member["id"])
        if (
            not _eligible(row)
            or _member(row) != member
            or configuration(row) != group["configuration"]
        ):
            raise SourceConflict(
                "A selected input, configuration or decision changed. Reopen the group; no new approvals were saved."
            )
        reviewed.append((member, row))
    return historical, reviewed


def review_group(service, actor, group, selected=None):
    historical, reviewed = verify_members(service, actor, group, selected)
    first = reviewed[0][1]
    fields = historical.review_summary(first["SourceID"], ACTION, first["EvidenceHash"])
    # Each member's input/date is shown separately by the selection view.
    return dict(group=group, fields=fields[1:], technical_row=first)


def approve_group(service, actor, group, selected):
    _, reviewed = verify_members(service, actor, group, selected)
    identifier = HistoricalRetirementGroupDAL(service.store).approve_selected(
        group,
        [m for m, _ in reviewed],
        f"discord:{actor.user_id}",
    )
    return service.review(actor, identifier)


class HistoricalBatchAdapter:
    kind = "historical_batch"
    observe_healthy = True

    def __init__(self, store):
        self.dal = HistoricalRetirementGroupDAL(store)

    def pending_recovery(self, *, after=None):
        return self.dal.pending_groups()

    def inspect(self, source_id):
        row, counts = self.dal.group_progress(source_id)
        evidence = dict(row["evidence"])
        approved = evidence["approved_count"]
        pending = counts.get("dispatched", 0) + counts.get("unknown", 0)
        verified = counts.get("verified", 0)
        changed = counts.get("not_applied", 0)
        complete = sum(counts.values()) == approved and pending == 0
        evidence.update(
            verified_count=verified,
            changed_count=changed,
            pending_count=pending,
            outcome=(
                ("verified" if verified == approved else "completed_with_exceptions")
                if complete
                else "running"
            ),
            explanation=(
                f"{verified}/{approved} selected obsolete exports retired and verified; {pending} awaiting verification; {changed} changed or not applied. "
                "SQL outcomes remain unknown. Captured bytes are retained. Changed members keep their individual recovery incidents."
            ),
        )
        return evidence, digest(evidence).hex(), complete
