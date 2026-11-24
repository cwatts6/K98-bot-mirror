"""Compose rollover recovery from authenticated registrations and private evidence."""

import hashlib

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
from services.export_execution_protocol import encode
from services.export_manual_enrollment import manual_profile
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_replacement_dal import ExportReplacementDAL
from services.export_replacement_verification import verification_plan
from services.rollover_containment import RolloverContainment
from services.rollover_containment_dal import RolloverContainmentDAL
from services.rollover_replacement import (
    RolloverReplacementContinuation,
    RolloverReplacementWorkflow,
)
from services.rollover_replacement_dal import RolloverReplacementDAL


def containment_service(authority, registration):
    connect = authority.dal.connect
    return RolloverContainment(
        pools=SourceOutputPoolDAL(connect, execution_evidence=True),
        dal=RolloverContainmentDAL(connect),
        discovery=ExportRecoveryDAL(connect, registration=registration),
        execution=authority.dal,
        store=authority.store,
        registration=registration,
    )


def workflow(owner, operation_id, *, ancestors=()):
    if operation_id in ancestors or len(ancestors) >= 32:
        raise SourceConflict(
            "Rollover repair ancestry cannot be verified; original history is retained."
        )
    registrations, current = owner.registrations()
    plans = ExportReplacementDAL(owner.connect, owner_kind="rollover")
    keys = plans.for_job(operation_id, account=owner.base.value()["account"])
    selected = None
    if keys:
        row = plans.read(keys[-1], account=owner.base.value()["account"])
        selected = next(
            (r for r in registrations if r.fingerprint == row["plan"]["BaseRegistrationHash"]), None
        )
    else:
        for registration in reversed(registrations):
            try:
                containment_service(owner.authority, registration).inspect(operation_id)
            except SourceConflict:
                continue
            selected = registration
            break
    if selected is None:
        raise SourceConflict("Original rollover registration cannot be authenticated.")
    service = owner.services(selected, history=registrations, owner_kind="rollover")
    current_service = owner.services(current, history=registrations, owner_kind="rollover")
    profile = manual_profile(owner.broker.boundary._manifest)
    session = owner.authority.dal.read_session(owner.authority.session_id)
    if session is None:
        raise SourceConflict("Original authority session is unavailable.")
    pools = SourceOutputPoolDAL(owner.connect, execution_evidence=True)
    return RolloverReplacementWorkflow(
        proposals=service.proposals,
        verification=service.verification,
        activation=service,
        continuation=RolloverReplacementContinuation(
            dal=RolloverReplacementDAL(pools),
            authority=owner.authority,
            next_workflow=lambda key: workflow(owner, key, ancestors=(*ancestors, operation_id)),
        ),
        plan_factory=lambda proposal, key: verification_plan(
            selected,
            proposal,
            verification_id=key,
            manifest_hash=bytes(session["ManifestHash"]).hex(),
            profile_hash=hashlib.sha256(encode(profile)).hexdigest(),
            project_id=profile["project_id"],
        ),
        proposal_writer=current_service.proposals,
    )
