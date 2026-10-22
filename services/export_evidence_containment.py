"""Find a lost isolation binding using only the authenticated registration prefix."""

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_containment_attestation import inspect, verify
from services.export_containment_attestation_dal import ContainmentAttestationDAL
from services.export_runtime_composition import RuntimeRegistration


def open_recovery(broker, reference):
    account = broker.base_registration.value()["account"]
    dal = ContainmentAttestationDAL(broker.authority.dal.connect, account)
    binding = dal.binding(reference)
    if binding["PreparationID"] is not None:
        raise SourceConflict("Read containment needs its separately typed recovery.")
    rollover = binding["OutputOperationID"] is not None
    source_id = binding["OutputOperationID"] if rollover else binding["JobID"]
    registrations = [broker.base_registration]
    records = list(broker.replacements.activation_dal.chain(account))
    if len(records) > 256:
        raise SourceConflict("Registration history exceeds the bounded successor review.")
    while records:
        current = registrations[-1]
        rows = [row for row in records if row["BaseRegistrationHash"] == current.fingerprint]
        if len(rows) != 1:
            raise SourceConflict(
                "Registration history is incomplete or branched; preserve it for review."
            )
        row = rows[0]
        try:
            result = broker.replacements.services(
                current,
                history=registrations,
                owner_kind="rollover" if row.get("OutputOperationID") else "job",
            ).verify(row, current)
        except (SourceConflict, OSError, ValueError, KeyError):
            break  # Do not treat unverified SQL registration JSON as authority.
        registrations.append(RuntimeRegistration(result["registration"]))
        records.remove(row)
    if rollover:
        from services.rollover_replacement_authority import containment_service as factory
    else:
        from services.export_target_recovery_authority import _service as factory
    for registration in reversed(registrations):
        service = factory(broker.authority, registration)
        try:
            scoped = service._scope(source_id)
            pool_id = scoped[1]
            snapshot = service.dal.snapshot(source_id, account=account, pool_id=pool_id)
            if snapshot["receipt"] != binding:
                raise SourceConflict("Containment binding changed during review.")
            proof, token, _ = inspect(service, snapshot)
        except (SourceConflict, ValueError, KeyError):
            continue
        verified = None
        try:
            verified = verify(service, snapshot)
        except (SourceConflict, OSError, ValueError, KeyError):
            pass
        return dict(
            service=service,
            snapshot=snapshot,
            proof=proof,
            token=token,
            attestation=dal.latest(binding["ContainmentID"]),
            verified=verified,
            source_id=source_id,
            owner_kind="rollover" if rollover else "job",
        )
    raise SourceConflict("No authenticated registration verifies these exact permanent fences.")


def summary(state):
    return dict(
        review_hash=state["token"],
        attestation=state["attestation"],
        verified=state["verified"],
        source_id=state["source_id"],
        owner_kind=state["owner_kind"],
    )
