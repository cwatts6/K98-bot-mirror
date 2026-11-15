"""Independently attest current permanent fences without recreating lost history.

This path performs no provider call, no resource release and no replay. The old
receipt remains missing. A new sealed witness can satisfy the current isolation
dependency only while all independent SQL owner, target and stream checks hold.
"""

import hashlib
import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_containment_attestation_dal import ContainmentAttestationDAL
from services.export_coordination_dal import identity
from services.export_execution_protocol import decode, encode


def projection(service, snapshot, dal):
    receipt = snapshot["receipt"]
    rollover = "operation" in snapshot
    owner = snapshot["operation" if rollover else "job"]
    owner_key = "OperationID" if rollover else "JobID"
    owner_column = "OutputOperationID" if rollover else "JobID"
    active_column = "ActiveOutputOperationID" if rollover else "ActiveJobID"
    account = service.registration.value()["account"]
    if (
        receipt is None
        or receipt["AccountKey"] != account
        or owner["AccountKey"] != account
        or identity(receipt[owner_column]) != identity(owner[owner_key])
        or receipt["PreparationID"] is not None
        or receipt["JobID" if rollover else "OutputOperationID"] is not None
        or (owner["OwnerID"], owner["Fence"], owner["Version"], owner["State"])
        != (receipt["OwnerID"], receipt["Fence"], receipt["OwnerVersion"] + 1, "uncertain")
        or (rollover and owner["Phase"] != "uncertain")
        or any(row[active_column] == owner[owner_key] for row in snapshot["resources"])
    ):
        raise SourceConflict(
            "Exact retained isolated owner and absence of its reservations must verify."
        )
    targets = service.dal.retained_targets(receipt["ContainmentID"])
    keys = ["account:" + account, *("destination:" + target for target in targets)]
    if (
        not targets
        or targets != sorted(set(targets))
        or snapshot["membership"] != keys
        or [row["ResourceKey"] for row in snapshot["resources"]] != keys
        or (not rollover and digest(targets).hex() != owner["DestinationSetHash"])
    ):
        raise SourceConflict("Complete permanent target membership must verify.")
    config = service.registration.value()
    pool = snapshot["pool"]["pool"] if rollover else snapshot["pool"]
    pool_projection = None
    if pool is not None:
        registered = [p for p in config["pools"] if p["pool_id"] == pool["PoolID"]]
        slots = snapshot["pool"]["slots"] if rollover else snapshot["slots"]
        if (
            len(registered) != 1
            or pool["AccountKey"] != account
            or pool["PoolState"] != "blocked"
            or pool["OwnerID"] is not None
            or pool["BlockedReason"]
            != "Targets permanently isolated; verified replacements required"
            or sorted([registered[0]["index_file_id"], *registered[0]["slot_file_ids"]]) != targets
            or sorted(row["FileID"] for row in slots) != sorted(registered[0]["slot_file_ids"])
        ):
            raise SourceConflict("The complete registered pool must remain permanently blocked.")
        retired = pool.get("RetiredByReplacementID")
        if retired:
            activation = service.dal.replacement_retirement(pool["PoolID"], account)
            if (
                not activation
                or activation["AccountKey"] != account
                or identity(activation["ContainmentID"]) != identity(receipt["ContainmentID"])
                or identity(activation["ReplacementID"]) != identity(retired)
                or identity(activation["OldPoolID"]) != identity(pool["PoolID"])
            ):
                raise SourceConflict("Pool retirement belongs to a different containment.")
        pool_projection = dict(
            pool={
                k: v
                for k, v in pool.items()
                if k not in {"Version", "UpdatedUTC", "RetiredByReplacementID"}
            },
            slots=slots,
        )
    streams = [
        row
        for row in snapshot["streams"]
        if row[owner_column] is not None
        and identity(row[owner_column]) == identity(owner[owner_key])
    ]
    retained = dal.streams(receipt["ContainmentID"])
    if (
        (not rollover and not streams)
        or len(streams) > 4096
        or {r["StreamID"] for r in streams} != {r["StreamID"] for r in retained}
    ):
        raise SourceConflict("The complete bounded isolated stream membership must verify.")
    records = {row["StreamID"]: row for row in retained}
    principals = {row["SessionID"]: row["AuthorityPrincipal"] for row in snapshot["sessions"]}
    seals = {}
    for stream in streams:
        retained_stream = records[stream["StreamID"]]
        owned = stream["OwnerID"] is not None and (
            identity(stream["OwnerID"]),
            stream["Fence"],
        ) == (identity(owner["OwnerID"]), owner["Fence"])
        prior_drain = rollover and (
            stream["OwnerID"],
            stream["Fence"],
            stream["ClaimVersion"],
            stream["Purpose"],
        ) == (None, 0, 1, "probe")
        if (
            stream["State"] != "target_contained"
            or stream["ActiveAccountKey"] is not None
            or stream["Version"] != retained_stream["OriginalVersion"] + 1
            or stream["ClosureReference"] != identity(receipt["ReceiptReference"])
            or stream["ClosureHash"] != receipt["ReceiptHash"]
            or stream["EventDigest"] != retained_stream["EventDigest"]
            or stream["LastSequence"] != retained_stream["LastSequence"]
            or stream["AccountKey"] != account
            or stream["PreparationID"] is not None
            or stream["JobID" if rollover else "OutputOperationID"] is not None
            or stream["ClaimVersion"] > owner["Version"]
            or not (owned or prior_drain)
            or stream["Epoch"] != owner["OldEpoch" if rollover else "PoolEpoch"]
            or (rollover and stream["NestedToken"] is not None)
            or stream["Purpose"] not in {"mutation", "probe"}
            or principals.get(stream["SessionID"]) != snapshot["principal"]
            or sorted(r["key"] for r in json.loads(stream["ScopeJson"])["resources"]) != keys
        ):
            raise SourceConflict("Independent permanent dispatch closure must verify.")
        service.registration.authorize_scope(
            dict(
                stream,
                OwnerKind="operation" if rollover else "job",
                ScopeJson=json.loads(stream["ScopeJson"]),
            )
        )
        seal = service._ledger(stream, targets)
        if seal != dict(
            last_sequence=retained_stream["LastSequence"],
            event_digest=retained_stream["EventDigest"],
        ):
            raise SourceConflict("Retained request/event membership changed after isolation.")
        seals[stream["StreamID"]] = seal
    return dict(
        kind="containment_present_state/1",
        original_receipt=receipt,
        registration_sha256=service.registration.fingerprint,
        owner_kind="rollover" if rollover else "job",
        owner=owner,
        targets=targets,
        pool=pool_projection,
        streams=streams,
        seals=seals,
        original_receipt_verified=False,
        provider_success=False,
        child_termination_verified=False,
    )


