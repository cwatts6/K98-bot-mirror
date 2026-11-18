"""Verify an explicitly discarded replacement read without asserting observation."""

import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.config_read_containment import read_ledger, stream_wire
from services.export_replacement_verification import ReplacementVerificationPlan


def verify_discarded_replacement(execution, store, stream, *, account, registration_hash):
    if (
        stream["State"] != "read_contained"
        or stream["Purpose"] != "enrollment"
        or stream["AccountKey"] != account
        or bytes(stream["RegistrationHash"]) != registration_hash
        or stream["ActiveAccountKey"] is not None
        or stream["PreparationID"] is None
        or any(
            stream[k] is not None for k in ("JobID", "OutputOperationID", "NestedToken", "Epoch")
        )
    ):
        raise SourceConflict("Exact discarded replacement read required.")
    try:
        raw = store.read_reference(stream["ClosureReference"], stream["ClosureHash"])
        if hashlib.sha256(raw).digest() != bytes(stream["ClosureHash"]):
            raise ValueError("Changed receipt")
        audit = json.loads(raw)
        before = audit["before"]
        plan = ReplacementVerificationPlan(json.loads(before["preparation"]["RequestJson"]))
        original = before["streams"][0]
        value = plan.value()
    except Exception as exc:
        raise SourceConflict("Private replacement read discard cannot be verified.") from exc
    if (
        audit.get("kind") != "export_replacement_read_discard/1"
        or audit.get("provider_observation") is not False
        or audit.get("child_termination_verified") is not False
        or len(before["streams"]) != 1
        or before["attempt"]["State"] != "checking"
        or before["attempt"]["VerificationID"] != value["plan_id"]
        or before["attempt"]["ReplacementID"] != value["replacement_id"]
        or before["attempt"]["PlanHash"] != plan.digest.hex()
        or before["preparation"]["RequestHash"] != plan.digest.hex()
        or value["account"] != account
        or str(stream["PreparationID"]).lower() != value["plan_id"]
        or registration_hash != plan.digest
    ):
        raise SourceConflict("Replacement discard differs from its original typed read plan.")
    current = stream_wire(stream)
    changed = {
        "State",
        "ActiveAccountKey",
        "Version",
        "ClosureHash",
        "ClosureReference",
        "EventDigest",
        "ClosedUTC",
    }
    if {k: v for k, v in current.items() if k not in changed} != {
        k: v for k, v in original.items() if k not in changed
    } or current["Version"] != original["Version"] + 1:
        raise SourceConflict("Discarded replacement stream identity changed.")
    seal = read_ledger(execution, stream)
    if seal != audit["ledger"] or seal["event_digest"] != bytes(stream["EventDigest"]).hex():
        raise SourceConflict("Discarded replacement read membership changed.")
    return seal
