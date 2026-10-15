"""Durable refused-stage discovery using existing immutable preparation inputs."""

from contextlib import contextmanager
from contextvars import ContextVar
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.producer_recovery_intent import validate_inputs

_serialized_source = ContextVar("serialized_refused_producer", default=None)


class ProducerRefusalDAL:
    def __init__(self, runtime):
        self.runtime, self.connect = runtime, runtime.dal.connect
        self.account, self.storage_owner = runtime.account, runtime.store.storage_owner

    def pending(self, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (100) PreparationID FROM dbo.ExportPreparation "
                "WHERE AccountKey=? AND StorageOwner=? AND State='unavailable' "
                "AND Version IN (2,4) AND GenerationJson IS NULL "
                "AND JSON_VALUE(RequestJson,'$.request.producer.parent') IS NULL "
                "AND JSON_VALUE(RequestJson,'$.request.producer.kind')='stats_import' "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(r["PreparationID"]) for r in rows(cursor)]

    def snapshot(self, source_id):
        source_id = identity(source_id)
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE PreparationID=? AND AccountKey=? AND StorageOwner=?",
                source_id,
                self.account,
                self.storage_owner,
            )
            prep = one(cursor)
            if prep is None:
                raise SourceConflict("Refused stage is outside registered custody.")
            cursor.execute(
                "SELECT ResourceKey FROM dbo.ExportPreparationResource WHERE PreparationID=? ORDER BY ResourceKey",
                source_id,
            )
            membership = [r["ResourceKey"] for r in rows(cursor)]
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportResource WHERE ActivePreparationID=?",
                source_id,
            )
            held = one(cursor)["n"]
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportExecutionStream WHERE PreparationID=?",
                source_id,
            )
            streams = one(cursor)["n"]
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.StatsImportExecution WHERE PreparationID=?",
                source_id,
            )
            execution = one(cursor)["n"]
            cursor.execute(
                "SELECT TOP (101) p.*,e.State AS ExecutionState,e.CompletedFileName,e.Resolution,"
                "(SELECT COUNT(*) FROM dbo.ExportResource r WHERE r.ActivePreparationID=p.PreparationID) AS HeldCount,"
                "(SELECT COUNT(*) FROM dbo.ExportExecutionStream s WHERE s.PreparationID=p.PreparationID) AS StreamCount "
                "FROM dbo.ExportPreparation p LEFT JOIN dbo.StatsImportExecution e ON e.PreparationID=p.PreparationID "
                "WHERE p.AccountKey=? AND p.StorageOwner=? "
                "AND JSON_VALUE(p.RequestJson,'$.request.producer.parent')=? ORDER BY p.EnqueueSequence,p.PreparationID",
                self.account,
                self.storage_owner,
                source_id,
            )
            attempts = rows(cursor)
            cursor.execute(
                "SELECT r.ResourceKey,r.ActiveJobID,r.ActivePreparationID,r.ActiveOutputOperationID,r.BlockedReason,"
                "p.ConsumerKind,p.State AS PreparationState,j.State AS JobState,"
                "p.AccountKey AS PreparationAccount,j.AccountKey AS JobAccount,o.AccountKey AS OperationAccount "
                "FROM dbo.ExportResource r LEFT JOIN dbo.ExportPreparation p ON p.PreparationID=r.ActivePreparationID "
                "LEFT JOIN dbo.ExportJob j ON j.JobID=r.ActiveJobID "
                "LEFT JOIN KVK.SourceOutputOperation o ON o.OperationID=r.ActiveOutputOperationID "
                "WHERE r.ResourceKey IN (?,?) AND (r.OwnerID IS NOT NULL OR r.BlockedReason IS NOT NULL)",
                "account:" + self.account,
                "sql_snapshot:legacy_outputs",
            )
            blockers = rows(cursor)
        document = json.loads(prep["RequestJson"])
        producer = document.get("request", {}).get("producer", {})
        validate_inputs(producer.get("inputs"))
        if (
            prep["ConsumerKind"] != "scan_data"
            or prep["State"] != "unavailable"
            or prep["Version"] not in {2, 4}
            or any(
                prep[k] is not None
                for k in ("GenerationJson", "SpoolKey", "SpoolBytes", "SpoolHash", "JobID")
            )
            or held
            or streams
            or execution
            or membership != ([] if prep["Version"] == 2 else ["account:" + self.account])
            or bytes(prep["RequestHash"]) != digest(document)
            or document.get("consumer") != "scan_data"
            or document.get("storage_owner") != self.storage_owner
            or document.get("request", {}).get("kind") != "scan_data"
            or producer.get("kind") != "stats_import"
            or producer.get("operation") != document["request"].get("operation")
        ):
            raise SourceConflict("Exact withdrawn stage with no producer execution is required.")
        identity(producer["operation"])
        if len(attempts) > 100:
            raise SourceConflict("Refused-stage attempt history exceeds its verification bound.")
        for attempt in attempts:
            child = json.loads(attempt["RequestJson"])
            expected = dict(document)
            expected["request"] = dict(document["request"])
            operation = identity(child["request"]["operation"])
            expected["request"].update(
                operation=operation,
                producer=dict(producer, parent=source_id, operation=operation),
            )
            if (
                child != expected
                or bytes(attempt["RequestHash"]) != digest(child)
                or attempt["ConsumerKind"] != "scan_data"
                or attempt["KVK_NO"] is not None
                or (
                    attempt["ExecutionState"] is not None
                    and attempt["CompletedFileName"] != producer["inputs"]["completed_filename"]
                )
            ):
                raise SourceConflict("Recovery attempt differs from the retained producer inputs.")
        # Global SQL contention may belong to another registered account. Do not
        # turn it into a link that adopts another account's recovery authority.
        for blocker in blockers:
            if blocker.pop("PreparationAccount") != self.account:
                blocker["ActivePreparationID"] = None
            if blocker.pop("JobAccount") != self.account:
                blocker["ActiveJobID"] = None
            if blocker.pop("OperationAccount") != self.account:
                blocker["ActiveOutputOperationID"] = None
        return _wire(
            dict(preparation=prep, producer=producer, attempts=attempts, blockers=blockers)
        )

    @contextmanager
    def serialized(self, source_id):
        """Exclude a live recovery dispatcher, including its drained worker threads."""
        connection = self.connect()
        connection.autocommit = True
        cursor = connection.cursor()
        resource = "k98-producer-recovery:" + identity(source_id)
        acquired = False
        try:
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',"
                "@LockOwner='Session',@LockTimeout=0; SELECT @r AS LockResult",
                resource,
            )
            acquired = one(cursor)["LockResult"] >= 0
            if not acquired:
                from services.stats_import_outcome_dal import ImportExecutionActive

                raise ImportExecutionActive("The confirmed continuation is still running.")
            token = _serialized_source.set((self, identity(source_id)))
            try:
                yield
            finally:
                _serialized_source.reset(token)
        finally:
            try:
                if acquired:
                    cursor.execute(
                        "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", resource
                    )
            finally:
                cursor.close()
                connection.close()

    def reserve(self, source_id, action_id):
        """A stable request is also a tombstone against late action dispatch."""
        self._require_serialized(source_id)
        state = self.snapshot(source_id)
        document = json.loads(state["preparation"]["RequestJson"])
        request = dict(document["request"])
        request.update(
            operation=identity(action_id),
            producer=dict(
                state["producer"], parent=identity(source_id), operation=identity(action_id)
            ),
        )
        return self.runtime.dal.request(
            account=self.account,
            consumer="scan_data",
            kvk_no=None,
            request=request,
            storage_owner=self.storage_owner,
            actor="recovery:" + identity(action_id),
            reason="Resume confirmed unstarted SQL stage",
        )

    def close_unused(self, source_id, action_id):
        """Called only under serialized(). Fence an attempt that never registered SQL.

        Both SQL execution guards and exact row ownership are checked in the same
        transaction as release. A receipt, stream or generation excludes this path.
        The durable marker prevents a late dispatcher from reusing this action.
        """
        self._require_serialized(source_id)
        state = self.snapshot(source_id)
        candidates = [
            p
            for p in state["attempts"]
            if json.loads(p["RequestJson"])["request"]["operation"] == identity(action_id)
        ]
        if len(candidates) != 1:
            raise SourceConflict("One exact continuation reservation is required.")
        candidate = candidates[0]
        identifier = identity(candidate["PreparationID"])
        marker = dict(
            producer_refusal_closed=dict(parent=identity(source_id), action=identity(action_id))
        )
        with transaction(self.connect) as cursor:
            from services.stats_import_outcome_dal import StatsImportOutcomeDAL

            StatsImportOutcomeDAL._idle(cursor, identifier)
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',"
                "@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult"
            )
            if one(cursor)["LockResult"] < 0:
                raise SourceConflict("A producer still holds the SQL execution guard.")
            _mutex(cursor, "account:" + self.account)
            _mutex(cursor, "sql_snapshot:legacy_outputs")
            prep, execution, resources = StatsImportOutcomeDAL._snapshot(cursor, identifier)
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportExecutionStream WHERE PreparationID=?",
                identifier,
            )
            streams = one(cursor)["n"]
            if (
                not prep
                or prep["Version"] != candidate["Version"]
                or prep["AccountKey"] != self.account
                or prep["StorageOwner"] != self.storage_owner
                or prep["ConsumerKind"] != "scan_data"
                or execution
                or streams
                or any(
                    prep[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID")
                )
            ):
                return False
            if prep["GenerationJson"] is not None:
                return (
                    prep["State"] == "unavailable"
                    and not resources
                    and json.loads(prep["GenerationJson"]) == marker
                )
            if prep["State"] not in {
                "pending",
                "preflight",
                "sql_pending",
                "writing",
                "uncertain",
                "unavailable",
            }:
                return False
            for r in resources:
                if (
                    r["ResourceKey"]
                    not in {"account:" + self.account, "sql_snapshot:legacy_outputs"}
                    or identity(r["OwnerID"]) != identity(prep["OwnerID"])
                    or r["Fence"] != prep["Fence"]
                    or r["ActiveJobID"] is not None
                    or r["ActiveOutputOperationID"] is not None
                ):
                    raise SourceConflict("Continuation ownership changed; release refused.")
            if any(r["ResourceKey"] == "account:" + self.account for r in resources):
                self.runtime.dal._execution_gate(cursor, self.account)
            for r in resources:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,"
                    "Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? "
                    "AND OwnerID=? AND Fence=? AND Version=?",
                    r["ResourceKey"],
                    identifier,
                    prep["OwnerID"],
                    prep["Fence"],
                    r["Version"],
                )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='unavailable',OwnerID=COALESCE(OwnerID,?),"
                "Fence=Fence+1,Version=Version+1,GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE PreparationID=? AND Version=?",
                identity(action_id),
                bounded_json(marker),
                identifier,
                prep["Version"],
            )
            return True

    def _require_serialized(self, source_id):
        if _serialized_source.get() != (self, identity(source_id)):
            raise SourceConflict("Exact continuation dispatcher exclusion required.")
