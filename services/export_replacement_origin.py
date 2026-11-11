"""Fresh-file lineage from the sealed replacement activation and complete read journal."""

import hashlib
import json

from core.export_execution_host import HostBoundaryError
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity
from services.export_replacement_verification import (
    ReplacementVerificationEvidence,
    ReplacementVerificationPlan,
)


def verify_replacement_origin(*, dal, store, account, targets, owner_email, editor_email):
    members = dal.read_replacement_origins(account, targets)
    if len(members) != len(targets) or [r["FileID"] for r in members] != targets:
        raise SourceConflict(
            "Unproven old files cannot be used; complete sealed replacement pool origins required."
        )
    first = members[0]
    if any(
        {k: v for k, v in member.items() if k != "FileID"}
        != {k: v for k, v in first.items() if k != "FileID"}
        for member in members
    ):
        raise SourceConflict("Replacement pool origins have different activation histories.")
    plan = ReplacementVerificationPlan(json.loads(first["RequestJson"]))
    value = plan.value()
    if (
        (
            value["account"],
            value["owner_email"],
            value["editor_email"],
            sorted(f["file_id"] for f in value["files"]),
        )
        != (account, owner_email, editor_email, targets)
        or plan.digest != bytes(first["PlanHash"])
        or plan.digest != bytes(first["RequestHash"])
    ):
        raise SourceConflict("Replacement origin policy differs from the registered pool.")
    try:
        try:
            raw = store.read_reference(first["ReceiptReference"], first["ReceiptHash"])
            if hashlib.sha256(raw).digest() != bytes(first["ReceiptHash"]):
                raise ValueError("Activation receipt changed")
            audit = json.loads(raw)
            activation_files = audit.get("verification", {}).get("files")
        except (HostBoundaryError, SourceConflict, OSError, KeyError, ValueError):
            from services.export_registration_attestation import read_sealed

            successor = read_sealed(dal.connect, store, account, first["ActivationID"])
            # These fields belong to the independently derived registration.
            # The missing original receipt is never restored or relabelled.
            audit = successor["expected_audit"]
            activation_files = successor["result"]["files"]
        verified_raw = store.read_reference(
            first["VerificationReceiptReference"], first["VerificationReceiptHash"]
        )
        if hashlib.sha256(verified_raw).digest() != bytes(first["VerificationReceiptHash"]):
            raise ValueError("Readback receipt changed")
        verified = json.loads(verified_raw)
    except Exception as exc:
        raise SourceConflict("Private replacement origin evidence is unavailable.") from exc
    actual = ReplacementVerificationEvidence(dal=dal, store=store).eligibility(
        plan, identity(first["StreamID"])
    )
    projected = audit.get("projected", {})
    pool = projected.get("pool_registration", {})
    if (
        audit.get("kind") != "export_replacement_activation/1"
        or audit.get("business_resolved") is not False
        or audit.get("activation_id") != identity(first["ActivationID"])
        or audit.get("replacement_id") != identity(first["ReplacementID"])
        or audit.get("verification_id") != identity(first["VerificationID"])
        or value["plan_id"] != identity(first["VerificationID"])
        or value["replacement_id"] != identity(first["ReplacementID"])
        or projected.get("registration_sha256") != bytes(first["RegistrationHash"]).hex()
        or projected.get("registration") != json.loads(first["RegistrationJson"])
        or not isinstance(pool, dict)
        or pool.get("replacement_id") != identity(first["NewPoolID"])
        or sorted([pool.get("index_file_id", ""), *pool.get("slot_file_ids", [])]) != targets
        or verified.get("kind") != "export_replacement_verification/1"
        or verified.get("provider_observation") is not True
        or verified.get("evidence") != actual
        or activation_files != actual["files"]
    ):
        raise SourceConflict("Replacement pool origin differs from its original sealed readback.")
    return actual
