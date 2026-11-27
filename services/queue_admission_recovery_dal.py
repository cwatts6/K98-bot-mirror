"""Guided withdrawal of a never-admitted queue ticket, with a durable fence.

Only the exact initial pending state is withdrawable. SQL-pending, provider
streams, receipts and held ownership go to their domain recovery workflows.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_contention import retry_coordination, transaction as coordination_transaction
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
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
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

    @staticmethod
    def health_probe(state):
        """Durable explicit opt-in, never infer health purpose from age or consumer."""
        prep = state["preparation"]
        request = json.loads(prep["RequestJson"])
        inner = request.get("request", {})
        try:
            identity(inner.get("read_configuration"))
        except (TypeError, ValueError):
            return False
        return (
            prep.get("Actor") == "system:health_probe:v1"
            and prep["ConsumerKind"] == "config"
            and prep["KVK_NO"] is None
            and set(inner) == {"read_configuration"}
            and request
            == dict(
                consumer="config", kvk_no=None, request=inner, storage_owner=prep["StorageOwner"]
            )
            and prep["RequestHash"].lower() == digest(request).hex()
        )

    @classmethod
    def health_withdrawn(cls, state):
        prep = state["preparation"]
        marker = json.loads(prep["GenerationJson"] or "{}").get("queue_withdrawal")
        return (
            cls.health_probe(state)
            and isinstance(marker, dict)
            and set(marker) == {"action", "token"}
            and marker["action"] == prep["OwnerID"]
            and isinstance(marker["token"], str)
            and len(marker["token"]) == 64
            and prep["State"] == "unavailable"
            and prep["Version"] == 2
            and prep["Fence"] == 1
            and all(prep[k] is None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID"))
            and not any(state["counts"].values())
        )

    @retry_coordination(budget_seconds=5)
    def withdraw_health_probe(self, source_id, token=None, action_id=None):
        """Fence only an explicitly disposable, never-admitted health request.

        A lost commit acknowledgement is not retried. Discovery finds the durable
        purpose even if request creation's acknowledgement was lost. Its later
        snapshot either proves withdrawal or rechecks the untouched initial state.
        """
        from uuid import uuid4

        with coordination_transaction(self.connect) as cursor:
            state = self._snapshot(cursor, source_id)
            if token is None and self.health_withdrawn(state):
                return
            actual = digest(state).hex()
            if (
                not self.health_probe(state)
                or not self.eligible(state)
                or (token is not None and token != actual)
            ):
                raise SourceConflict("Health probe changed or has execution evidence; retain it.")
            self._withdraw(cursor, source_id, actual, action_id or str(uuid4()))

    def withdraw(self, source_id, token, action_id):
        with transaction(self.connect) as cursor:
            state = self._snapshot(cursor, source_id)
            if digest(state).hex() != token or not self.eligible(state):
                raise SourceConflict(
                    "Queue admission changed. Review its current execution evidence."
                )
            self._withdraw(cursor, source_id, token, action_id)

    @staticmethod
    def _withdraw(cursor, source_id, token, action_id):
        marker = json.dumps(dict(queue_withdrawal=dict(action=identity(action_id), token=token)))
        _cas(
            cursor,
            "UPDATE dbo.ExportPreparation SET State='unavailable',OwnerID=?,Fence=1,Version=2,"
            "GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version "
            "WHERE PreparationID=? AND State='pending' AND Version=1 AND Fence=0 AND OwnerID IS NULL",
            identity(action_id),
            marker,
            identity(source_id),
        )

    @staticmethod
    def configuration_read_continuation_candidate(state):
        """Select the typed read's decision owner; this is not closure proof."""
        prep = state["preparation"]
        inner = json.loads(prep["RequestJson"]).get("request", {})
        association = inner.get("configuration_import")
        return (
            prep["ConsumerKind"] == "config"
            and prep["State"] == "unavailable"
            and "read_configuration" in inner
            and isinstance(association, dict)
            and association.get("invocation_mode") == "publish"
            and not any(state["counts"].values())
        )

    @staticmethod
    def withdrawn_read(state, *, closed=False):
        """Prove the initial read was withdrawn before ever acquiring admission.

        Historical untyped reads cannot establish an import/publication intent.
        Close only their queue incident; never manufacture a continuation.
        """
        prep = state["preparation"]
        request = json.loads(prep["RequestJson"])
        inner = request.get("request", {})
        generation = json.loads(prep["GenerationJson"] or "{}")
        marker = generation.get("withdrawn_read_closeout") if closed else None
        if closed:
            if not isinstance(marker, dict) or set(marker) != {"action", "token"}:
                return False
            try:
                identity(marker["action"])
            except (TypeError, ValueError):
                return False
            if not isinstance(marker["token"], str) or len(marker["token"]) != 64:
                return False
        try:
            identity(inner.get("read_configuration"))
        except (TypeError, ValueError):
            return False
        return (
            prep["ConsumerKind"] == "config"
            and prep["KVK_NO"] is None
            and request
            == dict(
                consumer="config", kvk_no=None, request=inner, storage_owner=prep["StorageOwner"]
            )
            and set(inner) == {"read_configuration"}
            and prep["RequestHash"].lower() == digest(request).hex()
            and prep["State"] == "unavailable"
            and prep["Fence"] == 1
            and prep["Version"] == (3 if closed else 2)
            and prep["OwnerID"] is not None
            and (
                set(generation) == {"withdrawn_read_closeout"}
                if closed
                else prep["GenerationJson"] is None
            )
            and all(prep[k] is None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID"))
            and not any(state["counts"].values())
        )

    def close_withdrawn_read(self, source_id, token, action_id):
        with transaction(self.connect) as cursor:
            state = self._snapshot(cursor, source_id)
            if digest(state).hex() != token or not self.withdrawn_read(state):
                raise SourceConflict("The withdrawn read changed. Review its current evidence.")
            marker = json.dumps(
                dict(withdrawn_read_closeout=dict(action=identity(action_id), token=token))
            )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET GenerationJson=?,Version=Version+1,"
                "UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? "
                "AND State='unavailable' AND Version=2 AND Fence=1 AND GenerationJson IS NULL",
                marker,
                identity(source_id),
            )
