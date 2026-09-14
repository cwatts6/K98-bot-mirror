"""S10A temporal contracts. No connection defaults, provider calls or lease stealing.

All queue writers serialize account admission, then sorted destination resources,
then job CAS. Locks live only inside these short transactions. Source publication
writers never acquire this admission lock. SQL constraints alone do not implement
these transitions or establish provider truth.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import re
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, canonical, digest, one, rows, transaction
from kvk.models.source_integration import identity


def bounded_json(value):
    json.dumps(value, allow_nan=False)
    result = canonical(value)
    if len(result.encode("utf-16-le")) > 65536:
        raise ValueError("Export evidence exceeds its durable bound.")
    return result


def account_identity(service_account, project):
    """Stable shared account/project namespace; never use a credential filename."""
    if not all(isinstance(v, str) and v and v == v.strip() for v in (service_account, project)):
        raise ValueError("Explicit account and project identities are required.")
    return hashlib.sha256(canonical([service_account.lower(), project]).encode()).hexdigest()


@dataclass(frozen=True)
class JobSpec:
    account: str
    consumer: str
    input_hash: bytes
    destinations: tuple[str, ...]
    actor: str
    reason: str
    kvk_no: int | None = None
    intent_id: str | None = None
    epoch: int | None = None
    repair_id: str | None = None
    spool_key: str | None = None
    spool_bytes: int | None = None
    storage_owner: str | None = None
    provenance: str = "{}"

    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", self.account):
            raise ValueError("Invalid account identity.")
        if self.consumer not in {"new_source", "all_kvk", "scan_data"}:
            raise ValueError("Invalid consumer.")
        if not isinstance(self.input_hash, bytes) or len(self.input_hash) != 32:
            raise ValueError("Exact input SHA256 required.")
        if (
            not isinstance(self.destinations, tuple)
            or not self.destinations
            or len(self.destinations) > 1024
            or self.destinations != tuple(sorted(set(self.destinations)))
            or any(not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", d) for d in self.destinations)
        ):
            raise ValueError("Canonical distinct registered spreadsheet IDs required.")
        for text, limit in ((self.actor, 128), (self.reason, 1024)):
            if (
                not isinstance(text, str)
                or not text.strip()
                or len(text.encode("utf-16-le")) > 2 * limit
            ):
                raise ValueError("Bounded actor and reason required.")
        if self.actor != self.actor.strip():
            raise ValueError("Actor must be canonical.")
        if self.consumer == "new_source":
            if self.intent_id is None or type(self.epoch) is not int or not 1 <= self.epoch < 2**63:
                raise ValueError("New-source intent and positive epoch required.")
            object.__setattr__(self, "intent_id", identity(self.intent_id))
        elif self.intent_id is not None or self.epoch is not None:
            raise ValueError("Legacy/daily work cannot reference source intent or epoch.")
        if self.consumer == "scan_data":
            if self.kvk_no is not None:
                raise ValueError("Daily work has no source season.")
        elif type(self.kvk_no) is not int or not 1 <= self.kvk_no <= 2147483647:
            raise ValueError("Explicit season required.")
        if self.repair_id is not None:
            object.__setattr__(self, "repair_id", identity(self.repair_id))
        spool = (self.spool_key, self.spool_bytes, self.storage_owner)
        if any(v is not None for v in spool) or self.consumer != "new_source":
            if (
                not isinstance(self.spool_key, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", self.spool_key)
                or type(self.spool_bytes) is not int
                or not 0 < self.spool_bytes < 2**63
                or not isinstance(self.storage_owner, str)
                or not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", self.storage_owner)
            ):
                raise ValueError("Complete bounded spool identity required.")
        if not isinstance(json.loads(self.provenance), dict):
            raise ValueError("Provenance must be an object.")
        bounded_json(json.loads(self.provenance))

    @property
    def resource_keys(self):
        return ("account:" + self.account, *("destination:" + d for d in self.destinations))

    @property
    def destination_hash(self):
        return digest(self.destinations)


@dataclass(frozen=True)
class Claim:
    job_id: str
    account: str
    owner_id: str
    fence: int
    version: int
    resources: tuple[tuple[str, int], ...]
    intent_id: str | None = None


def _job(cursor, job_id):
    cursor.execute("SELECT * FROM dbo.ExportJob WITH (UPDLOCK,HOLDLOCK) WHERE JobID=?", job_id)
    row = one(cursor)
    if row:
        for name in ("JobID", "SupersededByJobID", "RepairID"):
            if row[name] is not None:
                row[name] = identity(row[name])
    return row


def _mutex(cursor, key):
    cursor.execute(
        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,"
        "@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0;"
        "IF @r<0 THROW 51400,'Export admission busy',1;",
        "k98-export:" + hashlib.sha256(key.encode()).hexdigest(),
    )


def _cas(cursor, sql, *args):
    cursor.execute(sql, *args)
    result = one(cursor)
    if result is None:
        raise SourceConflict("Export version/ownership CAS lost.")
    return result


def validate_parts(parts, destinations):
    if not isinstance(parts, list) or not 1 <= len(parts) <= 1024:
        raise ValueError("A complete bounded part manifest is required.")
    files = [p["file_id"] for p in parts]
    if len(set(files)) != len(files) or not set(files) <= set(destinations):
        raise SourceConflict("Part files differ from admitted resources.")
    for part in parts:
        if set(part) != {"file_id", "role", "manifest_hash", "grids", "rows", "cells"}:
            raise ValueError("Unexpected part manifest fields.")
        if part["role"] not in {"index", "generation", "output"}:
            raise ValueError("Invalid part role.")
        if not re.fullmatch(r"[0-9a-f]{64}", part["manifest_hash"]):
            raise ValueError("Exact part manifest digest required.")
        if any(type(part[n]) is not int for n in ("grids", "rows", "cells")) or not (
            0 < part["grids"] <= 2147483647
            and 0 <= part["rows"] <= part["cells"] < 2**63
            and part["cells"] > 0
        ):
            raise ValueError("Invalid part dimensions.")
    bounded_json(parts)


class ExportCoordinationDAL:
    def __init__(self, connect):
        self.connect = connect

    @contextmanager
    def _account(self, account):
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + account)
            yield cursor

    def pending_intents(self, limit=32, *, after=(0, 0), registrations=()):
        if type(limit) is not int or not 1 <= limit <= 128:
            raise ValueError("Bounded discovery required.")
        if len(registrations) > 8:
            raise ValueError("At most eight explicit registrations are supported.")
        eligibility = "i.IntentState IN ('pending','waiting_destination')"
        parameters = []
        if registrations:
            # Exclude already materialized history while preserving missing
            # registration work after a restart partway through fan-out.
            eligibility = (
                "i.IntentState NOT IN ('blocked','coalesced') AND EXISTS (SELECT 1 FROM (VALUES "
                + ",".join("(?,?,?,?)" for _ in registrations)
                + ") r(KVK_NO,AccountKey,PoolEpoch,DestinationSetHash) WHERE r.KVK_NO=i.KVK_NO "
                "AND NOT EXISTS (SELECT 1 FROM dbo.ExportJob j WHERE j.IntentID=i.IntentID "
                "AND j.AccountKey=r.AccountKey AND j.PoolEpoch=r.PoolEpoch AND j.DestinationSetHash=r.DestinationSetHash AND j.RepairID IS NULL))"
            )
            for r in registrations:
                parameters.extend((r.kvk_no, r.account, r.epoch, digest(r.destinations)))
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) i.* FROM KVK.SourceExportIntent i "
                "WHERE " + eligibility + " "
                "AND (i.KVK_NO>? OR (i.KVK_NO=? AND i.CommitSequence>?)) "
                "ORDER BY i.KVK_NO,i.CommitSequence",
                limit,
                *parameters,
                after[0],
                after[0],
                after[1],
            )
            return rows(cursor)

    def enqueue(self, spec):
        if not isinstance(spec, JobSpec):
            raise ValueError("Validated immutable job specification required.")
        with self._account(spec.account) as cursor:
            if spec.intent_id is not None:
                _mutex(cursor, "intent:" + spec.intent_id)
            # Replay uniqueness includes exact NULL season/epoch/repair tuples.
            cursor.execute(
                "SELECT JobID FROM dbo.ExportJob WITH (UPDLOCK,HOLDLOCK) "
                "WHERE ConsumerKind=? AND AccountKey=? AND InputHash=? AND DestinationSetHash=? "
                "AND (KVK_NO=? OR (KVK_NO IS NULL AND CAST(? AS int) IS NULL)) "
                "AND (PoolEpoch=? OR (PoolEpoch IS NULL AND CAST(? AS bigint) IS NULL)) "
                "AND (RepairID=? OR (RepairID IS NULL AND CAST(? AS uniqueidentifier) IS NULL))",
                spec.consumer,
                spec.account,
                spec.input_hash,
                spec.destination_hash,
                spec.kvk_no,
                spec.kvk_no,
                spec.epoch,
                spec.epoch,
                spec.repair_id,
                spec.repair_id,
            )
            previous = one(cursor)
            if previous:
                row = _job(cursor, previous["JobID"])
                if (row["IntentID"], row["SpoolKey"], row["SpoolBytes"], row["StorageOwner"]) != (
                    spec.intent_id,
                    spec.spool_key,
                    spec.spool_bytes,
                    spec.storage_owner,
                ):
                    raise SourceConflict("Replay cannot replace immutable inputs or storage.")
                if spec.intent_id is not None:
                    self._sync_intent(cursor, spec.intent_id)
                return row
            if spec.repair_id is not None:
                raise SourceConflict("New repair admission requires the S10E authority workflow.")
            if spec.consumer == "new_source":
                from kvk.dal.season_source_dal import require_source
                from kvk.dal.source_update_dal import read_export_intent

                require_source(cursor, spec.kvk_no, "snapshot_report_v1")
                intent, _ = read_export_intent(cursor, spec.intent_id)
                if (
                    intent["KVK_NO"] != spec.kvk_no
                    or bytes(intent["VectorHash"]) != spec.input_hash
                ):
                    raise SourceConflict("Job differs from its sealed export vector.")
                if intent["IntentState"] in {"blocked", "coalesced"}:
                    raise SourceConflict("Intent is not eligible for materialization.")
            for key in spec.resource_keys:
                _mutex(cursor, key)
                cursor.execute(
                    "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ResourceKey=?",
                    key,
                )
                resource = one(cursor)
                kind = "account" if key.startswith("account:") else "destination"
                if resource and resource["ResourceKind"] != kind:
                    raise SourceConflict("Resource kind cannot change.")
                if not resource:
                    cursor.execute(
                        "INSERT dbo.ExportResource (ResourceKey,ResourceKind,Fence,Version) VALUES (?,?,0,1)",
                        key,
                        kind,
                    )
                if kind == "destination":
                    cursor.execute(
                        "SELECT j.ConsumerKind FROM dbo.ExportJobResource r JOIN dbo.ExportJob j ON j.JobID=r.JobID WHERE r.ResourceKey=?",
                        key,
                    )
                    if any(
                        (r["ConsumerKind"] == "new_source") != (spec.consumer == "new_source")
                        for r in rows(cursor)
                    ):
                        raise SourceConflict("New-source pool overlaps legacy/daily output.")
            cursor.execute(
                "SELECT ISNULL(MAX(EnqueueSequence),0)+1 AS Ticket FROM dbo.ExportJob WHERE AccountKey=?",
                spec.account,
            )
            ticket = one(cursor)["Ticket"]
            cursor.execute(
                "SELECT * FROM dbo.ExportJob WITH (UPDLOCK,HOLDLOCK) WHERE AccountKey=? "
                "AND ConsumerKind='new_source' AND State IN ('waiting','ready') "
                "AND KVK_NO=? AND DestinationSetHash=? AND PoolEpoch=? AND RepairID IS NULL "
                "AND NOT EXISTS (SELECT 1 FROM dbo.ExportAttempt a WHERE a.JobID=ExportJob.JobID)",
                spec.account,
                spec.kvk_no,
                spec.destination_hash,
                spec.epoch,
            )
            pending = rows(cursor) if spec.consumer == "new_source" else []
            if pending:
                # Out-of-order discovery cannot replace a newer pending vector.
                for old in pending:
                    cursor.execute(
                        "SELECT CommitSequence FROM KVK.SourceExportIntent WHERE IntentID=?",
                        old["IntentID"],
                    )
                    if one(cursor)["CommitSequence"] >= intent["CommitSequence"]:
                        raise SourceConflict("An equal/newer pending vector already exists.")
                ticket = min([ticket, *(r["EnqueueSequence"] for r in pending)])
            job_id = str(uuid4())
            cursor.execute(
                "INSERT dbo.ExportJob (JobID,ConsumerKind,SourceKey,IntentID,AccountKey,DestinationSetHash,InputHash,"
                "SpoolKey,SpoolBytes,StorageOwner,KVK_NO,PoolEpoch,RepairID,EnqueueSequence,State,Fence,Version,CreatedUTC,UpdatedUTC,Actor,Reason,ProvenanceJson) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,'ready',0,1,SYSUTCDATETIME(),SYSUTCDATETIME(),?,?,?)",
                job_id,
                spec.consumer,
                "snapshot_report_v1" if spec.consumer == "new_source" else None,
                spec.intent_id,
                spec.account,
                spec.destination_hash,
                spec.input_hash,
                spec.spool_key,
                spec.spool_bytes,
                spec.storage_owner,
                spec.kvk_no,
                spec.epoch,
                spec.repair_id,
                ticket,
                spec.actor,
                spec.reason,
                spec.provenance,
            )
            for key in spec.resource_keys:
                cursor.execute(
                    "INSERT dbo.ExportJobResource (JobID,ResourceKey) VALUES (?,?)", job_id, key
                )
            for old in pending:
                _mutex(cursor, "intent:" + old["IntentID"])
                _cas(
                    cursor,
                    "UPDATE dbo.ExportJob SET State='coalesced',SupersededByJobID=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                    "OUTPUT inserted.Version WHERE JobID=? AND Version=? AND State IN ('waiting','ready') AND OwnerID IS NULL AND Fence=0",
                    job_id,
                    old["JobID"],
                    old["Version"],
                )
                self._sync_intent(cursor, old["IntentID"])
            if spec.intent_id is not None:
                self._sync_intent(cursor, spec.intent_id)
            return _job(cursor, job_id)

    def _sync_intent(self, cursor, intent_id):
        """Aggregate registered jobs under the intent mutex, in their transaction."""
        cursor.execute(
            "SELECT IntentState,SupersededByIntentID FROM KVK.SourceExportIntent WITH (UPDLOCK,HOLDLOCK) WHERE IntentID=?",
            intent_id,
        )
        intent = one(cursor)
        if not intent:
            raise SourceConflict("Source intent disappeared during its job transition.")
        if intent["IntentState"] == "blocked":
            return
        cursor.execute(
            "SELECT j.State,s.IntentID AS SuccessorIntentID FROM dbo.ExportJob j LEFT JOIN dbo.ExportJob s ON s.JobID=j.SupersededByJobID WHERE j.IntentID=?",
            intent_id,
        )
        jobs = rows(cursor)
        if not jobs:
            raise SourceConflict("Materialized intent requires a durable job.")
        state, successor = "materialized", None
        if all(j["State"] == "confirmed" for j in jobs):
            state = "confirmed"
        elif all(j["State"] == "coalesced" for j in jobs):
            successors = {identity(j["SuccessorIntentID"]) for j in jobs}
            if len(successors) == 1:
                state, successor = "coalesced", successors.pop()
        if (state, successor) == (intent["IntentState"], intent["SupersededByIntentID"]):
            return
        _cas(
            cursor,
            "UPDATE KVK.SourceExportIntent SET IntentState=?,SupersededByIntentID=? OUTPUT inserted.IntentID WHERE IntentID=? AND IntentState=? AND (SupersededByIntentID=? OR (SupersededByIntentID IS NULL AND CAST(? AS uniqueidentifier) IS NULL))",
            state,
            successor,
            intent_id,
            intent["IntentState"],
            intent["SupersededByIntentID"],
            intent["SupersededByIntentID"],
        )

    def accounts(self):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT DISTINCT AccountKey FROM dbo.ExportJob WHERE State='ready' OR (State='failed' AND JSON_VALUE(ProvenanceJson,'$.safe_retry.requested')='true') ORDER BY AccountKey"
            )
            return [r["AccountKey"] for r in rows(cursor)]

    def claim_next(self, account, *, storage_owner=None):
        with self._account(account) as cursor:
            cursor.execute(
                "SELECT JobID FROM dbo.ExportJob WHERE AccountKey=? AND (State='ready' OR (State='failed' AND JSON_VALUE(ProvenanceJson,'$.safe_retry.requested')='true')) "
                "AND (StorageOwner IS NULL OR StorageOwner=?) ORDER BY EnqueueSequence,CreatedUTC,JobID",
                account,
                storage_owner,
            )
            candidates = rows(cursor)
            for candidate in candidates:
                cursor.execute(
                    "SELECT ResourceKey FROM dbo.ExportJobResource WHERE JobID=? ORDER BY ResourceKey",
                    candidate["JobID"],
                )
                keys = [r["ResourceKey"] for r in rows(cursor)]
                if not keys or keys[0] != "account:" + account:
                    raise SourceConflict("Missing account membership.")
                resources = []
                for key in keys:
                    _mutex(cursor, key)
                    cursor.execute(
                        "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ResourceKey=?",
                        key,
                    )
                    resources.append(one(cursor))
                if any(
                    not r or r["ActiveJobID"] is not None or r["BlockedReason"] for r in resources
                ):
                    continue
                job = _job(cursor, candidate["JobID"])
                retry = (
                    job["State"] == "failed"
                    and json.loads(job["ProvenanceJson"]).get("safe_retry", {}).get("requested")
                    is True
                )
                if not retry and (job["State"] != "ready" or job["OwnerID"] is not None):
                    raise SourceConflict("Job admission changed.")
                if retry:
                    cursor.execute(
                        "SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=?", job["JobID"]
                    )
                    if one(cursor):
                        raise SourceConflict(
                            "Attempted work requires authoritative reconciliation."
                        )
                    if job["ConsumerKind"] == "new_source":
                        from kvk.dal.season_source_dal import require_source

                        require_source(cursor, job["KVK_NO"], job["SourceKey"])
                destinations = tuple(
                    k.removeprefix("destination:") for k in keys if k.startswith("destination:")
                )
                if digest(destinations) != bytes(job["DestinationSetHash"]):
                    raise SourceConflict("Frozen destination membership changed.")
                # A predecessor receipt is not automatically mapped or reclaimed.
                for dest in destinations:
                    cursor.execute(
                        "SELECT PublicationID FROM KVK.SourceDelivery WHERE DestinationKind='sheets' AND DestinationID=? AND DeliveryState IN ('claimed','uncertain')",
                        dest,
                    )
                    if one(cursor):
                        raise SourceConflict(
                            "Retained predecessor receipt needs authoritative reconciliation."
                        )
                fence = max([job["Fence"], *(r["Fence"] for r in resources)]) + 1
                owner = str(uuid4())
                version = _cas(
                    cursor,
                    "UPDATE dbo.ExportJob SET State='running',OwnerID=?,Fence=?,ProvenanceJson=JSON_MODIFY(ProvenanceJson,'$.safe_retry',NULL),Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                    "OUTPUT inserted.Version WHERE JobID=? AND Version=? AND State=? AND Fence=?",
                    owner,
                    fence,
                    job["JobID"],
                    job["Version"],
                    job["State"],
                    job["Fence"],
                )["Version"]
                claimed = []
                for resource in resources:
                    result = _cas(
                        cursor,
                        "UPDATE dbo.ExportResource SET ActiveJobID=?,OwnerID=?,Fence=?,Version=Version+1 "
                        "OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActiveJobID IS NULL AND BlockedReason IS NULL",
                        job["JobID"],
                        owner,
                        fence,
                        resource["ResourceKey"],
                        resource["Version"],
                    )
                    claimed.append((resource["ResourceKey"], result["Version"]))
                return Claim(
                    job["JobID"], account, owner, fence, version, tuple(claimed), job["IntentID"]
                )
            return None

    @contextmanager
    def _owned(self, claim):
        with self._account(claim.account) as cursor:
            if claim.intent_id is not None:
                _mutex(cursor, "intent:" + claim.intent_id)
            for key, version in claim.resources:
                _mutex(cursor, key)
                cursor.execute(
                    "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ResourceKey=?",
                    key,
                )
                r = one(cursor)
                if not r or (
                    str(r["ActiveJobID"]).lower(),
                    r["OwnerID"],
                    r["Fence"],
                    r["Version"],
                    r["BlockedReason"],
                ) != (claim.job_id, claim.owner_id, claim.fence, version, None):
                    raise SourceConflict("Resource owner/fence/version changed or blocked.")
            job = _job(cursor, claim.job_id)
            if job and job.get("IntentID") != claim.intent_id:
                raise SourceConflict("Claim intent identity differs.")
            if not job or (
                job["AccountKey"],
                job["OwnerID"],
                job["Fence"],
                job["Version"],
                job["State"],
            ) != (claim.account, claim.owner_id, claim.fence, claim.version, "running"):
                raise SourceConflict("Job owner/fence/version changed.")
            cursor.execute(
                "SELECT ResourceKey FROM dbo.ExportJobResource WHERE JobID=? ORDER BY ResourceKey",
                claim.job_id,
            )
            if [r["ResourceKey"] for r in rows(cursor)] != [k for k, _ in claim.resources]:
                raise SourceConflict("Immutable resource membership changed.")
            yield cursor, job

    def authorize(self, claim, *, mutation=False):
        with self._owned(claim) as (cursor, job):
            if mutation:
                cursor.execute(
                    "SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=? AND OwnerID=? AND Fence=? AND Phase IN ('private_started','verified','publication_pending')",
                    claim.job_id,
                    claim.owner_id,
                    claim.fence,
                )
                if one(cursor) is None:
                    raise SourceConflict("A durable attempt must precede every mutation.")
            return job

    def request_safe_retry(
        self, job_id, account, *, expected_version, expected_epoch, actor, reason
    ):
        """Audit a never-mutated failure; retain identity, ticket and owner history.

        This is a DAL capability, not an operator command. Admission still waits
        its original turn and acquires the full resource set with a new fence.
        """
        if (
            not isinstance(actor, str)
            or not actor.strip()
            or len(actor) > 128
            or not isinstance(reason, str)
            or not reason.strip()
            or len(reason) > 1024
        ):
            raise ValueError("Bounded retry actor and reason required.")
        with self._account(account) as cursor:
            job = _job(cursor, identity(job_id))
            if not job or (job["AccountKey"], job["Version"], job["PoolEpoch"], job["State"]) != (
                account,
                expected_version,
                expected_epoch,
                "failed",
            ):
                raise SourceConflict("Safe retry scope/version changed.")
            cursor.execute("SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=?", job["JobID"])
            if one(cursor):
                raise SourceConflict("Attempted work cannot use safe retry.")
            if job["ConsumerKind"] == "new_source":
                from kvk.dal.season_source_dal import require_source

                require_source(cursor, job["KVK_NO"], job["SourceKey"])
            evidence = json.loads(job["ProvenanceJson"])
            history = evidence.setdefault("safe_retry_history", [])
            cursor.execute("SELECT CONVERT(varchar(33),SYSUTCDATETIME(),126) AS NowUTC")
            history.append(
                dict(
                    actor=actor,
                    reason=reason,
                    utc=one(cursor)["NowUTC"],
                    owner=job["OwnerID"],
                    fence=job["Fence"],
                    version=job["Version"],
                )
            )
            evidence["safe_retry"] = {"requested": True}
            _cas(
                cursor,
                "UPDATE dbo.ExportJob SET ProvenanceJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE JobID=? AND Version=? AND State='failed'",
                bounded_json(evidence),
                job["JobID"],
                expected_version,
            )

    def begin_attempt(self, claim, manifest, parts, *, legacy=None):
        with self._owned(claim) as (cursor, job):
            destinations = [
                k.removeprefix("destination:")
                for k, _ in claim.resources
                if k.startswith("destination:")
            ]
            validate_parts(parts, destinations)
            document = {"generation": manifest, "parts": parts}
            encoded = bounded_json(document)
            cursor.execute("SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=?", claim.job_id)
            if one(cursor):
                raise SourceConflict("Existing attempt requires an explicit recovery decision.")
            legacy_values = (None,) * 6
            if legacy is not None:
                if job["ConsumerKind"] != "new_source" or len(legacy) != 6:
                    raise SourceConflict("Invalid scoped predecessor receipt.")
                cursor.execute(
                    "SELECT v.PublicationID FROM KVK.SourceExportIntentPublication v JOIN KVK.SourceDelivery d "
                    "ON d.PublicationID=v.PublicationID AND d.SourceKey=v.SourceKey AND d.KVK_NO=v.KVK_NO AND d.PeriodID=v.PeriodID "
                    "WHERE v.IntentID=? AND v.PublicationID=? AND v.SourceKey=? AND v.KVK_NO=? AND v.PeriodID=? AND d.DestinationKind=? AND d.DestinationID=?",
                    job["IntentID"],
                    *legacy,
                )
                if one(cursor) is None or legacy[5] not in destinations:
                    raise SourceConflict(
                        "Predecessor receipt is outside the pinned vector/resources."
                    )
                legacy_values = tuple(legacy)
            attempt_id = str(uuid4())
            # Resource fences are monotonic across jobs sharing any destination.
            cursor.execute(
                "INSERT dbo.ExportAttempt (AttemptID,JobID,ConsumerKind,AttemptNo,OwnerID,Fence,Epoch,Phase,RemoteSequence,Version,CreatedUTC,UpdatedUTC,ManifestHash,ManifestJson,PartCount,"
                "LegacyPublicationID,LegacySourceKey,LegacyKVK_NO,LegacyPeriodID,LegacyDestinationKind,LegacyDestinationID) "
                "VALUES (?,?,?,1,?,?,?,'private_started',?,1,SYSUTCDATETIME(),SYSUTCDATETIME(),?,?,?,?,?,?,?,?,?)",
                attempt_id,
                claim.job_id,
                job["ConsumerKind"],
                claim.owner_id,
                claim.fence,
                job["PoolEpoch"],
                claim.fence,
                digest(document),
                encoded,
                len(parts),
                *legacy_values,
            )
            for number, part in enumerate(parts, 1):
                cursor.execute(
                    "INSERT dbo.ExportAttemptPart (AttemptID,PartNo,PartCount,FileID,Role,ManifestHash,GridCount,RowCount,CellCount,VerificationState,AclState,QuarantineState,Version) "
                    "VALUES (?,?,?,?,?,?,?,?,?,'pending','pending','none',1)",
                    attempt_id,
                    number,
                    len(parts),
                    part["file_id"],
                    part["role"],
                    bytes.fromhex(part["manifest_hash"]),
                    part["grids"],
                    part["rows"],
                    part["cells"],
                )
            return attempt_id

    def _attempt(self, cursor, claim, attempt_id):
        cursor.execute(
            "SELECT * FROM dbo.ExportAttempt WITH (UPDLOCK,HOLDLOCK) WHERE AttemptID=? AND JobID=? AND OwnerID=? AND Fence=?",
            attempt_id,
            claim.job_id,
            claim.owner_id,
            claim.fence,
        )
        attempt = one(cursor)
        if not attempt:
            raise SourceConflict("Attempt identity changed.")
        document = json.loads(attempt["ManifestJson"])
        if digest(document) != bytes(attempt["ManifestHash"]):
            raise SourceConflict("Attempt manifest hash differs.")
        cursor.execute(
            "SELECT * FROM dbo.ExportAttemptPart WITH (UPDLOCK,HOLDLOCK) WHERE AttemptID=? ORDER BY PartNo",
            attempt_id,
        )
        parts = rows(cursor)
        actual = [
            dict(
                file_id=p["FileID"],
                role=p["Role"],
                manifest_hash=bytes(p["ManifestHash"]).hex(),
                grids=p["GridCount"],
                rows=p["RowCount"],
                cells=p["CellCount"],
            )
            for p in parts
        ]
        if (
            len(parts) != attempt["PartCount"]
            or actual != document["parts"]
            or [p["PartNo"] for p in parts] != list(range(1, len(parts) + 1))
        ):
            raise SourceConflict("Attempt part cardinality or immutable manifest differs.")
        return attempt, parts

    def verified(self, claim, attempt_id):
        with self._owned(claim) as (cursor, _):
            attempt, parts = self._attempt(cursor, claim, attempt_id)
            if attempt["Phase"] != "private_started":
                raise SourceConflict("Only private work may become verified.")
            for p in parts:
                # Index remains the old pointer until publication; generation files
                # have been verified privately. Do not invent an index verification.
                if p["Role"] != "index":
                    _cas(
                        cursor,
                        "UPDATE dbo.ExportAttemptPart SET VerificationState='verified',VerifiedUTC=SYSUTCDATETIME(),AclState='private',AclCheckedUTC=SYSUTCDATETIME(),Version=Version+1 "
                        "OUTPUT inserted.Version WHERE AttemptID=? AND PartNo=? AND Version=? AND QuarantineState='none'",
                        attempt_id,
                        p["PartNo"],
                        p["Version"],
                    )
            _cas(
                cursor,
                "UPDATE dbo.ExportAttempt SET Phase='verified',VerifiedUTC=SYSUTCDATETIME(),UpdatedUTC=SYSUTCDATETIME(),Version=Version+1 OUTPUT inserted.Version WHERE AttemptID=? AND Version=? AND Phase='private_started'",
                attempt_id,
                attempt["Version"],
            )

    def publication_pending(self, claim, attempt_id):
        with self._owned(claim) as (cursor, _):
            attempt, _ = self._attempt(cursor, claim, attempt_id)
            _cas(
                cursor,
                "UPDATE dbo.ExportAttempt SET Phase='publication_pending',UpdatedUTC=SYSUTCDATETIME(),Version=Version+1 OUTPUT inserted.Version WHERE AttemptID=? AND Version=? AND Phase='verified'",
                attempt_id,
                attempt["Version"],
            )

    def confirm(self, claim, attempt_id, receipt):
        encoded = bounded_json(receipt)
        with self._owned(claim) as (cursor, job):
            attempt, parts = self._attempt(cursor, claim, attempt_id)
            document = json.loads(attempt["ManifestJson"])
            if (
                attempt["Phase"] != "publication_pending"
                or receipt.get("export_key") != document["generation"]["export_key"]
                or receipt.get("fence") != claim.fence
                or receipt.get("attempt_id") != attempt_id
                or receipt.get("files") != [p["FileID"] for p in parts]
                or receipt.get("audience") not in {"private", "public_viewer"}
                or not receipt.get("remote_id")
            ):
                raise SourceConflict("Confirmation differs from the pinned attempt.")
            for part in parts:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportAttemptPart SET VerificationState='verified',VerifiedUTC=SYSUTCDATETIME(),AclState=?,AclCheckedUTC=SYSUTCDATETIME(),Version=Version+1 "
                    "OUTPUT inserted.Version WHERE AttemptID=? AND PartNo=? AND Version=? AND QuarantineState='none'",
                    receipt["audience"],
                    attempt_id,
                    part["PartNo"],
                    part["Version"],
                )
            _cas(
                cursor,
                "UPDATE dbo.ExportAttempt SET Phase='published',ReceiptJson=?,PublishedUTC=SYSUTCDATETIME(),UpdatedUTC=SYSUTCDATETIME(),Version=Version+1 OUTPUT inserted.Version WHERE AttemptID=? AND Version=? AND Phase='publication_pending'",
                encoded,
                attempt_id,
                attempt["Version"],
            )
            self._finish(cursor, claim, job, "confirmed", release=True)

    def fail(self, claim, *, retain_claims=False):
        """Conservative stop. An attempt means mutations may have escaped; keep claims."""
        with self._owned(claim) as (cursor, job):
            cursor.execute("SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=?", claim.job_id)
            attempted = rows(cursor)
            for item in attempted:
                attempt, parts = self._attempt(cursor, claim, item["AttemptID"])
                _cas(
                    cursor,
                    "UPDATE dbo.ExportAttempt SET Phase='uncertain',UpdatedUTC=SYSUTCDATETIME(),Version=Version+1 OUTPUT inserted.Version WHERE AttemptID=? AND Version=?",
                    item["AttemptID"],
                    attempt["Version"],
                )
                for part in parts:
                    _cas(
                        cursor,
                        "UPDATE dbo.ExportAttemptPart SET QuarantineState='quarantined',QuarantinedUTC=SYSUTCDATETIME(),QuarantineReason='Outcome requires reconciliation',Version=Version+1 OUTPUT inserted.Version WHERE AttemptID=? AND PartNo=? AND Version=?",
                        item["AttemptID"],
                        part["PartNo"],
                        part["Version"],
                    )
            uncertain = bool(attempted) or retain_claims
            self._finish(
                cursor, claim, job, "uncertain" if uncertain else "failed", release=not uncertain
            )

    def _finish(self, cursor, claim, job, state, *, release):
        # Called only after evidence validation in confirm/fail, never on job state alone.
        _cas(
            cursor,
            "UPDATE dbo.ExportJob SET State=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE JobID=? AND Version=? AND OwnerID=? AND Fence=? AND State='running'",
            state,
            claim.job_id,
            job["Version"],
            claim.owner_id,
            claim.fence,
        )
        for key, version in claim.resources:
            if release:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActiveJobID=NULL,OwnerID=NULL,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActiveJobID=? AND OwnerID=? AND Fence=?",
                    key,
                    version,
                    claim.job_id,
                    claim.owner_id,
                    claim.fence,
                )
            else:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET BlockedReason='Outcome requires reconciliation',Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActiveJobID=? AND OwnerID=? AND Fence=?",
                    key,
                    version,
                    claim.job_id,
                    claim.owner_id,
                    claim.fence,
                )
        if claim.intent_id is not None:
            self._sync_intent(cursor, claim.intent_id)

    def reserve_request(self, account):
        with transaction(self.connect) as cursor:
            _mutex(cursor, "budget:" + account)
            cursor.execute("SELECT CAST(SYSUTCDATETIME() AS datetime2(3)) AS NowUTC")
            now = one(cursor)["NowUTC"]
            cursor.execute(
                "SELECT * FROM dbo.ExportRequestBudget WITH (UPDLOCK,HOLDLOCK) WHERE AccountKey=? AND BudgetKind='google_request'",
                account,
            )
            row = one(cursor)
            reserved = (
                max(now, row["NextAllowedUTC"], row["CooldownUntilUTC"] or now) if row else now
            )
            interval = row["IntervalMilliseconds"] if row else 2100
            if interval < 2100:
                raise SourceConflict("Budget policy is weaker than the admitted spacing.")
            next_time = reserved + timedelta(milliseconds=interval)
            if row:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportRequestBudget SET NextAllowedUTC=?,Version=Version+1 OUTPUT inserted.Version WHERE AccountKey=? AND BudgetKind='google_request' AND Version=?",
                    next_time,
                    account,
                    row["Version"],
                )
            else:
                cursor.execute(
                    "INSERT dbo.ExportRequestBudget (AccountKey,BudgetKind,NextAllowedUTC,IntervalMilliseconds,PolicyVersion,Version) VALUES (?,'google_request',?,2100,1,1)",
                    account,
                    next_time,
                )
            return {
                "ReservedUTC": reserved,
                "WaitSeconds": max(0, (reserved - now).total_seconds()),
            }

    def refresh_reservation(self, account, reserved):
        with transaction(self.connect) as cursor:
            _mutex(cursor, "budget:" + account)
            cursor.execute(
                "SELECT CAST(SYSUTCDATETIME() AS datetime2(3)) AS NowUTC,* FROM dbo.ExportRequestBudget WITH (UPDLOCK,HOLDLOCK) WHERE AccountKey=? AND BudgetKind='google_request'",
                account,
            )
            row = one(cursor)
            if not row:
                raise SourceConflict("Durable reservation disappeared.")
            now = row["NowUTC"]
            interval = timedelta(milliseconds=row["IntervalMilliseconds"])
            if (
                row["CooldownUntilUTC"] is not None and row["CooldownUntilUTC"] > reserved
            ) or now >= reserved + interval:
                # Stale slots are consumed, never refunded. Rebook each waiter
                # separately so a common cooldown cannot release a request burst.
                reserved = max(now, row["NextAllowedUTC"], row["CooldownUntilUTC"] or now)
                _cas(
                    cursor,
                    "UPDATE dbo.ExportRequestBudget SET NextAllowedUTC=?,Version=Version+1 OUTPUT inserted.Version WHERE AccountKey=? AND BudgetKind='google_request' AND Version=?",
                    reserved + interval,
                    account,
                    row["Version"],
                )
            return {
                "ReservedUTC": reserved,
                "WaitSeconds": max(0, (reserved - now).total_seconds()),
            }

    def complete_request(self, account):
        """Persist a full interval after actual completion, before releasing admission."""
        with transaction(self.connect) as cursor:
            _mutex(cursor, "budget:" + account)
            cursor.execute(
                "SELECT CAST(SYSUTCDATETIME() AS datetime2(3)) AS NowUTC,* FROM dbo.ExportRequestBudget WITH (UPDLOCK,HOLDLOCK) WHERE AccountKey=? AND BudgetKind='google_request'",
                account,
            )
            row = one(cursor)
            if not row or row["IntervalMilliseconds"] < 2100:
                raise SourceConflict("Request completion requires its admitted budget policy.")
            until = max(
                row["CooldownUntilUTC"] or row["NowUTC"],
                row["NowUTC"] + timedelta(milliseconds=row["IntervalMilliseconds"]),
            )
            _cas(
                cursor,
                "UPDATE dbo.ExportRequestBudget SET CooldownUntilUTC=?,NextAllowedUTC=?,Version=Version+1 OUTPUT inserted.Version WHERE AccountKey=? AND BudgetKind='google_request' AND Version=?",
                until,
                max(until, row["NextAllowedUTC"]),
                account,
                row["Version"],
            )

    def extend_cooldown(self, account, seconds):
        absolute = isinstance(seconds, datetime)
        if absolute and seconds.tzinfo is None:
            raise ValueError("HTTP-date cooldown must include a timezone.")
        if not absolute and (not isinstance(seconds, (int, float)) or not 0 < seconds <= 3600):
            raise ValueError("Bounded cooldown required.")
        with transaction(self.connect) as cursor:
            _mutex(cursor, "budget:" + account)
            cursor.execute("SELECT CAST(SYSUTCDATETIME() AS datetime2(3)) AS NowUTC")
            now = one(cursor)["NowUTC"]
            if absolute:
                seconds = min(
                    3600,
                    max(1, (seconds.astimezone(UTC).replace(tzinfo=None) - now).total_seconds()),
                )
            cursor.execute(
                "SELECT * FROM dbo.ExportRequestBudget WITH (UPDLOCK,HOLDLOCK) WHERE AccountKey=? AND BudgetKind='google_request'",
                account,
            )
            row = one(cursor)
            if not row:
                raise SourceConflict("A reservation must precede provider feedback.")
            until = max(row["CooldownUntilUTC"] or now, now + timedelta(seconds=seconds))
            _cas(
                cursor,
                "UPDATE dbo.ExportRequestBudget SET CooldownUntilUTC=?,Version=Version+1 OUTPUT inserted.Version WHERE AccountKey=? AND BudgetKind='google_request' AND Version=?",
                until,
                account,
                row["Version"],
            )
