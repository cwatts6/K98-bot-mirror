"""Trusted private-journal verification for S11 reconciliation.

Closed request evidence is necessary, not sufficient, for a settlement proof.
This verifier never infers complete historical coverage or current provider truth,
never issues a ProofID, and never releases claims or dispatches a request.
"""

from contextlib import AbstractContextManager, closing
from copy import deepcopy
from dataclasses import dataclass
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import (
    CATALOGUE_SEED,
    ProviderRequest,
    catalogue_step,
    decode,
    encode,
    proof_membership,
    uuid_text,
    validate_response,
)


@dataclass(frozen=True)
class ClosedStreamEvidence:
    stream_id: str
    version: int
    request_count: int
    dispatched_mutations: int
    successful_reads: int
    event_digest: str


class ClosedStreamVerifier:
    def __init__(self, *, dal, store):
        self.dal, self.store = dal, store

    def _document(self, reference, expected_hash):
        return decode(self.store.read_reference(reference, expected_hash))

    def verify(self, stream_id, *, account, registration_hash, require_observation=True):
        uuid_text(stream_id)
        stream = self.dal.read_stream(stream_id)
        if (
            stream is None
            or str(stream["StreamID"]).lower() != stream_id
            or stream["State"] != "closed"
            or stream["ActiveAccountKey"] is not None
            or stream["AccountKey"] != account
            or bytes(stream["RegistrationHash"]) != registration_hash
            or stream["Purpose"] not in {"mutation", "probe", "enrollment"}
        ):
            raise SourceConflict("Exact registered closed stream required.")
        sequence, event_digest = self.dal.stream_digest(stream_id)
        if sequence != stream["LastSequence"] or event_digest != bytes(stream["EventDigest"]):
            raise SourceConflict("Closed request membership differs from its seal.")
        closure = self._document(stream["ClosureReference"], stream["ClosureHash"])
        observed = closure.get("closure", {})
        if (
            closure.get("stream_id") != stream_id
            or closure.get("version") != stream["Version"] - 1
            or closure.get("last_sequence") != sequence
            or closure.get("event_digest") != event_digest.hex()
            or observed.get("child_id") != str(stream["ChildIdentity"]).lower()
            or observed.get("job_empty") is not True
            or observed.get("process_signaled") is not True
        ):
            raise SourceConflict("Private closure evidence differs from the exact child/stream.")
        count = mutations = reads = 0
        with closing(self.dal.request_ids(stream_id)) as identities:
            for identifier in identities:
                request, events = self.dal.read_request(identifier)
                count += 1
                if (
                    request is None
                    or str(request["RequestID"]).lower() != identifier
                    or str(request["StreamID"]).lower() != stream_id
                    or request["Sequence"] != count
                ):
                    raise SourceConflict("Request identity or sequence is incomplete.")
                payload = self._document(request["PayloadReference"], request["PayloadHash"])
                typed = ProviderRequest.parse(payload, enrollment=stream["Purpose"] == "enrollment")
                if (
                    typed.request_id != identifier
                    or typed.stream_id != stream_id
                    or typed.operation != request["Operation"]
                    or typed.target != request["TargetID"]
                    or request["RequestKind"] != ("mutation" if typed.mutation else "read")
                    or (stream["Purpose"] == "probe" and typed.mutation)
                ):
                    raise SourceConflict("Private payload differs from immutable request identity.")
                states = [event["State"] for event in events]
                if states not in (
                    ["prepared", "not_sent"],
                    ["prepared", "dispatch_intent", "succeeded"],
                ):
                    raise SourceConflict("Unknown request outcome cannot become finality proof.")
                event_ids = set()
                for index, event in enumerate(events, 1):
                    event_id = str(event["EventID"]).lower()
                    if (
                        event["EventSequence"] != index
                        or str(event["RequestID"]).lower() != identifier
                        or event_id in event_ids
                    ):
                        raise SourceConflict("Event identity or sequence is incomplete.")
                    event_ids.add(event_id)
                    body = self._document(event["EvidenceReference"], event["EvidenceHash"])
                    if body.get("request_id") != identifier:
                        raise SourceConflict("Private response belongs to another request.")
                    if (
                        event["State"] == "prepared"
                        and body.get("payload_hash") != bytes(request["PayloadHash"]).hex()
                    ):
                        raise SourceConflict("Prepared payload binding differs.")
                    if event["State"] == "succeeded":
                        validate_response(typed, body.get("response"))
                if states[-1] == "succeeded":
                    mutations += int(typed.mutation)
                    reads += int(not typed.mutation)
        if count != sequence:
            raise SourceConflict("Closed request membership was truncated.")
        if require_observation and stream["Purpose"] == "probe" and reads == 0:
            raise SourceConflict("An empty probe establishes no provider observation.")
        return ClosedStreamEvidence(
            stream_id, stream["Version"], count, mutations, reads, event_digest.hex()
        )


