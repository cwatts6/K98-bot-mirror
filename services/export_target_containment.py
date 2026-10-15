"""Explicit whole-target isolation; never assert success or replay an unknown write.

The authority derives every target from its installed registration and the SQL
owner. A sealed decision permanently retires those physical files. Replacement
and publication remain separate required steps after account availability.
"""

from contextlib import closing
import hashlib
import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_read_containment import stream_wire
from services.export_coordination_dal import identity
from services.export_execution_protocol import encode
from services.legacy_export_snapshot_service import configuration_digest


class ExportTargetContainment:
    def __init__(self, *, dal, discovery, execution, store, registration):
        self.dal, self.discovery, self.execution, self.store = dal, discovery, execution, store
        self.registration = registration

    def _scope(self, job_id):
        job = self.discovery.job(job_id)["job"]
        config = self.registration.value()
        if job["ConsumerKind"] == "new_source":
            matches = [
                p
                for p in config["pools"]
                if digest(sorted([p["index_file_id"], *p["slot_file_ids"]])).hex()
                == job["DestinationSetHash"]
            ]
            if len(matches) != 1:
                raise SourceConflict("Unknown-write job must match one complete installed pool.")
            pool = matches[0]
            return config, pool["pool_id"], pool["registration_sha256"]
        if (
            job["ConsumerKind"] not in {"scan_data", "all_kvk"}
            or job["StorageOwner"] != config["storage_owner"]
        ):
            raise SourceConflict("Unknown-write job is outside registered custody.")
        # The registration uses the writer kind, rather than its SQL consumer
        # name. Resolve it by its explicit consumer; do not guess an alias.
        matches = [
            v
            for v in config["legacy_configuration"].values()
            if v["consumer"] == job["ConsumerKind"]
        ]
        if len(matches) != 1:
            raise SourceConflict("One exact legacy writer registration required.")
        return config, None, configuration_digest(matches[0])

    def _ledger(self, stream, targets):
        stream_id = stream["StreamID"]
        raw = self.execution.read_stream(stream_id)
        if raw is None or stream_wire(raw) != stream:
            raise SourceConflict("Provider execution changed during containment review.")
        count = 0
        with closing(self.execution.request_ids(stream_id)) as request_ids:
            for request_id in request_ids:
                request, events = self.execution.read_request(request_id)
                count += 1
                if (
                    request is None
                    or identity(request["StreamID"]) != stream_id
                    or request["Sequence"] != count
                    or request["Operation"] == "sheets.create"
                    or request["TargetID"] not in targets
                    or not events
                    or any(
                        e["EventSequence"] != i or identity(e["RequestID"]) != request_id
                        for i, e in enumerate(events, 1)
                    )
                ):
                    raise SourceConflict(
                        "Complete typed target membership is required for containment."
                    )
        last_sequence, event_digest = self.execution.stream_digest(stream_id)
        if (
            count != last_sequence
            or last_sequence != stream["LastSequence"]
            or stream_wire(self.execution.read_stream(stream_id)) != stream
        ):
            raise SourceConflict("Provider request ledger changed during containment review.")
        return dict(last_sequence=last_sequence, event_digest=event_digest.hex())

    def inspect(self, job_id):
        job_id = identity(job_id)
        config, pool_id, registration_hash = self._scope(job_id)
        snapshot = self.dal.snapshot(job_id, account=config["account"], pool_id=pool_id)
        job = snapshot["job"]
        if snapshot["receipt"] is not None:
            return self.verify(snapshot)
        if (
            job["State"] not in {"running", "uncertain"}
            or job["OwnerID"] is None
            or job["Fence"] <= 0
        ):
            raise SourceConflict("Exact unfinished provider owner required.")
        resources = snapshot["resources"]
        keys = [r["ResourceKey"] for r in resources]
        targets = sorted(
            k.removeprefix("destination:") for k in keys if k.startswith("destination:")
        )
        if (
            not targets
            or keys != ["account:" + config["account"], *("destination:" + f for f in targets)]
            or keys != snapshot["membership"]
            or digest(targets).hex() != job["DestinationSetHash"]
            or any(
                (
                    r["ActiveJobID"],
                    r["OwnerID"],
                    r["Fence"],
                    r["ActivePreparationID"],
                    r["ActiveOutputOperationID"],
                )
                != (job_id, job["OwnerID"], job["Fence"], None, None)
                for r in resources
            )
        ):
            raise SourceConflict("Complete exact held resource membership required.")
        if pool_id is not None:
            self.registration.sheets(snapshot)
            pool = snapshot["pool"]
            if (pool["PoolState"], pool["OwnerID"], pool["Epoch"], pool["ActiveKVK"]) != (
                "active",
                None,
                job["PoolEpoch"],
                job["KVK_NO"],
            ):
                raise SourceConflict("Current pool ownership or season changed.")
        seals = {}
        principals = {s["SessionID"]: s["AuthorityPrincipal"] for s in snapshot["sessions"]}
        if not 1 <= len(snapshot["streams"]) <= 4096:
            raise SourceConflict("Complete bounded original provider stream set required.")
        for stream in snapshot["streams"]:
            if (
                stream["JobID"],
                stream["AccountKey"],
                stream["OwnerID"],
                stream["Fence"],
                stream["RegistrationHash"],
                stream["Epoch"],
            ) != (
                job_id,
                config["account"],
                job["OwnerID"],
                job["Fence"],
                registration_hash,
                job["PoolEpoch"],
            ):
                raise SourceConflict("Provider stream differs from the original registered owner.")
            if (
                stream["Purpose"] not in {"mutation", "probe"}
                or stream["State"] not in {"open", "frozen", "closed"}
                or stream["ClaimVersion"] > job["Version"]
                or stream["PreparationID"] is not None
                or stream["OutputOperationID"] is not None
                or principals.get(stream["SessionID"]) != snapshot["principal"]
            ):
                raise SourceConflict("Original stream authority cannot be verified.")
            scope = json.loads(stream["ScopeJson"])
            if sorted(r["key"] for r in scope["resources"]) != keys:
                raise SourceConflict("Complete possible provider target set differs.")
            self.registration.authorize_scope(
                dict(
                    AccountKey=stream["AccountKey"],
                    ScopeJson=scope,
                    OwnerKind="job",
                    Purpose=stream["Purpose"],
                    RegistrationHash=registration_hash,
                    Epoch=stream["Epoch"],
                    NestedToken=stream["NestedToken"],
                )
            )
            seals[stream["StreamID"]] = self._ledger(stream, targets)
        if self.dal.snapshot(job_id, account=config["account"], pool_id=pool_id) != snapshot:
            raise SourceConflict("Containment evidence changed during investigation.")
        return dict(
            snapshot=snapshot,
            seals=seals,
            targets=targets,
            registration_hash=registration_hash,
            token=digest(dict(snapshot=snapshot, seals=seals)).hex(),
            outcome="held",
            business_resolved=False,
        )

    def apply(self, job_id, *, token, actor, reason):
        if not isinstance(actor, str) or not actor.startswith("recovery:"):
            raise ValueError("Durable recovery action identity required.")
        containment_id = identity(actor.removeprefix("recovery:"))
        if actor != "recovery:" + containment_id:
            raise ValueError("Canonical durable recovery action identity required.")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 512:
            raise ValueError("Bounded containment reason required.")
        if not isinstance(token, str) or re.fullmatch(r"[0-9a-f]{64}", token) is None:
            raise ValueError("Exact reviewed containment evidence required.")
        report = self.inspect(job_id)
        if report["outcome"] == "targets_isolated":
            if report["token"] != token or report["actor"] != actor or report["reason"] != reason:
                raise SourceConflict("Another containment decision owns this receipt.")
            return report
        if report["token"] != token:
            raise SourceConflict("Containment evidence changed; review the current decision.")
        audit = dict(
            kind="export_target_containment/1",
            containment_id=containment_id,
            actor=actor,
            reason=reason,
            before=report["snapshot"],
            seals=report["seals"],
            targets=report["targets"],
            token=token,
            registration_hash=report["registration_hash"],
            provider_success=False,
            child_termination_verified=False,
            business_resolved=False,
        )
        raw = encode(audit)
        stored = self.store.put(raw)
        receipt = dict(reference=identity(stored.key), sha256=stored.sha256)
        if self.store.read_reference(receipt["reference"], bytes.fromhex(receipt["sha256"])) != raw:
            raise SourceConflict(
                "Private containment decision did not verify; no ownership released."
            )
        self.dal.settle(
            report["snapshot"],
            containment_id=containment_id,
            snapshot_hash=token,
            receipt=receipt,
            seals=report["seals"],
            actor=actor,
            reason=reason,
            registration_hash=report["registration_hash"],
        )
        return self.inspect(job_id)

    def verify(self, snapshot):
        receipt = snapshot["receipt"]
        raw = self.store.read_reference(
            identity(receipt["ReceiptReference"]), bytes.fromhex(receipt["ReceiptHash"])
        )
        if hashlib.sha256(raw).hexdigest() != receipt["ReceiptHash"]:
            raise SourceConflict("Original private containment receipt cannot be verified.")
        audit = json.loads(raw)
        before = audit["before"]
        if (
            audit["kind"] != "export_target_containment/1"
            or audit["provider_success"] is not False
            or audit["child_termination_verified"] is not False
            or audit["business_resolved"] is not False
            or digest(dict(snapshot=before, seals=audit["seals"])).hex() != audit["token"]
            or audit["token"] != receipt["SnapshotHash"]
            or audit["containment_id"] != identity(receipt["ContainmentID"])
            or audit["actor"] != receipt["Actor"]
            or audit["reason"] != receipt["Reason"]
            or before["job"]["JobID"] != snapshot["job"]["JobID"]
        ):
            raise SourceConflict("Containment receipt differs from its original decision.")
        if self.dal.retained_targets(audit["containment_id"]) != audit["targets"]:
            raise SourceConflict("Permanent target membership changed after containment.")
        if before["pool"] is not None:
            old_pool, current_pool = before["pool"], snapshot["pool"]
            if current_pool and current_pool.get("RetiredByReplacementID") is not None:
                activation = self.dal.replacement_retirement(
                    current_pool["PoolID"], current_pool["AccountKey"]
                )
                if activation is None:
                    raise SourceConflict("Retired pool has no replacement activation receipt.")
                activation_raw = self.store.read_reference(
                    identity(activation["ReceiptReference"]),
                    bytes.fromhex(activation["ReceiptHash"]),
                )
                activation_audit = json.loads(activation_raw)
                isolated_pool = activation_audit.get("before_pool")
                if (
                    hashlib.sha256(activation_raw).hexdigest() != activation["ReceiptHash"]
                    or activation_audit.get("kind") != "export_replacement_activation/1"
                    or activation_audit.get("activation_id") != identity(activation["ActivationID"])
                    or activation_audit.get("replacement_id")
                    != identity(activation["ReplacementID"])
                    or identity(activation["ContainmentID"]) != audit["containment_id"]
                    or identity(current_pool["RetiredByReplacementID"])
                    != identity(activation["ReplacementID"])
                    or not isinstance(isolated_pool, dict)
                    or current_pool["Version"] != isolated_pool["Version"] + 1
                    or {
                        k: v
                        for k, v in current_pool.items()
                        if k not in {"RetiredByReplacementID", "Version", "UpdatedUTC"}
                    }
                    != {
                        k: v
                        for k, v in isolated_pool.items()
                        if k not in {"RetiredByReplacementID", "Version", "UpdatedUTC"}
                    }
                ):
                    raise SourceConflict("Pool replacement differs from its sealed retirement.")
                current_pool = isolated_pool
            # Older immutable receipts precede the additive nullable column.
            # Only a null value is equivalent to an absent historical key.
            old_pool = dict(old_pool)
            old_pool.setdefault("RetiredByReplacementID", None)
            changed_pool = {"PoolState", "BlockedReason", "Version", "UpdatedUTC"}
            if (
                current_pool is None
                or current_pool["PoolState"] != "blocked"
                or current_pool["Version"] != old_pool["Version"] + 1
                or current_pool["BlockedReason"]
                != "Targets permanently isolated; verified replacements required"
                or {k: v for k, v in current_pool.items() if k not in changed_pool}
                != {k: v for k, v in old_pool.items() if k not in changed_pool}
                or snapshot["slots"] != before["slots"]
            ):
                raise SourceConflict("Retired pool and original slot history are not verified.")
        old_job, current_job = before["job"], snapshot["job"]
        changed_job = {"State", "Version", "UpdatedUTC"}
        if (
            current_job["State"] != "uncertain"
            or current_job["Version"] != old_job["Version"] + 1
            or {k: v for k, v in current_job.items() if k not in changed_job}
            != {k: v for k, v in old_job.items() if k not in changed_job}
            or any(r["ActiveJobID"] == current_job["JobID"] for r in snapshot["resources"])
        ):
            raise SourceConflict("Exact isolated job release is not verified.")
        old_streams = {s["StreamID"]: s for s in before["streams"]}
        current_streams = [s for s in snapshot["streams"] if s["JobID"] == current_job["JobID"]]
        if {s["StreamID"] for s in current_streams} != set(old_streams):
            raise SourceConflict("Original isolated stream membership changed.")
        changed_stream = {
            "State",
            "Version",
            "ActiveAccountKey",
            "ClosureHash",
            "ClosureReference",
            "EventDigest",
            "ClosedUTC",
        }
        for stream in current_streams:
            original = old_streams[stream["StreamID"]]
            if (
                stream["State"] != "target_contained"
                or stream["ActiveAccountKey"] is not None
                or stream["Version"] != original["Version"] + 1
                or stream["ClosureHash"] != receipt["ReceiptHash"]
                or stream["ClosureReference"] != identity(receipt["ReceiptReference"])
                or {k: v for k, v in stream.items() if k not in changed_stream}
                != {k: v for k, v in original.items() if k not in changed_stream}
                or self._ledger(stream, audit["targets"]) != audit["seals"][stream["StreamID"]]
                or stream["EventDigest"] != audit["seals"][stream["StreamID"]]["event_digest"]
            ):
                raise SourceConflict("Permanent dispatch isolation is not verified.")
        return dict(
            outcome="targets_isolated",
            business_resolved=False,
            token=audit["token"],
            targets=audit["targets"],
            actor=audit["actor"],
            reason=audit["reason"],
        )
