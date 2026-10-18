"""Durable confirmed configuration continuation, separate from read admission."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _cas, bounded_json, identity
from services.producer_refusal_dal import ProducerRefusalDAL


class ConfigurationContinuationDAL(ProducerRefusalDAL):
    def __init__(self, runtime, outcomes):
        super().__init__(runtime)
        self.outcomes = outcomes

    def pending(self, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) PreparationID FROM dbo.ExportPreparation "
                "WHERE AccountKey=? AND StorageOwner=? AND ConsumerKind='scan_data' "
                "AND JSON_VALUE(RequestJson,'$.request.producer.kind')='configuration_import' "
                "AND JSON_VALUE(RequestJson,'$.request.producer.parent') IS NULL "
                "AND JSON_VALUE(GenerationJson,'$.configuration_cancelled.actor') IS NOT NULL "
                "AND ISNULL(JSON_VALUE(GenerationJson,'$.configuration_continuation.choice'),'')<>'keep_prior' "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["PreparationID"]) for row in rows(cursor)]

    def snapshot(self, source_id):
        from services.replacement_admission_dal import admission_blocker

        preview = self.outcomes.inspect(source_id)
        root = preview["preparation"]
        request = self.outcomes.request(root)
        if preview["action"] != "cancelled" or "parent" in request["request"]["producer"]:
            raise SourceConflict("A verified closed original configuration attempt is required.")
        marker = json.loads(root["GenerationJson"]).get("configuration_continuation")
        child = None
        if marker and marker.get("action"):
            operation = identity(marker["action"])
            with transaction(self.connect) as cursor:
                cursor.execute(
                    "SELECT * FROM dbo.ExportPreparation WHERE AccountKey=? AND StorageOwner=? "
                    "AND JSON_VALUE(RequestJson,'$.request.producer.parent')=? "
                    "AND JSON_VALUE(RequestJson,'$.request.producer.operation')=?",
                    self.account,
                    self.storage_owner,
                    identity(source_id),
                    operation,
                )
                matches = rows(cursor)
            if len(matches) > 1:
                raise SourceConflict("More than one configuration continuation has this action.")
            if matches:
                child = matches[0]
                expected = self.child_request(source_id, marker)
                document = self.outcomes.request(child)
                if document["request"] != expected:
                    raise SourceConflict("Continuation differs from its confirmed registration.")
        blocker = (
            admission_blocker(self.connect, account=self.account)
            if child is None or child["State"] == "unavailable"
            else None
        )
        return _wire(
            dict(
                root=root,
                marker=marker,
                child=child,
                blocker=blocker,
                current=json.loads(self.runtime.configuration),
            )
        )

    @staticmethod
    def child_request(source_id, marker):
        operation = identity(marker["action"])
        return dict(
            operation=operation,
            kind="scan_data",
            config=marker["configuration"]["scan_data"],
            producer=dict(
                kind="configuration_import",
                atomic_checkpoint=1,
                operation=operation,
                parent=identity(source_id),
            ),
        )

    def record(self, source_id, expected_token, marker):
        self._require_serialized(source_id)
        state = self.snapshot(source_id)
        if digest(state).hex() != expected_token:
            raise SourceConflict("Configuration continuation evidence changed.")
        generation = json.loads(state["root"]["GenerationJson"])
        generation["configuration_continuation"] = marker
        encoded = bounded_json(generation)
        with transaction(self.connect) as cursor:
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET GenerationJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE PreparationID=? AND AccountKey=? AND StorageOwner=? "
                "AND Version=? AND State='unavailable' AND JobID IS NULL AND SpoolKey IS NULL "
                "AND NOT EXISTS(SELECT 1 FROM dbo.ExportResource WHERE ActivePreparationID=?)",
                encoded,
                identity(source_id),
                self.account,
                self.storage_owner,
                state["root"]["Version"],
                identity(source_id),
            )

    def reserve_for_reconciliation(self, source_id, marker):
        """Only after dispatch ends: pre-reservation would block its own fresh read."""
        self._require_serialized(source_id)
        return self.runtime.dal.request(
            account=self.account,
            consumer="scan_data",
            kvk_no=None,
            request=self.child_request(source_id, marker),
            storage_owner=self.storage_owner,
            actor="recovery:" + identity(marker["action"]),
            reason="Confirmed fresh configuration",
        )

    def close_uncommitted(self, identifier, marker):
        preview = self.outcomes.inspect(identifier)
        if preview["action"] == self.outcomes.cancel_action:
            self.outcomes.cancel(
                identifier,
                preview["token"],
                "recovery:" + identity(marker["action"]),
                "Reconciled configuration continuation without atomic commit",
            )
            preview = self.outcomes.inspect(identifier)
        return preview["action"] == "cancelled"
