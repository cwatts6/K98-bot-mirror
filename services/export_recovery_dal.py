"""Bounded discovery tied to the protected runtime's account, custody and pools."""

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import identity


class ExportRecoveryDAL:
    def __init__(self, connect, *, registration, history=()):
        self.connect, self.registration = connect, registration
        config = registration.value()
        self.account, self.storage_owner = config["account"], config["storage_owner"]
        self.history = tuple(history) or (registration,)
        if any(
            (r.value()["account"], r.value()["storage_owner"]) != (self.account, self.storage_owner)
            for r in self.history
        ):
            raise SourceConflict("Recovery history crosses registered account or custody.")
        self.pools = {p["pool_id"]: p for r in self.history for p in r.value()["pools"]}
        self.destinations = {
            digest(sorted([p["index_file_id"], *p["slot_file_ids"]])): frozenset(
                [
                    "account:" + self.account,
                    "destination:" + p["index_file_id"],
                    *("destination:" + f for f in p["slot_file_ids"]),
                ]
            )
            for p in self.pools.values()
        }
        # New-source rows have no spool/storage owner by their SQL contract.
        # Only exact destination sets from THIS storage owner's protected runtime
        # registration may enter recovery; consumer kind alone grants no scope.
        self.job_scope = (
            "AccountKey=? AND ((ConsumerKind IN ('scan_data','all_kvk') AND StorageOwner=?) "
            "OR (ConsumerKind='new_source' AND StorageOwner IS NULL AND DestinationSetHash IN ("
            + ",".join("?" for _ in self.destinations)
            + ")))"
        )
        self.job_parameters = (self.account, self.storage_owner, *self.destinations)

    def pending_jobs(self, *, after=None):
        from services.export_target_admission_dal import ISOLATED_JOB_TARGETS_SQL

        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) JobID FROM dbo.ExportJob WHERE "
                + self.job_scope
                + " AND (State IN ('failed','uncertain') OR (State='confirmed' AND EXISTS "
                "(SELECT 1 FROM OPENJSON(ProvenanceJson,'$.reconciliations') WITH "
                "(ProofState varchar(32) '$.proof.state') a WHERE a.ProofState='damaged')) "
                "OR (State IN ('running','waiting','ready') "
                "AND (UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()) OR "
                + ISOLATED_JOB_TARGETS_SQL
                + "))) "
                "ORDER BY CASE WHEN JobID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,JobID",
                *self.job_parameters,
                identity(after) if after else None,
            )
            return [identity(row["JobID"]) for row in rows(cursor)]

    def pending_rollovers(self, *, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) OperationID FROM KVK.SourceOutputOperation WHERE AccountKey=? "
                "AND PoolID IN (" + ",".join("?" for _ in self.pools) + ") "
                "AND (State IN ('blocked','uncertain') OR (State IN ('closing','ready','running') "
                "AND UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()))) "
                "ORDER BY CASE WHEN OperationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,OperationID",
                self.account,
                *self.pools,
                identity(after) if after else None,
            )
            return [identity(row["OperationID"]) for row in rows(cursor)]

    def job(self, job_id):
        job_id = identity(job_id)
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT *,CASE WHEN UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()) "
                "THEN 1 ELSE 0 END AS Stalled FROM dbo.ExportJob WHERE JobID=? AND "
                + self.job_scope,
                job_id,
                *self.job_parameters,
            )
            job = one(cursor)
            if job is None:
                raise SourceConflict("Export is outside this protected recovery registration.")
            cursor.execute(
                "SELECT * FROM dbo.ExportAttempt WHERE JobID=? ORDER BY AttemptID", job_id
            )
            attempts = rows(cursor)
            cursor.execute(
                "SELECT StreamID FROM dbo.ExportExecutionStream WHERE JobID=? ORDER BY StreamID",
                job_id,
            )
            streams = rows(cursor)
            cursor.execute(
                "SELECT r.* FROM dbo.ExportResource r JOIN dbo.ExportJobResource m "
                "ON m.ResourceKey=r.ResourceKey WHERE m.JobID=? ORDER BY r.ResourceKey",
                job_id,
            )
            resources = rows(cursor)
            cursor.execute(
                "SELECT c.FileID,c.ContainmentID FROM dbo.ExportContainedTarget c "
                "JOIN dbo.ExportJobResource m ON m.ResourceKey='destination:'+c.FileID "
                "WHERE m.JobID=? ORDER BY c.FileID",
                job_id,
            )
            isolated_targets = rows(cursor)
            if job["ConsumerKind"] == "new_source" and frozenset(
                r["ResourceKey"] for r in resources
            ) != self.destinations.get(bytes(job["DestinationSetHash"])):
                raise SourceConflict("Export resource membership differs from its registered pool.")
            season = None
            if job["ConsumerKind"] == "new_source":
                cursor.execute(
                    "SELECT SourceKey,SeasonState,SeasonVersion FROM KVK.SeasonSource WHERE KVK_NO=?",
                    job["KVK_NO"],
                )
                season = one(cursor)
            return _wire(
                dict(
                    job=job,
                    attempts=attempts,
                    streams=streams,
                    resources=resources,
                    isolated_targets=isolated_targets,
                    season=season,
                )
            )

    def repairs(self, job_id):
        original = self.job(job_id)["job"]
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT JobID FROM dbo.ExportJob WHERE "
                + self.job_scope
                + " AND RepairID IS NOT NULL AND ConsumerKind='new_source' "
                "AND DestinationSetHash=CAST(? AS binary(32)) "
                "AND JSON_VALUE(ProvenanceJson,'$.repair.snapshot.job.JobID')=?",
                *self.job_parameters,
                bytes.fromhex(original["DestinationSetHash"]),
                identity(job_id),
            )
            ids = [identity(row["JobID"]) for row in rows(cursor)]
        # A registered hash alone does not establish complete resource membership.
        return [self.job(key)["job"] for key in ids]

    def registered_publication(self, job_id, coordinator):
        self.job(job_id)
        snapshot = coordinator.operator_snapshot(job_id)
        self.registration.sheets(snapshot["pool"])
        return snapshot

    def rollover(self, operation_id, pools):
        snapshot = pools.operation_snapshot(identity(operation_id))
        op = snapshot["operation"]
        if op["AccountKey"] != self.account or op["PoolID"] not in self.pools:
            raise SourceConflict("Rollover is outside this protected recovery registration.")
        registered = next(
            (
                r
                for r in reversed(self.history)
                if any(p["pool_id"] == op["PoolID"] for p in r.value()["pools"])
            ),
            None,
        )
        if registered is None:
            raise SourceConflict("Original rollover registration is unavailable.")
        registered.sheets(snapshot["pool"])
        return snapshot
