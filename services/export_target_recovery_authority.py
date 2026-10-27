"""Bounded IPC-facing diagnosis for guided permanent target isolation."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_target_containment import ExportTargetContainment
from services.export_target_containment_dal import ExportTargetContainmentDAL


def _service(authority, registration):
    return ExportTargetContainment(
        dal=ExportTargetContainmentDAL(authority.dal.connect),
        discovery=ExportRecoveryDAL(authority.dal.connect, registration=registration),
        execution=authority.dal,
        store=authority.store,
        registration=registration,
    )


def _present(job_id, report):
    isolated = report["outcome"] == "targets_isolated"
    return dict(
        job_id=job_id,
        token=report["token"],
        outcome="targets_isolated" if isolated else "unknown_write",
        eligible=not isolated,
        targets=report["targets"],
        actor=report.get("actor"),
        reason=report.get("reason"),
        explanation=(
            "The original targets are permanently isolated and the exact reservations are released. "
            "A delayed old write may still change those files. Replacement outputs and verified publication "
            "are still required; this export is not resolved."
            if isolated
            else "The original provider outcome is uncertain. The authority verified the complete registered target set "
            "and exact ownership. With admin confirmation it can permanently retire these files, prevent further "
            "dispatch and release only this job's reservations. Already-dispatched writes may still reach the old "
            "files. Replacement outputs are required; this action does not claim delivery or replay the write."
        ),
    )


def inspect_target_recovery(authority, registration, job_id):
    job_id = identity(job_id)
    with authority._lock:
        service = _service(authority, registration)
        # Scope failures must not disclose another account's job/evidence.
        scoped = service.discovery.job(job_id)
        try:
            return _present(job_id, service.inspect(job_id))
        except SourceConflict as exc:
            return dict(
                job_id=job_id,
                token=digest(scoped).hex(),
                outcome="held",
                eligible=False,
                targets=[],
                actor=None,
                reason=None,
                explanation=str(exc),
            )


def isolate_export_targets(authority, registration, job_id, token, actor, reason):
    job_id = identity(job_id)
    with authority._lock:
        return _present(
            job_id,
            _service(authority, registration).apply(
                job_id, token=token, actor=actor, reason=reason
            ),
        )
