"""Explicit no-dispatch configuration recovery. Never a provider health proof."""

from dataclasses import asdict, dataclass
import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_reconciliation_service import ClosedStreamVerifier


@dataclass(frozen=True)
class RecoveryTarget:
    server: str
    database: str
    preparation_id: str
    account: str
    owner: str
    fence: int
    version: int
    resources: tuple[tuple[str, int], ...]
    stream_ids: tuple[str, ...]


def validate_snapshot(
    snapshot, target, *, registration_hash, storage_owner, allow_reads=False, containment=False
):
    """Require the complete exact abandoned read; no writes or inferred success."""
    p = snapshot["preparation"]
    if not p or p["State"] not in {"preflight", "uncertain"}:
        raise SourceConflict("Exact unfinished configuration read required.")
    offset = 1 if p["State"] == "uncertain" else 0
    if (
        snapshot["server"].casefold() != target.server.casefold()
        or snapshot["database"] != target.database
        or not p
        or (p["PreparationID"], p["AccountKey"], p["OwnerID"], p["Fence"], p["Version"])
        != (target.preparation_id, target.account, target.owner, target.fence, target.version)
        or (p["ConsumerKind"], p["KVK_NO"], p["StorageOwner"]) != ("config", None, storage_owner)
        or any(
            p[k] is not None
            for k in ("JobID", "GenerationJson", "SpoolKey", "SpoolBytes", "SpoolHash")
        )
        or p["RequestHash"] != digest(json.loads(p["RequestJson"])).hex()
    ):
        raise SourceConflict("Exact uncertain configuration read required.")
    keys = [key for key, _ in target.resources]
    if (
        not keys
        or keys != sorted(set(keys))
        or "account:" + target.account not in keys
        or any(not key.startswith(("account:", "destination:")) for key in keys)
        or snapshot["membership"] != keys
        or [r["ResourceKey"] for r in snapshot["resources"]] != keys
    ):
        raise SourceConflict("Complete exact configuration resource membership required.")
    for r, (key, version) in zip(snapshot["resources"], target.resources, strict=True):
        if (
            (r["ActivePreparationID"], r["OwnerID"], r["Fence"], r["Version"])
            != (target.preparation_id, target.owner, target.fence, version)
            or r["ActiveJobID"] is not None
            or r["ActiveOutputOperationID"] is not None
            or r["BlockedReason"]
            != ("Preparation requires authoritative reconciliation" if offset else None)
        ):
            raise SourceConflict("Resource claim changed; retain all claims.")
    streams = snapshot["streams"]
    if tuple(s["StreamID"] for s in streams) != target.stream_ids:
        raise SourceConflict("Complete stream membership changed or a conflicting stream exists.")
    if not streams:
        from services.export_execution_protocol import uuid_text

        request = json.loads(p["RequestJson"])
        if (
            not containment
            or set(request) != {"read_configuration"}
            or snapshot["request_count"] != 0
            or snapshot["event_count"] != 0
        ):
            raise SourceConflict(
                "An unstarted read needs its exact request and empty execution ledger."
            )
        uuid_text(request["read_configuration"])
    for s in streams:
        scope = json.loads(s["ScopeJson"])
        if set(scope) not in ({"resources"}, {"resources", "host_birth"}):
            raise SourceConflict("Configuration stream scope fields differ.")
        if (
            (s["PreparationID"], s["AccountKey"], s["OwnerID"], s["Fence"], s["ClaimVersion"])
            != (
                target.preparation_id,
                target.account,
                target.owner,
                target.fence,
                target.version - offset,
            )
            or s["Purpose"] != "probe"
            or (
                (s["State"], s["ActiveAccountKey"])
                not in (("open", target.account), ("frozen", target.account), ("closed", None))
                if containment
                else (s["State"], s["ActiveAccountKey"]) != ("closed", None)
            )
            or (not allow_reads and s["LastSequence"] != 0)
            or any(s[k] is not None for k in ("JobID", "OutputOperationID", "NestedToken", "Epoch"))
            or s["RegistrationHash"] != registration_hash
            or (not allow_reads and s["EventDigest"] != hashlib.sha256(b"").hexdigest())
            or scope["resources"]
            != [{"key": k, "version": v - offset} for k, v in target.resources]
        ):
            raise SourceConflict("Stream is not the exact closed, empty configuration read.")
    if not allow_reads and (snapshot["request_count"] != 0 or snapshot["event_count"] != 0):
        raise SourceConflict("Any request/event excludes this no-dispatch recovery.")


