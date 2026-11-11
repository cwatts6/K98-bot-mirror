"""Exact rollover-owner snapshots and atomic permanent target fencing."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL, _wire
from services.config_read_containment import stream_wire
from services.export_coordination_dal import _mutex, identity
from services.export_target_containment_dal import ExportTargetContainmentDAL


class RolloverContainmentDAL(ExportTargetContainmentDAL):
    @staticmethod
    def _snapshot(cursor, operation_id, account, pool_id):
        _mutex(cursor, "account:" + account)
        cursor.execute(
            "SELECT ResourceKey FROM KVK.SourceOutputOperationResource WHERE OperationID=? "
            "UNION SELECT ResourceKey FROM dbo.ExportResource WHERE ActiveOutputOperationID=? ORDER BY ResourceKey",
            operation_id,
            operation_id,
        )
        keys = [r["ResourceKey"] for r in rows(cursor)]
        for key in keys:
            _mutex(cursor, key)
        _mutex(cursor, "pool:" + pool_id)
        cursor.execute(
            "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS server,DB_NAME() AS [database],USER_NAME() AS principal"
        )
        target = one(cursor)
        cursor.execute(
            "SELECT * FROM KVK.SourceOutputOperation WITH(UPDLOCK,HOLDLOCK) WHERE OperationID=?",
            operation_id,
        )
        operation = one(cursor)
        if (
            operation is None
            or operation["AccountKey"] != account
            or identity(operation["PoolID"]) != pool_id
        ):
            raise SourceConflict("Exact registered rollover containment owner required.")
        cursor.execute(
            "SELECT ResourceKey FROM KVK.SourceOutputOperationResource WITH(UPDLOCK,HOLDLOCK) WHERE OperationID=? ORDER BY ResourceKey",
            operation_id,
        )
        membership = [r["ResourceKey"] for r in rows(cursor)]
        if keys != membership:
            raise SourceConflict("Unexpected rollover reservation prevents partial containment.")
        cursor.execute(
            "SELECT r.* FROM dbo.ExportResource r WITH(UPDLOCK,HOLDLOCK) JOIN KVK.SourceOutputOperationResource m ON m.ResourceKey=r.ResourceKey WHERE m.OperationID=? ORDER BY r.ResourceKey",
            operation_id,
        )
        resources = rows(cursor)
        cursor.execute(
            "SELECT * FROM dbo.ExportExecutionStream WITH(UPDLOCK,HOLDLOCK) WHERE OutputOperationID=? OR ActiveAccountKey=? ORDER BY CONVERT(varchar(36),StreamID)",
            operation_id,
            account,
        )
        streams = [stream_wire(s) for s in rows(cursor)]
        cursor.execute(
            "SELECT a.SessionID,a.AuthorityPrincipal FROM dbo.ExportExecutionSession a WHERE EXISTS(SELECT 1 FROM dbo.ExportExecutionStream s WHERE s.OutputOperationID=? AND s.SessionID=a.SessionID) ORDER BY CONVERT(varchar(36),a.SessionID)",
            operation_id,
        )
        sessions = [
            dict(SessionID=identity(r["SessionID"]), AuthorityPrincipal=r["AuthorityPrincipal"])
            for r in rows(cursor)
        ]
        pool = SourceOutputPoolDAL._snapshot(cursor, pool_id)
        cursor.execute(
            "SELECT * FROM dbo.ExportTargetContainment WITH(UPDLOCK,HOLDLOCK) WHERE OutputOperationID=?",
            operation_id,
        )
        return _wire(
            dict(
                **target,
                operation=operation,
                membership=membership,
                resources=resources,
                streams=streams,
                sessions=sessions,
                pool=pool,
                receipt=one(cursor),
            )
        )

    def snapshot(self, operation_id, *, account, pool_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, identity(operation_id), account, identity(pool_id))

    def settle(
        self,
        expected,
        *,
        containment_id,
        snapshot_hash,
        receipt,
        seals,
        actor,
        reason,
        registration_hash,
    ):
        op, pool = expected["operation"], expected["pool"]["pool"]
        with transaction(self.connect) as cursor:
            if (
                self._snapshot(cursor, op["OperationID"], op["AccountKey"], pool["PoolID"])
                != expected
            ):
                raise SourceConflict("Rollover evidence changed; no ownership was released.")
            cursor.execute(
                "EXEC dbo.usp_ExportRolloverContainTargets @ContainmentID=?,@AccountKey=?,@OperationID=?,@OwnerID=?,@Fence=?,@ExpectedVersion=?,@SnapshotHash=?,@ReceiptHash=?,@ReceiptReference=?,@ResourcesJson=?,@StreamsJson=?,@Actor=?,@Reason=?,@RegistrationHash=?,@PoolID=?,@PoolVersion=?",
                identity(containment_id),
                op["AccountKey"],
                op["OperationID"],
                op["OwnerID"],
                op["Fence"],
                op["Version"],
                bytes.fromhex(snapshot_hash),
                bytes.fromhex(receipt["sha256"]),
                identity(receipt["reference"]),
                json.dumps(
                    [
                        dict(key=r["ResourceKey"], version=r["Version"])
                        for r in expected["resources"]
                    ]
                ),
                json.dumps(
                    [
                        dict(stream_id=s["StreamID"], version=s["Version"], **seals[s["StreamID"]])
                        for s in expected["streams"]
                    ]
                ),
                actor,
                reason,
                bytes.fromhex(registration_hash),
                pool["PoolID"],
                pool["Version"],
            )
            if one(cursor) is None:
                raise SourceConflict(
                    "Rollover isolation reply missing; verify the original decision."
                )
