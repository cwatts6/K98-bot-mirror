"""Seal a separate verified registration dependency without rewriting lost history."""

import hashlib
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_execution_protocol import decode, encode
from services.export_registration_attestation_dal import RegistrationAttestationDAL
from services.export_runtime_composition import RuntimeRegistration


def inspect(service, row, base):
    proof = service.projection(row, base)
    dal = RegistrationAttestationDAL(service.dal.connect, base.value()["account"])
    return proof, digest(proof).hex(), dal


def read_sealed(connect, store, account, activation_id):
    """Read the new witness as a new witness, bound to the unchanged SQL row."""
    from services.export_replacement_activation_dal import ReplacementActivationDAL

    saved = RegistrationAttestationDAL(connect, account).latest(activation_id)
    current = [
        row
        for row in ReplacementActivationDAL(connect).chain(account)
        if identity(row["ActivationID"]) == identity(activation_id)
    ]
    if saved is None or len(current) != 1:
        raise SourceConflict("Independent activation witness and exact SQL binding required.")
    raw = store.read_reference(saved["ReceiptReference"], bytes.fromhex(saved["ReceiptHash"]))
    audit = decode(raw)
    proof = audit.get("projection")
    if (
        hashlib.sha256(raw).hexdigest() != saved["ReceiptHash"]
        or not isinstance(proof, dict)
        or audit.get("kind") != "registration_attestation/1"
        or proof.get("original") != current[0]
        or proof.get("original_receipt_verified") is not False
        or digest(proof).hex() != saved["ProjectionHash"]
        or saved["OriginalReference"] != identity(current[0]["ReceiptReference"])
        or saved["OriginalHash"] != current[0]["ReceiptHash"]
        or audit.get("action_id") != saved["ActionID"]
        or audit.get("actor") != saved["Actor"]
        or saved["Actor"] != "recovery:" + saved["ActionID"]
        or audit.get("reason") != saved["Reason"]
        or audit.get("review_hash") != saved["ReviewHash"]
    ):
        raise SourceConflict("The new registration witness differs from its own sealed commitment.")
    return proof


def verify(service, row, base, proof=None):
    derived, _, dal = (
        inspect(service, row, base)
        if proof is None
        else (proof, None, RegistrationAttestationDAL(service.dal.connect, base.value()["account"]))
    )
    saved = dal.latest(row["ActivationID"])
    if saved is None:
        raise SourceConflict(
            "Missing activation receipt requires a separate verified registration attestation."
        )
    raw = service.authority.store.read_reference(
        saved["ReceiptReference"], bytes.fromhex(saved["ReceiptHash"])
    )
    audit = decode(raw)
    if (
        hashlib.sha256(raw).hexdigest() != saved["ReceiptHash"]
        or audit.get("kind") != "registration_attestation/1"
        or audit.get("projection") != derived
        or digest(derived).hex() != saved["ProjectionHash"]
        or saved["OriginalReference"] != identity(row["ReceiptReference"])
        or saved["OriginalHash"] != row["ReceiptHash"]
        or audit.get("action_id") != saved["ActionID"]
        or audit.get("actor") != saved["Actor"]
        or saved["Actor"] != "recovery:" + saved["ActionID"]
        or audit.get("reason") != saved["Reason"]
        or audit.get("review_hash") != saved["ReviewHash"]
    ):
        raise SourceConflict("Independent registration attestation no longer verifies.")
    return derived["result"]


def apply(service, row, base, *, token, actor, reason):
    if (
        not isinstance(actor, str)
        or not actor.startswith("recovery:")
        or not isinstance(token, str)
        or re.fullmatch(r"[0-9a-f]{64}", token) is None
        or not isinstance(reason, str)
        or not 1 <= len(reason.strip()) <= 512
    ):
        raise SourceConflict("Confirmed exact registration attestation required.")
    action_id = identity(actor[9:])
    proof, current, dal = inspect(service, row, base)
    saved = dal.latest(row["ActivationID"])
    if saved and saved["ActionID"] == action_id:
        if saved["ReviewHash"] != token or saved["Actor"] != actor or saved["Reason"] != reason:
            raise SourceConflict("Another review owns this registration attestation.")
        return verify(service, row, base, proof)
    if current != token:
        raise SourceConflict("Registration dependencies changed; review again.")
    raw = encode(
        dict(
            kind="registration_attestation/1",
            action_id=action_id,
            projection=proof,
            actor=actor,
            reason=reason,
            review_hash=token,
        )
    )
    stored = service.authority.store.put(raw)
    receipt = dict(reference=identity(stored.key), sha256=stored.sha256)
    if (
        service.authority.store.read_reference(
            receipt["reference"], bytes.fromhex(receipt["sha256"])
        )
        != raw
    ):
        raise SourceConflict("New registration attestation could not be read back.")
    dal.save(
        row, proof, action_id=action_id, token=token, receipt=receipt, actor=actor, reason=reason
    )
    return verify(service, row, base)


def open_recovery(broker, reference):
    """Walk verified predecessors only; never bootstrap from RegistrationJson."""
    registrations = [broker.base_registration]
    pending = list(broker.replacements.activation_dal.chain(registrations[0].value()["account"]))
    if len(pending) > 256:
        raise SourceConflict("Registration history exceeds the bounded recovery review.")
    seen = {registrations[0].fingerprint}
    while pending:
        base = registrations[-1]
        candidates = [r for r in pending if r["BaseRegistrationHash"] == base.fingerprint]
        if len(candidates) != 1:
            raise SourceConflict("Registration history is incomplete or branched.")
        row = candidates[0]
        if row["AccountKey"] != base.value()["account"] or row["RegistrationHash"] in seen:
            raise SourceConflict("Registration history crosses scope or cycles.")
        service = broker.replacements.services(
            base,
            history=registrations,
            owner_kind="rollover" if row.get("OutputOperationID") else "job",
        )
        if identity(row["ReceiptReference"]) == identity(reference):
            proof, token, dal = inspect(service, row, base)
            saved = dal.latest(row["ActivationID"])
            verified = False
            try:
                verify(service, row, base, proof)
                verified = True
            except (SourceConflict, OSError, KeyError, ValueError):
                pass
            return dict(
                service=service,
                row=row,
                base=base,
                proof=proof,
                token=token,
                attestation=saved,
                verified=verified,
            )
        result = service.verify(row, base)
        registrations.append(RuntimeRegistration(result["registration"]))
        seen.add(registrations[-1].fingerprint)
        pending.remove(row)
    raise SourceConflict("No exact activation binding exists in this account's history.")


def summary(state):
    return dict(
        review_hash=state["token"],
        attestation=state["attestation"],
        verified=state["verified"],
        activation_id=identity(state["row"]["ActivationID"]),
        registration_sha256=state["proof"]["result"]["registration_sha256"],
    )
