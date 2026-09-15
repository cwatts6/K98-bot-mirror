"""S10C preparation ownership. Short CAS transactions and separate session guard.

No default connection, lease stealing, provider I/O, or best-effort evidence.
Unknown commits leave durable ownership blocked for authoritative reconciliation.
"""

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, transaction
from services.export_coordination_dal import _cas, _mutex, bounded_json


@dataclass(frozen=True)
class PreparationClaim:
    preparation_id: str
    account: str
    owner: str
    fence: int
    version: int
    resources: tuple[tuple[str, int], ...]


class LegacySnapshotDAL:
    def __init__(self, connect):
        self.connect = connect

    def request(self, *, account, consumer, kvk_no, request, storage_owner, actor, reason):
        if consumer not in {"all_kvk", "scan_data", "config"}:
            raise ValueError("Unknown preparation consumer.")
        if (consumer == "all_kvk" and (type(kvk_no) is not int or kvk_no <= 0)) or (
            consumer != "all_kvk" and kvk_no is not None
        ):
            raise ValueError("Invalid preparation season.")
        import re

        if any(
            not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", item) for item in (account, storage_owner)
        ):
            raise ValueError("Canonical account and storage owner required.")
        if not actor or len(actor) > 128 or not reason or len(reason) > 1024:
            raise ValueError("Bounded actor/reason required.")
        document = bounded_json(
            dict(consumer=consumer, kvk_no=kvk_no, request=request, storage_owner=storage_owner)
        )
        request_hash = digest(json.loads(document))
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + account)
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE AccountKey=? AND RequestHash=?",
                account,
                request_hash,
            )
            previous = one(cursor)
            if previous:
                return str(previous["PreparationID"]).lower()
            cursor.execute(
                "SELECT ISNULL(MAX(Ticket),0)+1 AS Ticket FROM (SELECT EnqueueSequence AS Ticket FROM dbo.ExportJob WHERE AccountKey=? UNION ALL SELECT EnqueueSequence FROM dbo.ExportPreparation WHERE AccountKey=?) q",
                account,
                account,
            )
            ticket = one(cursor)["Ticket"]
            identifier = str(uuid4())
            cursor.execute(
                "INSERT dbo.ExportPreparation (PreparationID,AccountKey,ConsumerKind,KVK_NO,RequestHash,EnqueueSequence,State,Fence,Version,StorageOwner,RequestJson,Actor,Reason,CreatedUTC,UpdatedUTC) VALUES (?,?,?,?,?,?,'pending',0,1,?,?,?, ?,SYSUTCDATETIME(),SYSUTCDATETIME())",
                identifier,
                account,
                consumer,
                kvk_no,
                request_hash,
                ticket,
                storage_owner,
                document,
                actor,
                reason,
            )
            return identifier

    def read(self, identifier):
        with transaction(self.connect) as cursor:
            cursor.execute("SELECT * FROM dbo.ExportPreparation WHERE PreparationID=?", identifier)
            result = one(cursor)
            if not result:
                raise SourceConflict("Preparation is unavailable.")
            return result

    def latest_ready(self, *, account, consumer, kvk_no, storage_owner):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) PreparationID,State FROM dbo.ExportPreparation WHERE AccountKey=? AND ConsumerKind=? AND (KVK_NO=? OR (KVK_NO IS NULL AND CAST(? AS int) IS NULL)) AND StorageOwner=? ORDER BY EnqueueSequence DESC,PreparationID",
                account,
                consumer,
                kvk_no,
                kvk_no,
                storage_owner,
            )
            result = one(cursor)
            if not result or result["State"] not in {"captured", "materialized"}:
                raise SourceConflict(
                    "No verified ready output capture; manual recomputation was not attempted."
                )
            return str(result["PreparationID"]).lower()

    def withdraw_unstarted(self, identifier):
        """Withdraw this refused operation, never reclaim an admitted/old writer.

        A synchronous producer has not executed at this point. An acknowledged
        CAS makes that explicit; a lost acknowledgment remains pending evidence.
        No lease, age or job-state inference is used to release resources.
        """
        observed = self.read(identifier)
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + observed["AccountKey"])
            _cas(
                cursor,
                "UPDATE p SET State='unavailable',OwnerID=COALESCE(OwnerID,?),Fence=Fence+1,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version FROM dbo.ExportPreparation p WHERE PreparationID=? AND AccountKey=? AND Version=? AND State IN ('pending','sql_pending') AND NOT EXISTS(SELECT 1 FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ActivePreparationID=p.PreparationID)",
                str(uuid4()),
                identifier,
                observed["AccountKey"],
                observed["Version"],
            )

    def claim(self, identifier, *, account, storage_owner, stage, resource_keys):
        transitions = {"preflight": "pending", "writing": "sql_pending"}
        if (
            stage not in transitions
            or not resource_keys
            or resource_keys != tuple(sorted(set(resource_keys)))
        ):
            raise ValueError("Canonical preparation stage/resources required.")
        if stage == "preflight" and resource_keys[0] != "account:" + account:
            raise ValueError("Account admission required before provider preflight.")
        if stage == "writing" and any(not k.startswith("sql_snapshot:") for k in resource_keys):
            raise ValueError("SQL stage cannot retain provider resources.")
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + account)
            resources = []
            for key in resource_keys:
                if len(key) > 256 or not key.startswith(
                    ("account:", "destination:", "sql_snapshot:")
                ):
                    raise ValueError("Invalid preparation resource.")
                _mutex(cursor, key)
                cursor.execute(
                    "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ResourceKey=?",
                    key,
                )
                resource = one(cursor)
                if resource is None:
                    cursor.execute(
                        "INSERT dbo.ExportResource(ResourceKey,ResourceKind,Fence,Version) VALUES (?,?,0,1)",
                        key,
                        key.split(":", 1)[0],
                    )
                    resource = dict(
                        ResourceKey=key,
                        ActiveJobID=None,
                        ActivePreparationID=None,
                        OwnerID=None,
                        Fence=0,
                        Version=1,
                        BlockedReason=None,
                    )
                if (
                    resource["ActiveJobID"] is not None
                    or resource["ActivePreparationID"] is not None
                    or resource["BlockedReason"]
                ):
                    return None
                resources.append(resource)
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
                identifier,
            )
            preparation = one(cursor)
            if not preparation or (
                preparation["AccountKey"],
                preparation["StorageOwner"],
                preparation["State"],
            ) != (account, storage_owner, transitions[stage]):
                raise SourceConflict("Preparation state/owner changed.")
            if stage == "preflight":
                cursor.execute(
                    "SELECT TOP (1) Ticket FROM (SELECT EnqueueSequence AS Ticket FROM dbo.ExportJob WHERE AccountKey=? AND State='ready' UNION ALL SELECT EnqueueSequence FROM dbo.ExportPreparation WHERE AccountKey=? AND State='pending') q WHERE Ticket<?",
                    account,
                    account,
                    preparation["EnqueueSequence"],
                )
                if one(cursor):
                    return None
            fence = max(preparation["Fence"], *(r["Fence"] for r in resources)) + 1
            owner = str(uuid4())
            version = _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State=?,OwnerID=?,Fence=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND Version=? AND State=?",
                stage,
                owner,
                fence,
                identifier,
                preparation["Version"],
                transitions[stage],
            )["Version"]
            claimed = []
            for resource in resources:
                key = resource["ResourceKey"]
                cursor.execute(
                    "IF NOT EXISTS(SELECT 1 FROM dbo.ExportPreparationResource WHERE PreparationID=? AND ResourceKey=?) INSERT dbo.ExportPreparationResource(PreparationID,ResourceKey) VALUES (?,?)",
                    identifier,
                    key,
                    identifier,
                    key,
                )
                rv = _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActivePreparationID=?,OwnerID=?,Fence=?,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActiveJobID IS NULL AND ActivePreparationID IS NULL AND BlockedReason IS NULL",
                    identifier,
                    owner,
                    fence,
                    key,
                    resource["Version"],
                )["Version"]
                claimed.append((key, rv))
            return PreparationClaim(identifier, account, owner, fence, version, tuple(claimed))

    def _authorize(self, cursor, claim):
        _mutex(cursor, "account:" + claim.account)
        for key, version in claim.resources:
            _mutex(cursor, key)
            cursor.execute(
                "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ResourceKey=?", key
            )
            r = one(cursor)
            if not r or (
                str(r["ActivePreparationID"]).lower(),
                r["ActiveJobID"],
                str(r["OwnerID"]).lower(),
                r["Fence"],
                r["Version"],
                r["BlockedReason"],
            ) != (claim.preparation_id, None, claim.owner, claim.fence, version, None):
                raise SourceConflict("Preparation resource ownership changed.")
        cursor.execute(
            "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
            claim.preparation_id,
        )
        row = one(cursor)
        if not row or (
            row["AccountKey"],
            str(row["OwnerID"]).lower(),
            row["Fence"],
            row["Version"],
        ) != (
            claim.account,
            claim.owner,
            claim.fence,
            claim.version,
        ):
            raise SourceConflict("Preparation owner/fence/version changed.")
        return row

    def authorize(self, claim):
        with transaction(self.connect) as cursor:
            return self._authorize(cursor, claim)

    def transition(
        self, claim, *, expected, state, generation=None, release=False, external_cursor=None
    ):
        allowed = {
            ("preflight", "sql_pending"),
            ("preflight", "completed"),
            ("writing", "committed"),
            ("writing", "completed"),
            ("writing", "unavailable"),
            ("committed", "unavailable"),
            ("committed", "committed"),
        }
        if (expected, state) not in allowed:
            raise ValueError("Unsupported preparation transition.")
        if state == "committed" and generation is None:
            raise ValueError("Committed generation proof required.")
        # A producer may append its completion to its existing transaction. This
        # DAL neither commits nor closes that cursor; UPDATE_ALL2 uses no ambient
        # transaction and records its acknowledged completion separately.
        with (
            nullcontext(external_cursor)
            if external_cursor is not None
            else transaction(self.connect)
        ) as cursor:
            row = self._authorize(cursor, claim)
            if row["State"] != expected:
                raise SourceConflict("Preparation phase changed.")
            if expected == state == "committed":
                previous = json.loads(row["GenerationJson"])
                if (
                    previous.get("capture") != "pending"
                    or generation.get("capture") != "complete"
                    or any(
                        previous.get(k) != generation.get(k)
                        for k in ("commit_identity", "registration_sha256", "completion")
                    )
                ):
                    raise SourceConflict("Committed generation evidence cannot be replaced.")
            version = _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State=?,GenerationJson=COALESCE(?,GenerationJson),Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND OwnerID=? AND Fence=? AND Version=? AND State=?",
                state,
                bounded_json(generation) if generation is not None else None,
                claim.preparation_id,
                claim.owner,
                claim.fence,
                claim.version,
                expected,
            )["Version"]
            if release:
                self._release(cursor, claim)
            return PreparationClaim(
                claim.preparation_id,
                claim.account,
                claim.owner,
                claim.fence,
                version,
                () if release else claim.resources,
            )

    def _release(self, cursor, claim):
        for key, version in claim.resources:
            _cas(
                cursor,
                "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? AND Version=? AND ActiveJobID IS NULL AND BlockedReason IS NULL",
                key,
                claim.preparation_id,
                claim.owner,
                claim.fence,
                version,
            )

    def uncertain(self, claim):
        with transaction(self.connect) as cursor:
            self._authorize(cursor, claim)
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='uncertain',Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND OwnerID=? AND Fence=? AND Version=?",
                claim.preparation_id,
                claim.owner,
                claim.fence,
                claim.version,
            )
            for key, version in claim.resources:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET BlockedReason='Preparation requires authoritative reconciliation',Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? AND Version=?",
                    key,
                    claim.preparation_id,
                    claim.owner,
                    claim.fence,
                    version,
                )

    def captured(self, claim, receipt):
        with transaction(self.connect) as cursor:
            row = self._authorize(cursor, claim)
            if row["State"] != "committed" or row["StorageOwner"] != receipt.storage_owner:
                raise SourceConflict("Capture is not the committed owned generation.")
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='captured',SpoolKey=?,SpoolBytes=?,SpoolHash=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND OwnerID=? AND Fence=? AND Version=? AND State='committed' AND SpoolKey IS NULL",
                receipt.key,
                receipt.byte_count,
                bytes.fromhex(receipt.sha256),
                claim.preparation_id,
                claim.owner,
                claim.fence,
                claim.version,
            )
            self._release(cursor, claim)

    @contextmanager
    def session(self, claim, connection):
        """Only the producer acquires this; nested helpers receive its token.

        The connection must remain open and autocommit at entry/exit. Procedure
        transactions are owned by the existing writer, never by this guard.
        """
        self.authorize(claim)
        if not connection.autocommit:
            raise ValueError("Session admission requires an autocommit connection.")
        cursor = connection.cursor()
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; IF @r<0 THROW 51421,'Legacy snapshot busy',1;"
        )
        try:
            yield claim
        finally:
            # Releasing this SQL session lock never releases durable ownership.
            cursor.execute(
                "EXEC sys.sp_releaseapplock @Resource=N'k98-legacy-output-snapshot',@LockOwner='Session';"
            )
            cursor.close()

    @staticmethod
    def capture_result_sets(cursor, names):
        from services.legacy_export_snapshot_service import OutputSection, SnapshotUnavailable

        result = []
        while True:
            if cursor.description is not None:
                if len(result) >= len(names):
                    raise SnapshotUnavailable("Unexpected export result set.")
                columns = tuple(c[0] for c in cursor.description)
                result.append(
                    OutputSection(
                        names[len(result)], columns, tuple(tuple(r) for r in cursor.fetchall())
                    )
                )
            if not cursor.nextset():
                break
        if len(result) != len(names):
            raise SnapshotUnavailable("Missing export result set, including empty headers.")
        return tuple(result)

    @staticmethod
    def capture_outputs(connection, scope):
        """Read all mutable output under producer admission; no provider or rebuild."""
        import pandas as pd

        import gsheet_module as gm
        from services.legacy_export_snapshot_service import OutputSection

        cursor = connection.cursor()
        try:
            if scope["consumer"] == "all_kvk":
                cursor.execute("EXEC KVK.sp_KVK_Get_Exports @KVK_NO=?", scope["kvk_no"])
                raw = LegacySnapshotDAL.capture_result_sets(cursor, gm.KVK_EXPORT_SECTION_NAMES)
                frames = [pd.DataFrame(s.rows, columns=s.columns) for s in raw]
                return gm.plan_legacy_outputs(scope, frames=frames)
            results = []
            from constants import CONFIG_FILE

            with open(CONFIG_FILE, encoding="utf-8") as stream:
                allowed = frozenset(j["query"] for j in json.load(stream))
            for index, export in enumerate(scope["exports"]):
                # This is reviewed operator configuration, never a command query.
                # Validate its exact table/projection against the checked-in plan.
                if export["query"] not in allowed:
                    raise SourceConflict("Scan query is not in the reviewed export configuration.")
                cursor.execute(export["query"])
                columns = tuple(c[0] for c in cursor.description)
                results.append(
                    OutputSection(str(index), columns, tuple(tuple(r) for r in cursor.fetchall()))
                )
            return gm.plan_legacy_outputs(
                scope, frames=[pd.DataFrame(s.rows, columns=s.columns) for s in results]
            )
        finally:
            cursor.close()