class PoolOriginVerifier:
    """Bind a probe's complete pool to authenticated original enrollment evidence.

    Origin is a prerequisite to automatic reconciliation, not evidence that all
    deployed credential users are excluded. This performs only existing DAL and
    private-journal reads; it cannot enroll/adopt a file or issue a ProofID.
    """

    def __init__(self, *, dal, store, registration):
        from kvk.services.new_source_export_service import SheetsRegistration
        from services.export_enrollment_service import ManagedOriginVerifier

        if not isinstance(registration, SheetsRegistration):
            raise SourceConflict("Exact typed pool registration required for origin verification.")
        self.registration = registration
        self.origins = ManagedOriginVerifier(dal=dal, store=store)

    def verify(self, *, snapshot, account):
        from kvk.dal.new_source_import_dal import digest

        targets = ExportExecutionDAL.proof_targets(snapshot)
        context = snapshot["pool"] if "pool" in snapshot["pool"] else snapshot
        pool = context["pool"]
        registration = self.registration
        if (
            pool["AccountKey"] != account
            or pool["IndexFileID"] != registration.index_file_id
            or targets != sorted((registration.index_file_id, *registration.slot_file_ids))
            or pool["ExpectedOwner"] != registration.owner_email
            or digest(json.loads(pool["RegistrationJson"])).hex() != pool["RegistrationHash"]
        ):
            raise SourceConflict("Probe pool differs from its exact registered origin scope.")
        seal = self.origins.verify(
            account=account,
            targets=targets,
            owner_email=registration.owner_email,
            editor_email=registration.service_account_email,
        )
        return digest(seal).hex()


@dataclass(frozen=True)
class VerifiedCatalogue:
    """Closed S11 ledger coverage only; never a pre-S11 or provider-state certificate."""

    account: str
    targets: tuple[str, ...]
    count: int
    sha256: str


