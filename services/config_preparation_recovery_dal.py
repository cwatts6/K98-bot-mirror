"""Operational CAS for one verified empty configuration preparation.

Uses existing S10C/S11 objects; no schema migration, automatic worker or retry.
"""

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity as identifier


class ConfigPreparationRecoveryDAL:
    def __init__(self, connect):
        self.connect = connect

    def identity(self):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS server, DB_NAME() AS [database]"
            )
            return one(cursor)

    def pending_recovery(self, *, account, storage_owner, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) PreparationID FROM dbo.ExportPreparation WHERE AccountKey=? "
                "AND StorageOwner=? AND ConsumerKind='config' AND State IN ('preflight','uncertain') "
                "AND UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()) "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                account,
                storage_owner,
                identifier(after) if after else None,
            )
            return [identifier(row["PreparationID"]) for row in rows(cursor)]

    def target_data(self, preparation_id, *, account, storage_owner):
        """Select a target from the registered database; callers cannot supply ownership."""
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE PreparationID=? AND AccountKey=? "
                "AND StorageOwner=? AND ConsumerKind='config'",
                identifier(preparation_id),
                account,
                storage_owner,
            )
            preparation = one(cursor)
            if not preparation:
                raise SourceConflict("Configuration read is outside the registered recovery scope.")
            cursor.execute(
                "SELECT ResourceKey,Version,ActivePreparationID FROM dbo.ExportResource "
                "WHERE ActivePreparationID=? ORDER BY ResourceKey",
                identifier(preparation_id),
            )
            resources = rows(cursor)
            cursor.execute(
                "SELECT StreamID FROM dbo.ExportExecutionStream WHERE PreparationID=? "
                "ORDER BY CONVERT(varchar(36),StreamID)",
                identifier(preparation_id),
            )
            return _wire(
                dict(
                    preparation=preparation,
                    resources=resources,
                    stream_ids=[identifier(row["StreamID"]) for row in rows(cursor)],
                )
            )

    def _snapshot(self, cursor, target):
        # Same account -> sorted resources -> owner lock order as normal admission.
        _mutex(cursor, "account:" + target.account)
        for key, _ in target.resources:
            _mutex(cursor, key)
        cursor.execute(
            "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS server, DB_NAME() AS [database]"
        )
        identity = one(cursor)
        if (identity["server"].casefold(), identity["database"]) != (
            target.server.casefold(),
            target.database,
        ):
            raise SourceConflict("Recovery SQL target differs.")
        cursor.execute(
            "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
            target.preparation_id,
        )
        preparation = one(cursor)
        cursor.execute(
            "SELECT ResourceKey FROM dbo.ExportPreparationResource WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=? ORDER BY ResourceKey",
            target.preparation_id,
        )
        membership = [r["ResourceKey"] for r in rows(cursor)]
        # Include unexpected owned resources too; a partial key list cannot unlock.
        cursor.execute(
            "SELECT r.* FROM dbo.ExportResource r WITH (UPDLOCK,HOLDLOCK) WHERE "
            "r.ActivePreparationID=? OR EXISTS (SELECT 1 FROM dbo.ExportPreparationResource m "
            "WITH (UPDLOCK,HOLDLOCK) WHERE m.PreparationID=? AND m.ResourceKey=r.ResourceKey) ORDER BY r.ResourceKey",
            target.preparation_id,
            target.preparation_id,
        )
        resources = rows(cursor)
        cursor.execute(
            "SELECT s.* FROM dbo.ExportExecutionStream s WITH (UPDLOCK,HOLDLOCK) WHERE "
            "s.PreparationID=? OR s.ActiveAccountKey=? OR (s.State<>'closed' AND EXISTS ("
            "SELECT 1 FROM OPENJSON(s.ScopeJson,'$.resources') WITH (ResourceKey varchar(256) '$.key') x "
            "JOIN dbo.ExportPreparationResource m ON m.ResourceKey=x.ResourceKey COLLATE Latin1_General_100_BIN2 "
            "WHERE m.PreparationID=?)) ORDER BY CONVERT(varchar(36),s.StreamID)",
            target.preparation_id,
            target.account,
            target.preparation_id,
        )
        streams = rows(cursor)
        cursor.execute(
            "SELECT COUNT_BIG(*) AS n FROM dbo.ExportProviderRequest r WITH (UPDLOCK,HOLDLOCK) "
            "JOIN dbo.ExportExecutionStream s ON s.StreamID=r.StreamID WHERE s.PreparationID=?",
            target.preparation_id,
        )
        requests = one(cursor)["n"]
        cursor.execute(
            "SELECT COUNT_BIG(*) AS n FROM dbo.ExportProviderRequestEvent e WITH (UPDLOCK,HOLDLOCK) "
            "JOIN dbo.ExportProviderRequest r ON r.RequestID=e.RequestID "
            "JOIN dbo.ExportExecutionStream s ON s.StreamID=r.StreamID WHERE s.PreparationID=?",
            target.preparation_id,
        )
        result = _wire(
            dict(
                **identity,
                preparation=preparation,
                membership=membership,
                resources=resources,
                streams=streams,
                request_count=requests,
                event_count=one(cursor)["n"],
            )
        )
        for stream in result["streams"]:
            for column in (
                "StreamID",
                "SessionID",
                "ChildIdentity",
                "ClosureReference",
                "NestedToken",
                "OutputOperationID",
            ):
                if stream[column] is not None:
                    stream[column] = str(stream[column]).lower()
        return result

    def snapshot(self, target):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, target)

    def settle(self, target, expected, audit):
        if not audit.get("actor") or not audit.get("reason"):
            raise ValueError("Recovery requires an actor and reason.")
        evidence = bounded_json(audit)
        with transaction(self.connect) as cursor:
            if self._snapshot(cursor, target) != expected:
                raise SourceConflict("Recovery raced with current state; no claims released.")
            # Unavailable records an abandoned read, never successful health.
            # Owner/fence and immutable membership remain as historical evidence.
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='unavailable',GenerationJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE PreparationID=? AND OwnerID=? AND Fence=? AND Version=? AND State IN ('preflight','uncertain') "
                "AND ConsumerKind='config' AND KVK_NO IS NULL AND JobID IS NULL AND GenerationJson IS NULL",
                evidence,
                target.preparation_id,
                target.owner,
                target.fence,
                target.version,
            )
            for key, version in target.resources:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,Version=Version+1 "
                    "OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? AND Version=? "
                    "AND ActiveJobID IS NULL AND ActiveOutputOperationID IS NULL "
                    "AND (BlockedReason IS NULL OR BlockedReason=N'Preparation requires authoritative reconciliation')",
                    key,
                    target.preparation_id,
                    target.owner,
                    target.fence,
                    version,
                )
