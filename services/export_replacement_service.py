"""Authority-sealed proposals with restart and lost-acknowledgement verification.

A proposed file is not yet verified or activated. This service never dispatches
provider requests, changes registration or settles the original business job.
"""

import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity
from services.export_execution_protocol import encode
from services.export_replacement_plan import replacement_registration


class ExportReplacementService:
    def __init__(self, *, dal, containment, registration, store):
        self.dal, self.containment = dal, containment
        self.registration, self.store = registration, store

    def _read_receipt(self, reference, expected_hash):
        try:
            raw = self.store.read_reference(reference, bytes.fromhex(expected_hash))
        except Exception as exc:
            raise SourceConflict("Private replacement evidence is unavailable.") from exc
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise SourceConflict("Private replacement receipt hash differs.")
        return raw

    def propose(self, job_id, *, token, replacements, actor, reason, owner_email=None):
        job_id = identity(job_id)
        if not isinstance(actor, str) or not actor.startswith("recovery:"):
            raise SourceConflict("Durable admin recovery action required.")
        replacement_id = identity(actor.removeprefix("recovery:"))
        if (
            actor != "recovery:" + replacement_id
            or not isinstance(reason, str)
            or not reason.strip()
            or len(reason) > 512
        ):
            raise SourceConflict("Canonical recovery identity and bounded reason required.")
        existing = self.dal.read(replacement_id, account=self.registration.value()["account"])
        if existing is not None:
            result = self.verify(existing)
            if owner_email is not None and result["owner_email"] != owner_email:
                raise SourceConflict("Another proposal owns this recovery action.")
            if (
                result["job_id"],
                result["containment_token"],
                result["mapping"],
                result["actor"],
                result["reason"],
            ) != (job_id, token, replacements, actor, reason):
                raise SourceConflict("Another proposal owns this recovery action.")
            return result
        isolated = self.containment.inspect(job_id)
        if isolated["outcome"] != "targets_isolated" or isolated["token"] != token:
            raise SourceConflict(
                "Verified permanent isolation and the exact reviewed decision are required."
            )
        containment_id = identity(isolated["actor"].removeprefix("recovery:"))
        from services.export_replacement_input import replacement_owners

        owners = replacement_owners(self.registration, isolated["targets"])
        if owner_email is None and len(owners) == 1:
            owner_email = owners[0]
        if owner_email not in owners:
            raise SourceConflict("Choose a registered owner using the guided replacement form.")
        proposal = replacement_registration(
            self.registration,
            targets=isolated["targets"],
            replacements=replacements,
            replacement_id=replacement_id,
        )
        audit = dict(
            kind="export_replacement_plan/1",
            job_id=job_id,
            containment_id=containment_id,
            containment_token=token,
            proposal=proposal,
            actor=actor,
            reason=reason,
            owner_email=owner_email,
            files_verified=False,
            registration_activated=False,
            business_resolved=False,
        )
        raw = encode(audit)
        receipt = self.store.put(raw)
        reference = identity(receipt.key)
        if self._read_receipt(reference, receipt.sha256) != raw:
            raise SourceConflict("Private replacement proposal did not verify.")
        self.dal.create(
            proposal=proposal,
            containment_id=containment_id,
            account=self.registration.value()["account"],
            receipt=dict(reference=reference, sha256=receipt.sha256),
            actor=actor,
            reason=reason,
        )
        return self.inspect(replacement_id)

    def inspect(self, replacement_id):
        record = self.dal.read(
            identity(replacement_id), account=self.registration.value()["account"]
        )
        if record is None:
            raise SourceConflict("Replacement proposal is unavailable in this account.")
        return self.verify(record)

    def verify(self, record):
        plan = record["plan"]
        raw = self._read_receipt(plan["ReceiptReference"], plan["ReceiptHash"])
        audit = json.loads(raw)
        proposal = audit["proposal"]
        mapping = {r["OldFileID"]: r["NewFileID"] for r in record["targets"]}
        isolated = self.containment.inspect(plan["JobID"])
        expected = replacement_registration(
            self.registration,
            targets=isolated["targets"],
            replacements=mapping,
            replacement_id=plan["ReplacementID"],
        )
        from services.export_replacement_input import replacement_owners

        if (
            audit.get("kind") != "export_replacement_plan/1"
            or any(
                audit.get(k) is not False
                for k in ("files_verified", "registration_activated", "business_resolved")
            )
            or plan["AccountKey"] != self.registration.value()["account"]
            or isolated["outcome"] != "targets_isolated"
            or isolated["token"] != audit["containment_token"]
            or isolated["actor"] != "recovery:" + plan["ContainmentID"]
            or proposal != expected
            or audit.get("owner_email")
            not in replacement_owners(self.registration, isolated["targets"])
            or (audit["job_id"], audit["containment_id"], audit["actor"], audit["reason"])
            != (plan["JobID"], plan["ContainmentID"], plan["Actor"], plan["Reason"])
            or plan["Actor"] != "recovery:" + plan["ReplacementID"]
            or plan["BaseRegistrationHash"] != expected["base_registration_sha256"]
            or plan["ProjectedRegistrationHash"] != expected["registration_sha256"]
            or json.loads(plan["MappingJson"])
            != [dict(old=old, new=new) for old, new in sorted(mapping.items())]
        ):
            raise SourceConflict("Replacement proposal differs from its sealed decision.")
        return dict(
            replacement_id=plan["ReplacementID"],
            job_id=plan["JobID"],
            containment_token=audit["containment_token"],
            mapping=mapping,
            actor=plan["Actor"],
            reason=plan["Reason"],
            owner_email=audit["owner_email"],
            outcome="verification_required",
            files_verified=False,
            registration_activated=False,
            business_resolved=False,
        )