def inspect(service, snapshot):
    dal = ContainmentAttestationDAL(service.dal.connect, service.registration.value()["account"])
    proof = projection(service, snapshot, dal)
    return proof, digest(dict(snapshot=snapshot, projection=proof)).hex(), dal


def verify(service, snapshot):
    proof, _, dal = inspect(service, snapshot)
    row = dal.latest(snapshot["receipt"]["ContainmentID"])
    if row is None:
        raise SourceConflict(
            "The original containment receipt is unavailable. Review a separate present-state attestation in its private-evidence incident."
        )
    raw = service.store.read_reference(row["ReceiptReference"], bytes.fromhex(row["ReceiptHash"]))
    audit = decode(raw)
    original = snapshot["receipt"]
    if (
        hashlib.sha256(raw).hexdigest() != row["ReceiptHash"]
        or audit.get("kind") != "containment_attestation/1"
        or audit.get("projection") != proof
        or digest(proof).hex() != row["ProjectionHash"]
        or row["OriginalReference"] != identity(original["ReceiptReference"])
        or row["OriginalHash"] != original["ReceiptHash"]
        or audit.get("action_id") != row["ActionID"]
        or audit.get("actor") != row["Actor"]
        or audit.get("reason") != row["Reason"]
        or audit.get("review_hash") != row["ReviewHash"]
        or row["Actor"] != "recovery:" + row["ActionID"]
    ):
        raise SourceConflict("The separate present-state attestation no longer verifies.")
    owner = proof["owner"]
    fields = (
        (
            "OperationID",
            "AccountKey",
            "PoolID",
            "SourceKey",
            "OldKVK",
            "OldChoiceID",
            "NewKVK",
            "NewChoiceID",
            "OldEpoch",
            "TargetEpoch",
            "PlanHash",
            "PlanJson",
        )
        if proof["owner_kind"] == "rollover"
        else ("JobID", "AccountKey", "ConsumerKind", "InputHash", "IntentID", "ProvenanceJson")
    )
    return dict(
        outcome="targets_isolated",
        business_resolved=False,
        input_commitment={key: owner[key] for key in fields},
        # Compatibility identity of the original SQL containment, not a claim
        # that its missing audit bytes were restored or its old outcome proved.
        token=original["SnapshotHash"],
        targets=proof["targets"],
        actor=original["Actor"],
        reason=original["Reason"],
        attestation_id=row["ActionID"],
        original_receipt_verified=False,
    )


def apply(service, snapshot, *, token, actor, reason):
    if (
        not isinstance(actor, str)
        or not actor.startswith("recovery:")
        or not isinstance(token, str)
        or re.fullmatch(r"[0-9a-f]{64}", token) is None
        or not isinstance(reason, str)
        or not 1 <= len(reason.strip()) <= 512
    ):
        raise SourceConflict("Exact confirmed present-state review required.")
    action_id = identity(actor.removeprefix("recovery:"))
    proof, current, dal = inspect(service, snapshot)
    existing = dal.latest(snapshot["receipt"]["ContainmentID"])
    if existing and existing["ActionID"] == action_id:
        if (
            existing["ReviewHash"] != token
            or existing["Reason"] != reason
            or existing["Actor"] != actor
        ):
            raise SourceConflict("Another review owns this attestation identity.")
        return verify(service, snapshot)
    if token != current:
        raise SourceConflict("Containment evidence changed; review the current fences.")
    audit = dict(
        kind="containment_attestation/1",
        action_id=action_id,
        review_hash=token,
        projection=proof,
        actor=actor,
        reason=reason,
    )
    raw = encode(audit)
    stored = service.store.put(raw)
    receipt = dict(reference=identity(stored.key), sha256=stored.sha256)
    if service.store.read_reference(receipt["reference"], bytes.fromhex(receipt["sha256"])) != raw:
        raise SourceConflict("New private attestation did not independently verify.")
    dal.save(
        service,
        snapshot,
        proof,
        action_id=action_id,
        token=token,
        receipt=receipt,
        actor=actor,
        reason=reason,
    )
    owner = proof["owner"]
    source_id = owner["OperationID" if proof["owner_kind"] == "rollover" else "JobID"]
    return service.inspect(source_id)