class CatalogueVerifier:
    """Read every relevant former stream, then bind one fresh observational probe.

    The DAL closes each catalogue-read SQL connection before private journal I/O.
    A concurrent insert, new nested writer, omitted page or changed closure cannot
    survive the independent SQL issue/settlement catalogue recheck. No timestamp,
    lease, previous receipt or fabricated historical stream establishes coverage.
    """

    def __init__(self, *, dal, store):
        self.dal = dal
        self.closed = ClosedStreamVerifier(dal=dal, store=store)

    def _catalogue(self, *, account, targets, probe_id=None):
        root, count, previous, probe = CATALOGUE_SEED, 0, "", None
        with closing(self.dal.read_catalogue(account, list(targets))) as streams:
            for stream in streams:
                identifier = str(stream["StreamID"]).lower()
                if identifier <= previous:
                    raise SourceConflict("Duplicate or unordered historical stream membership.")
                previous = identifier
                if identifier == probe_id:
                    probe = stream
                    continue
                result = self.closed.verify(
                    identifier,
                    account=account,
                    registration_hash=bytes(stream["RegistrationHash"]),
                    require_observation=False,
                )
                if (result.version, result.event_digest) != (
                    stream["Version"],
                    bytes(stream["EventDigest"]).hex(),
                ):
                    raise SourceConflict("Historical stream differs from the catalogue seal.")
                root = catalogue_step(
                    root, identifier, result.version, bytes.fromhex(result.event_digest)
                )
                count += 1
        return VerifiedCatalogue(account, tuple(targets), count, root.hex()), probe

    def before_probe(self, *, snapshot, account):
        targets = ExportExecutionDAL.proof_targets(snapshot)
        result, _ = self._catalogue(account=account, targets=targets)
        return result

    def bind_probe(self, history, *, snapshot, stream_id):
        """Return bounded inventory membership, never an outcome or ProofID."""
        uuid_text(stream_id)
        if (
            not isinstance(history, VerifiedCatalogue)
            or tuple(ExportExecutionDAL.proof_targets(snapshot)) != history.targets
        ):
            raise SourceConflict("Probe registration differs from the verified historical scope.")
        current, probe = self._catalogue(
            account=history.account, targets=history.targets, probe_id=stream_id
        )
        from kvk.dal.new_source_import_dal import digest

        pool = snapshot["pool"]
        pool = pool.get("pool", pool)
        if (
            current != history
            or probe is None
            or probe["Purpose"] != "probe"
            or bytes(probe["SnapshotHash"]) != digest(snapshot)
            or bytes(probe["RegistrationHash"]).hex() != pool["RegistrationHash"]
        ):
            raise SourceConflict("A writer changed the catalogue around the fresh probe.")
        verified = self.closed.verify(
            stream_id, account=history.account, registration_hash=bytes(probe["RegistrationHash"])
        )
        if (
            verified.version != probe["Version"]
            or verified.event_digest != bytes(probe["EventDigest"]).hex()
        ):
            raise SourceConflict("Fresh probe closure differs from the observed catalogue.")
        membership = dict(
            version=2,
            targets=list(history.targets),
            history=dict(count=history.count, sha256=history.sha256),
            probe=dict(stream_id=stream_id, version=verified.version),
        )
        # Use the same exact parser as SQL-proof consumers before any issue call.
        return proof_membership(encode(membership).decode("utf-8"))


class ClosedProbeReplay(AbstractContextManager):
    """Run existing readback validators against one sealed private probe transcript.

    The bridge never calls SQL transitions, IPC, a provider or a retry path. It
    exposes only the next exact successful read and requires full consumption.
    Evaluating a transcript is not a fresh probe, historical finality or ProofID:
    the issuer must independently bind the catalogue and deployment coverage.
    """

    def __init__(self, *, dal, store, stream_id, snapshot, account):
        self.verifier = ClosedStreamVerifier(dal=dal, store=store)
        self.stream_id = uuid_text(stream_id)
        self.snapshot, self.account = snapshot, account
        self._entered = self._active = False
        self._failed = False
        self._identities = None
        self._sequence = 0

    def __enter__(self):
        from kvk.dal.new_source_import_dal import digest

        if self._entered:
            raise SourceConflict("A probe transcript cannot be reopened or replayed twice.")
        self._entered = True
        pool = self.snapshot["pool"]
        pool = pool.get("pool", pool)
        stream = self.verifier.dal.read_stream(self.stream_id)
        if (
            stream is None
            or stream["Purpose"] != "probe"
            or bytes(stream["SnapshotHash"]) != digest(self.snapshot)
        ):
            raise SourceConflict("Exact snapshot-bound observational stream required.")
        self.verifier.verify(
            self.stream_id,
            account=self.account,
            registration_hash=bytes.fromhex(pool["RegistrationHash"]),
        )
        self._identities = self.verifier.dal.request_ids(self.stream_id)
        self._active = True
        return self

    def execute(self, message):
        try:
            return self._read_next(message)
        except BaseException:
            self._failed = True
            raise

    def _read_next(self, message):
        requested = ProviderRequest.parse(message)
        if (
            not self._active
            or self._failed
            or requested.stream_id != self.stream_id
            or requested.mutation
        ):
            raise SourceConflict("Only exact reads from the opened probe may be evaluated.")
        identifier = next(self._identities, None)
        if identifier is None:
            raise SourceConflict("Probe transcript has no further observed request.")
        self._sequence += 1
        request, events = self.verifier.dal.read_request(identifier)
        if (
            request is None
            or str(request["StreamID"]).lower() != self.stream_id
            or str(request["RequestID"]).lower() != identifier
            or request["Sequence"] != self._sequence
            or [event["State"] for event in events] != ["prepared", "dispatch_intent", "succeeded"]
        ):
            raise SourceConflict("An unobserved read cannot satisfy the probe evaluator.")
        recorded = ProviderRequest.parse(
            self.verifier._document(request["PayloadReference"], request["PayloadHash"])
        )
        if (
            recorded.request_id != identifier
            or recorded.stream_id != self.stream_id
            or (recorded.operation, recorded.target, recorded.arguments_json)
            != (requested.operation, requested.target, requested.arguments_json)
        ):
            raise SourceConflict("Readback requested a different method, file or projection.")
        event = events[-1]
        body = self.verifier._document(event["EvidenceReference"], event["EvidenceHash"])
        if body.get("request_id") != identifier:
            raise SourceConflict("Observed response belongs to another request.")
        response = body.get("response")
        validate_response(recorded, response)
        return response

    def __exit__(self, exc_type, _value, _traceback):
        self._active = False
        try:
            if exc_type is None:
                if self._failed:
                    raise SourceConflict("A rejected read invalidates this probe evaluation.")
                if next(self._identities, None) is not None:
                    raise SourceConflict("Readback left unevaluated probe observations.")
        finally:
            self._identities.close()
        return False


