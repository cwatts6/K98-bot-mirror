"""Fresh read checks after lost terminal evidence, never substituted eligibility.

Only the guided workflow uses this fallback. Activation and authenticated history
continue to require the original complete private verification evidence.
"""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_read_containment import read_ledger
from services.export_coordination_dal import identity


def terminal_read_snapshot(service, verification_id):
    found = service._snapshot(verification_id)
    if found is None:
        raise SourceConflict("The original replacement check is missing.")
    snapshot, plan = found
    attempt, preparation = snapshot["attempt"], snapshot["preparation"]
    expected_resources = [
        "account:" + plan.value()["account"],
        *("destination:" + f["file_id"] for f in plan.value()["files"]),
    ]
    if (
        attempt["State"] not in {"verified", "discarded"}
        or attempt["Version"] != 2
        or preparation["State"]
        != ("completed" if attempt["State"] == "verified" else "unavailable")
        or preparation["Version"] != 2
        or len(snapshot["streams"]) > 1
        or (attempt["State"] == "verified" and len(snapshot["streams"]) != 1)
        or sorted(r["ResourceKey"] for r in snapshot["resources"]) != sorted(expected_resources)
        or any(
            identity(r[field]) == verification_id
            for r in snapshot["resources"]
            for field in ("ActivePreparationID", "OwnerID")
            if r[field] is not None
        )
    ):
        raise SourceConflict("Only a settled read check with released ownership can be replaced.")
    for stream in snapshot["streams"]:
        if (
            stream["State"] != ("closed" if attempt["State"] == "verified" else "read_contained")
            or stream["ActiveAccountKey"] is not None
            or stream["Purpose"] != "enrollment"
            or stream["AccountKey"] != plan.value()["account"]
            or identity(stream["PreparationID"]) != verification_id
            or identity(stream["SessionID"]) != attempt["SessionID"]
            or identity(stream["OwnerID"]) != verification_id
            or stream["Fence"] != preparation["Fence"]
            or stream["ClaimVersion"] != 1
            or stream["RegistrationHash"] != plan.digest.hex()
            or stream["SnapshotHash"] != plan.digest.hex()
            or any(
                stream[k] is not None
                for k in ("JobID", "OutputOperationID", "NestedToken", "Epoch")
            )
        ):
            raise SourceConflict("The original check does not have a terminal read dispatch fence.")
        current = service.authority.dal.read_stream(stream["StreamID"])
        ledger = read_ledger(service.authority.dal, current)
        if ledger["event_digest"] != stream["EventDigest"]:
            raise SourceConflict("The original check's typed ledger changed.")
    if service._snapshot(verification_id)[0] != snapshot:
        raise SourceConflict("The original read check changed during investigation.")
    return snapshot


def inspect_read_check(service, verification_id):
    try:
        return service.inspect(verification_id)
    except (SourceConflict, ValueError, KeyError, TypeError):
        # Re-read and authenticate the proposal independently. This cannot
        # rescue a missing proposal, a live claim, a mutation, or bad membership.
        snapshot = terminal_read_snapshot(service, verification_id)
        attempt = snapshot["attempt"]
        return dict(
            verification_id=verification_id,
            replacement_id=attempt["ReplacementID"],
            state="unverifiable",
            original_state=attempt["State"],
            token=digest(snapshot).hex(),
            files=[],
            actor=attempt["Actor"],
            reason=attempt["Reason"],
        )
