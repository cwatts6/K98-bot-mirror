"""Fixed, read-only ordinary-retirement observations; never release authority.

Managed publication/reference readback and closed S11 history cannot establish
external references, pre-S11 writer coverage or provider finality. A trusted
issuer must establish those independently before authorizing any retirement.
"""

from copy import deepcopy
from dataclasses import dataclass

from kvk.dal.new_source_delivery_dal import Destination
from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.dal.source_output_pool_dal import reusable_attempts
from kvk.services.new_source_export_service import GoogleSheetsTransport
from services.export_coordination_dal import bounded_json, checked_attempt_manifest, validate_parts
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import ProviderRequest, encode, uuid_text
from services.export_reconciliation_service import (
    CatalogueVerifier,
    ClosedProbeReplay,
    PoolOriginVerifier,
    observe_publication,
)


@dataclass(frozen=True)
class ObservedRetirement:
    """Current pointer/content and old unretained assignment, with original receipts."""

    snapshot_hash: str
    registration_hash: str
    probe_stream_id: str
    current_attempt_id: str
    old_attempt_id: str
    old_files: tuple[str, ...]
    current_receipt_json: str
    old_receipt_json: str


def _selection(snapshot, current_attempt_id, old_attempt_id):
    """Select immutable SQL identities before any provider request is admitted."""
    uuid_text(current_attempt_id)
    uuid_text(old_attempt_id)
    pool = snapshot["pool"]
    targets = ExportExecutionDAL.proof_targets(snapshot)
    if (
        current_attempt_id == old_attempt_id
        or pool["PoolState"] != "active"
        or pool["OwnerID"] is not None
        or type(snapshot["registration_count"]) is not int
        or not 1 <= snapshot["registration_count"] <= 8
        or len({j["JobID"] for j in snapshot["jobs"]}) != len(snapshot["jobs"])
        or len({a["AttemptID"] for a in snapshot["attempts"]}) != len(snapshot["attempts"])
        or old_attempt_id not in reusable_attempts(snapshot, current_attempt_id)
    ):
        raise SourceConflict("Exact active pool and explicitly unretained assignment required.")
    selected = []
    for identifier, state, phase in (
        (current_attempt_id, "running", "publication_pending"),
        (old_attempt_id, "confirmed", "published"),
    ):
        attempts = [a for a in snapshot["attempts"] if a["AttemptID"] == identifier]
        if len(attempts) != 1:
            raise SourceConflict("Exact current and old retirement attempts required.")
        attempt = attempts[0]
        jobs = [j for j in snapshot["jobs"] if j["JobID"] == attempt["JobID"]]
        if len(jobs) != 1:
            raise SourceConflict("Retirement attempt job is missing or ambiguous.")
        job = jobs[0]
        uuid_text(job["JobID"])
        uuid_text(job["OwnerID"])
        parts = [p for p in snapshot["parts"] if p["AttemptID"] == identifier]
        document = checked_attempt_manifest(attempt, parts)
        validate_parts(document["parts"], targets)
        if (
            job["State"] != state
            or attempt["Phase"] != phase
            or job["ConsumerKind"] != "new_source"
            or attempt["ConsumerKind"] != "new_source"
            or (job["AccountKey"], job["KVK_NO"], job["PoolEpoch"])
            != (pool["AccountKey"], pool["ActiveKVK"], pool["Epoch"])
            or (attempt["OwnerID"], attempt["Fence"], attempt["Epoch"])
            != (job["OwnerID"], job["Fence"], pool["Epoch"])
            or any(type(v) is not int or v <= 0 for v in (job["Fence"], job["Version"]))
            or job["DestinationSetHash"] != digest(tuple(targets)).hex()
            or parts[0]["FileID"] != pool["IndexFileID"]
            or parts[0]["Role"] != "index"
            or any(p["Role"] != "generation" for p in parts[1:])
            or any(p["CellCount"] > GoogleSheetsTransport.MAX_CELLS for p in parts)
        ):
            raise SourceConflict("Retirement job, attempt or ordered file identity differs.")
        selected.append((job, attempt, parts, document))
    current, old = selected
    if (
        current[0]["JobID"] == old[0]["JobID"]
        or current[3]["generation"]["export_key"] == old[3]["generation"]["export_key"]
        or {p["FileID"] for p in current[2][1:]} & {p["FileID"] for p in old[2][1:]}
        or any(
            s["PoolID"] != pool["PoolID"]
            or s["Epoch"] != pool["Epoch"]
            or s["Fence"] != old[1]["Fence"]
            or type(s["Version"]) is not int
            or s["Version"] <= 0
            for s in snapshot["slots"]
            if s["AttemptID"] == old_attempt_id
        )
    ):
        raise SourceConflict("Retirement cannot alias the current or another epoch assignment.")
    for slot in snapshot["slots"]:
        if slot["AttemptID"] == old_attempt_id:
            uuid_text(slot["AssignmentID"])
    return current, old