@dataclass(frozen=True)
class ObservedPublication:
    """Exact successful readback only; no termination assertion or settlement authority."""

    snapshot_hash: str
    registration_hash: str
    probe_stream_id: str
    receipt_json: str | None
    state: str = "confirmed"
    observed_manifest_json: str | None = None


def observe_publication(
    *, snapshot, registration, protected_file_ids, execute, stream_id, allow_absent=False
):
    """Fixed read-only evaluator shared by fresh probes and sealed transcript replay.

    Registration/execution are authority-owned dependencies, never IPC-supplied
    callbacks. The future issuer must separately establish complete coverage and
    a fresh catalogue binding before it can authorize a SQL ProofID.
    """
    from kvk.dal.new_source_delivery_dal import Destination
    from kvk.dal.new_source_import_dal import digest
    from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration
    from services.export_coordination_dal import (
        bounded_json,
        checked_attempt_manifest,
        validate_parts,
    )

    uuid_text(stream_id)
    snapshot = deepcopy(snapshot)
    job, context = snapshot["job"], snapshot["pool"]
    pool, slots = context["pool"], context["slots"]
    if (
        not isinstance(registration, SheetsRegistration)
        or registration.index_file_id != pool["IndexFileID"]
        or set(registration.slot_file_ids) != {s["FileID"] for s in slots}
        or registration.owner_email != pool["ExpectedOwner"]
        or not 2 <= len(slots) <= 16
        or job["ConsumerKind"] != "new_source"
        or job["AccountKey"] != pool["AccountKey"]
        or (job["KVK_NO"], job["PoolEpoch"]) != (pool["ActiveKVK"], pool["Epoch"])
        or job["State"] not in {"running", "uncertain", "confirmed"}
        or len(snapshot["attempts"]) != 1
        or digest(json.loads(pool["RegistrationJson"])).hex() != pool["RegistrationHash"]
    ):
        raise SourceConflict("Exact registered new-source publication snapshot required.")
    attempt, parts = snapshot["attempts"][0], snapshot["parts"]
    uuid_text(job["JobID"])
    uuid_text(attempt["AttemptID"])
    document = checked_attempt_manifest(attempt, parts)
    targets = ExportExecutionDAL.proof_targets(snapshot)
    validate_parts(document["parts"], targets)
    files = [p["FileID"] for p in parts]
    if (
        (attempt["JobID"], attempt["OwnerID"], attempt["Fence"], attempt["Epoch"])
        != (job["JobID"], job["OwnerID"], job["Fence"], job["PoolEpoch"])
        or attempt["ConsumerKind"] != "new_source"
        or files[0] != registration.index_file_id
        or parts[0]["Role"] != "index"
        or any(p["Role"] != "generation" for p in parts[1:])
        or any(p["AttemptID"] != attempt["AttemptID"] for p in parts)
        or digest(tuple(targets)).hex() != job["DestinationSetHash"]
    ):
        raise SourceConflict("Exact attempt, owner, fence and file membership required.")

    def read_only(message):
        request = ProviderRequest.parse(message)
        if request.mutation or request.stream_id != stream_id:
            raise SourceConflict("Publication observation cannot dispatch mutations.")
        return execute(message)

    transport = GoogleSheetsTransport.from_authority(
        registration=registration,
        reuse_guard=lambda *_: False,
        protected_file_ids=protected_file_ids,
        execution=read_only,
        stream_id=stream_id,
        authorize=lambda **_: None,
    )
    # Other quarantined generations remain untouched. The attempted generation
    # itself must still be read when reconciling an uncertain assignment.
    transport.quarantined = frozenset(
        s["FileID"] for s in slots if s["State"] == "quarantined" and s["FileID"] not in files
    )
    transport._registered_quarantine = True
    generation = document["generation"]
    state, contents = "confirmed", None
    if allow_absent and job["State"] in {"running", "uncertain"} and attempt["ReceiptJson"] is None:
        # This path additionally requires the closed catalogue to show that this
        # exact job never dispatched a mutation. A missing pointer alone never
        # supplies that fact, and SQL checks all job streams again at issue.
        metadata = {target: transport._get(target) for target in targets}
        if not any(
            f.get("appProperties", {}).get("k98Generation") == generation["export_key"]
            for f in metadata.values()
        ):
            pointer = transport._pointer(metadata[registration.index_file_id])
            previous = []
            confirmed = {
                j["JobID"]
                for j in context.get("jobs", [])
                if j["State"] == "confirmed" and j["JobID"] != job["JobID"]
            }
            for old in context.get("attempts", []):
                if old["JobID"] in confirmed and old["ReceiptJson"] is not None:
                    prior = json.loads(old["ReceiptJson"])
                    previous.append(
                        [[prior["export_key"], str(prior["fence"]), prior["remote_id"]]]
                    )
            if pointer == [] or pointer in previous:
                return ObservedPublication(
                    digest(snapshot).hex(), pool["RegistrationHash"], stream_id, None, "absent"
                )
            raise SourceConflict("Unrecognized pointer cannot establish publication absence.")
    if job["State"] == "confirmed":
        if attempt["ReceiptJson"] is None:
            raise SourceConflict("Confirmed assessment requires its retained receipt bytes.")
        remote, contents = transport.assess_confirmed_contents(
            Destination("sheets", registration.index_file_id),
            generation["export_key"],
            job["Fence"],
            manifest=generation["tables"],
            files=files,
        )
        if contents != generation["tables"]:
            state = "damaged"
    else:
        remote = transport.read_coordinated_publication(
            Destination("sheets", registration.index_file_id),
            generation["export_key"],
            job["Fence"],
            manifest=generation["tables"],
            files=files,
        )
    receipt = bounded_json(
        dict(
            export_key=generation["export_key"],
            fence=job["Fence"],
            attempt_id=attempt["AttemptID"],
            files=files,
            audience=registration.audience,
            remote_id=remote,
        )
    )
    if attempt["ReceiptJson"] is not None and attempt["ReceiptJson"] != receipt:
        raise SourceConflict("Observed publication cannot replace retained receipt bytes.")
    return ObservedPublication(
        digest(snapshot).hex(),
        pool["RegistrationHash"],
        stream_id,
        receipt,
        state,
        bounded_json(contents) if contents is not None else None,
    )


