"""Typed S10E ownership. Every write is short, fenced and scoped to immutable facts.

There is no SQL connection default, remote I/O, lease takeover or history rewrite.
Use only after the separately installed S10E ownership contract is attested.
"""

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, replace
import json
from uuid import UUID, uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.export_coordination_dal import ExportCoordinationDAL, _cas, _mutex, bounded_json


def _wire(value):
    if isinstance(value, dict):
        guid_columns = {
            "PoolID",
            "OperationID",
            "ActiveOutputOperationID",
            "JobID",
            "ActiveJobID",
            "PreparationID",
            "ActivePreparationID",
            "RepairID",
            "AssignmentID",
            "LastDispositionID",
            "OldChoiceID",
            "NewChoiceID",
        }
        return {
            k: str(v).lower() if k in guid_columns and v is not None else _wire(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_wire(v) for v in value]
    if isinstance(value, UUID):
        return str(value).lower()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


@dataclass(frozen=True)
class OutputClaim:
    operation_id: str
    account: str
    owner: str
    fence: int
    version: int
    resources: tuple[tuple[str, int], ...]
    pool_version: int


def record_export_parts(cursor, job, claim, attempt_id, parts, *, action, damage_proof=None):
    """Append scoped assignment/quarantine events in the owning job transaction.

    Receipt mapping comes exclusively from exact ExportAttemptPart membership.
    No historical SourceDelivery text is guessed or rewritten.
    """
    if action not in {"assign", "quarantine"}:
        raise ValueError("Unsupported export disposition.")
    index = [p["file_id"] for p in parts if p["role"] == "index"]
    if len(index) != 1:
        raise SourceConflict("Exactly one immutable index part is required.")
    cursor.execute(
        "SELECT * FROM KVK.SourceOutputPool WITH (UPDLOCK,HOLDLOCK) WHERE IndexFileID=? AND AccountKey=? AND ActiveKVK=? AND Epoch=?",
        index[0],
        job["AccountKey"],
        job["KVK_NO"],
        job["PoolEpoch"],
    )
    pool = one(cursor)
    if not pool or pool["PoolState"] not in {"active", "closing"}:
        raise SourceConflict("Attempt pool/epoch is unavailable.")
    cursor.execute(
        "SELECT ISNULL(MAX(SequenceNo),0) AS SequenceNo FROM KVK.SourceOutputDisposition WHERE PoolID=?",
        pool["PoolID"],
    )
    sequence = one(cursor)["SequenceNo"]
    for number, part in enumerate(parts, 1):
        file_id = part["file_id"]
        cursor.execute(
            "SELECT * FROM KVK.SourceOutputSlot WITH (UPDLOCK,HOLDLOCK) WHERE PoolID=? AND FileID=?",
            pool["PoolID"],
            file_id,
        )
        slot = one(cursor)
        if part["role"] != "index" and not slot:
            raise SourceConflict("Attempt part is not a scoped registered slot.")
        if (
            slot
            and action == "assign"
            and (
                slot["State"] != "free"
                or slot["OwnerID"] is not None
                or slot["Epoch"] != job["PoolEpoch"]
            )
        ):
            raise SourceConflict(
                "Assignment requires audited private clear; occupied slots cannot be relabeled."
            )
        expected_owner = None if damage_proof is not None else claim.owner_id
        if damage_proof is not None and (
            damage_proof.get("writer_terminated") is not True
            or damage_proof.get("state") != "damaged"
            or not damage_proof.get("evidence_id")
        ):
            raise SourceConflict("Confirmed damage requires independent termination proof.")
        if (
            slot
            and action == "quarantine"
            and (str(slot["AttemptID"]).lower(), slot["PartNo"], slot["OwnerID"], slot["Fence"])
            != (attempt_id, number, expected_owner, claim.fence)
        ):
            raise SourceConflict("Quarantine requires the exact assigned attempt owner.")
        if action == "quarantine":
            cursor.execute(
                "SELECT JobID,AttemptID,PartNo,FileID FROM KVK.SourceOutputDisposition WHERE PoolID=? AND OperationID=? AND FileID=? AND Action='quarantine'",
                pool["PoolID"],
                attempt_id,
                file_id,
            )
            previous = _wire(one(cursor))
            if previous is not None:
                if previous != dict(
                    JobID=claim.job_id, AttemptID=attempt_id, PartNo=number, FileID=file_id
                ) or (slot and slot["State"] != "quarantined"):
                    raise SourceConflict(
                        "Retained quarantine differs from exact attempted membership."
                    )
                # A later repair retains the original quarantine event. Its separate
                # repair plan carries the fresh damage/termination evidence.
                continue
        event = str(uuid4())
        sequence += 1
        sv = slot["Version"] if slot else None
        evidence = dict(
            job_id=claim.job_id,
            attempt_id=attempt_id,
            part_no=number,
            part=part,
            action=action,
            damage_proof=damage_proof,
        )
        cursor.execute(
            "INSERT KVK.SourceOutputDisposition (DispositionID,OperationID,PoolID,SequenceNo,FileID,FileKind,ResourceKey,SlotFileID,IndexFileID,AccountKey,SourceKey,KVK_NO,ChoiceID,NewKVK_NO,NewChoiceID,OldEpoch,NewEpoch,Action,OwnerID,Fence,FromPoolVersion,ToPoolVersion,FromSlotVersion,ToSlotVersion,JobID,ConsumerKind,DestinationSetHash,AttemptID,PartNo,AttemptEpoch,Actor,Reason,OccurredUTC,EvidenceHash,EvidenceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,SYSUTCDATETIME(),?,?)",
            event,
            attempt_id,
            pool["PoolID"],
            sequence,
            file_id,
            "slot" if slot else "index",
            "destination:" + file_id,
            file_id if slot else None,
            None if slot else file_id,
            job["AccountKey"],
            pool["SourceKey"],
            job["KVK_NO"],
            pool["ChoiceID"],
            job["KVK_NO"],
            pool["ChoiceID"],
            job["PoolEpoch"],
            job["PoolEpoch"],
            action,
            claim.owner_id,
            claim.fence,
            pool["Version"],
            pool["Version"] + 1,
            sv,
            sv + 1 if sv is not None else None,
            claim.job_id,
            "new_source",
            bytes(job["DestinationSetHash"]),
            attempt_id,
            number,
            job["PoolEpoch"],
            job["Actor"],
            job["Reason"],
            digest(evidence),
            bounded_json(evidence),
        )
        if slot:
            if action == "assign":
                _cas(
                    cursor,
                    "UPDATE KVK.SourceOutputSlot SET State='staging',OwnerID=?,Fence=?,Version=Version+1,AssignmentID=?,AssignmentAction='assign',AttemptID=?,PartNo=?,AssignmentVersion=Version+1,LastDispositionID=?,LastAction='assign',LastDispositionVersion=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND Version=? AND Epoch=? AND State='free' AND OwnerID IS NULL",
                    claim.owner_id,
                    claim.fence,
                    event,
                    attempt_id,
                    number,
                    event,
                    pool["PoolID"],
                    file_id,
                    sv,
                    job["PoolEpoch"],
                )
            else:
                _cas(
                    cursor,
                    "UPDATE KVK.SourceOutputSlot SET State='quarantined',QuarantineReason='Outcome requires reconciliation',Version=Version+1,LastDispositionID=?,LastAction='quarantine',LastDispositionVersion=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND Version=? AND Epoch=? AND (OwnerID=? OR (OwnerID IS NULL AND CAST(? AS uniqueidentifier) IS NULL)) AND Fence=?",
                    event,
                    pool["PoolID"],
                    file_id,
                    sv,
                    job["PoolEpoch"],
                    expected_owner,
                    expected_owner,
                    claim.fence,
                )
        pool["Version"] = _cas(
            cursor,
            "UPDATE KVK.SourceOutputPool SET Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND Version=? AND Epoch=? AND Fence=?",
            pool["PoolID"],
            pool["Version"],
            job["PoolEpoch"],
            pool["Fence"],
        )["Version"]


def finish_export_parts(cursor, claim, attempt_id):
    cursor.execute(
        "SELECT * FROM KVK.SourceOutputSlot WITH (UPDLOCK,HOLDLOCK) WHERE AttemptID=? ORDER BY FileID",
        attempt_id,
    )
    for slot in rows(cursor):
        _cas(
            cursor,
            "UPDATE KVK.SourceOutputSlot SET State='active',OwnerID=NULL,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE FileID=? AND AttemptID=? AND State='staging' AND OwnerID=? AND Fence=? AND Version=?",
            slot["FileID"],
            attempt_id,
            claim.owner_id,
            claim.fence,
            slot["Version"],
        )


def settle_reconciled_parts(cursor, claim, attempt_id, *, confirmed):
    """Release only a proven-terminated slot owner; quarantine is never made reusable.

    Called in the reconciliation transaction after immutable snapshot/proof checks.
    The original assignment, quarantine event and receipt bytes remain retained.
    """
    cursor.execute(
        "SELECT * FROM KVK.SourceOutputSlot WITH (UPDLOCK,HOLDLOCK) WHERE AttemptID=? ORDER BY FileID",
        attempt_id,
    )
    for slot in rows(cursor):
        if (str(slot["OwnerID"]).lower(), slot["Fence"]) != (claim.owner_id, claim.fence):
            raise SourceConflict("Reconciliation cannot release another assigned slot owner.")
        if slot["State"] == "staging" and confirmed:
            state = "active"
        elif slot["State"] == "quarantined":
            state = "quarantined"
        else:
            raise SourceConflict("Reconciled slot requires an exact terminal disposition.")
        _cas(
            cursor,
            "UPDATE KVK.SourceOutputSlot SET State=?,OwnerID=NULL,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND AttemptID=? AND Epoch=? AND State=? AND OwnerID=? AND Fence=? AND Version=?",
            state,
            slot["PoolID"],
            slot["FileID"],
            attempt_id,
            slot["Epoch"],
            slot["State"],
            claim.owner_id,
            claim.fence,
            slot["Version"],
        )


def reusable_attempts(snapshot, current_attempt_id):
    """Only explicitly unretained, exact confirmed assignments are candidates.

    This is eligibility, not release authority. Independent termination/reference
    evidence and private clear/readback are still required under the new job owner.
    Older manifests without an explicit retention decision stay protected.
    """
    confirmed = {j["JobID"] for j in snapshot["jobs"] if j["State"] == "confirmed"}
    result = []
    for attempt in snapshot["attempts"]:
        if attempt["AttemptID"] == current_attempt_id or attempt["JobID"] not in confirmed:
            continue
        document = json.loads(attempt["ManifestJson"])
        if attempt["Phase"] != "published" or document["generation"].get("retain") is not False:
            continue
        slots = [s for s in snapshot["slots"] if s["AttemptID"] == attempt["AttemptID"]]
        parts = [p for p in snapshot["parts"] if p["AttemptID"] == attempt["AttemptID"]]
        receipt = json.loads(attempt["ReceiptJson"]) if attempt.get("ReceiptJson") else {}
        if (
            len(parts) != attempt["PartCount"]
            or len(slots) != len(parts) - 1
            or receipt.get("attempt_id") != attempt["AttemptID"]
            or receipt.get("files") != [p["FileID"] for p in parts]
            or receipt.get("export_key") != document["generation"]["export_key"]
            or receipt.get("fence") != attempt["Fence"]
            or not slots
        ):
            continue
        exact = {(p["FileID"], p["PartNo"]) for p in parts if p["Role"] == "generation"}
        if {(s["FileID"], s["PartNo"]) for s in slots} != exact:
            continue
        if any(s["State"] != "active" or s["OwnerID"] is not None for s in slots):
            continue
        result.append(attempt["AttemptID"])
    return result


def pending_retirements(snapshot):
    """Reconstruct unfinished clears from hashed append-only dispositions, never memory."""
    pool = snapshot["pool"]["pool"]
    job = snapshot["job"]
    attempts = snapshot["attempts"]
    if len(attempts) != 1:
        raise SourceConflict("One exact publishing attempt required for retirement recovery.")
    current = attempts[0]["AttemptID"]
    events = {e["DispositionID"]: e for e in snapshot.get("retirement_events", [])}
    result = []
    for slot in snapshot["pool"]["slots"]:
        if slot["State"] != "retired":
            continue
        event = events.get(slot["LastDispositionID"])
        if not event:
            raise SourceConflict("Retired slot has no durable retirement evidence.")
        evidence = json.loads(event["EvidenceJson"])
        if digest(evidence).hex() != event["EvidenceHash"]:
            raise SourceConflict("Retirement evidence hash differs.")
        # Other publishing jobs cannot adopt this retirement, even on the same pool.
        if evidence.get("current_attempt_id") != current:
            raise SourceConflict("Retired slot belongs to another publishing attempt.")
        previous = evidence.get("previous_assignment", {})
        proof = evidence.get("proof", {})
        if (
            (
                event["PoolID"],
                event["FileID"],
                event["OldEpoch"],
                event["NewEpoch"],
                event["Action"],
                event["OwnerID"],
                event["Fence"],
                event["ToSlotVersion"],
            )
            != (
                pool["PoolID"],
                slot["FileID"],
                pool["Epoch"],
                pool["Epoch"],
                "retire",
                job["OwnerID"],
                job["Fence"],
                slot["Version"],
            )
            or slot["OwnerID"] is not None
            or slot["LastAction"] != "retire"
            or any(
                previous.get(k) != slot[k]
                for k in ("FileID", "Epoch", "AssignmentID", "AttemptID", "PartNo", "Fence")
            )
            or previous.get("Version", -1) + 1 != slot["Version"]
            or previous.get("State") != "active"
            or previous.get("OwnerID") is not None
            or proof.get("current_attempt_id") != current
            or proof.get("old_attempt_id") != slot["AttemptID"]
            or any(
                proof.get(k) is not True
                for k in ("writer_terminated", "current_pointer_verified", "no_live_references")
            )
            or not proof.get("evidence_id")
        ):
            raise SourceConflict("Retirement scope/assignment/owner evidence differs.")
        result.append(
            dict(
                operation_id=event["OperationID"],
                pool_id=pool["PoolID"],
                epoch=pool["Epoch"],
                current_attempt_id=current,
                slots=[
                    dict(
                        file_id=slot["FileID"],
                        version=slot["Version"],
                        event=event["DispositionID"],
                        evidence_hash=event["EvidenceHash"],
                    )
                ],
            )
        )
    return result


def assert_registration(cursor, *, account, kvk_no, epoch, destinations):
    cursor.execute(
        "SELECT p.* FROM KVK.SourceOutputPool p WHERE AccountKey=? AND ActiveKVK=? AND Epoch=?",
        account,
        kvk_no,
        epoch,
    )
    candidates = rows(cursor)
    for pool in candidates:
        if digest(json.loads(pool["RegistrationJson"])) != bytes(pool["RegistrationHash"]):
            raise SourceConflict("Immutable registration hash differs.")
        cursor.execute(
            "SELECT FileID FROM KVK.SourceOutputSlot WHERE PoolID=? ORDER BY FileID",
            pool["PoolID"],
        )
        files = tuple(sorted((pool["IndexFileID"], *(r["FileID"] for r in rows(cursor)))))
        if files == destinations:
            if pool["PoolState"] != "active" or pool["OwnerID"] is not None:
                raise SourceConflict("Pool admission is closed; owned delivery may still drain.")
            return pool
    raise SourceConflict("Exact active pool registration/season/epoch required.")


class SourceOutputPoolDAL:
    def __init__(self, connect, *, execution_evidence=False):
        self.connect = connect
        self.execution_evidence = execution_evidence

    def _execution_gate(self, cursor, account):
        if self.execution_evidence:
            from services.export_execution_dal import ExportExecutionDAL

            ExportExecutionDAL.assert_no_active_stream(cursor, account)

    @staticmethod
    def _snapshot(cursor, pool_id):
        cursor.execute("SELECT * FROM KVK.SourceOutputPool WHERE PoolID=?", pool_id)
        pool = one(cursor)
        if not pool:
            raise SourceConflict("Registered pool not found.")
        if digest(json.loads(pool["RegistrationJson"])) != bytes(pool["RegistrationHash"]):
            raise SourceConflict("Immutable registration hash differs.")
        cursor.execute("SELECT * FROM KVK.SourceOutputSlot WHERE PoolID=? ORDER BY FileID", pool_id)
        slots = rows(cursor)
        cursor.execute("SELECT COUNT(*) AS Count FROM KVK.SourceOutputPool")
        count = one(cursor)["Count"]
        cursor.execute(
            "SELECT j.* FROM dbo.ExportJob j WHERE j.AccountKey=? AND j.ConsumerKind='new_source' AND j.KVK_NO=? AND j.PoolEpoch=? AND EXISTS (SELECT 1 FROM dbo.ExportJobResource r WHERE r.JobID=j.JobID AND r.ResourceKey=?) ORDER BY j.EnqueueSequence,j.JobID",
            pool["AccountKey"],
            pool["ActiveKVK"],
            pool["Epoch"],
            "destination:" + pool["IndexFileID"],
        )
        jobs = rows(cursor)
        attempts, parts = [], []
        from kvk.dal.new_source_delivery_dal import read_coordinated_receipts

        for job in jobs:
            job_attempts, job_parts = read_coordinated_receipts(cursor, job["JobID"])
            attempts.extend(job_attempts)
            parts.extend(job_parts)
        cursor.execute(
            "SELECT * FROM KVK.SourceDelivery WHERE DestinationKind='sheets' AND DestinationID=? ORDER BY PublicationID",
            pool["IndexFileID"],
        )
        legacy = rows(cursor)
        return _wire(
            dict(
                pool=pool,
                slots=slots,
                jobs=jobs,
                attempts=attempts,
                parts=parts,
                legacy_receipts=legacy,
                registration_count=count,
            )
        )

    def snapshot(self, pool_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, str(UUID(str(pool_id))))

    @contextmanager
    def _retirement_owned(self, coordinator, claim, current_attempt_id):
        with coordinator._owned(claim) as (cursor, job):
            attempt, parts = coordinator._attempt(cursor, claim, current_attempt_id)
            if job["ConsumerKind"] != "new_source" or attempt["Phase"] != "publication_pending":
                raise SourceConflict("Retirement requires the exact publishing job owner.")
            index = [p["FileID"] for p in parts if p["Role"] == "index"]
            if len(index) != 1:
                raise SourceConflict("Exact current index required.")
            cursor.execute(
                "SELECT PoolID FROM KVK.SourceOutputPool WHERE IndexFileID=? AND AccountKey=? AND ActiveKVK=? AND Epoch=?",
                index[0],
                job["AccountKey"],
                job["KVK_NO"],
                job["PoolEpoch"],
            )
            pool = one(cursor)
            if not pool:
                raise SourceConflict("Retirement registration changed.")
            _mutex(cursor, "pool:" + str(pool["PoolID"]).lower())
            snapshot = self._snapshot(cursor, pool["PoolID"])
            current_pool = snapshot["pool"]
            if current_pool["PoolState"] == "closing" and current_pool["OwnerID"] is not None:
                # Closing reserves the pool for rollover, but leaves this job's
                # resource claim intact until owned delivery has drained.
                operation = self._operation(cursor, current_pool["OwnerID"])
                if not operation or (
                    operation["PoolID"],
                    operation["AccountKey"],
                    operation["OldEpoch"],
                    operation["State"],
                    operation["Phase"],
                    operation["OwnerID"],
                ) != (
                    current_pool["PoolID"],
                    claim.account,
                    current_pool["Epoch"],
                    "closing",
                    "draining",
                    None,
                ):
                    raise SourceConflict("Closing reservation differs from the draining pool.")
            elif current_pool["PoolState"] != "active" or current_pool["OwnerID"] is not None:
                raise SourceConflict("Retirement pool ownership changed.")
            files = {snapshot["pool"]["IndexFileID"], *(s["FileID"] for s in snapshot["slots"])}
            owned_files = {
                k.removeprefix("destination:")
                for k, _ in claim.resources
                if k.startswith("destination:")
            }
            if files != owned_files:
                raise SourceConflict("Retirement requires exact registered resource membership.")
            yield cursor, job, snapshot

    def retirement_snapshot(self, coordinator, claim, current_attempt_id):
        with self._retirement_owned(coordinator, claim, current_attempt_id) as (_, _, snapshot):
            return snapshot

    def retire_generation(
        self, coordinator, claim, current_attempt_id, snapshot, old_attempt_id, proof
    ):
        """Journal intent before provider I/O. Interrupted retirement stays reserved."""
        if self.execution_evidence != (getattr(coordinator, "execution_evidence", False) is True):
            raise SourceConflict(
                "Retirement requires the same execution-evidence contract on both DALs."
            )

        def validate_proof(proof):
            if (
                not isinstance(proof, dict)
                or proof.get("snapshot_hash") != digest(snapshot).hex()
                or proof.get("current_attempt_id") != current_attempt_id
                or proof.get("old_attempt_id") != old_attempt_id
                or proof.get("writer_terminated") is not True
                or proof.get("current_pointer_verified") is not True
                or proof.get("no_live_references") is not True
                or not proof.get("evidence_id")
            ):
                raise SourceConflict("Exact termination and reference evidence required.")

        if not self.execution_evidence:
            validate_proof(proof)
        with self._retirement_owned(coordinator, claim, current_attempt_id) as (
            cursor,
            job,
            actual,
        ):
            if actual["pool"].get("PoolState") == "closing":
                # Rollover won the admission race while the independent probe ran.
                # Leave historical cleanup to rollover and finish this owned export.
                return None
            if actual != snapshot or old_attempt_id not in reusable_attempts(
                actual, current_attempt_id
            ):
                raise SourceConflict("Retirement snapshot or protected assignment changed.")
            if self.execution_evidence:
                from services.export_execution_dal import ExportExecutionDAL

                proof = ExportExecutionDAL.settlement_proof(
                    cursor, proof, snapshot=snapshot, account=claim.account, kind="retirement"
                )
                validate_proof(proof)
            pool = actual["pool"]
            operation_id = str(uuid4())
            retired = []
            for slot in actual["slots"]:
                if slot["AttemptID"] != old_attempt_id:
                    continue
                evidence = dict(
                    proof=proof, previous_assignment=slot, current_attempt_id=current_attempt_id
                )
                event = self._retirement_event(
                    cursor, pool, slot, claim, job, operation_id, "retire", evidence
                )
                version = _cas(
                    cursor,
                    "UPDATE KVK.SourceOutputSlot SET State='retired',Version=Version+1,LastDispositionID=?,LastAction='retire',LastDispositionVersion=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND Epoch=? AND State='active' AND OwnerID IS NULL AND Fence=? AND Version=? AND AssignmentID=? AND AttemptID=? AND PartNo=?",
                    event,
                    pool["PoolID"],
                    slot["FileID"],
                    pool["Epoch"],
                    slot["Fence"],
                    slot["Version"],
                    slot["AssignmentID"],
                    old_attempt_id,
                    slot["PartNo"],
                )["Version"]
                retired.append(
                    dict(
                        file_id=slot["FileID"],
                        version=version,
                        event=event,
                        evidence_hash=digest(evidence).hex(),
                    )
                )
            return dict(
                operation_id=operation_id,
                pool_id=pool["PoolID"],
                epoch=pool["Epoch"],
                current_attempt_id=current_attempt_id,
                slots=retired,
            )

    @staticmethod
    def _retirement_event(cursor, pool, slot, claim, job, operation_id, action, evidence):
        event = str(uuid4())
        cursor.execute(
            "SELECT ISNULL(MAX(SequenceNo),0)+1 AS SequenceNo FROM KVK.SourceOutputDisposition WHERE PoolID=?",
            pool["PoolID"],
        )
        sequence = one(cursor)["SequenceNo"]
        cursor.execute(
            "INSERT KVK.SourceOutputDisposition (DispositionID,OperationID,PoolID,SequenceNo,FileID,FileKind,ResourceKey,SlotFileID,IndexFileID,AccountKey,SourceKey,KVK_NO,ChoiceID,NewKVK_NO,NewChoiceID,OldEpoch,NewEpoch,Action,OwnerID,Fence,FromPoolVersion,ToPoolVersion,FromSlotVersion,ToSlotVersion,Actor,Reason,OccurredUTC,EvidenceHash,EvidenceJson) VALUES (?,?,?,?,?,'slot',?,?,NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,SYSUTCDATETIME(),?,?)",
            event,
            operation_id,
            pool["PoolID"],
            sequence,
            slot["FileID"],
            "destination:" + slot["FileID"],
            slot["FileID"],
            pool["AccountKey"],
            pool["SourceKey"],
            pool["ActiveKVK"],
            pool["ChoiceID"],
            pool["ActiveKVK"],
            pool["ChoiceID"],
            pool["Epoch"],
            pool["Epoch"],
            action,
            claim.owner_id,
            claim.fence,
            pool["Version"],
            pool["Version"] + 1,
            slot["Version"],
            slot["Version"] + 1,
            job["Actor"],
            "Superseded unretained generation: " + action,
            digest(evidence),
            bounded_json(evidence),
        )
        pool["Version"] = _cas(
            cursor,
            "UPDATE KVK.SourceOutputPool SET Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND Version=? AND Epoch=? AND Fence=? AND (OwnerID=? OR (OwnerID IS NULL AND CAST(? AS uniqueidentifier) IS NULL)) AND PoolState IN ('active','closing')",
            pool["PoolID"],
            pool["Version"],
            pool["Epoch"],
            pool["Fence"],
            pool.get("OwnerID"),
            pool.get("OwnerID"),
        )["Version"]
        return event

    def clear_retired_slot(
        self, coordinator, claim, retirement, member, evidence, *, recovery=False
    ):
        if self.execution_evidence != (getattr(coordinator, "execution_evidence", False) is True):
            raise SourceConflict(
                "Retirement clear requires the same evidence contract on both DALs."
            )
        if (
            evidence.get("file_id") != member["file_id"]
            or evidence.get("private") is not True
            or evidence.get("empty") is not True
            or not evidence.get("manifest_hash")
        ):
            raise SourceConflict("Exact private empty readback required.")
        owner = self._recovery_owned if recovery else self._retirement_owned
        with owner(coordinator, claim, retirement["current_attempt_id"]) as (
            cursor,
            job,
            snapshot,
        ):
            # A private readback does not by itself stop its writer. Closure must
            # commit before this slot becomes reusable under the account lock.
            if self.execution_evidence:
                self._execution_gate(cursor, claim.account)
            pool = snapshot["pool"]
            slot = next((s for s in snapshot["slots"] if s["FileID"] == member["file_id"]), None)
            if (pool["PoolID"], pool["Epoch"]) != (
                retirement["pool_id"],
                retirement["epoch"],
            ) or not slot:
                raise SourceConflict("Retirement pool/epoch changed.")
            if (slot["State"], slot["OwnerID"], slot["Version"], slot["LastDispositionID"]) != (
                "retired",
                None,
                member["version"],
                member["event"],
            ):
                raise SourceConflict("Retired assignment/version changed; no automatic recovery.")
            cursor.execute(
                "SELECT EvidenceHash,OwnerID,Fence FROM KVK.SourceOutputDisposition WHERE DispositionID=? AND OperationID=? AND PoolID=? AND FileID=? AND Action='retire'",
                member["event"],
                retirement["operation_id"],
                pool["PoolID"],
                slot["FileID"],
            )
            event = one(cursor)
            if not event or (
                bytes(event["EvidenceHash"]).hex(),
                str(event["OwnerID"]).lower(),
                event["Fence"],
            ) != (member["evidence_hash"], claim.owner_id, claim.fence):
                raise SourceConflict("Retirement owner/evidence changed.")
            cleared = self._retirement_event(
                cursor,
                pool,
                slot,
                claim,
                job,
                retirement["operation_id"],
                "clear",
                dict(retirement=member, readback=evidence),
            )
            _cas(
                cursor,
                "UPDATE KVK.SourceOutputSlot SET State='free',Fence=?,Version=Version+1,AssignmentID=NULL,AssignmentAction=NULL,AttemptID=NULL,PartNo=NULL,AssignmentVersion=NULL,LastDispositionID=?,LastAction='clear',LastDispositionVersion=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND Epoch=? AND State='retired' AND OwnerID IS NULL AND Fence=? AND Version=? AND LastDispositionID=?",
                claim.fence,
                cleared,
                pool["PoolID"],
                slot["FileID"],
                pool["Epoch"],
                slot["Fence"],
                member["version"],
                member["event"],
            )

    @contextmanager
    def _recovery_owned(self, coordinator, claim, current_attempt_id):
        with coordinator._owned(claim) as (cursor, job):
            audit = json.loads(job["ProvenanceJson"]).get("retirement_recovery", {})
            if (audit.get("state"), audit.get("attempt_id"), audit.get("version")) != (
                "owned",
                current_attempt_id,
                claim.version,
            ) or not audit.get("token"):
                raise SourceConflict("Retirement recovery owner was revoked.")
            _mutex(cursor, "pool:" + audit["pool_id"])
            snapshot = coordinator._operator_snapshot(cursor, claim.job_id)
            pool = snapshot["pool"]["pool"]
            if (pool["PoolID"], pool["Epoch"], pool["RegistrationHash"]) != (
                audit["pool_id"],
                audit["epoch"],
                audit["registration_hash"],
            ) or pool["PoolState"] not in {"active", "closing"}:
                raise SourceConflict("Recovery registration/epoch changed.")
            if pool["PoolState"] == "closing":
                operation = self._operation(cursor, pool["OwnerID"])
                if (
                    operation["PoolID"],
                    operation["AccountKey"],
                    operation["OldEpoch"],
                    operation["State"],
                    operation["Phase"],
                    operation["OwnerID"],
                ) != (
                    pool["PoolID"],
                    claim.account,
                    pool["Epoch"],
                    "closing",
                    "draining",
                    None,
                ):
                    raise SourceConflict("Closing reservation changed during recovery.")
            elif pool["OwnerID"] is not None:
                raise SourceConflict("Recovery pool has another owner.")
            yield cursor, job, snapshot["pool"]

    def claim_retirement_recovery(self, coordinator, snapshot, proof, *, actor):
        """Explicit nested owner after independent termination; never replays export."""
        from services.export_coordination_dal import Claim, validate_confirmed_probe

        if self.execution_evidence != (getattr(coordinator, "execution_evidence", False) is True):
            raise SourceConflict(
                "Recovery requires the same execution-evidence contract on both DALs."
            )

        if not self.execution_evidence:
            validate_confirmed_probe(snapshot, proof)
        pending = pending_retirements(snapshot)
        job = snapshot["job"]
        if (
            not coordinator.output_operations
            or not pending
            or job["State"] not in {"uncertain", "running"}
        ):
            raise SourceConflict("Exact interrupted retirement required.")

        def validate_recovery(proof):
            validate_confirmed_probe(snapshot, proof)
            if (
                proof.get("retirement_outcomes_reconciled") is not True
                or proof.get("no_delayed_retirement_effects") is not True
            ):
                raise SourceConflict(
                    "Reconcile all prior retirement requests before resuming clear."
                )

        if not self.execution_evidence:
            validate_recovery(proof)
        pool = snapshot["pool"]["pool"]
        expected = {
            "account:" + job["AccountKey"],
            "destination:" + pool["IndexFileID"],
            *("destination:" + s["FileID"] for s in snapshot["pool"]["slots"]),
        }
        if {r["ResourceKey"] for r in snapshot["resources"]} != expected:
            raise SourceConflict("Recovery requires complete registered resource membership.")
        with coordinator._account(job["AccountKey"]) as cursor:
            for resource in sorted(snapshot["resources"], key=lambda row: row["ResourceKey"]):
                _mutex(cursor, resource["ResourceKey"])
            _mutex(cursor, "pool:" + pool["PoolID"])
            if coordinator._operator_snapshot(cursor, job["JobID"]) != snapshot:
                raise SourceConflict("Retirement recovery snapshot changed.")
            if self.execution_evidence:
                from services.export_execution_dal import ExportExecutionDAL

                proof = ExportExecutionDAL.settlement_proof(
                    cursor,
                    proof,
                    snapshot=snapshot,
                    account=job["AccountKey"],
                    kind="retirement_recovery",
                )
                validate_recovery(proof)
            audit = json.loads(job["ProvenanceJson"])
            recovery = dict(
                token=str(uuid4()),
                state="owned",
                version=job["Version"] + 1,
                attempt_id=snapshot["attempts"][0]["AttemptID"],
                pool_id=pool["PoolID"],
                epoch=pool["Epoch"],
                registration_hash=pool["RegistrationHash"],
                actor=actor,
                proof=proof,
            )
            history = audit.setdefault("retirement_recoveries", [])
            history.append(recovery)
            audit["retirement_recovery"] = recovery
            version = _cas(
                cursor,
                "UPDATE dbo.ExportJob SET State='running',ProvenanceJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE JobID=? AND Version=? AND OwnerID=? AND Fence=? AND State=?",
                bounded_json(audit),
                job["JobID"],
                job["Version"],
                job["OwnerID"],
                job["Fence"],
                job["State"],
            )["Version"]
            claimed = []
            for r in snapshot["resources"]:
                if (
                    r["ActiveJobID"],
                    r["OwnerID"],
                    r["Fence"],
                    r.get("ActivePreparationID"),
                    r.get("ActiveOutputOperationID"),
                ) != (job["JobID"], job["OwnerID"], job["Fence"], None, None):
                    raise SourceConflict("Recovery cannot adopt another resource owner.")
                v = _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET BlockedReason=NULL,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActiveJobID=? AND OwnerID=? AND Fence=? AND ActivePreparationID IS NULL AND ActiveOutputOperationID IS NULL",
                    r["ResourceKey"],
                    r["Version"],
                    job["JobID"],
                    job["OwnerID"],
                    job["Fence"],
                )["Version"]
                claimed.append((r["ResourceKey"], v))
            return Claim(
                job["JobID"],
                job["AccountKey"],
                job["OwnerID"],
                job["Fence"],
                version,
                tuple(claimed),
                job["IntentID"],
            )

    def interrupt_retirement_recovery(self, coordinator, claim, attempt_id):
        with self._recovery_owned(coordinator, claim, attempt_id) as (cursor, job, _):
            coordinator._finish(cursor, claim, job, "uncertain", release=False)

    def finish_retirement_recovery(self, coordinator, claim, attempt_id):
        # Revoke the nested provider owner BEFORE taking a fresh read-only probe.
        if self.execution_evidence != (getattr(coordinator, "execution_evidence", False) is True):
            raise SourceConflict(
                "Recovery completion requires the same evidence contract on both DALs."
            )
        with self._recovery_owned(coordinator, claim, attempt_id) as (cursor, job, _):
            if self.execution_evidence:
                self._execution_gate(cursor, claim.account)
            if pending_retirements(coordinator._operator_snapshot(cursor, claim.job_id)):
                raise SourceConflict("Retirement recovery has unfinished clears.")
            _cas(
                cursor,
                "UPDATE dbo.ExportJob SET State='uncertain',ProvenanceJson=JSON_MODIFY(ProvenanceJson,'$.retirement_recovery.state','complete'),Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE JobID=? AND Version=? AND OwnerID=? AND Fence=? AND State='running'",
                claim.job_id,
                claim.version,
                claim.owner_id,
                claim.fence,
            )

    def choice(self, kvk_no):
        if type(kvk_no) is not int or not 0 < kvk_no < 2**31:
            raise ValueError("Explicit positive target season required.")
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT KVK_NO,SourceKey,ChoiceID FROM KVK.SeasonSource WHERE KVK_NO=?", kvk_no
            )
            result = one(cursor)
            if not result:
                raise SourceConflict("Target season has no fixed source choice.")
            return _wire(result)

    def resolve(self, kvk_no, index_file_id=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT PoolID,IndexFileID FROM KVK.SourceOutputPool WHERE ActiveKVK=? ORDER BY RegistrationNo",
                kvk_no,
            )
            matches = [
                r
                for r in rows(cursor)
                if index_file_id is None or r["IndexFileID"] == index_file_id
            ]
            if len(matches) != 1:
                raise SourceConflict("Select one exact registered index file for this season.")
            return str(matches[0]["PoolID"]).lower()

    def is_index(self, file_id):
        with transaction(self.connect) as cursor:
            cursor.execute("SELECT PoolID FROM KVK.SourceOutputPool WHERE IndexFileID=?", file_id)
            return one(cursor) is not None

    def pending(self, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT OperationID FROM KVK.SourceOutputOperation WHERE AccountKey=? AND State IN ('closing','ready') ORDER BY EnqueueSequence,OperationID",
                account,
            )
            return tuple(str(r["OperationID"]).lower() for r in rows(cursor))

    def completed_setup(self, pool_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT o.OldKVK,o.NewKVK FROM KVK.SourceOutputOperation o JOIN KVK.SourceOutputPool p ON p.PoolID=o.PoolID AND p.Epoch=o.TargetEpoch WHERE p.PoolID=? AND o.State='completed'",
                pool_id,
            )
            return one(cursor)

    def export_context(self, pool_id):
        with transaction(self.connect) as cursor:
            result = self._snapshot(cursor, pool_id)
            pool = result["pool"]
            cursor.execute(
                "SELECT TOP (1) * FROM KVK.SourceExportIntent WHERE KVK_NO=? AND SourceKey=? AND ChoiceID=? ORDER BY CommitSequence DESC",
                pool["ActiveKVK"],
                pool["SourceKey"],
                pool["ChoiceID"],
            )
            result["intent"] = _wire(one(cursor))
            cursor.execute(
                "SELECT OperationID,State,Phase,OldKVK,NewKVK,OldEpoch,TargetEpoch FROM KVK.SourceOutputOperation WHERE ActivePoolID=?",
                pool_id,
            )
            result["operation"] = _wire(one(cursor))
            return result

    @contextmanager
    def _locked(self, pool_id):
        with transaction(self.connect) as cursor:
            cursor.execute("SELECT AccountKey FROM KVK.SourceOutputPool WHERE PoolID=?", pool_id)
            scope = one(cursor)
            if not scope:
                raise SourceConflict("Pool not found.")
            _mutex(cursor, "account:" + scope["AccountKey"])
            cursor.execute(
                "SELECT AccountResourceKey AS ResourceKey FROM KVK.SourceOutputPool WHERE PoolID=? UNION SELECT f.ResourceKey FROM KVK.SourceOutputFile f WHERE f.FileID IN (SELECT IndexFileID FROM KVK.SourceOutputPool WHERE PoolID=? UNION SELECT FileID FROM KVK.SourceOutputSlot WHERE PoolID=?) ORDER BY ResourceKey",
                pool_id,
                pool_id,
                pool_id,
            )
            for resource in rows(cursor):
                _mutex(cursor, resource["ResourceKey"])
            _mutex(cursor, "pool:" + str(pool_id))
            cursor.execute(
                "SELECT * FROM KVK.SourceOutputPool WITH (UPDLOCK,HOLDLOCK) WHERE PoolID=?",
                pool_id,
            )
            yield cursor, one(cursor)

    @staticmethod
    def _operation(cursor, operation_id):
        cursor.execute("SELECT * FROM KVK.SourceOutputOperation WHERE OperationID=?", operation_id)
        result = one(cursor)
        if not result:
            raise SourceConflict("Durable rollover operation not found.")
        if digest(json.loads(result["PlanJson"])) != bytes(result["PlanHash"]):
            raise SourceConflict("Immutable confirmed operation plan differs.")
        return _wire(result)

    def operation(self, operation_id):
        with transaction(self.connect) as cursor:
            return self._operation(cursor, str(UUID(str(operation_id))))

    def operation_snapshot(self, operation_id):
        with transaction(self.connect) as cursor:
            op = self._operation(cursor, str(UUID(str(operation_id))))
            cursor.execute(
                "SELECT r.* FROM dbo.ExportResource r JOIN KVK.SourceOutputOperationResource m ON m.ResourceKey=r.ResourceKey WHERE m.OperationID=? ORDER BY r.ResourceKey",
                operation_id,
            )
            resources = rows(cursor)
            return _wire(
                dict(operation=op, resources=resources, pool=self._snapshot(cursor, op["PoolID"]))
            )

    def reconcile_complete(self, snapshot, proof, *, actor):
        op = snapshot["operation"]
        expected = {
            snapshot["pool"]["pool"]["IndexFileID"],
            *(s["FileID"] for s in snapshot["pool"]["slots"]),
        }

        def validate_proof(proof):
            if (
                proof.get("snapshot_hash") != digest(snapshot).hex()
                or proof.get("writer_terminated") is not True
                or proof.get("state") != "completed"
                or not proof.get("evidence_id")
                or set(proof.get("files", {})) != expected
                or not proof.get("setup")
            ):
                raise SourceConflict(
                    "Exact terminal rollover readback and old-writer termination required."
                )
            for file_id, evidence in proof["files"].items():
                if (
                    evidence.get("file_id") != file_id
                    or evidence.get("private") is not True
                    or evidence.get("empty") is not True
                    or not evidence.get("manifest_hash")
                ):
                    raise SourceConflict(
                        "Every registered file needs complete private-clear evidence."
                    )
            setup = proof["setup"]
            if (
                setup.get("file_id"),
                setup.get("private"),
                setup.get("setup"),
                setup.get("old_kvk"),
                setup.get("new_kvk"),
            ) != (snapshot["pool"]["pool"]["IndexFileID"], True, True, op["OldKVK"], op["NewKVK"]):
                raise SourceConflict("Exact setup marker evidence required.")
            return setup

        if not self.execution_evidence:
            setup = validate_proof(proof)
        with self._locked(op["PoolID"]) as (cursor, pool):
            current = self._operation(cursor, op["OperationID"])
            cursor.execute(
                "SELECT r.* FROM dbo.ExportResource r JOIN KVK.SourceOutputOperationResource m ON m.ResourceKey=r.ResourceKey WHERE m.OperationID=? ORDER BY r.ResourceKey",
                op["OperationID"],
            )
            resources = rows(cursor)
            if _wire(
                dict(
                    operation=current,
                    resources=resources,
                    pool=self._snapshot(cursor, op["PoolID"]),
                )
            ) != snapshot or current["State"] not in {"running", "uncertain"}:
                raise SourceConflict("Rollover reconciliation snapshot changed.")
            if self.execution_evidence:
                from services.export_execution_dal import ExportExecutionDAL

                proof = ExportExecutionDAL.settlement_proof(
                    cursor,
                    proof,
                    snapshot=snapshot,
                    account=op["AccountKey"],
                    kind="rollover_complete",
                )
                setup = validate_proof(proof)
            for resource in _wire(resources):
                if (
                    resource["ActiveOutputOperationID"],
                    resource["OwnerID"],
                    resource["Fence"],
                    resource["ActiveJobID"],
                    resource["ActivePreparationID"],
                    resource["BlockedReason"],
                ) != (op["OperationID"], op["OwnerID"], op["Fence"], None, None, None):
                    raise SourceConflict("Reconciliation cannot release another resource owner.")
            if (
                pool["OwnerID"] != op["OperationID"]
                or pool["Fence"] != op["Fence"]
                or pool["Epoch"] != op["OldEpoch"]
                or pool["PoolState"] != "closing"
            ):
                raise SourceConflict("Closing pool ownership changed.")
            progress = json.loads(op["ProgressJson"])
            progress.update(
                files=proof["files"], setup=setup, reconciliation=dict(actor=actor, proof=proof)
            )
            version = _cas(
                cursor,
                "UPDATE KVK.SourceOutputOperation SET State='running',Phase='setup_verified',ProgressJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE OperationID=? AND OwnerID=? AND Fence=? AND Version=? AND State=?",
                bounded_json(progress),
                op["OperationID"],
                op["OwnerID"],
                op["Fence"],
                op["Version"],
                op["State"],
            )["Version"]
            claim = OutputClaim(
                op["OperationID"],
                op["AccountKey"],
                op["OwnerID"],
                op["Fence"],
                version,
                tuple((r["ResourceKey"], r["Version"]) for r in resources),
                pool["Version"],
            )
            current.update(
                State="running",
                Phase="setup_verified",
                ProgressJson=bounded_json(progress),
                Version=version,
            )
            return self.complete(claim, _owned_values=(cursor, pool, current))

    def confirm(self, operation_id, plan):
        operation_id = str(UUID(str(operation_id)))
        document = bounded_json(plan)
        pool_id = plan["snapshot"]["pool"]["PoolID"]
        with self._locked(pool_id) as (cursor, pool):
            cursor.execute(
                "SELECT * FROM KVK.SourceOutputOperation WHERE OperationID=?", operation_id
            )
            previous = one(cursor)
            if previous:
                if bytes(previous["PlanHash"]) != digest(plan) or previous["PlanJson"] != document:
                    raise SourceConflict("Operation replay payload changed.")
                return _wire(previous)
            if self._snapshot(cursor, pool_id) != plan["snapshot"]:
                raise SourceConflict("Preview is stale; preview the current exact pool again.")
            if pool["PoolState"] != "active" or pool["OwnerID"] is not None:
                raise SourceConflict("Pool admission is already closed.")
            target = plan["new_choice"]
            cursor.execute(
                "SELECT KVK_NO,SourceKey,ChoiceID FROM KVK.SeasonSource WHERE KVK_NO=?",
                target["KVK_NO"],
            )
            if _wire(one(cursor)) != target or target["SourceKey"] != pool["SourceKey"]:
                raise SourceConflict("Fixed target choice changed.")
            cursor.execute(
                "SELECT ISNULL(MAX(Ticket),0)+1 AS Ticket FROM (SELECT EnqueueSequence AS Ticket FROM dbo.ExportJob WHERE AccountKey=? UNION ALL SELECT EnqueueSequence FROM dbo.ExportPreparation WHERE AccountKey=? UNION ALL SELECT EnqueueSequence FROM KVK.SourceOutputOperation WHERE AccountKey=?) q",
                pool["AccountKey"],
                pool["AccountKey"],
                pool["AccountKey"],
            )
            ticket = one(cursor)["Ticket"]
            cursor.execute(
                "INSERT KVK.SourceOutputOperation (OperationID,PoolID,AccountKey,SourceKey,OldKVK,OldChoiceID,NewKVK,NewChoiceID,OldEpoch,TargetEpoch,PlanHash,PlanJson,ConfirmedBy,GuildID,ChannelID,Reason,ConfirmedUTC,EnqueueSequence,State,ActivePoolID,OwnerID,Fence,Version,Phase,ProgressJson,UpdatedUTC) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,SYSUTCDATETIME(),?,'closing',?,NULL,0,1,'draining',N'{}',SYSUTCDATETIME())",
                operation_id,
                pool_id,
                pool["AccountKey"],
                pool["SourceKey"],
                pool["ActiveKVK"],
                pool["ChoiceID"],
                target["KVK_NO"],
                target["ChoiceID"],
                pool["Epoch"],
                pool["Epoch"] + 1,
                digest(plan),
                document,
                plan["actor"],
                plan["guild"],
                plan["channel"],
                plan["reason"],
                ticket,
                pool_id,
            )
            members = [
                (pool["AccountResourceKey"], "account", None, None, None),
                (
                    "destination:" + pool["IndexFileID"],
                    "destination",
                    pool["IndexFileID"],
                    pool["IndexFileID"],
                    None,
                ),
            ]
            members.extend(
                ("destination:" + s["FileID"], "destination", s["FileID"], None, s["FileID"])
                for s in plan["snapshot"]["slots"]
            )
            for resource, kind, file_id, index_id, slot_id in sorted(members):
                cursor.execute(
                    "INSERT KVK.SourceOutputOperationResource (OperationID,PoolID,AccountKey,ResourceKey,ResourceKind,FileID,IndexFileID,SlotFileID) VALUES (?,?,?,?,?,?,?,?)",
                    operation_id,
                    pool_id,
                    pool["AccountKey"],
                    resource,
                    kind,
                    file_id,
                    index_id,
                    slot_id,
                )
            _cas(
                cursor,
                "UPDATE KVK.SourceOutputPool SET PoolState='closing',OwnerID=?,Fence=Fence+1,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND Version=? AND Epoch=? AND PoolState='active' AND OwnerID IS NULL",
                operation_id,
                pool_id,
                pool["Version"],
                pool["Epoch"],
            )
            # Only never-attempted, unowned pending work may be cancelled. Running A
            # retains its job/resource ownership and finishes against its pinned vector.
            coordination = ExportCoordinationDAL(
                self.connect, preparations=True, output_operations=True
            )
            for job in plan["snapshot"]["jobs"]:
                if job["State"] not in {"waiting", "ready"} or job["OwnerID"] is not None:
                    continue
                cursor.execute(
                    "SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=?", job["JobID"]
                )
                if one(cursor):
                    continue
                provenance = json.loads(job["ProvenanceJson"])
                provenance["rollover_cancel"] = dict(
                    operation_id=operation_id, actor=plan["actor"], reason=plan["reason"]
                )
                _cas(
                    cursor,
                    "UPDATE dbo.ExportJob SET State='cancelled',ProvenanceJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE JobID=? AND Version=? AND OwnerID IS NULL AND State IN ('waiting','ready') AND NOT EXISTS(SELECT 1 FROM dbo.ExportAttempt WHERE JobID=?)",
                    bounded_json(provenance),
                    job["JobID"],
                    job["Version"],
                    job["JobID"],
                )
                coordination._sync_intent(cursor, job["IntentID"])
            return self._operation(cursor, operation_id)

    def drain_snapshot(self, operation_id):
        operation = self.operation(operation_id)
        return self.snapshot(operation["PoolID"])

    def ready(self, operation_id, drain, proof):
        operation = self.operation(operation_id)
        with self._locked(operation["PoolID"]) as (cursor, pool):
            current = self._operation(cursor, operation_id)
            if current["State"] != "closing" or self._snapshot(cursor, pool["PoolID"]) != drain:
                raise SourceConflict("Drain evidence changed; reconcile again.")
            if any(
                j["State"] in {"running", "uncertain", "ready", "waiting"} for j in drain["jobs"]
            ):
                raise SourceConflict("Old delivery is still pending or uncertain.")
            if any(
                r["DeliveryState"] in {"claimed", "uncertain"} for r in drain["legacy_receipts"]
            ):
                raise SourceConflict("Historical publication still requires reconciliation.")
            if self.execution_evidence:
                from services.export_execution_dal import ExportExecutionDAL

                proof = ExportExecutionDAL.settlement_proof(
                    cursor,
                    proof,
                    snapshot=drain,
                    account=current["AccountKey"],
                    kind="rollover_drain",
                )
            if (
                proof.get("snapshot_hash") != digest(drain).hex()
                or proof.get("all_writers_terminated") is not True
                or proof.get("remote_outcomes_reconciled") is not True
                or not proof.get("evidence_id")
            ):
                raise SourceConflict("Exact independently verified drain proof required.")
            _cas(
                cursor,
                "UPDATE KVK.SourceOutputOperation SET State='ready',Phase='ready',ProgressJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE OperationID=? AND State='closing' AND Version=? AND OwnerID IS NULL",
                bounded_json(dict(drain_hash=digest(drain).hex(), proof=proof, files={})),
                operation_id,
                current["Version"],
            )

    def files(self, operation_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT FileID FROM KVK.SourceOutputOperationResource WHERE OperationID=? AND FileID IS NOT NULL ORDER BY FileID",
                operation_id,
            )
            return tuple(r["FileID"] for r in rows(cursor))

    def claim(self, operation_id):
        operation = self.operation(operation_id)
        with self._locked(operation["PoolID"]) as (cursor, pool):
            op = self._operation(cursor, operation_id)
            if op["State"] != "ready" or op["OwnerID"] is not None:
                raise SourceConflict("Only ready operations can be admitted.")
            cursor.execute(
                "SELECT TOP (1) Ticket FROM (SELECT EnqueueSequence AS Ticket FROM dbo.ExportJob WHERE AccountKey=? AND (State='ready' OR (State='failed' AND JSON_VALUE(ProvenanceJson,'$.safe_retry.requested')='true')) UNION ALL SELECT EnqueueSequence FROM dbo.ExportPreparation WHERE AccountKey=? AND State='pending' UNION ALL SELECT EnqueueSequence FROM KVK.SourceOutputOperation WHERE AccountKey=? AND State='ready') q WHERE Ticket<?",
                op["AccountKey"],
                op["AccountKey"],
                op["AccountKey"],
                op["EnqueueSequence"],
            )
            if one(cursor):
                return None
            cursor.execute(
                "SELECT r.* FROM dbo.ExportResource r WITH (UPDLOCK,HOLDLOCK) JOIN KVK.SourceOutputOperationResource m ON m.ResourceKey=r.ResourceKey WHERE m.OperationID=? ORDER BY r.ResourceKey",
                operation_id,
            )
            resources = rows(cursor)
            if len(resources) != len(json.loads(op["PlanJson"])["snapshot"]["slots"]) + 2:
                raise SourceConflict("Operation resource membership differs.")
            if any(
                any(
                    r[k] is not None
                    for k in (
                        "ActiveJobID",
                        "ActivePreparationID",
                        "ActiveOutputOperationID",
                        "OwnerID",
                        "BlockedReason",
                    )
                )
                for r in resources
            ):
                return None
            self._execution_gate(cursor, op["AccountKey"])
            fence = max(pool["Fence"], op["Fence"], *(r["Fence"] for r in resources)) + 1
            owner = str(uuid4())
            version = _cas(
                cursor,
                "UPDATE KVK.SourceOutputOperation SET State='running',OwnerID=?,Fence=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE OperationID=? AND Version=? AND State='ready' AND OwnerID IS NULL",
                owner,
                fence,
                operation_id,
                op["Version"],
            )["Version"]
            claimed = []
            for r in resources:
                rv = _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActiveOutputOperationID=?,OwnerID=?,Fence=?,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActiveJobID IS NULL AND ActivePreparationID IS NULL AND ActiveOutputOperationID IS NULL AND OwnerID IS NULL AND BlockedReason IS NULL",
                    operation_id,
                    owner,
                    fence,
                    r["ResourceKey"],
                    r["Version"],
                )["Version"]
                claimed.append((r["ResourceKey"], rv))
            pool_version = _cas(
                cursor,
                "UPDATE KVK.SourceOutputPool SET Fence=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND Version=? AND Fence=? AND OwnerID=? AND PoolState='closing' AND Epoch=?",
                fence,
                pool["PoolID"],
                pool["Version"],
                pool["Fence"],
                operation_id,
                op["OldEpoch"],
            )["Version"]
            return OutputClaim(
                operation_id,
                op["AccountKey"],
                owner,
                fence,
                version,
                tuple(claimed),
                pool_version,
            )

    @contextmanager
    def _owned(self, claim):
        operation = self.operation(claim.operation_id)
        with self._locked(operation["PoolID"]) as (cursor, pool):
            op = self._operation(cursor, claim.operation_id)
            if (op["OwnerID"], op["Fence"], op["Version"], op["State"], op["AccountKey"]) != (
                claim.owner,
                claim.fence,
                claim.version,
                "running",
                claim.account,
            ):
                raise SourceConflict("Operation owner/fence/version changed.")
            cursor.execute(
                "SELECT ResourceKey FROM KVK.SourceOutputOperationResource WHERE OperationID=? ORDER BY ResourceKey",
                claim.operation_id,
            )
            if tuple(r["ResourceKey"] for r in rows(cursor)) != tuple(
                k for k, _ in claim.resources
            ):
                raise SourceConflict("Immutable operation membership changed.")
            for key, version in claim.resources:
                cursor.execute(
                    "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ResourceKey=?",
                    key,
                )
                r = _wire(one(cursor))
                if not r or (
                    r["ActiveOutputOperationID"],
                    r["OwnerID"],
                    r["Fence"],
                    r["Version"],
                    r["ActiveJobID"],
                    r["ActivePreparationID"],
                    r["BlockedReason"],
                ) != (claim.operation_id, claim.owner, claim.fence, version, None, None, None):
                    raise SourceConflict("Operation resource ownership changed.")
            if (
                pool["PoolState"] != "closing"
                or pool["Epoch"] != op["OldEpoch"]
                or pool["OwnerID"] != claim.operation_id
                or pool["Fence"] != claim.fence
                or pool["Version"] != claim.pool_version
            ):
                raise SourceConflict("Closing pool identity changed.")
            yield cursor, pool, op

    def authorize(self, claim):
        with self._owned(claim) as (_, _, op):
            return op

    def phase(self, claim, phase, file_id, evidence=None):
        with self._owned(claim) as (cursor, _, op):
            cursor.execute(
                "SELECT FileID FROM KVK.SourceOutputOperationResource WHERE OperationID=? AND FileID=?",
                claim.operation_id,
                file_id,
            )
            if not one(cursor):
                raise SourceConflict("Provider file is outside exact operation membership.")
            progress = json.loads(op["ProgressJson"])
            old = op["Phase"]
            valid = {
                "private_pending": {"ready", "clear_verified"},
                "private_verified": {"private_pending"},
                "clear_pending": {"private_verified"},
                "clear_verified": {"clear_pending"},
                "setup_pending": {"clear_verified"},
                "setup_verified": {"setup_pending"},
            }
            if (
                phase not in valid
                or old not in valid[phase]
                or (
                    phase not in {"private_pending", "setup_pending"}
                    and op["CurrentFileID"] != file_id
                )
            ):
                raise SourceConflict("Provider phase cannot be skipped or replayed.")
            if phase == "private_pending" and file_id in progress["files"]:
                raise SourceConflict("A cleared file cannot be cleared again.")
            if phase.startswith("setup_"):
                plan = json.loads(op["PlanJson"])
                pool = plan["snapshot"]["pool"]
                expected = {
                    pool["IndexFileID"],
                    *(s["FileID"] for s in plan["snapshot"]["slots"]),
                }
                if file_id != pool["IndexFileID"] or set(progress["files"]) != expected:
                    raise SourceConflict("Setup follows complete verified clear of every file.")
            if phase.endswith("verified"):
                if (
                    not isinstance(evidence, dict)
                    or evidence.get("file_id") != file_id
                    or evidence.get("private") is not True
                ):
                    raise SourceConflict("Exact private file readback required.")
                if phase == "clear_verified":
                    if evidence.get("empty") is not True:
                        raise SourceConflict("Complete empty readback required.")
                    progress["files"][file_id] = evidence
                elif phase == "setup_verified":
                    if evidence.get("setup") is not True or (
                        evidence.get("old_kvk"),
                        evidence.get("new_kvk"),
                    ) != (op["OldKVK"], op["NewKVK"]):
                        raise SourceConflict("Exact private season-ended/setup readback required.")
                    progress["setup"] = evidence
            progress["request"] = dict(phase=phase, file_id=file_id, evidence=evidence)
            version = _cas(
                cursor,
                "UPDATE KVK.SourceOutputOperation SET Phase=?,CurrentFileID=?,ProgressJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE OperationID=? AND OwnerID=? AND Fence=? AND Version=? AND State='running'",
                phase,
                file_id,
                bounded_json(progress),
                claim.operation_id,
                claim.owner,
                claim.fence,
                claim.version,
            )["Version"]
            return replace(claim, version=version)

    def uncertain(self, claim):
        with self._owned(claim) as (cursor, _, _):
            _cas(
                cursor,
                "UPDATE KVK.SourceOutputOperation SET State='uncertain',Phase='uncertain',Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE OperationID=? AND OwnerID=? AND Fence=? AND Version=? AND State='running'",
                claim.operation_id,
                claim.owner,
                claim.fence,
                claim.version,
            )
            # Resource owner tokens remain byte-for-byte intact. No independent release.

    def complete(self, claim, *, _owned_values=None):
        with self._owned(claim) if _owned_values is None else nullcontext(_owned_values) as (
            cursor,
            pool,
            op,
        ):
            self._execution_gate(cursor, claim.account)
            progress = json.loads(op["ProgressJson"])
            plan = json.loads(op["PlanJson"])
            files = {pool["IndexFileID"], *(s["FileID"] for s in plan["snapshot"]["slots"])}
            if (
                op["Phase"] != "setup_verified"
                or not progress.get("setup")
                or set(progress["files"]) != files
            ):
                raise SourceConflict("Every exact registered file requires verified private clear.")
            for file_id, evidence in progress["files"].items():
                if not isinstance(evidence, dict) or (
                    evidence.get("file_id"),
                    evidence.get("private"),
                    evidence.get("empty"),
                ) != (file_id, True, True):
                    raise SourceConflict(
                        "Every exact registered file requires verified private clear."
                    )
            setup = progress["setup"]
            if not isinstance(setup, dict) or (
                setup.get("file_id"),
                setup.get("private"),
                setup.get("setup"),
                setup.get("old_kvk"),
                setup.get("new_kvk"),
            ) != (pool["IndexFileID"], True, True, op["OldKVK"], op["NewKVK"]):
                raise SourceConflict("Exact new-season setup readback required before release.")
            cursor.execute(
                "SELECT ISNULL(MAX(SequenceNo),0) AS SequenceNo FROM KVK.SourceOutputDisposition WHERE PoolID=?",
                pool["PoolID"],
            )
            sequence = one(cursor)["SequenceNo"]
            pv = pool["Version"]
            for file_id in sorted(files):
                cursor.execute(
                    "SELECT * FROM KVK.SourceOutputSlot WITH (UPDLOCK,HOLDLOCK) WHERE PoolID=? AND FileID=?",
                    pool["PoolID"],
                    file_id,
                )
                slot = one(cursor)
                if slot and (
                    slot["Epoch"] != op["OldEpoch"]
                    or slot["State"] in {"quarantined", "retired", "staging"}
                    or slot["OwnerID"] is not None
                ):
                    raise SourceConflict("Slot did not drain into eligible audited rollover state.")
                event = str(uuid4())
                evidence = bounded_json(
                    dict(
                        plan_hash=op["PlanHash"],
                        termination=progress["proof"],
                        readback=progress["files"][file_id],
                        retired_assignment=_wire(slot),
                    )
                )
                # Retire the old remote representation separately from the new-epoch
                # empty-file disposition. Original assignments/receipts stay intact.
                retirement = str(uuid4())
                sequence += 1
                cursor.execute(
                    "INSERT KVK.SourceOutputDisposition (DispositionID,OperationID,PoolID,SequenceNo,FileID,FileKind,ResourceKey,SlotFileID,IndexFileID,AccountKey,SourceKey,KVK_NO,ChoiceID,NewKVK_NO,NewChoiceID,OldEpoch,NewEpoch,Action,OwnerID,Fence,FromPoolVersion,ToPoolVersion,FromSlotVersion,ToSlotVersion,Actor,Reason,OccurredUTC,EvidenceHash,EvidenceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'retire',?,?,?,?,?,?,?, ?,SYSUTCDATETIME(),?,?)",
                    retirement,
                    claim.operation_id,
                    pool["PoolID"],
                    sequence,
                    file_id,
                    "slot" if slot else "index",
                    "destination:" + file_id,
                    file_id if slot else None,
                    None if slot else file_id,
                    op["AccountKey"],
                    op["SourceKey"],
                    op["OldKVK"],
                    op["OldChoiceID"],
                    op["OldKVK"],
                    op["OldChoiceID"],
                    op["OldEpoch"],
                    op["OldEpoch"],
                    claim.owner,
                    claim.fence,
                    pv,
                    pv + 1,
                    slot["Version"] if slot else None,
                    slot["Version"] + 1 if slot else None,
                    op["ConfirmedBy"],
                    op["Reason"],
                    digest(json.loads(evidence)),
                    evidence,
                )
                if slot:
                    slot["Version"] = _cas(
                        cursor,
                        "UPDATE KVK.SourceOutputSlot SET State='retired',OwnerID=NULL,Fence=?,Version=Version+1,LastDispositionID=?,LastAction='retire',LastDispositionVersion=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND Version=? AND Epoch=? AND OwnerID IS NULL",
                        claim.fence,
                        retirement,
                        pool["PoolID"],
                        file_id,
                        slot["Version"],
                        op["OldEpoch"],
                    )["Version"]
                pv += 1
                sequence += 1
                cursor.execute(
                    "INSERT KVK.SourceOutputDisposition (DispositionID,OperationID,PoolID,SequenceNo,FileID,FileKind,ResourceKey,SlotFileID,IndexFileID,AccountKey,SourceKey,KVK_NO,ChoiceID,NewKVK_NO,NewChoiceID,OldEpoch,NewEpoch,Action,OwnerID,Fence,FromPoolVersion,ToPoolVersion,FromSlotVersion,ToSlotVersion,Actor,Reason,OccurredUTC,EvidenceHash,EvidenceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'clear',?,?,?,?,?,?,?, ?,SYSUTCDATETIME(),?,?)",
                    event,
                    claim.operation_id,
                    pool["PoolID"],
                    sequence,
                    file_id,
                    "slot" if slot else "index",
                    "destination:" + file_id,
                    file_id if slot else None,
                    None if slot else file_id,
                    op["AccountKey"],
                    op["SourceKey"],
                    op["OldKVK"],
                    op["OldChoiceID"],
                    op["NewKVK"],
                    op["NewChoiceID"],
                    op["OldEpoch"],
                    op["TargetEpoch"],
                    claim.owner,
                    claim.fence,
                    pv,
                    pv + 1,
                    slot["Version"] if slot else None,
                    slot["Version"] + 1 if slot else None,
                    op["ConfirmedBy"],
                    op["Reason"],
                    digest(json.loads(evidence)),
                    evidence,
                )
                if slot:
                    _cas(
                        cursor,
                        "UPDATE KVK.SourceOutputSlot SET Epoch=?,State='free',OwnerID=NULL,Fence=?,Version=Version+1,AssignmentID=NULL,AssignmentAction=NULL,AttemptID=NULL,PartNo=NULL,AssignmentVersion=NULL,LastDispositionID=?,LastAction='clear',LastDispositionVersion=Version+1,QuarantineReason=NULL,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND FileID=? AND Version=? AND Epoch=? AND OwnerID IS NULL",
                        op["TargetEpoch"],
                        claim.fence,
                        event,
                        pool["PoolID"],
                        file_id,
                        slot["Version"],
                        op["OldEpoch"],
                    )
                pv += 1
            _cas(
                cursor,
                "UPDATE KVK.SourceOutputPool SET ActiveKVK=?,ChoiceID=?,Epoch=?,PoolState='active',OwnerID=NULL,Fence=?,Version=?,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PoolID=? AND Version=? AND Epoch=? AND PoolState='closing' AND OwnerID=?",
                op["NewKVK"],
                op["NewChoiceID"],
                op["TargetEpoch"],
                claim.fence,
                pv,
                pool["PoolID"],
                pool["Version"],
                op["OldEpoch"],
                claim.operation_id,
            )
            for key, version in claim.resources:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActiveOutputOperationID=NULL,OwnerID=NULL,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActiveOutputOperationID=? AND OwnerID=? AND Fence=? AND Version=? AND ActiveJobID IS NULL AND ActivePreparationID IS NULL AND BlockedReason IS NULL",
                    key,
                    claim.operation_id,
                    claim.owner,
                    claim.fence,
                    version,
                )
            _cas(
                cursor,
                "UPDATE KVK.SourceOutputOperation SET State='completed',Phase='complete',ActivePoolID=NULL,OwnerID=NULL,CurrentFileID=NULL,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE OperationID=? AND OwnerID=? AND Fence=? AND Version=? AND State='running'",
                claim.operation_id,
                claim.owner,
                claim.fence,
                claim.version,
            )
            return self._operation(cursor, claim.operation_id)