class ConfigPreparationRecovery:
    def __init__(
        self, *, dal, execution, store, target, registration_hash, storage_owner, allow_reads=False
    ):
        self.dal, self.execution, self.target = dal, execution, target
        self.verifier = ClosedStreamVerifier(dal=execution, store=store)
        self.registration_hash, self.storage_owner = registration_hash, storage_owner
        self.allow_reads = allow_reads

    def inspect(self):
        snapshot = self.dal.snapshot(self.target)
        validate_snapshot(
            snapshot,
            self.target,
            registration_hash=self.registration_hash,
            storage_owner=self.storage_owner,
            allow_reads=self.allow_reads,
        )
        verified = []
        for stream in snapshot["streams"]:
            evidence = self.verifier.verify(
                stream["StreamID"],
                account=self.target.account,
                registration_hash=bytes.fromhex(self.registration_hash),
                require_observation=False,
                allow_failed_reads=self.allow_reads,
            )
            if evidence.dispatched_mutations or (not self.allow_reads and evidence.request_count):
                raise SourceConflict("No-dispatch recovery cannot settle a provider request.")
            if (evidence.version, evidence.event_digest) != (
                stream["Version"],
                stream["EventDigest"],
            ):
                raise SourceConflict("Closure changed during private verification.")
            verified.append(asdict(evidence))
        if self.dal.snapshot(self.target) != snapshot:
            raise SourceConflict("Recovery snapshot changed during private verification.")
        return dict(
            snapshot=snapshot,
            snapshot_sha256=digest(snapshot).hex(),
            closures=verified,
            outcome="abandoned_read" if self.allow_reads else "abandoned_before_dispatch",
            provider_observation=False,
        )

    def apply(self, *, approved_snapshot_sha256, actor, reason):
        # Reverify private evidence on every apply, never consume an operator
        # authored success flag or a prior inspection as proof.
        report = self.inspect()
        if report["snapshot_sha256"] != approved_snapshot_sha256:
            raise SourceConflict("Approved recovery snapshot changed.")
        audit = dict(
            kind="config_no_dispatch_recovery/1",
            actor=actor,
            reason=reason,
            snapshot_sha256=report["snapshot_sha256"],
            closures=report["closures"],
            outcome=report["outcome"],
            provider_observation=False,
            before=report["snapshot"],
        )
        self.dal.settle(self.target, report["snapshot"], audit)
        return audit


def recover_owned_configuration(authority, registration, stream_id):
    """Authority-only automatic settlement of its own closed read, never adoption.

    Old preparations after a restart still need the explicit exact-target tool.
    Neither IPC caller flags nor elapsed time can prove safety.
    """
    from services.config_preparation_recovery_dal import ConfigPreparationRecoveryDAL
    from services.legacy_export_snapshot_service import configuration_digest

    with authority._lock:
        owned = authority._streams.get(stream_id)
        if owned is None or not owned.closed or owned.purpose != "probe":
            raise SourceConflict("Only this authority's closed configuration probe can recover.")
        stream = authority.dal.read_stream(stream_id)
        configured = registration.value()
        scope = configured["legacy_configuration"]["config"]
        if (
            not stream
            or str(stream["SessionID"]).lower() != authority.session_id
            or str(stream["ChildIdentity"]).lower() != owned.child.identity
            or stream["PreparationID"] is None
            or stream["JobID"] is not None
            or stream["OutputOperationID"] is not None
            or stream["AccountKey"] != configured["account"]
        ):
            raise SourceConflict("Configuration recovery owner/session differs.")
        resources = json.loads(stream["ScopeJson"])["resources"]
        keys = sorted(
            {
                "account:" + configured["account"],
                *("destination:" + d for d in scope["destinations"]),
            }
        )
        if [r["key"] for r in resources] != keys:
            raise SourceConflict("Configuration recovery registration differs.")
        # Database identity is read from this already configured authority DAL;
        # no caller can select another connection or recovery target over IPC.
        recovery_dal = ConfigPreparationRecoveryDAL(authority.dal.connect)
        identity = recovery_dal.identity()
        target = RecoveryTarget(
            identity["server"],
            identity["database"],
            str(stream["PreparationID"]).lower(),
            configured["account"],
            str(stream["OwnerID"]).lower(),
            stream["Fence"],
            stream["ClaimVersion"] + 1,
            tuple((r["key"], r["version"] + 1) for r in resources),
            (stream_id,),
        )
        recovery = ConfigPreparationRecovery(
            dal=recovery_dal,
            execution=authority.dal,
            store=authority.store,
            target=target,
            registration_hash=configuration_digest(scope),
            storage_owner=configured["storage_owner"],
            allow_reads=True,
        )
        report = recovery.inspect()
        recovery.apply(
            approved_snapshot_sha256=report["snapshot_sha256"],
            actor="system:configuration_recovery",
            reason="Verified terminated read-only probe",
        )
        return dict(
            stream_id=stream_id,
            preparation_id=target.preparation_id,
            state="unavailable",
            provider_observation=False,
        )