def observe_closed_publication(
    *, dal, store, snapshot, registration, protected_file_ids, stream_id, allow_absent=False
):
    """Evaluate private response evidence; neither perform a new probe nor issue proof."""
    with ClosedProbeReplay(
        dal=dal,
        store=store,
        stream_id=stream_id,
        snapshot=snapshot,
        account=snapshot["job"]["AccountKey"],
    ) as replay:
        result = observe_publication(
            snapshot=snapshot,
            registration=registration,
            protected_file_ids=protected_file_ids,
            execute=replay.execute,
            stream_id=stream_id,
            allow_absent=allow_absent,
        )
    return result


@dataclass(frozen=True)
class SealedPublicationObservation:
    """Closed S11 history and readback; deployment coverage is still independent."""

    publication: ObservedPublication
    membership_json: str
    origin_hash: str


class PublicationProbe:
    """Authority-owned fixed probe sequence, with no settlement or retry operation.

    The protected composition supplies the coordinator, private evidence store,
    registered transport identity and stream factory. None comes from a Bot IPC
    payload. This result cannot be used as a SQL ProofID or as proof that writers
    outside the recorded S11 history have been excluded.
    """

    def __init__(self, *, coordinator, streams, dal, store, registration, protected_file_ids):
        if (
            coordinator.execution_evidence is not True
            or coordinator.output_operations is not True
            or streams.coordinator is not coordinator
        ):
            raise SourceConflict("Publication probes require the same complete S11 coordinator.")
        self.coordinator, self.streams = coordinator, streams
        self.dal, self.store = dal, store
        self.registration = registration
        self.protected_file_ids = tuple(protected_file_ids)
        self.origins = PoolOriginVerifier(dal=dal, store=store, registration=registration)

    def run(self, job_id):
        uuid_text(job_id)
        snapshot = deepcopy(self.coordinator.operator_snapshot(job_id))
        if snapshot["job"]["JobID"] != job_id:
            raise SourceConflict("Publication snapshot belongs to another job.")
        origin_hash = self.origins.verify(snapshot=snapshot, account=snapshot["job"]["AccountKey"])
        catalogue = CatalogueVerifier(dal=self.dal, store=self.store)
        history = catalogue.before_probe(snapshot=snapshot, account=snapshot["job"]["AccountKey"])
        allow_absent = snapshot["job"]["State"] in {"running", "uncertain"}
        if allow_absent:
            with closing(
                self.dal.read_catalogue(
                    snapshot["job"]["AccountKey"], ExportExecutionDAL.proof_targets(snapshot)
                )
            ) as streams:
                for prior in streams:
                    if prior.get("JobID") is not None and str(prior["JobID"]).lower() == job_id:
                        checked = catalogue.closed.verify(
                            str(prior["StreamID"]).lower(),
                            account=snapshot["job"]["AccountKey"],
                            registration_hash=bytes(prior["RegistrationHash"]),
                            require_observation=False,
                        )
                        if checked.dispatched_mutations:
                            allow_absent = False
        # Admission independently rereads the exact domain snapshot. Every exit,
        # including readback failure, closes the owned stream once; a lost close
        # acknowledgment propagates uncertainty and cannot trigger a second try.
        with self.streams.probe(snapshot) as stream:
            observed = observe_publication(
                snapshot=snapshot,
                registration=self.registration,
                protected_file_ids=self.protected_file_ids,
                execute=stream.execute,
                stream_id=stream.stream_id,
                allow_absent=allow_absent,
            )
        if self.coordinator.operator_snapshot(job_id) != snapshot:
            raise SourceConflict("Publication snapshot changed during the probe.")
        membership = catalogue.bind_probe(history, snapshot=snapshot, stream_id=stream.stream_id)
        # The return value is derived again from private, durably sealed response
        # bytes; a successful response retained only in memory is insufficient.
        replayed = observe_closed_publication(
            dal=self.dal,
            store=self.store,
            snapshot=snapshot,
            registration=self.registration,
            protected_file_ids=self.protected_file_ids,
            stream_id=stream.stream_id,
            allow_absent=allow_absent,
        )
        if replayed != observed:
            raise SourceConflict("Sealed publication differs from the fresh observation.")
        # Neither this check nor the prior catalogue read replaces the independent
        # account-locked enumeration at SQL proof issue and consuming settlement.
        if (
            self.origins.verify(snapshot=snapshot, account=snapshot["job"]["AccountKey"])
            != origin_hash
            or self.coordinator.operator_snapshot(job_id) != snapshot
        ):
            raise SourceConflict("Publication snapshot changed during sealed evaluation.")
        return SealedPublicationObservation(
            replayed, encode(membership).decode("utf-8"), origin_hash
        )


