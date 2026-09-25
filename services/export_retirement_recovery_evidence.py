"""Interrupted-retirement journal and readback evidence, with no recovery authority.

An empty workbook cannot prove absence of delayed effects. Historical SQL proofs
authenticate the original retirement decision only; every former request stream
and deployment/writer boundary still requires independent verification.
"""

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.dal.source_output_pool_dal import pending_retirements
from kvk.services.new_source_export_service import GoogleSheetsTransport
from services.export_coordination_dal import Claim, bounded_json
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import ProviderRequest, encode, proof_membership, uuid_text
from services.export_reconciliation_service import (
    CatalogueVerifier,
    ClosedProbeReplay,
    PoolOriginVerifier,
    observe_publication,
)
from services.export_runtime_composition import new_source_job_scope


def recovery_journal(snapshot):
    """Validate the exact retained owner and complete pending disposition projection."""
    job, context = snapshot["job"], snapshot["pool"]
    pool, events = context["pool"], snapshot["retirement_events"]
    uuid_text(job["JobID"])
    uuid_text(job["OwnerID"])
    claim = Claim(
        job["JobID"],
        job["AccountKey"],
        job["OwnerID"],
        job["Fence"],
        job["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in snapshot["resources"]),
        job["IntentID"],
    )
    scope = new_source_job_scope(snapshot, claim, purpose="probe")
    pending = pending_retirements(snapshot)
    files = {m["file_id"] for token in pending for m in token["slots"]}
    retired = {s["FileID"] for s in context["slots"] if s["State"] == "retired"}
    if (
        job["State"] not in {"running", "uncertain"}
        or not pending
        or len(pending) != len(files)
        or files != retired
        or files.intersection(p["FileID"] for p in snapshot["parts"])
        or len(events) != len(files)
        or len({e["DispositionID"] for e in events}) != len(events)
        or len({e["FileID"] for e in events}) != len(events)
        or {e["FileID"] for e in events} != files
        or any(
            (r["ActiveJobID"], r["OwnerID"], r["Fence"])
            != (job["JobID"], job["OwnerID"], job["Fence"])
            for r in snapshot["resources"]
        )
        or any(p["CellCount"] > GoogleSheetsTransport.MAX_CELLS for p in snapshot["parts"])
    ):
        raise SourceConflict(
            "Exact retained recovery owner and complete retired-slot journal required."
        )
    recovery = json.loads(job["ProvenanceJson"]).get("retirement_recovery")
    if recovery is not None and recovery.get("state") != "owned":
        raise SourceConflict("Completed recovery cannot retain unfinished retirement slots.")
    previous_sequence = 0
    for event in events:
        for name in ("DispositionID", "OperationID", "PoolID", "OwnerID"):
            uuid_text(event[name])
        previous = json.loads(event["EvidenceJson"])["previous_assignment"]
        if (
            type(event["SequenceNo"]) is not int
            or event["SequenceNo"] <= previous_sequence
            or event["AccountKey"] != job["AccountKey"]
            or (event["SourceKey"], event["KVK_NO"], event["ChoiceID"])
            != (pool["SourceKey"], pool["ActiveKVK"], pool["ChoiceID"])
            or (event["NewKVK_NO"], event["NewChoiceID"]) != (pool["ActiveKVK"], pool["ChoiceID"])
            or (event["FileKind"], event["SlotFileID"], event["IndexFileID"], event["ResourceKey"])
            != ("slot", event["FileID"], None, "destination:" + event["FileID"])
            or previous["PoolID"] != pool["PoolID"]
            or event["FromSlotVersion"] != previous["Version"]
            or type(event["FromPoolVersion"]) is not int
            or event["FromPoolVersion"] <= 0
            or event["ToPoolVersion"] != event["FromPoolVersion"] + 1
            or event["ToPoolVersion"] > pool["Version"]
        ):
            raise SourceConflict(
                "Retirement journal scope, ordering or version transition differs."
            )
        previous_sequence = event["SequenceNo"]
    return pending, scope["NestedToken"]


class RetirementJournalVerifier:
    """Resolve original S11 ProofIDs; a stored hash/Boolean is not their authority."""

    def __init__(self, *, dal):
        self.dal = dal

    def verify(self, snapshot):
        recovery_journal(snapshot)
        pool = snapshot["pool"]["pool"]
        targets = ExportExecutionDAL.proof_targets(snapshot)
        records = []
        for event in snapshot["retirement_events"]:
            association = json.loads(event["EvidenceJson"])["proof"]
            identifier = association.get("proof_id")
            uuid_text(identifier)
            row = self.dal.read_proof(identifier)
            if (
                row is None
                or str(row["ProofID"]).lower() != identifier
                or row["AccountKey"] != snapshot["job"]["AccountKey"]
                or (row["ProofKind"], row["Outcome"]) != ("retirement", "confirmed")
                or bytes(row["RegistrationHash"]).hex() != pool["RegistrationHash"]
                or len(bytes(row["SnapshotHash"])) != 32
            ):
                raise SourceConflict(
                    "Original trusted retirement ProofID is unavailable or differs."
                )
            uuid_text(str(row["SessionID"]).lower())
            evidence = json.loads(row["EvidenceJson"])
            if (
                not isinstance(evidence, dict)
                or evidence.get("snapshot_hash") != bytes(row["SnapshotHash"]).hex()
                or evidence.get("state") != "confirmed"
                or "proof_id" in evidence
                or bounded_json(dict(evidence, proof_id=identifier)) != bounded_json(association)
                or hashlib.sha256(row["MembershipJson"].encode("utf-16-le")).digest()
                != bytes(row["MembershipHash"])
                or proof_membership(row["MembershipJson"])["targets"] != targets
            ):
                raise SourceConflict("Retirement disposition differs from its immutable SQL proof.")
            bounded_json(association)
            # Historical membership is immutable but is no longer the current
            # catalogue. Never reuse it as the fresh recovery probe's membership.
            records.append(
                dict(
                    disposition_id=event["DispositionID"],
                    proof_id=identifier,
                    session_id=str(row["SessionID"]).lower(),
                    snapshot_hash=bytes(row["SnapshotHash"]).hex(),
                    membership_hash=bytes(row["MembershipHash"]).hex(),
                    evidence_hash=hashlib.sha256(
                        row["EvidenceJson"].encode("utf-16-le")
                    ).hexdigest(),
                )
            )
        return digest(records).hex()


@dataclass(frozen=True)
class ObservedRecoverySlot:
    file_id: str
    disposition_id: str
    version: int
    retirement_evidence_hash: str
    empty_json: str | None


@dataclass(frozen=True)
class ObservedRetirementRecovery:
    snapshot_hash: str
    registration_hash: str
    probe_stream_id: str
    nested_token: str | None
    receipt_json: str
    journal_hash: str
    slots: tuple[ObservedRecoverySlot, ...]


def observe_retirement_recovery(*, snapshot, registration, protected_file_ids, execute, stream_id):
    """Observe current publication and every pending clear, never retry one."""
    uuid_text(stream_id)
    snapshot = deepcopy(snapshot)
    pending, nested_token = recovery_journal(snapshot)
    publication = observe_publication(
        snapshot=snapshot,
        registration=registration,
        protected_file_ids=protected_file_ids,
        execute=execute,
        stream_id=stream_id,
    )

    def read_only(message):
        request = ProviderRequest.parse(message)
        if request.mutation or request.stream_id != stream_id:
            raise SourceConflict("Recovery observation cannot dispatch mutations.")
        return execute(message)

    transport = GoogleSheetsTransport.from_authority(
        registration=registration,
        reuse_guard=lambda *_: False,
        protected_file_ids=protected_file_ids,
        execution=read_only,
        stream_id=stream_id,
        authorize=lambda **_: None,
    )
    observed = []
    for token in pending:
        for member in token["slots"]:
            empty = transport.retirement_readback(member["file_id"])
            observed.append(
                ObservedRecoverySlot(
                    member["file_id"],
                    member["event"],
                    member["version"],
                    member["evidence_hash"],
                    bounded_json(empty) if empty is not None else None,
                )
            )
    return ObservedRetirementRecovery(
        digest(snapshot).hex(),
        publication.registration_hash,
        stream_id,
        nested_token,
        publication.receipt_json,
        digest(snapshot["retirement_events"]).hex(),
        tuple(observed),
    )


def observe_closed_retirement_recovery(*, dal, store, **arguments):
    with ClosedProbeReplay(
        dal=dal,
        store=store,
        stream_id=arguments["stream_id"],
        snapshot=arguments["snapshot"],
        account=arguments["snapshot"]["job"]["AccountKey"],
    ) as replay:
        result = observe_retirement_recovery(execute=replay.execute, **arguments)
    return result


@dataclass(frozen=True)
class SealedRetirementRecoveryObservation:
    recovery: ObservedRetirementRecovery
    retirement_proofs_hash: str
    membership_json: str
    origin_hash: str


class RetirementRecoveryProbe:
    """Fixed authority-owned reconciliation probe; never creates a nested owner."""

    def __init__(self, *, coordinator, streams, dal, store, registration, protected_file_ids):
        if (
            coordinator.execution_evidence is not True
            or coordinator.output_operations is not True
            or streams.coordinator is not coordinator
        ):
            raise SourceConflict("Recovery probes require the same complete S11 coordinator.")
        self.coordinator, self.streams = coordinator, streams
        self.dal, self.store, self.registration = dal, store, registration
        self.protected_file_ids = tuple(protected_file_ids)
        self.origins = PoolOriginVerifier(dal=dal, store=store, registration=registration)

    def run(self, job_id):
        uuid_text(job_id)
        snapshot = deepcopy(self.coordinator.operator_snapshot(job_id))
        if snapshot["job"]["JobID"] != job_id:
            raise SourceConflict("Recovery snapshot belongs to another job.")
        origin_hash = self.origins.verify(snapshot=snapshot, account=snapshot["job"]["AccountKey"])
        journal = RetirementJournalVerifier(dal=self.dal)
        proofs = journal.verify(snapshot)
        catalogue = CatalogueVerifier(dal=self.dal, store=self.store)
        history = catalogue.before_probe(snapshot=snapshot, account=snapshot["job"]["AccountKey"])
        arguments = dict(
            snapshot=snapshot,
            registration=self.registration,
            protected_file_ids=self.protected_file_ids,
        )
        with self.streams.probe(snapshot) as stream:
            arguments["stream_id"] = stream.stream_id
            observed = observe_retirement_recovery(execute=stream.execute, **arguments)
        if (
            self.coordinator.operator_snapshot(job_id) != snapshot
            or journal.verify(snapshot) != proofs
        ):
            raise SourceConflict("Recovery snapshot or historical proof changed during the probe.")
        membership = catalogue.bind_probe(history, snapshot=snapshot, stream_id=stream.stream_id)
        replayed = observe_closed_retirement_recovery(dal=self.dal, store=self.store, **arguments)
        if replayed != observed:
            raise SourceConflict("Sealed recovery differs from the fresh observation.")
        if (
            journal.verify(snapshot) != proofs
            or self.origins.verify(snapshot=snapshot, account=snapshot["job"]["AccountKey"])
            != origin_hash
            or self.coordinator.operator_snapshot(job_id) != snapshot
        ):
            raise SourceConflict(
                "Recovery snapshot or historical proof changed during sealed evaluation."
            )
        return SealedRetirementRecoveryObservation(
            replayed, proofs, encode(membership).decode("utf-8"), origin_hash
        )
