"""Discover and fence retained all-KVK captures using their atomic producer checkpoint."""

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from services.export_coordination_dal import identity
from services.stats_import_outcome_dal import ImportExecutionActive, StatsImportOutcomeDAL


class AllKvkCaptureRecoveryDAL:
    consumer = "all_kvk"
    token = staticmethod(StatsImportOutcomeDAL.token)

    def __init__(self, connect, *, account, storage_owner):
        self.connect = connect
        self.account = account
        self.storage_owner = storage_owner

    def _scope(self, prep):
        if not prep or (prep["AccountKey"], prep["StorageOwner"], prep["ConsumerKind"]) != (
            self.account,
            self.storage_owner,
            self.consumer,
        ):
            raise SourceConflict("Exact runtime account, storage and all-KVK capture required.")

    @staticmethod
    def _snapshot(cursor, preparation_id):
        cursor.execute(
            "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
            preparation_id,
        )
        prep = one(cursor)
        cursor.execute(
            "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) "
            "WHERE ActivePreparationID=? ORDER BY ResourceKey",
            preparation_id,
        )
        return prep, None, rows(cursor)

    @staticmethod
    def capture_completed(prep, execution, resources):
        return bool(
            not resources
            and prep["State"] in {"captured", "materialized"}
            and prep["SpoolKey"]
            and prep["SpoolHash"]
            and prep["SpoolBytes"] > 0
        )

    @classmethod
    def action(cls, prep, execution, resources):
        if cls.capture_completed(prep, execution, resources):
            return "resolved" if prep["JobID"] else "queue_capture"
        if (
            prep["State"] not in {"committed", "uncertain"}
            or not prep["GenerationJson"]
            or prep["JobID"]
            or prep["SpoolKey"]
        ):
            raise SourceConflict("A committed producer checkpoint is required to finish capture.")
        if len(resources) != 1 or resources[0]["ResourceKey"] != "sql_snapshot:legacy_outputs":
            raise SourceConflict("The exact retained SQL snapshot reservation is required.")
        resource = resources[0]
        if (
            identity(resource["OwnerID"]),
            resource["Fence"],
            resource["ActiveJobID"],
            resource["ActiveOutputOperationID"],
        ) != (identity(prep["OwnerID"]), prep["Fence"], None, None):
            raise SourceConflict("Snapshot ownership changed; preserve the retained output.")
        return "resume_capture"

    def inspect(self, preparation_id):
        with transaction(self.connect) as cursor:
            # Conflicts with every legacy producer/capture session, including work
            # still running after a client timeout. Age is only a discovery hint.
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock "
                "@Resource=N'k98-legacy-output-snapshot',@LockMode='Exclusive',"
                "@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult"
            )
            result = one(cursor)
            if not result or result["LockResult"] < 0:
                raise ImportExecutionActive("A SQL producer or capture is still active.")
            prep, execution, resources = self._snapshot(cursor, identity(preparation_id))
            self._scope(prep)
            explanation = None
            try:
                action = self.action(prep, execution, resources)
            except SourceConflict as exc:
                action, explanation = "hold", str(exc)
            return dict(
                preparation=prep,
                execution=execution,
                resources=resources,
                action=action,
                token=self.token(prep, execution, resources),
                explanation=explanation,
                captured=self.capture_completed(prep, execution, resources),
            )

    def pending_recovery(self, *, after=None, limit=20):
        if type(limit) is not int or not 1 <= limit <= 25:
            raise ValueError("Bounded recovery discovery required.")
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) PreparationID FROM dbo.ExportPreparation "
                "WHERE AccountKey=? AND StorageOwner=? AND ConsumerKind='all_kvk' "
                "AND State IN ('writing','committed','uncertain','captured') AND JobID IS NULL "
                "AND UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()) "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,"
                "PreparationID",
                limit,
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["PreparationID"]) for row in rows(cursor)]
