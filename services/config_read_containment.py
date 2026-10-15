"""Explicit read dispatch containment when historical private closure is unavailable.

SQL typed requests are authoritative for read/write admission. This path seals that
ledger, fences future dispatch and discards the result; it proves neither a dead
child nor provider success. It cannot contain a mutation or supply a fresh probe.
"""

from contextlib import closing
import hashlib
import json
from uuid import UUID

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.dal.source_output_pool_dal import _wire
from services.config_preparation_recovery_service import validate_snapshot
from services.export_execution_protocol import encode

READ_OPERATIONS = frozenset(
    (
        "sheets.get",
        "sheets.values.get",
        "sheets.values.batchGet",
        "drive.files.get",
        "drive.permissions.list",
    )
)
READ_PREFIXES = (
    ["prepared"],
    ["prepared", "dispatch_intent"],
    ["prepared", "not_sent"],
    ["prepared", "dispatch_intent", "succeeded"],
    ["prepared", "dispatch_intent", "unknown"],
)


def stream_wire(stream):
    value = _wire(stream)
    for key in (
        "StreamID",
        "SessionID",
        "ChildIdentity",
        "ClosureReference",
        "NestedToken",
        "OutputOperationID",
    ):
        if value[key] is not None:
            value[key] = str(value[key]).lower()
    return value


def read_ledger(execution, stream):
    """Read all typed SQL membership; recheck the stream around these short reads."""
    identifier = str(stream["StreamID"]).lower()
    count = 0
    with closing(execution.request_ids(identifier)) as identities:
        for request_id in identities:
            request, events = execution.read_request(request_id)
            count += 1
            if (
                request is None
                or str(request["RequestID"]).lower() != request_id
                or str(request["StreamID"]).lower() != identifier
                or request["Sequence"] != count
                or request["RequestKind"] != "read"
                or request["Operation"] not in READ_OPERATIONS
                or [e["State"] for e in events] not in READ_PREFIXES
                or any(
                    e["EventSequence"] != i or str(e["RequestID"]).lower() != request_id
                    for i, e in enumerate(events, 1)
                )
            ):
                raise SourceConflict("Only a complete typed read ledger can be isolated.")
    sequence, event_digest = execution.stream_digest(identifier)
    if count != sequence or sequence != stream["LastSequence"]:
        raise SourceConflict("Read request membership changed or is incomplete.")
    if stream_wire(execution.read_stream(identifier)) != stream_wire(stream):
        raise SourceConflict("Read execution changed during investigation.")
    return dict(last_sequence=sequence, event_digest=event_digest.hex())


class ConfigReadContainment:
    def __init__(self, *, dal, execution, store, target, registration_hash, storage_owner):
        self.dal, self.execution, self.store, self.target = dal, execution, store, target
        self.registration_hash, self.storage_owner = registration_hash, storage_owner

    def inspect(self):
        snapshot = self.dal.snapshot(self.target)
        validate_snapshot(
            snapshot,
            self.target,
            registration_hash=self.registration_hash,
            storage_owner=self.storage_owner,
            allow_reads=True,
            containment=True,
        )
        if json.loads(snapshot["preparation"]["RequestJson"]).get("purpose") == "output_enrollment":
            raise SourceConflict("Enrollment cannot use configuration read containment.")
        seals = {}
        for expected in snapshot["streams"]:
            stream = self.execution.read_stream(expected["StreamID"])
            if stream_wire(stream) != expected:
                raise SourceConflict("Exact configuration stream changed.")
            seals[expected["StreamID"]] = read_ledger(self.execution, stream)
        if self.dal.snapshot(self.target) != snapshot:
            raise SourceConflict("Read containment ownership changed during investigation.")
        return dict(snapshot=snapshot, snapshot_sha256=digest(snapshot).hex(), streams=seals)

    def apply(self, *, approved_snapshot_sha256, actor, reason):
        report = self.inspect()
        if report["snapshot_sha256"] != approved_snapshot_sha256:
            raise SourceConflict("Approved read containment evidence changed.")
        audit = dict(
            kind="config_read_containment/1",
            actor=actor,
            reason=reason,
            snapshot_sha256=approved_snapshot_sha256,
            before=report["snapshot"],
            streams=report["streams"],
            outcome="read_isolated",
            provider_observation=False,
            child_termination_verified=False,
        )
        raw = encode(audit)
        receipt = self.store.put(raw)
        reference = str(UUID(receipt.key))
        if self.store.read_reference(reference, bytes.fromhex(receipt.sha256)) != raw:
            raise SourceConflict("Private read containment receipt did not verify.")
        binding = dict(reference=reference, sha256=receipt.sha256, streams=report["streams"])
        self.dal.settle(
            self.target, report["snapshot"], dict(audit, receipt=binding), containment=binding
        )


def verify_contained_read(execution, store, stream, *, account, registration_hash):
    """Historical no-write coverage only. Never a provider observation or child wait."""
    if (
        stream["State"] != "read_contained"
        or stream["Purpose"] != "probe"
        or stream["AccountKey"] != account
        or bytes(stream["RegistrationHash"]) != registration_hash
        or stream["ActiveAccountKey"] is not None
        or stream["PreparationID"] is None
        or any(
            stream[k] is not None for k in ("JobID", "OutputOperationID", "NestedToken", "Epoch")
        )
    ):
        raise SourceConflict("Exact contained configuration read required.")
    raw = store.read_reference(stream["ClosureReference"], stream["ClosureHash"])
    if hashlib.sha256(raw).digest() != bytes(stream["ClosureHash"]):
        raise SourceConflict("Private read containment receipt differs.")
    audit = json.loads(raw)
    if (
        audit.get("kind") != "config_read_containment/1"
        or audit.get("provider_observation") is not False
        or audit.get("child_termination_verified") is not False
        or digest(audit["before"]).hex() != audit["snapshot_sha256"]
    ):
        raise SourceConflict("Read containment receipt cannot establish coverage.")
    identifier = str(stream["StreamID"]).lower()
    matches = [s for s in audit["before"]["streams"] if s["StreamID"] == identifier]
    if len(matches) != 1:
        raise SourceConflict("Contained read is absent from its original decision.")
    original, current = matches[0], stream_wire(stream)
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
    } or stream["Version"] != original["Version"] + 1:
        raise SourceConflict("Contained stream identity differs from its original decision.")
    seal = read_ledger(execution, stream)
    if (
        seal != audit["streams"][identifier]
        or seal["event_digest"] != bytes(stream["EventDigest"]).hex()
    ):
        raise SourceConflict("Contained read ledger differs from its private seal.")
    return seal
