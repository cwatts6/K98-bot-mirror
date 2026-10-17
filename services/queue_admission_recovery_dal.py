"""Guided withdrawal of a never-admitted queue ticket, with a durable fence.

Only the exact initial pending state is withdrawable. SQL-pending, provider
streams, receipts and held ownership go to their domain recovery workflows.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _cas, _mutex, identity


class QueueAdmissionDAL:
    def __init__(self, runtime):
        self.connect = runtime.dal.connect
        self.account, self.storage_owner = runtime.account, runtime.store.storage_owner

    def pending(self, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) PreparationID FROM dbo.ExportPreparation WHERE AccountKey=? "
                "AND StorageOwner=? AND State IN ('pending','sql_pending') "
                "ORDER BY EnqueueSequence,PreparationID",
                self.account,
                self.storage_owner,
            )
            return [identity(r["PreparationID"]) for r in rows(cursor)]

    def _snapshot(self, cursor, source_id):
        _mutex(cursor, "account:" + self.account)
        cursor.execute(
            "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=? "
            "AND AccountKey=? AND StorageOwner=?",
            identity(source_id),
            self.account,
            self.storage_owner,
        )
        prep = one(cursor)
        if not prep:
            raise SourceConflict("Queue ticket is outside this recovery scope.")
        counts = {}
        for table in (
            "ExportPreparationResource",
            "ExportResource",
            "ExportExecutionStream",
            "StatsImportExecution",
        ):
            column = "ActivePreparationID" if table == "ExportResource" else "PreparationID"
            cursor.execute(
                f"SELECT COUNT_BIG(*) AS Total FROM dbo.{table} WITH (UPDLOCK,HOLDLOCK) WHERE {column}=?",
                identity(source_id),
            )
            counts[table] = one(cursor)["Total"]
        return _wire(dict(preparation=prep, counts=counts))

    def snapshot(self, source_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, source_id)

    @staticmethod
    def eligible(state):
        prep = state["preparation"]
        request = json.loads(prep["RequestJson"])
        return (
            prep["State"] == "pending"
            # Typed producers own cancellation and continuation receipts. A
            # generic tombstone would strand their saved inputs after closure.
            and not request.get("request", {}).get("producer")
            and prep["Version"] == 1
            and prep["Fence"] == 0
            and all(
                prep[k] is None
                for k in (
                    "OwnerID",
                    "GenerationJson",
                    "SpoolKey",
                    "SpoolBytes",
                    "SpoolHash",
                    "JobID",
                )
            )
            and not any(state["counts"].values())
            and prep["RequestHash"].lower() == digest(request).hex()
        )

    def withdraw(self, source_id, token, action_id):
        with transaction(self.connect) as cursor:
            state = self._snapshot(cursor, source_id)
            if digest(state).hex() != token or not self.eligible(state):
                raise SourceConflict(
                    "Queue admission changed. Review its current execution evidence."
                )
            marker = json.dumps(
                dict(queue_withdrawal=dict(action=identity(action_id), token=token))
            )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2,"
                "GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version "
                "WHERE PreparationID=? AND State='pending' AND Version=1 AND Fence=0 AND OwnerID IS NULL",
                identity(action_id),
                marker,
                identity(source_id),
            )
