"""Link lost read evidence to guided fresh verification and verify supersession."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_replacement_check_recovery import terminal_read_snapshot


def replacement_check_recovery(broker, catalog, reference):
    bound = catalog.replacement_check(reference)
    job_id, check_id = bound["JobID"], bound["VerificationID"]
    workflow = broker.replacements.workflow(job_id)
    old = terminal_read_snapshot(workflow.verification, check_id)
    proposal = workflow.proposals.inspect(old["attempt"]["ReplacementID"])
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
