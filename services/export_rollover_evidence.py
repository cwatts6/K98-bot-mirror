"""Fixed rollover drain/completion observations; no proof issue, adoption or retry.

Current index setup is not emptiness. Its earlier private clear must be evaluated
from the original closed phase stream, as must every other registered clear.
These observations still require independent complete deployment/writer coverage.
"""

from collections import deque
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.services.new_source_export_service import (
    GoogleSheetsTransport,
    SheetsRegistration,
    rollover_marker,
)
from services.export_coordination_dal import bounded_json
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import ProviderRequest, encode, proof_membership, uuid_text
from services.export_reconciliation_service import (
    CatalogueVerifier,
    ClosedProbeReplay,
    ClosedStreamVerifier,
    PoolOriginVerifier,
)
from services.export_runtime_composition import output_operation_scope


def _operation_context(snapshot):
    """Common registered season plan and drained ownership; no outcome is inferred."""
    scope = output_operation_scope(snapshot, purpose="probe")
    op, context = snapshot["operation"], snapshot["pool"]
    pool = context["pool"]
    plan = json.loads(op["PlanJson"])
    previous, choice = plan["snapshot"]["pool"], plan["new_choice"]
    for key in ("OperationID", "PoolID", "OldChoiceID", "NewChoiceID"):
        uuid_text(op[key])
    rollover_marker(op["OldKVK"], op["NewKVK"])
    if (
        type(op["TargetEpoch"]) is not int
        or op["TargetEpoch"] != op["OldEpoch"] + 1
        or type(context["registration_count"]) is not int
        or previous["PoolState"] != "active"
        or previous["OwnerID"] is not None
        or (pool["SourceKey"], pool["ActiveKVK"], pool["ChoiceID"])
        != (op["SourceKey"], op["OldKVK"], op["OldChoiceID"])
        or op["SourceKey"] != "snapshot_report_v1"
        or (
            previous["PoolID"],
            previous["AccountKey"],
            previous["SourceKey"],
            previous["ActiveKVK"],
            previous["ChoiceID"],
            previous["Epoch"],
        )
        != (
            op["PoolID"],
            op["AccountKey"],
            op["SourceKey"],
            op["OldKVK"],
            op["OldChoiceID"],
            op["OldEpoch"],
        )
        or (choice["SourceKey"], choice["KVK_NO"], choice["ChoiceID"])
        != (op["SourceKey"], op["NewKVK"], op["NewChoiceID"])
        or any(r["BlockedReason"] is not None for r in snapshot["resources"])
        or any(
            s["State"] not in {"active", "free"}
            or s["OwnerID"] is not None
            or s["Epoch"] != op["OldEpoch"]
            or s["PoolID"] != op["PoolID"]
            for s in context["slots"]
        )
        or any(j["State"] in {"running", "ready", "waiting", "uncertain"} for j in context["jobs"])
        or any(r["DeliveryState"] in {"claimed", "uncertain"} for r in context["legacy_receipts"])
    ):
        raise SourceConflict("Exact rollover season plan and drained ownership required.")
    return scope


