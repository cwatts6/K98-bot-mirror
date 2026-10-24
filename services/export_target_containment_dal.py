"""Authority-side snapshots and atomic permanent target isolation.

No provider truth is inferred here. The reviewed SQL procedure owns the target
fence and exact reservation release in the same transaction as snapshot CAS.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.config_read_containment import stream_wire
from services.export_coordination_dal import _mutex, identity


class ExportTargetContainmentDAL:
    def __init__(self, connect):
        self.connect = connect

    @staticmethod
    def _snapshot(cursor, job_id, account, pool_id):
        _mutex(cursor, "account:" + account)
        cursor.execute(
            "SELECT ResourceKey FROM dbo.ExportJobResource WHERE JobID=? "
            "UNION SELECT ResourceKey FROM dbo.ExportResource WHERE ActiveJobID=? ORDER BY ResourceKey",
            job_id,
            job_id,
        )
        keys = [r["ResourceKey"] for r in rows(cursor)]
        for key in keys:
            _mutex(cursor, key)
        if pool_id is not None:
            _mutex(cursor, "pool:" + pool_id)
        cursor.execute(
            "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS server,"
            "DB_NAME() AS [database],USER_NAME() AS principal"
        )
        target = one(cursor)
        cursor.execute("SELECT * FROM dbo.ExportJob WITH(UPDLOCK,HOLDLOCK) WHERE JobID=?", job_id)
        job = one(cursor)
        if job is None or job["AccountKey"] != account:
            raise SourceConflict("Exact registered containment job required.")
        cursor.execute(
            "SELECT ResourceKey FROM dbo.ExportJobResource WITH(UPDLOCK,HOLDLOCK) WHERE JobID=? ORDER BY ResourceKey",
            job_id,
        )
        membership = [r["ResourceKey"] for r in rows(cursor)]
        if keys != membership:
            raise SourceConflict("Unexpected job reservation prevents partial containment.")
        cursor.execute(
            "SELECT r.* FROM dbo.ExportResource r WITH(UPDLOCK,HOLDLOCK) "
            "JOIN dbo.ExportJobResource m ON m.ResourceKey=r.ResourceKey WHERE m.JobID=? ORDER BY r.ResourceKey",
            job_id,
        )
        resources = rows(cursor)
        cursor.execute(
            "SELECT * FROM dbo.ExportExecutionStream WITH(UPDLOCK,HOLDLOCK) "
            "WHERE JobID=? OR ActiveAccountKey=? ORDER BY CONVERT(varchar(36),StreamID)",
            job_id,
            account,
        )
        streams = [stream_wire(s) for s in rows(cursor)]
        cursor.execute(
            "SELECT a.SessionID,a.AuthorityPrincipal FROM dbo.ExportExecutionSession a "
            "WHERE EXISTS(SELECT 1 FROM dbo.ExportExecutionStream s WHERE s.JobID=? AND s.SessionID=a.SessionID) "
            "ORDER BY CONVERT(varchar(36),a.SessionID)",
            job_id,
        )
        sessions = [
            {"SessionID": identity(r["SessionID"]), "AuthorityPrincipal": r["AuthorityPrincipal"]}
            for r in rows(cursor)
        ]
        pool, slots, registration_count = None, [], None
        if pool_id is not None:
            cursor.execute(
                "SELECT * FROM KVK.SourceOutputPool WITH(UPDLOCK,HOLDLOCK) WHERE PoolID=?", pool_id
            )
            pool = one(cursor)
            cursor.execute(
                "SELECT * FROM KVK.SourceOutputSlot WITH(UPDLOCK,HOLDLOCK) WHERE PoolID=? ORDER BY FileID",
                pool_id,
            )
            slots = rows(cursor)
            cursor.execute(
                "SELECT COUNT(*) AS n FROM KVK.SourceOutputPool WHERE RetiredByReplacementID IS NULL"
            )
            registration_count = one(cursor)["n"]
        cursor.execute(
            "SELECT * FROM dbo.ExportTargetContainment WITH(UPDLOCK,HOLDLOCK) WHERE JobID=?", job_id
        )
        receipt = one(cursor)
        return _wire(
            dict(
                **target,
                job=job,
                membership=membership,
                resources=resources,
                streams=streams,
                sessions=sessions,
                pool=pool,
                slots=slots,
                registration_count=registration_count,
                receipt=receipt,
            )
        )

    def snapshot(self, job_id, *, account, pool_id=None):
        with transaction(self.connect) as cursor:
            return self._snapshot(
                cursor, identity(job_id), account, identity(pool_id) if pool_id else None
            )

    def replacement_retirement(self, pool_id, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT a.*,p.ContainmentID FROM dbo.ExportReplacementActivation a "
                "JOIN dbo.ExportReplacementPlan p ON p.ReplacementID=a.ReplacementID "
                "WHERE a.OldPoolID=? AND a.AccountKey=? AND p.AccountKey=a.AccountKey",
                identity(pool_id),
                account,
            )
            result = one(cursor)
            return _wire(result) if result is not None else None

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
        job = expected["job"]
        pool = expected["pool"]
        with transaction(self.connect) as cursor:
            current = self._snapshot(
                cursor, job["JobID"], job["AccountKey"], pool["PoolID"] if pool else None
            )
            if current != expected:
                raise SourceConflict(
                    "Containment evidence changed; no target or reservation was changed."
                )
            # Parameter names are fixed by the authoritative SQL contract. All
            # caller data stays in bound values; no identifiers come from IPC.
            cursor.execute(
                "EXEC dbo.usp_ExportJobContainTargets @ContainmentID=?,@AccountKey=?,@JobID=?,"
                "@OwnerID=?,@Fence=?,@ExpectedVersion=?,@SnapshotHash=?,@ReceiptHash=?,@ReceiptReference=?,"
                "@ResourcesJson=?,@StreamsJson=?,@Actor=?,@Reason=?,@RegistrationHash=?,@StorageOwner=?,"
                "@PoolID=?,@PoolVersion=?",
                identity(containment_id),
                job["AccountKey"],
                job["JobID"],
                job["OwnerID"],
                job["Fence"],
                job["Version"],
                bytes.fromhex(snapshot_hash),
                bytes.fromhex(receipt["sha256"]),
                receipt["reference"],
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
                job["StorageOwner"],
                pool["PoolID"] if pool else None,
                pool["Version"] if pool else None,
            )
            if one(cursor) is None:
                raise SourceConflict(
                    "Containment acknowledgement is missing; reconcile the original decision."
                )

    def retained_targets(self, containment_id):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT FileID FROM dbo.ExportContainedTarget WHERE ContainmentID=? ORDER BY FileID",
                identity(containment_id),
            )
            return [r["FileID"] for r in rows(cursor)]
