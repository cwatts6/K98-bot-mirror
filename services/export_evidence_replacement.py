"""Link lost read evidence to guided fresh verification and verify supersession."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_replacement_check_recovery import terminal_read_snapshot
from services.export_replacement_proposal_recovery import (
    discard_service,
    inspect_lost_proposal,
)


def _original_workflow(broker, workflow, replacement_id):
    """Use the authenticated base of an obsolete proposal after another recovery."""
    from copy import copy

    row = workflow.proposals.dal.read(replacement_id, account=workflow.account)
    if row is None:
        raise SourceConflict("The original proposal is unavailable.")
    registrations, _ = broker.replacements.registrations()
    base = next(
        (r for r in registrations if r.fingerprint == row["plan"]["BaseRegistrationHash"]), None
    )
    if base is None:
        raise SourceConflict("The original proposal registration is unauthenticated.")
    original = copy(workflow)
    service = broker.replacements.services(base, history=registrations)
    original.registration = base
    original.proposals, original.verification, original.activation = (
        service.proposals,
        service.verification,
        service,
    )
    return original


def replacement_proposal_recovery(broker, catalog, reference):
    bound = catalog.replacement_proposal(reference)
    job_id, replacement_id = bound["JobID"], bound["ReplacementID"]
    workflow = broker.replacements.workflow(job_id)
    old = inspect_lost_proposal(
        _original_workflow(broker, workflow, replacement_id), replacement_id
    )
    if old["job_id"] != job_id:
        raise SourceConflict("Lost proposal belongs to another recovery.")
    state = workflow._state(job_id)
    proposal, checked = state["proposal"], state["check"]
    successor = (
        checked["verification_id"]
        if proposal
        and proposal["replacement_id"] != replacement_id
        and checked
        and checked["state"] == "verified"
        and old["checking"] is None
        else None
    )
    return dict(
        job_id=job_id,
        lost_proposal_id=replacement_id,
        successor_check_id=successor,
        token=digest(dict(original=old, current=state)).hex(),
    )


def replacement_check_recovery(broker, catalog, reference):
    bound = catalog.replacement_check(reference)
    job_id, check_id = bound["JobID"], bound["VerificationID"]
    workflow = broker.replacements.workflow(job_id)
    snapshot = workflow.verification.dal.snapshot(check_id, account=workflow.account)
    if snapshot is None:
        raise SourceConflict("The original replacement check is missing.")
    replacement_id = snapshot["attempt"]["ReplacementID"]
    original = _original_workflow(broker, workflow, replacement_id)
    try:
        proposal = original.proposals.inspect(replacement_id)
        service = original.verification
    except (SourceConflict, ValueError, KeyError, TypeError):
        proposal = inspect_lost_proposal(original, replacement_id)
        service = discard_service(original, replacement_id, check_id)
    old = terminal_read_snapshot(service, check_id)
    if proposal["job_id"] != job_id or any(
        identity(row["VerificationID"]) == check_id
        for row in workflow.activation.dal.chain(workflow.account)
    ):
        raise SourceConflict("Activated read evidence requires original-history recovery.")
    state = workflow._state(job_id)
    checked = state["check"]
    successor = (
        checked["verification_id"]
        if checked and checked["state"] == "verified" and checked["verification_id"] != check_id
        else None
    )
    return dict(
        job_id=job_id,
        lost_check_id=check_id,
        successor_check_id=successor,
        token=digest(dict(original=old, current=state)).hex(),
    )