def completion_context(snapshot):
    """Require the original complete phase journal, never infer partial-operation retry."""
    scope = _operation_context(snapshot)
    op, pool = snapshot["operation"], snapshot["pool"]["pool"]
    progress = json.loads(op["ProgressJson"])
    request = progress.get("request", {})
    targets = ExportExecutionDAL.proof_targets(snapshot)
    uuid_text(op["OwnerID"])
    if (
        op["State"] not in {"running", "uncertain"}
        or (op["State"] == "uncertain" and op["Phase"] != "uncertain")
        or (op["State"] == "running" and op["Phase"] != request.get("phase"))
        or request.get("phase") not in {"setup_pending", "setup_verified"}
        or (op["CurrentFileID"], request.get("file_id")) != (pool["IndexFileID"],) * 2
        or set(progress.get("files", {})) != set(targets)
        or (request["phase"] == "setup_verified" and not progress.get("setup"))
        or (request["phase"] == "setup_pending" and progress.get("setup") is not None)
        or bounded_json(request.get("evidence")) != bounded_json(progress.get("setup"))
        or pool["Fence"] != op["Fence"]
    ):
        raise SourceConflict("Complete owned rollover setup journal required.")
    for file_id, evidence in progress["files"].items():
        if (
            set(evidence) != {"file_id", "private", "empty", "manifest_hash", "sheet_id"}
            or evidence["file_id"] != file_id
            or evidence["private"] is not True
            or evidence["empty"] is not True
            or not isinstance(evidence["manifest_hash"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", evidence["manifest_hash"])
            or type(evidence["sheet_id"]) is not int
            or not 0 <= evidence["sheet_id"] < 2**31
        ):
            raise SourceConflict(
                "Every original private clear needs exact manifest/sheet evidence."
            )
    setup_version = (
        op["Version"] - int(op["State"] == "uncertain") - int(request["phase"] == "setup_verified")
    )
    # advance() has exactly private_pending/verified, clear_pending/verified per
    # sorted file, then setup_pending/verified. No resume or extra phase is allowed.
    phases = {setup_version: ("setup", pool["IndexFileID"])}
    for offset, file_id in enumerate(reversed(targets)):
        version = setup_version - 2 - 4 * offset
        phases[version] = ("clear", file_id)
        phases[version - 2] = ("private", file_id)
    if min(phases) <= 0:
        raise SourceConflict("Rollover phase versions cannot precede the original claim.")
    return scope, progress, phases


def _transport(snapshot, registration, protected_file_ids, execute, stream_id):
    pool, slots = snapshot["pool"]["pool"], snapshot["pool"]["slots"]
    if (
        not isinstance(registration, SheetsRegistration)
        or registration.index_file_id != pool["IndexFileID"]
        or set(registration.slot_file_ids) != {s["FileID"] for s in slots}
        or registration.owner_email != pool["ExpectedOwner"]
    ):
        raise SourceConflict("Exact rollover registration and owner required.")

    def read_only(message):
        request = ProviderRequest.parse(message)
        if request.mutation or request.stream_id != stream_id:
            raise SourceConflict("Rollover evaluation may consume only exact read observations.")
        return execute(message)

    return GoogleSheetsTransport.from_authority(
        registration=registration,
        protected_file_ids=protected_file_ids,
        reuse_guard=lambda *_: False,
        execution=read_only,
        stream_id=stream_id,
        authorize=lambda **_: None,
    )


class _PhaseReadback:
    """Only the fixed final reads of a separately fully verified mutation stream.

    Prefix requests were already checked for exact identity, success and closure.
    This cannot replay a mutation or silently skip a read in the selected suffix.
    """

    def __init__(self, stream_id, tail):
        self.stream_id, self.tail = stream_id, deque(tail)

    def execute(self, message):
        requested = ProviderRequest.parse(message)
        if not self.tail or requested.stream_id != self.stream_id or requested.mutation:
            raise SourceConflict("Exact historical phase readback exhausted or invalid.")
        recorded, response = self.tail.popleft()
        if (requested.operation, requested.target, requested.arguments_json) != (
            recorded.operation,
            recorded.target,
            recorded.arguments_json,
        ):
            raise SourceConflict("Historical phase readback method, target or projection differs.")
        return deepcopy(response)

    def finished(self):
        if self.tail:
            raise SourceConflict("Historical phase readback was not completely evaluated.")


class RolloverJournalVerifier:
    """Validate original drain ProofID and every actual operation phase stream."""

    def __init__(self, *, dal, store, registration, protected_file_ids):
        self.dal, self.store = dal, store
        self.registration, self.protected_file_ids = registration, tuple(protected_file_ids)
        self.closed = ClosedStreamVerifier(dal=dal, store=store)

    def _drain(self, snapshot, progress):
        association = progress["proof"]
        proof_id = uuid_text(association.get("proof_id"))
        row = self.dal.read_proof(proof_id)
        if row is None:
            raise SourceConflict("Original protected rollover drain proof is unavailable.")
        body = json.loads(row["EvidenceJson"])
        membership = proof_membership(row["MembershipJson"])
        if (
            str(row["ProofID"]).lower() != proof_id
            or row["AccountKey"] != snapshot["operation"]["AccountKey"]
            or (row["ProofKind"], row["Outcome"]) != ("rollover_drain", "confirmed")
            or bytes(row["RegistrationHash"]).hex() != snapshot["pool"]["pool"]["RegistrationHash"]
            or bytes(row["SnapshotHash"]).hex() != progress["drain_hash"]
            or len(bytes(row["SnapshotHash"])) != 32
            or body.get("snapshot_hash") != progress["drain_hash"]
            or body.get("state") != "confirmed"
            or "proof_id" in body
            or body.get("all_writers_terminated") is not True
            or body.get("remote_outcomes_reconciled") is not True
            or not body.get("evidence_id")
            or bounded_json(dict(body, proof_id=proof_id)) != bounded_json(association)
            or hashlib.sha256(row["MembershipJson"].encode("utf-16-le")).digest()
            != bytes(row["MembershipHash"])
            or membership["targets"] != ExportExecutionDAL.proof_targets(snapshot)
        ):
            raise SourceConflict(
                "Rollover drain journal differs from its original protected proof."
            )
        return dict(
            proof_id=proof_id,
            session_id=uuid_text(str(row["SessionID"]).lower()),
            evidence_hash=hashlib.sha256(row["EvidenceJson"].encode("utf-16-le")).hexdigest(),
            membership_hash=bytes(row["MembershipHash"]).hex(),
            snapshot_hash=progress["drain_hash"],
        )

    def _phase(self, snapshot, stream, phase, file_id, progress):
        identifier = str(stream["StreamID"]).lower()
        verified = self.closed.verify(
            identifier,
            account=snapshot["operation"]["AccountKey"],
            registration_hash=bytes(stream["RegistrationHash"]),
            require_observation=False,
        )
        if (verified.version, verified.event_digest) != (
            stream["Version"],
            bytes(stream["EventDigest"]).hex(),
        ):
            raise SourceConflict("Operation phase catalogue seal changed.")
        tail, mutations = deque(maxlen=3), []
        allowed = {
            "private": {"drive.files.get", "drive.permissions.delete"},
            "clear": {
                "drive.files.get",
                "drive.permissions.delete",
                "sheets.get",
                "sheets.batchUpdate",
                "drive.files.update",
            },
            "setup": {"sheets.values.update", "sheets.get", "sheets.values.get", "drive.files.get"},
        }[phase]
        with closing(self.dal.request_ids(identifier)) as identifiers:
            for request_id in identifiers:
                request, events = self.dal.read_request(request_id)
                typed = ProviderRequest.parse(
                    self.closed._document(request["PayloadReference"], request["PayloadHash"])
                )
                if (
                    typed.target != file_id
                    or typed.operation not in allowed
                    or [e["State"] for e in events] != ["prepared", "dispatch_intent", "succeeded"]
                ):
                    raise SourceConflict("Operation phase has an unexpected request or outcome.")
                response = self.closed._document(
                    events[-1]["EvidenceReference"], events[-1]["EvidenceHash"]
                )["response"]
                tail.append((typed, response))
                if typed.mutation:
                    mutations.append(typed)
                    if len(mutations) > 3:
                        raise SourceConflict("Rollover phase cannot contain extra mutations.")
        if phase == "private":
            if len(mutations) > 1 or verified.successful_reads != 2:
                raise SourceConflict("Private phase requires its two original ACL reads.")
            replay = _PhaseReadback(identifier, list(tail)[-1:])
            transport = _transport(
                snapshot, self.registration, self.protected_file_ids, replay.execute, identifier
            )
            fresh = transport._get(file_id)
            if any(p.get("type") == "anyone" for p in fresh["permissions"]):
                raise SourceConflict("Original private phase did not establish private sharing.")
            replay.finished()
        else:
            size = 2 if phase == "clear" else 3
            replay = _PhaseReadback(identifier, list(tail)[-size:])
            transport = _transport(
                snapshot, self.registration, self.protected_file_ids, replay.execute, identifier
            )
            sheet_id = progress["files"][file_id]["sheet_id"]
            if phase == "clear":
                operations = [m.operation for m in mutations]
                if (
                    operations.count("sheets.batchUpdate") != 1
                    or operations.count("drive.files.update") != 1
                    or operations.count("drive.permissions.delete") > 1
                ):
                    raise SourceConflict("Exact original clear mutations required.")
                batch = next(m for m in mutations if m.operation == "sheets.batchUpdate")
                resets = [
                    r["addSheet"]["properties"]
                    for r in batch.arguments["body"]["requests"]
                    if "addSheet" in r
                ]
                if len(resets) != 1 or resets[0]["sheetId"] != sheet_id:
                    raise SourceConflict("Original replacement sheet differs from clear journal.")
                result = transport.retirement_readback(file_id, expected_sheet_id=sheet_id)
                if bounded_json(result) != bounded_json(progress["files"][file_id]):
                    raise SourceConflict("Original clear readback differs from the phase journal.")
            else:
                op = snapshot["operation"]
                expected = dict(
                    range="Sheet1!A1",
                    valueInputOption="RAW",
                    body=dict(values=[[rollover_marker(op["OldKVK"], op["NewKVK"])]]),
                )
                if (
                    len(mutations) != 1
                    or mutations[0].operation != "sheets.values.update"
                    or mutations[0].arguments != expected
                ):
                    raise SourceConflict("Exact original setup marker mutation required.")
                result = transport.rollover_setup_readback(
                    file_id, op["OldKVK"], op["NewKVK"], expected_sheet_id=sheet_id
                )
                if result is None or (
                    progress.get("setup") is not None
                    and bounded_json(result) != bounded_json(progress["setup"])
                ):
                    raise SourceConflict("Original setup readback differs from the phase journal.")
            replay.finished()
        return dict(
            stream_id=identifier,
            version=verified.version,
            claim_version=stream["ClaimVersion"],
            phase=phase,
            file_id=file_id,
            event_digest=verified.event_digest,
        )

    def verify(self, snapshot):
        scope, progress, phases = completion_context(snapshot)
        drain = self._drain(snapshot, progress)
        op, records, seen = snapshot["operation"], [], set()
        with closing(
            self.dal.read_catalogue(op["AccountKey"], ExportExecutionDAL.proof_targets(snapshot))
        ) as streams:
            for stream in streams:
                if (
                    str(stream["OutputOperationID"]).lower() != op["OperationID"]
                    or stream["Purpose"] != "mutation"
                ):
                    continue
                version = stream["ClaimVersion"]
                if (
                    version not in phases
                    or version in seen
                    or stream["JobID"] is not None
                    or stream["PreparationID"] is not None
                    or stream["NestedToken"] is not None
                    or str(stream["OwnerID"]).lower() != scope["OwnerID"]
                    or (stream["Fence"], stream["Epoch"]) != (scope["Fence"], scope["Epoch"])
                    or bytes(stream["RegistrationHash"]).hex() != scope["RegistrationHash"]
                    or len(bytes(stream["SnapshotHash"])) != 32
                    or bounded_json(json.loads(stream["ScopeJson"]))
                    != bounded_json(scope["ScopeJson"])
                ):
                    raise SourceConflict(
                        "Original operation phase owner, version or membership differs."
                    )
                seen.add(version)
                records.append(self._phase(snapshot, stream, *phases[version], progress))
        if seen != set(phases):
            raise SourceConflict("Complete original operation phase history is unavailable.")
        return digest(
            dict(drain=drain, phases=sorted(records, key=lambda r: r["claim_version"]))
        ).hex()


@dataclass(frozen=True)
class ObservedRolloverCompletion:
    snapshot_hash: str
    registration_hash: str
    probe_stream_id: str
    original_clears_json: str
    current_slots_json: str
    setup_json: str


def observe_rollover_completion(*, snapshot, registration, protected_file_ids, execute, stream_id):
    uuid_text(stream_id)
    snapshot = deepcopy(snapshot)
    scope, progress, _ = completion_context(snapshot)
    transport = _transport(snapshot, registration, protected_file_ids, execute, stream_id)
    op, slots = snapshot["operation"], {}
    for file_id in sorted(registration.slot_file_ids):
        empty = transport.retirement_readback(
            file_id, expected_sheet_id=progress["files"][file_id]["sheet_id"]
        )
        if empty is None:
            raise SourceConflict(
                "Rollover slot is not the exact current private empty representation."
            )
        slots[file_id] = empty
    setup = transport.rollover_setup_readback(
        registration.index_file_id,
        op["OldKVK"],
        op["NewKVK"],
        expected_sheet_id=progress["files"][registration.index_file_id]["sheet_id"],
    )
    if setup is None:
        raise SourceConflict("Rollover final index setup is unresolved.")
    return ObservedRolloverCompletion(
        digest(snapshot).hex(),
        scope["RegistrationHash"],
        stream_id,
        bounded_json(progress["files"]),
        bounded_json(slots),
        bounded_json(setup),
    )


@dataclass(frozen=True)
class SealedRolloverCompletionObservation:
    completion: ObservedRolloverCompletion
    original_journal_hash: str
    membership_json: str
    origin_hash: str


class RolloverCompletionProbe:
    def __init__(self, *, pools, streams, dal, store, registration, protected_file_ids):
        if pools.execution_evidence is not True or streams.pools is not pools:
            raise SourceConflict(
                "Completion probe requires the same complete S11 pool composition."
            )
        self.pools, self.streams, self.dal, self.store = pools, streams, dal, store
        self.registration, self.protected_file_ids = registration, tuple(protected_file_ids)
        self.origins = PoolOriginVerifier(dal=dal, store=store, registration=registration)

    def run(self, operation_id):
        uuid_text(operation_id)
        snapshot = deepcopy(self.pools.operation_snapshot(operation_id))
        if snapshot["operation"]["OperationID"] != operation_id:
            raise SourceConflict("Completion snapshot belongs to another operation.")
        completion_context(snapshot)
        origin_hash = self.origins.verify(
            snapshot=snapshot, account=snapshot["operation"]["AccountKey"]
        )
        journal = RolloverJournalVerifier(
            dal=self.dal,
            store=self.store,
            registration=self.registration,
            protected_file_ids=self.protected_file_ids,
        )
        catalogue = CatalogueVerifier(dal=self.dal, store=self.store)
        account = snapshot["operation"]["AccountKey"]
        history = catalogue.before_probe(snapshot=snapshot, account=account)
        original = journal.verify(snapshot)
        arguments = dict(
            snapshot=snapshot,
            registration=self.registration,
            protected_file_ids=self.protected_file_ids,
        )
        with self.streams.completion_probe(snapshot) as stream:
            arguments["stream_id"] = stream.stream_id
            observed = observe_rollover_completion(execute=stream.execute, **arguments)
        if (
            self.pools.operation_snapshot(operation_id) != snapshot
            or journal.verify(snapshot) != original
        ):
            raise SourceConflict(
                "Completion snapshot or original phase journal changed during probe."
            )
        membership = catalogue.bind_probe(history, snapshot=snapshot, stream_id=stream.stream_id)
        with ClosedProbeReplay(
            dal=self.dal,
            store=self.store,
            stream_id=stream.stream_id,
            snapshot=snapshot,
            account=account,
        ) as replay:
            replayed = observe_rollover_completion(execute=replay.execute, **arguments)
        if (
            replayed != observed
            or journal.verify(snapshot) != original
            or self.origins.verify(snapshot=snapshot, account=account) != origin_hash
            or self.pools.operation_snapshot(operation_id) != snapshot
        ):
            raise SourceConflict("Completion snapshot/journal differs from sealed evaluation.")
        return SealedRolloverCompletionObservation(
            replayed, original, encode(membership).decode("utf-8"), origin_hash
        )


def drain_context(snapshot):
    scope = _operation_context(snapshot)
    op = snapshot["operation"]
    if (
        scope["OwnerID"] is not None
        or (op["State"], op["Phase"], op["Version"], op["CurrentFileID"])
        != ("closing", "draining", 1, None)
        or json.loads(op["ProgressJson"]) != {}
    ):
        raise SourceConflict("Only the original unowned closing operation may be drained.")
    return scope


@dataclass(frozen=True)
class ObservedRolloverDrain:
    operation_snapshot_hash: str
    snapshot_hash: str
    registration_hash: str
    probe_stream_id: str
    files_json: str


def observe_rollover_drain(*, snapshot, registration, protected_file_ids, execute, stream_id):
    """Observe registered ownership/sharing without clearing or asserting finality.

    Current content is intentionally not called empty or published. SQL consumes
    the exact pool snapshot; the complete operation snapshot is pinned separately.
    Independent historical writer/SQL-producer coverage is still required.
    """
    uuid_text(stream_id)
    snapshot = deepcopy(snapshot)
    scope = drain_context(snapshot)
    transport = _transport(snapshot, registration, protected_file_ids, execute, stream_id)
    files = {
        file_id: dict(file_id=file_id, metadata_hash=digest(transport._get(file_id)).hex())
        for file_id in ExportExecutionDAL.proof_targets(snapshot)
    }
    return ObservedRolloverDrain(
        digest(snapshot).hex(),
        scope["SnapshotHash"],
        scope["RegistrationHash"],
        stream_id,
        bounded_json(files),
    )


@dataclass(frozen=True)
class SealedRolloverDrainObservation:
    drain: ObservedRolloverDrain
    membership_json: str
    origin_hash: str


class RolloverDrainProbe:
    """Read-only drain observation; never claim, ready, clear or issue a proof."""

    def __init__(self, *, pools, streams, dal, store, registration, protected_file_ids):
        if pools.execution_evidence is not True or streams.pools is not pools:
            raise SourceConflict("Drain probe requires the same complete S11 pool composition.")
        self.pools, self.streams, self.dal, self.store = pools, streams, dal, store
        self.registration, self.protected_file_ids = registration, tuple(protected_file_ids)
        self.origins = PoolOriginVerifier(dal=dal, store=store, registration=registration)

    def run(self, operation_id):
        uuid_text(operation_id)
        snapshot = deepcopy(self.pools.operation_snapshot(operation_id))
        if snapshot["operation"]["OperationID"] != operation_id:
            raise SourceConflict("Drain snapshot belongs to another operation.")
        drain_context(snapshot)
        context, account = snapshot["pool"], snapshot["operation"]["AccountKey"]
        origin_hash = self.origins.verify(snapshot=context, account=account)
        catalogue = CatalogueVerifier(dal=self.dal, store=self.store)
        history = catalogue.before_probe(snapshot=context, account=account)
        arguments = dict(
            snapshot=snapshot,
            registration=self.registration,
            protected_file_ids=self.protected_file_ids,
        )
        with self.streams.closing_probe(snapshot) as stream:
            arguments["stream_id"] = stream.stream_id
            observed = observe_rollover_drain(execute=stream.execute, **arguments)
        if self.pools.operation_snapshot(operation_id) != snapshot:
            raise SourceConflict("Closing operation or drain snapshot changed during probe.")
        membership = catalogue.bind_probe(history, snapshot=context, stream_id=stream.stream_id)
        with ClosedProbeReplay(
            dal=self.dal,
            store=self.store,
            stream_id=stream.stream_id,
            snapshot=context,
            account=account,
        ) as replay:
            replayed = observe_rollover_drain(execute=replay.execute, **arguments)
        if (
            replayed != observed
            or self.origins.verify(snapshot=context, account=account) != origin_hash
            or self.pools.operation_snapshot(operation_id) != snapshot
        ):
            raise SourceConflict("Closing operation or drain differs from sealed evaluation.")
        return SealedRolloverDrainObservation(
            replayed, encode(membership).decode("utf-8"), origin_hash
        )
