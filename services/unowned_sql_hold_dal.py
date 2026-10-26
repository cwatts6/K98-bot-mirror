"""Exact disposition of an unowned SQL blocker, never release a durable owner."""

import json
from uuid import NAMESPACE_URL, uuid5

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_contention import retry_coordination, transaction as retry_transaction
from services.export_coordination_dal import _cas, _mutex, identity
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL

RESOURCE = "sql_snapshot:legacy_outputs"


def source_id(account, storage_owner):
    return str(uuid5(NAMESPACE_URL, json.dumps(["k98-unowned-sql-hold/1", account, storage_owner])))


class WriterGuards(ImportCaptureRecoveryDAL):
    def guards(self, preparation_id):
        return ("k98-legacy-output-snapshot", "K98:post-import-stats:v1")


class UnownedSqlHoldDAL:
    def __init__(self, runtime):
        self.connect = runtime.dal.connect
        self.account, self.storage_owner = runtime.account, runtime.store.storage_owner
        self.source_id = source_id(self.account, self.storage_owner)

    def _scope(self, source):
        if identity(source) != self.source_id:
            raise SourceConflict("Exact account-scoped SQL hold required.")

    def pending(self, after=None):
        state = self.snapshot(self.source_id)
        return [self.source_id] if state["resource"] and state["resource"]["BlockedReason"] else []

    def _snapshot(self, cursor):
        _mutex(cursor, "account:" + self.account)
        _mutex(cursor, RESOURCE)
        cursor.execute(
            "SELECT * FROM dbo.ExportResource WITH(UPDLOCK,HOLDLOCK) WHERE ResourceKey=?", RESOURCE
        )
        resource = one(cursor)
        # Global SQL outputs are shared. Foreign and contradictory durable
        # owners remain blockers even if their resource pointer was cleared.
        cursor.execute(
            "SELECT TOP(101) p.PreparationID,p.AccountKey,p.StorageOwner,p.ConsumerKind,p.State,p.Version,"
            "JSON_VALUE(p.RequestJson,'$.request.producer.kind') AS ProducerKind "
            "FROM dbo.ExportPreparation p WITH(UPDLOCK,HOLDLOCK) "
            "LEFT JOIN dbo.StatsImportExecution e WITH(UPDLOCK,HOLDLOCK) ON e.PreparationID=p.PreparationID "
            "WHERE EXISTS(SELECT 1 FROM dbo.ExportPreparationResource m WITH(HOLDLOCK) "
            "WHERE m.PreparationID=p.PreparationID AND m.ResourceKey=?) "
            "AND (p.State IN ('writing','committed','uncertain') OR (e.Resolution IS NULL "
            "AND e.State IN ('prepared','running','import_committed','partial'))) ORDER BY p.PreparationID",
            RESOURCE,
        )
        producers = rows(cursor)
        cursor.execute(
            "SELECT COUNT_BIG(*) AS n FROM dbo.ExportExecutionStream WITH(UPDLOCK,HOLDLOCK) "
            "WHERE ActiveAccountKey IS NOT NULL OR State IN ('open','frozen')"
        )
        streams = one(cursor)["n"]
        cursor.execute(
            "SELECT TOP(1) * FROM dbo.ExportUnownedHoldDisposition WHERE AccountKey=? AND StorageOwner=? "
            "ORDER BY AfterVersion DESC",
            self.account,
            self.storage_owner,
        )
        return _wire(
            dict(resource=resource, producers=producers, streams=streams, disposition=one(cursor))
        )

    @retry_coordination(budget_seconds=5)
    def snapshot(self, source):
        self._scope(source)
        with retry_transaction(self.connect) as cursor:
            return self._snapshot(cursor)

    @staticmethod
    def eligible(state):
        row = state["resource"]
        return bool(
            row
            and row["ResourceKind"] == "sql_snapshot"
            and row["BlockedReason"]
            and all(
                row[key] is None
                for key in (
                    "OwnerID",
                    "ActiveJobID",
                    "ActivePreparationID",
                    "ActiveOutputOperationID",
                )
            )
            and not state["producers"]
            and not state["streams"]
        )

    def action(self, action_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportUnownedHoldDisposition WHERE ActionID=? AND AccountKey=? AND StorageOwner=?",
                identity(action_id),
                self.account,
                self.storage_owner,
            )
            row = one(cursor)
            if row is None:
                return None
            saved = _wire(row)
            before = json.loads(saved["BeforeJson"])
            cursor.execute("SELECT * FROM dbo.ExportResource WHERE ResourceKey=?", RESOURCE)
            current = one(cursor)
            if (
                saved["ResourceKey"] != RESOURCE
                or before.get("ResourceKey") != RESOURCE
                or before.get("ResourceKind") != "sql_snapshot"
                or not before.get("BlockedReason")
                or any(
                    before.get(key) is not None
                    for key in (
                        "OwnerID",
                        "ActiveJobID",
                        "ActivePreparationID",
                        "ActiveOutputOperationID",
                    )
                )
                or type(before.get("Version")) is not int
                or saved["AfterVersion"] != before["Version"] + 1
                or saved["Actor"] != "recovery:" + identity(action_id)
                or current is None
                or current["Version"] < saved["AfterVersion"]
                or (
                    current["Version"] == saved["AfterVersion"]
                    and _wire(current)
                    != dict(before, Version=saved["AfterVersion"], BlockedReason=None)
                )
            ):
                raise SourceConflict(
                    "The saved unowned-hold disposition does not independently verify."
                )
            return saved

    def clear(self, source, *, token, actor, reason):
        self._scope(source)
        action_id = identity(actor.removeprefix("recovery:"))
        if (
            actor != "recovery:" + action_id
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise SourceConflict("Confirmed explicit unowned-hold disposition required.")
        saved = self.action(action_id)
        if saved:
            if saved["ReviewHash"] != token or saved["Actor"] != actor or saved["Reason"] != reason:
                raise SourceConflict("Another decision owns this hold disposition.")
            return saved
        with WriterGuards(self).session(source) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                state = self._snapshot(cursor)
                cursor.execute(
                    "DECLARE @r int; EXEC dbo.ACQUIRE_KS4_IMPORT_LOCK @LockTimeout=0,@LockResult=@r OUTPUT; SELECT @r AS LockResult"
                )
                lock = one(cursor)
                if not lock or lock["LockResult"] < 0:
                    raise SourceConflict("A scan writer remains active; preserve the blocker.")
                if not self.eligible(state) or digest(state).hex() != token:
                    raise SourceConflict("Ownership or SQL hold evidence changed; review again.")
                before = state["resource"]
                after = _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET BlockedReason=NULL,Version=Version+1 OUTPUT inserted.Version "
                    "WHERE ResourceKey=? AND Version=? AND Fence=? AND BlockedReason=? AND OwnerID IS NULL "
                    "AND ActiveJobID IS NULL AND ActivePreparationID IS NULL AND ActiveOutputOperationID IS NULL",
                    RESOURCE,
                    before["Version"],
                    before["Fence"],
                    before["BlockedReason"],
                )["Version"]
                cursor.execute(
                    "INSERT dbo.ExportUnownedHoldDisposition(ActionID,AccountKey,StorageOwner,ResourceKey,ReviewHash,BeforeJson,"
                    "AfterVersion,Actor,Reason) VALUES(?,?,?,?,?,?,?,?,?)",
                    action_id,
                    self.account,
                    self.storage_owner,
                    RESOURCE,
                    bytes.fromhex(token),
                    json.dumps(before, sort_keys=True, separators=(",", ":")),
                    after,
                    actor,
                    reason,
                )
                cursor.execute("COMMIT TRANSACTION")
            except BaseException:
                try:
                    cursor.execute("IF @@TRANCOUNT>0 ROLLBACK")
                except Exception:
                    pass
                raise
            finally:
                cursor.close()
        return self.action(action_id)
