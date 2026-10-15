"""Authority-sealed effective registrations; original manifests remain immutable."""

import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity
from services.export_execution_protocol import decode, encode
from services.export_replacement_plan import replacement_registration, verified_registration
from services.export_runtime_composition import RuntimeRegistration


class ReplacementActivationService:
    def __init__(self, *, dal, proposals, verification, authority):
        self.dal, self.proposals, self.verification, self.authority = (
            dal,
            proposals,
            verification,
            authority,
        )

    def apply(self, replacement_id, verification_id, *, token, actor, reason):
        action_id = identity(actor.removeprefix("recovery:"))
        if (
            actor != "recovery:" + action_id
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise SourceConflict("Durable activation action and bounded reason required.")
        with self.authority._lock:
            existing = [
                r
                for r in self.dal.chain(self.proposals.registration.value()["account"])
                if identity(r["ReplacementID"]) == replacement_id
            ]
            if existing:
                row = existing[0]
                if (
                    identity(row["ActivationID"]) != action_id
                    or row["Actor"] != actor
                    or row["Reason"] != reason
                ):
                    raise SourceConflict("Another action owns the registered replacement.")
                return self.verify(row, self.proposals.registration)
            proposal = self.proposals.inspect(replacement_id)
            checked = self.verification.inspect(verification_id)
            if (
                checked is None
                or checked["state"] != "verified"
                or checked["replacement_id"] != replacement_id
                or checked["token"] != token
            ):
                raise SourceConflict(
                    "Review the current successful replacement verification before activation."
                )
            if any(f.get("configuration_summary") for f in checked["files"]):
                readiness = self.verification.configuration_readiness(verification_id)
                if not readiness["ready"]:
                    raise SourceConflict(readiness["issue"])
            projected = replacement_registration(
                self.proposals.registration,
                targets=sorted(proposal["mapping"]),
                replacements=proposal["mapping"],
                replacement_id=replacement_id,
            )
            projected = verified_registration(projected, checked["files"])
            isolated = self.proposals.containment.inspect(proposal["job_id"])
            if isolated["outcome"] != "targets_isolated":
                raise SourceConflict("Original targets are no longer verified as isolated.")
            pool_document = projected["pool_registration"]
            before_pool = None
            if pool_document is not None:
                snapshot = self.proposals.containment.dal.snapshot(
                    proposal["job_id"],
                    account=self.proposals.registration.value()["account"],
                    pool_id=pool_document["previous_pool_id"],
                )
                before_pool = snapshot["pool"]
            audit = dict(
                kind="export_replacement_activation/1",
                activation_id=action_id,
                replacement_id=replacement_id,
                verification_id=verification_id,
                proposal=proposal,
                projected=projected,
                verification=checked,
                before_pool=before_pool,
                actor=actor,
                reason=reason,
                business_resolved=False,
            )
            raw = encode(audit)
            stored = self.authority.store.put(raw)
            receipt = dict(reference=identity(stored.key), sha256=stored.sha256)
            if (
                self.authority.store.read_reference(
                    receipt["reference"], bytes.fromhex(receipt["sha256"])
                )
                != raw
            ):
                raise SourceConflict("Activation receipt did not verify.")
            self.dal.activate(
                activation_id=action_id,
                proposal=projected,
                verification_id=verification_id,
                account=self.proposals.registration.value()["account"],
                receipt=receipt,
                actor=actor,
                reason=reason,
                old_pool=before_pool,
            )
            records = [
                r
                for r in self.dal.chain(self.proposals.registration.value()["account"])
                if identity(r["ActivationID"]) == action_id
            ]
            if len(records) != 1:
                raise SourceConflict("Original activation receipt is unavailable.")
            return self.verify(records[0], self.proposals.registration)

    def verify(self, row, base):
        raw = self.proposals._read_receipt(identity(row["ReceiptReference"]), row["ReceiptHash"])
        if hashlib.sha256(raw).hexdigest() != row["ReceiptHash"]:
            raise SourceConflict("Private activation receipt hash differs.")
        audit = decode(raw)
        proposal = self.proposals.inspect(identity(row["ReplacementID"]))
        observed = self.verification.inspect(identity(row["VerificationID"]))
        if observed is None or observed["state"] != "verified":
            raise SourceConflict("Activation has no verified replacement file history.")
        projected = verified_registration(
            replacement_registration(
                base,
                targets=sorted(proposal["mapping"]),
                replacements=proposal["mapping"],
                replacement_id=proposal["replacement_id"],
            ),
            observed["files"],
        )
        if (
            audit.get("kind") != "export_replacement_activation/1"
            or audit.get("business_resolved") is not False
            or audit.get("activation_id") != identity(row["ActivationID"])
            or audit.get("replacement_id") != identity(row["ReplacementID"])
            or audit.get("verification_id") != identity(row["VerificationID"])
            or audit.get("proposal") != proposal
            or audit.get("projected") != projected
            or audit.get("verification", {}).get("files") != observed["files"]
            or row["BaseRegistrationHash"] != base.fingerprint
            or row["RegistrationHash"] != projected["registration_sha256"]
            or json.loads(row["RegistrationJson"]) != projected["registration"]
            or audit.get("actor") != row["Actor"]
            or audit.get("reason") != row["Reason"]
        ):
            raise SourceConflict("Activation differs from its exact sealed proposal and readback.")
        return dict(
            activation_id=identity(row["ActivationID"]),
            replacement_id=proposal["replacement_id"],
            verification_id=identity(row["VerificationID"]),
            job_id=proposal["job_id"],
            registration=projected["registration"],
            registration_sha256=projected["registration_sha256"],
            mapping=proposal["mapping"],
            files=observed["files"],
            input_commitment=self.proposals.containment.inspect(proposal["job_id"])[
                "input_commitment"
            ],
            business_resolved=False,
        )


def effective_registration(base, records, make_service):
    """Reconstruct one authenticated unbranched chain after every restart."""
    current, history = base, []
    pending = list(records)
    seen = {base.fingerprint}
    while pending:
        next_rows = [r for r in pending if r["BaseRegistrationHash"] == current.fingerprint]
        if len(next_rows) != 1:
            raise SourceConflict("Replacement registration chain is incomplete or branched.")
        row = next_rows[0]
        if row["AccountKey"] != base.value()["account"] or row["RegistrationHash"] in seen:
            raise SourceConflict(
                "Replacement registration chain crosses scope or contains a cycle."
            )
        result = make_service(current).verify(row, current)
        history.append(result)
        current = RuntimeRegistration(result["registration"])
        seen.add(current.fingerprint)
        pending.remove(row)
    return current, history