class TrustedProofIssuer:
    """Fixed authority-local probes; IPC supplies identities, never observations.

    All dispatched requests must have authenticated successful outcomes before
    these producers can issue. Unknown histories remain unresolved even after a
    child exits or a later empty read. No absence/damage is inferred from a probe
    exception. The SQL API independently binds catalogue and snapshot at issue
    and again at consuming CAS; issuance itself neither releases nor retries.
    """

    def __init__(self, *, authority, boundary, registration, coordinator, pools, client):
        from core.export_execution_host import DeploymentBoundary
        from services.export_runtime_composition import (
            LocalAuthorityClient,
            NewSourceJobStreams,
            OutputOperationStreams,
            RuntimeRegistration,
        )

        if (
            not isinstance(boundary, DeploymentBoundary)
            or not isinstance(registration, RuntimeRegistration)
            or not isinstance(client, LocalAuthorityClient)
            or client.broker.authority is not authority
            or not coordinator.execution_evidence
            or not coordinator.output_operations
            or not pools.execution_evidence
        ):
            raise SourceConflict("Complete private authority proof composition required.")
        self.authority, self.boundary, self.registration = authority, boundary, registration
        self.coordinator, self.pools = coordinator, pools
        self.jobs = NewSourceJobStreams(coordinator=coordinator, client=client)
        self.operations = OutputOperationStreams(pools=pools, client=client)

    def issue(
        self, *, kind, object_id, snapshot_hash, current_attempt_id=None, old_attempt_id=None
    ):
        from dataclasses import asdict
        from uuid import uuid4

        from kvk.dal.new_source_import_dal import digest
        from services.export_coordination_dal import Claim, bounded_json
        from services.export_retirement_evidence import RetirementProbe
        from services.export_retirement_recovery_evidence import RetirementRecoveryProbe
        from services.export_rollover_evidence import RolloverCompletionProbe, RolloverDrainProbe

        uuid_text(object_id)
        if kind not in {
            "publication",
            "retirement",
            "retirement_recovery",
            "rollover_drain",
            "rollover_complete",
        }:
            raise SourceConflict("Unsupported fixed proof producer.")
        if kind == "retirement":
            uuid_text(current_attempt_id)
            uuid_text(old_attempt_id)
        elif current_attempt_id is not None or old_attempt_id is not None:
            raise SourceConflict("Attempt selectors belong only to ordinary retirement.")
        # Reentrant: the fixed probes use the same in-process broker and lock.
        # No Bot request can interleave with the local producer. SQL independently
        # protects against another connection/process at all durable boundaries.
        with self.authority._lock:
            if self.authority._closed:
                raise SourceConflict("Authority admission is closed.")
            boundary_hash = self.boundary.recheck()
            claim = None
            if kind.startswith("rollover_"):
                read = lambda: self.pools.operation_snapshot(object_id)
            elif kind == "retirement":
                job_snapshot = self.coordinator.operator_snapshot(object_id)
                job = job_snapshot["job"]
                claim = Claim(
                    job["JobID"],
                    job["AccountKey"],
                    job["OwnerID"],
                    job["Fence"],
                    job["Version"],
                    tuple((r["ResourceKey"], r["Version"]) for r in job_snapshot["resources"]),
                    job["IntentID"],
                )
                read = lambda: self.pools.retirement_snapshot(
                    self.coordinator, claim, current_attempt_id
                )
            else:
                read = lambda: self.coordinator.operator_snapshot(object_id)
            snapshot = deepcopy(read())
            consumed = snapshot["pool"] if kind == "rollover_drain" else snapshot
            if digest(consumed).hex() != snapshot_hash:
                raise SourceConflict("Requested proof snapshot is stale.")
            context = snapshot if kind == "retirement" else snapshot["pool"]
            registration = self.registration.sheets(context)
            account = context["pool"]["AccountKey"]
            common = dict(
                dal=self.authority.dal,
                store=self.authority.store,
                registration=registration,
                protected_file_ids=self.registration.value()["protected_file_ids"],
            )
            if kind == "publication":
                sealed = PublicationProbe(
                    coordinator=self.coordinator, streams=self.jobs, **common
                ).run(object_id)
                observation = sealed.publication
                evidence = dict(writer_terminated=True)
                if observation.state == "absent":
                    evidence["no_delayed_effect"] = True
                else:
                    evidence["receipt"] = json.loads(observation.receipt_json)
            elif kind == "retirement_recovery":
                sealed = RetirementRecoveryProbe(
                    coordinator=self.coordinator, streams=self.jobs, **common
                ).run(object_id)
                observation = sealed.recovery
                evidence = dict(
                    receipt=json.loads(observation.receipt_json),
                    writer_terminated=True,
                    retirement_outcomes_reconciled=True,
                    no_delayed_retirement_effects=True,
                )
            elif kind == "retirement":
                sealed = RetirementProbe(
                    pools=self.pools, coordinator=self.coordinator, streams=self.jobs, **common
                ).run(snapshot, claim, current_attempt_id, old_attempt_id)
                observation = sealed.retirement
                evidence = dict(
                    current_attempt_id=current_attempt_id,
                    old_attempt_id=old_attempt_id,
                    writer_terminated=True,
                    current_pointer_verified=True,
                    no_live_references=True,
                )
            elif kind == "rollover_drain":
                sealed = RolloverDrainProbe(
                    pools=self.pools, streams=self.operations, **common
                ).run(object_id)
                observation = sealed.drain
                evidence = dict(all_writers_terminated=True, remote_outcomes_reconciled=True)
            else:
                sealed = RolloverCompletionProbe(
                    pools=self.pools, streams=self.operations, **common
                ).run(object_id)
                observation = sealed.completion
                evidence = dict(
                    writer_terminated=True,
                    files=json.loads(observation.original_clears_json),
                    setup=json.loads(observation.setup_json),
                )
            if observation.snapshot_hash != snapshot_hash or read() != snapshot:
                raise SourceConflict("Fixed probe differs from the exact requested snapshot.")
            # SQL rows alone cannot authorize reading another host's DPAPI data.
            # Pin every participating session to the approved single host as well
            # as the private history checks already performed by the producers.
            with closing(
                self.authority.dal.read_catalogue(
                    account, ExportExecutionDAL.proof_targets(consumed)
                )
            ) as streams:
                for stream in streams:
                    session = self.authority.dal.read_session(str(stream["SessionID"]).lower())
                    if (
                        session is None
                        or session["HostIdentity"].lower()
                        != self.boundary._manifest["deployment_boundary"]["host"]["hostname"]
                    ):
                        raise SourceConflict("Foreign or missing authority host history.")
            if self.boundary.recheck() != boundary_hash or read() != snapshot:
                raise SourceConflict("Deployment or snapshot changed during proof production.")
            audit = encode(
                dict(
                    version=1,
                    deployment_hash=boundary_hash,
                    kind=kind,
                    snapshot=snapshot,
                    observation=asdict(sealed),
                )
            )
            receipt = self.authority.store.put(audit)
            if self.authority.store.read(receipt) != audit:
                raise SourceConflict("Private proof evidence readback differs.")
            proof_id = str(uuid4())
            evidence.update(
                state=(
                    observation.state
                    if kind == "publication"
                    else ("completed" if kind == "rollover_complete" else "confirmed")
                ),
                snapshot_hash=snapshot_hash,
                evidence_id=receipt.key,
                evidence_hash=receipt.sha256,
                deployment_hash=boundary_hash,
            )
            self.authority.dal.transition(
                "proof",
                SessionID=self.authority.session_id,
                ProofID=proof_id,
                AccountKey=account,
                SnapshotHash=bytes.fromhex(snapshot_hash),
                RegistrationHash=bytes.fromhex(observation.registration_hash),
                ProofKind=kind,
                Outcome=evidence["state"],
                MembershipJson=sealed.membership_json,
                EvidenceJson=bounded_json(evidence),
            )
            return dict(evidence, proof_id=proof_id)
