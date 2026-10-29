"""Separate fresh report approval after verified closure of a failed cache producer."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, rows, transaction
from services.configuration_continuation_dal import ConfigurationContinuationDAL
from services.export_coordination_dal import identity


class PlayerReportContinuationDAL(ConfigurationContinuationDAL):
    marker_key = "player_report_continuation"

    def pending(self, after=None):
        # One current cache decision, not a new incident for every historical
        # failed startup. Older closures remain individually accessible.
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) PreparationID,GenerationJson FROM dbo.ExportPreparation "
                "WHERE AccountKey=? AND StorageOwner=? AND ConsumerKind='scan_data' "
                "AND JSON_VALUE(RequestJson,'$.request.producer.kind')='player_stats_report' "
                "AND JSON_VALUE(RequestJson,'$.request.producer.parent') IS NULL "
                "AND JSON_VALUE(RequestJson,'$.request.producer.export_disposition')='cache_only_v1' "
                "AND JSON_VALUE(GenerationJson,'$.report_cancelled.actor') IS NOT NULL "
                "ORDER BY CreatedUTC DESC,PreparationID DESC",
                self.account,
                self.storage_owner,
            )
            found = rows(cursor)
        if not found:
            return []
        marker = json.loads(found[0]["GenerationJson"] or "{}").get(self.marker_key) or {}
        return (
            []
            if marker.get("choice") == "keep_prior" or marker.get("cache_receipt")
            else [identity(found[0]["PreparationID"])]
        )

    def original(self, source_id):
        preview = self.outcomes.inspect(source_id)
        root = preview["preparation"]
        producer = self.outcomes.request(root)["request"]["producer"]
        if (
            preview["action"] != "cancelled"
            or "parent" in producer
            or producer.get("kind") != "player_stats_report"
            or producer.get("export_disposition") != "cache_only_v1"
        ):
            raise SourceConflict("A verified closed cache-only report attempt is required.")
        return root

    @staticmethod
    def child_request(source_id, marker):
        operation = identity(marker["action"])
        return dict(
            operation=operation,
            kind="scan_data",
            config=marker["configuration"]["scan_data"],
            producer=dict(
                kind="player_stats_report",
                atomic_checkpoint=1,
                operation=operation,
                parent=identity(source_id),
                export_disposition="cache_only_v1",
            ),
        )