def observe_retirement(
    *,
    snapshot,
    current_attempt_id,
    old_attempt_id,
    registration,
    protected_file_ids,
    execute,
    stream_id,
):
    """Evaluate managed references only; mismatches remain unresolved, never absent."""
    uuid_text(stream_id)
    snapshot = deepcopy(snapshot)
    current, old = _selection(snapshot, current_attempt_id, old_attempt_id)
    job, attempt, parts, _document = current
    publication = observe_publication(
        snapshot=dict(job=job, attempts=[attempt], parts=parts, pool=snapshot),
        registration=registration,
        protected_file_ids=protected_file_ids,
        execute=execute,
        stream_id=stream_id,
    )

    def read_only(message):
        request = ProviderRequest.parse(message)
        if request.mutation or request.stream_id != stream_id:
            raise SourceConflict("Retirement observation cannot dispatch mutations.")
        return execute(message)

    transport = GoogleSheetsTransport.from_authority(
        registration=registration,
        reuse_guard=lambda *_: False,
        protected_file_ids=protected_file_ids,
        execution=read_only,
        stream_id=stream_id,
        authorize=lambda **_: None,
    )
    transport.quarantined = frozenset(
        s["FileID"] for s in snapshot["slots"] if s["State"] == "quarantined"
    )
    transport._registered_quarantine = True
    _job, old_attempt, old_parts, old_document = old
    generation = old_document["generation"]
    files = [p["FileID"] for p in old_parts]
    remote = transport.read_retirement_generation(
        Destination("sheets", registration.index_file_id),
        generation["export_key"],
        manifest=generation["tables"],
        files=files,
    )
    receipt = bounded_json(
        dict(
            export_key=generation["export_key"],
            fence=old_attempt["Fence"],
            attempt_id=old_attempt_id,
            files=files,
            audience=registration.audience,
            remote_id=remote,
        )
    )
    if old_attempt["ReceiptJson"] != receipt:
        raise SourceConflict("Old retirement receipt must remain byte-exact.")
    return ObservedRetirement(
        digest(snapshot).hex(),
        snapshot["pool"]["RegistrationHash"],
        stream_id,
        current_attempt_id,
        old_attempt_id,
        tuple(files[1:]),
        publication.receipt_json,
        receipt,
    )


def observe_closed_retirement(*, dal, store, **arguments):
    """Replay every sealed private response through the same fixed evaluator."""
    with ClosedProbeReplay(
        dal=dal,
        store=store,
        stream_id=arguments["stream_id"],
        snapshot=arguments["snapshot"],
        account=arguments["snapshot"]["pool"]["AccountKey"],
    ) as replay:
        result = observe_retirement(execute=replay.execute, **arguments)
    return result


@dataclass(frozen=True)
class SealedRetirementObservation:
    retirement: ObservedRetirement
    membership_json: str
    origin_hash: str


class RetirementProbe:
    """Authority-owned ordinary-retirement observation; no issue, journal or clear."""

    def __init__(
        self, *, pools, coordinator, streams, dal, store, registration, protected_file_ids
    ):
        if (
            pools.execution_evidence is not True
            or coordinator.execution_evidence is not True
            or coordinator.output_operations is not True
            or streams.coordinator is not coordinator
        ):
            raise SourceConflict("Retirement probes require the same complete S11 composition.")
        self.pools, self.coordinator, self.streams = pools, coordinator, streams
        self.dal, self.store, self.registration = dal, store, registration
        self.protected_file_ids = tuple(protected_file_ids)
        self.origins = PoolOriginVerifier(dal=dal, store=store, registration=registration)

    def run(self, snapshot, claim, current_attempt_id, old_attempt_id):
        snapshot = deepcopy(snapshot)
        _selection(snapshot, current_attempt_id, old_attempt_id)

        def unchanged():
            if (
                self.pools.retirement_snapshot(self.coordinator, claim, current_attempt_id)
                != snapshot
            ):
                raise SourceConflict("Owned retirement context changed around the probe.")

        unchanged()
        origin_hash = self.origins.verify(snapshot=snapshot, account=claim.account)
        catalogue = CatalogueVerifier(dal=self.dal, store=self.store)
        history = catalogue.before_probe(snapshot=snapshot, account=claim.account)
        arguments = dict(
            snapshot=snapshot,
            current_attempt_id=current_attempt_id,
            old_attempt_id=old_attempt_id,
            registration=self.registration,
            protected_file_ids=self.protected_file_ids,
        )
        with self.streams.retirement_probe(snapshot, claim, current_attempt_id) as stream:
            arguments["stream_id"] = stream.stream_id
            observed = observe_retirement(execute=stream.execute, **arguments)
        unchanged()
        membership = catalogue.bind_probe(history, snapshot=snapshot, stream_id=stream.stream_id)
        replayed = observe_closed_retirement(dal=self.dal, store=self.store, **arguments)
        if replayed != observed:
            raise SourceConflict("Sealed retirement differs from the fresh observation.")
        if self.origins.verify(snapshot=snapshot, account=claim.account) != origin_hash:
            raise SourceConflict("Retirement origin evidence changed during the probe.")
        unchanged()
        return SealedRetirementObservation(
            replayed, encode(membership).decode("utf-8"), origin_hash
        )
