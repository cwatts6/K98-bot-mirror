"""Whole-pool retirement for interrupted rollover; no claim about old write outcomes."""

import hashlib
import json
import re

from core.export_execution_host import HostBoundaryError
from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_execution_protocol import encode
from services.export_runtime_composition import output_operation_scope
from services.export_target_containment import ExportTargetContainment


class RolloverContainment(ExportTargetContainment):
    def __init__(self, *, pools, **kwargs):
        super().__init__(**kwargs)
        self.pools = pools

    def _scope(self, operation_id):
        snapshot = self.discovery.rollover(operation_id, self.pools)
        self.registration.sheets(snapshot["pool"])
        return snapshot["operation"]["AccountKey"], snapshot["operation"]["PoolID"]

    def inspect(self, operation_id):
        operation_id = identity(operation_id)
        account, pool_id = self._scope(operation_id)
        snapshot = self.dal.snapshot(operation_id, account=account, pool_id=pool_id)
        if snapshot["receipt"] is not None:
            return self.verify(snapshot)
        op = snapshot["operation"]
        scope = output_operation_scope(snapshot, purpose="probe")
        if op["State"] not in {"running", "uncertain"} or op["OwnerID"] is None:
            raise SourceConflict("An exact unfinished rollover owner is required.")
        targets = sorted(k[12:] for k in snapshot["membership"] if k.startswith("destination:"))
        keys = [r["key"] for r in scope["ScopeJson"]["resources"]]
        if keys != snapshot["membership"] or len(snapshot["streams"]) > 4096:
            raise SourceConflict("Complete bounded rollover membership required.")
        principals = {s["SessionID"]: s["AuthorityPrincipal"] for s in snapshot["sessions"]}
        seals = {}
        for stream in snapshot["streams"]:
            owned = (stream["OwnerID"], stream["Fence"]) == (op["OwnerID"], op["Fence"])
            drained = (
                stream["OwnerID"],
                stream["Fence"],
                stream["ClaimVersion"],
                stream["Purpose"],
                stream["State"],
            ) == (None, 0, 1, "probe", "closed")
            if (
                stream["OutputOperationID"] != operation_id
                or stream["JobID"] is not None
                or stream["PreparationID"] is not None
                or stream["NestedToken"] is not None
                or stream["AccountKey"] != account
                or stream["RegistrationHash"] != scope["RegistrationHash"]
                or stream["Epoch"] != op["OldEpoch"]
                or stream["ClaimVersion"] > op["Version"]
                or stream["State"] not in {"open", "frozen", "closed"}
                or stream["Purpose"] not in {"mutation", "probe"}
                or not (owned or drained)
                or principals.get(stream["SessionID"]) != snapshot["principal"]
                or sorted(r["key"] for r in json.loads(stream["ScopeJson"])["resources"]) != keys
            ):
                raise SourceConflict("Complete original rollover stream authority must verify.")
            seals[stream["StreamID"]] = self._ledger(stream, targets)
        if self.dal.snapshot(operation_id, account=account, pool_id=pool_id) != snapshot:
            raise SourceConflict("Rollover containment evidence changed.")
        return dict(
            snapshot=snapshot,
            seals=seals,
            targets=targets,
            registration_hash=scope["RegistrationHash"],
            token=digest(dict(snapshot=snapshot, seals=seals)).hex(),
            outcome="held",
            business_resolved=False,
        )

    def apply(self, operation_id, *, token, actor, reason):
        action_id = identity(actor.removeprefix("recovery:"))
        if (
            actor != "recovery:" + action_id
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
            or not isinstance(token, str)
            or re.fullmatch(r"[0-9a-f]{64}", token) is None
        ):
            raise SourceConflict("Exact confirmed rollover isolation decision required.")
        report = self.inspect(operation_id)
        if report["outcome"] == "targets_isolated":
            if (report["token"], report["actor"], report["reason"]) != (token, actor, reason):
                raise SourceConflict("Another isolation decision owns this rollover.")
            return report
        if report["token"] != token:
            raise SourceConflict("Rollover evidence changed; review again.")
        audit = dict(
            kind="rollover_target_containment/1",
            containment_id=action_id,
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
            raise SourceConflict("Private rollover isolation decision did not verify.")
        self.dal.settle(
            report["snapshot"],
            containment_id=action_id,
            snapshot_hash=token,
            receipt=receipt,
            seals=report["seals"],
            actor=actor,
            reason=reason,
            registration_hash=report["registration_hash"],
        )
        return self.inspect(operation_id)

    def verify(self, snapshot):
        receipt = snapshot["receipt"]
        try:
            raw = self.store.read_reference(
                identity(receipt["ReceiptReference"]), bytes.fromhex(receipt["ReceiptHash"])
            )
        except (HostBoundaryError, SourceConflict, OSError, ValueError, KeyError):
            from services.export_containment_attestation import verify

            return verify(self, snapshot)
        audit = json.loads(raw)
        before, op = audit["before"], snapshot["operation"]
        if (
            hashlib.sha256(raw).hexdigest() != receipt["ReceiptHash"]
            or audit["kind"] != "rollover_target_containment/1"
            or any(
                audit[k] is not False
                for k in ("provider_success", "child_termination_verified", "business_resolved")
            )
            or digest(dict(snapshot=before, seals=audit["seals"])).hex() != audit["token"]
            or audit["token"] != receipt["SnapshotHash"]
            or audit["containment_id"] != identity(receipt["ContainmentID"])
            or (audit["actor"], audit["reason"]) != (receipt["Actor"], receipt["Reason"])
            or before["operation"]["OperationID"] != op["OperationID"]
            or self.dal.retained_targets(audit["containment_id"]) != audit["targets"]
        ):
            raise SourceConflict("Rollover isolation receipt does not verify.")
        changed = {"State", "Phase", "Version", "UpdatedUTC"}
        original = before["operation"]
        if (
            op["State"] != "uncertain"
            or op["Phase"] != "uncertain"
            or op["Version"] != original["Version"] + 1
            or {k: v for k, v in op.items() if k not in changed}
            != {k: v for k, v in original.items() if k not in changed}
            or any(r["ActiveOutputOperationID"] == op["OperationID"] for r in snapshot["resources"])
        ):
            raise SourceConflict("Exact rollover release is not verified.")
        pool = snapshot["pool"]["pool"]
        if pool.get("RetiredByReplacementID") is not None:
            from services.export_pool_retirement_evidence import isolated_pool

            pool = isolated_pool(
                self.dal,
                self.store,
                pool,
                before["pool"]["pool"],
                audit["containment_id"],
                rollover=True,
            )
        original_pool = dict(before["pool"]["pool"])
        original_pool.setdefault("RetiredByReplacementID", None)
        pool_fields = {"PoolState", "OwnerID", "BlockedReason", "Version", "UpdatedUTC"}
        if (
            pool["PoolState"] != "blocked"
            or pool["OwnerID"] is not None
            or pool["BlockedReason"]
            != "Targets permanently isolated; verified replacements required"
            or pool["Version"] != original_pool["Version"] + 1
            or {k: v for k, v in pool.items() if k not in pool_fields}
            != {k: v for k, v in original_pool.items() if k not in pool_fields}
            or snapshot["pool"]["slots"] != before["pool"]["slots"]
        ):
            raise SourceConflict("Original rollover pool history does not verify.")
        old_streams = {s["StreamID"]: s for s in before["streams"]}
        streams = [s for s in snapshot["streams"] if s["OutputOperationID"] == op["OperationID"]]
        if {s["StreamID"] for s in streams} != set(old_streams):
            raise SourceConflict("Isolated rollover stream membership changed.")
        changed_stream = {
            "State",
            "Version",
            "ActiveAccountKey",
            "ClosureHash",
            "ClosureReference",
            "EventDigest",
            "ClosedUTC",
        }
        for stream in streams:
            old = old_streams[stream["StreamID"]]
            if (
                stream["State"] != "target_contained"
                or stream["ActiveAccountKey"] is not None
                or stream["Version"] != old["Version"] + 1
                or stream["ClosureHash"] != receipt["ReceiptHash"]
                or stream["ClosureReference"] != identity(receipt["ReceiptReference"])
                or {k: v for k, v in stream.items() if k not in changed_stream}
                != {k: v for k, v in old.items() if k not in changed_stream}
                or self._ledger(stream, audit["targets"]) != audit["seals"][stream["StreamID"]]
                or stream["EventDigest"] != audit["seals"][stream["StreamID"]]["event_digest"]
            ):
                raise SourceConflict("Permanent rollover dispatch isolation does not verify.")
        return dict(
            outcome="targets_isolated",
            business_resolved=False,
            input_commitment={
                k: original[k]
                for k in (
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
            },
            token=audit["token"],
            targets=audit["targets"],
            actor=audit["actor"],
            reason=audit["reason"],
        )
