"""Guided continuation of an identified configuration import refused before its read."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.configuration_continuation_dal import ConfigurationContinuationDAL
from services.configuration_producer_recovery import ConfigurationProducerDAL
from services.export_coordination_dal import identity


class ConfigurationReadContinuationDAL(ConfigurationContinuationDAL):
    def pending(self, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) PreparationID FROM dbo.ExportPreparation "
                "WHERE AccountKey=? AND StorageOwner=? AND ConsumerKind='config' "
                "AND State='unavailable' "
                "AND Fence=1 AND (GenerationJson IS NULL OR "
                "JSON_VALUE(GenerationJson,'$.configuration_continuation.action') IS NOT NULL) "
                "AND JSON_VALUE(RequestJson,'$.request.configuration_import.producer.kind')='configuration_import' "
                "AND JSON_VALUE(RequestJson,'$.request.configuration_import.invocation_mode')='publish' "
                "AND ISNULL(JSON_VALUE(GenerationJson,'$.configuration_continuation.choice'),'')<>'keep_prior' "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["PreparationID"]) for row in rows(cursor)]

    def original(self, source_id):
        source_id = identity(source_id)
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE PreparationID=? "
                "AND AccountKey=? AND StorageOwner=? AND ConsumerKind='config'",
                source_id,
                self.account,
                self.storage_owner,
            )
            root = one(cursor)
            if not root:
                raise SourceConflict("Configuration read is outside this recovery scope.")
            cursor.execute(
                "SELECT (SELECT COUNT_BIG(*) FROM dbo.ExportPreparationResource WHERE PreparationID=?) "
                "+(SELECT COUNT_BIG(*) FROM dbo.ExportResource WHERE ActivePreparationID=?) "
                "+(SELECT COUNT_BIG(*) FROM dbo.ExportExecutionStream WHERE PreparationID=?) "
                "+(SELECT COUNT_BIG(*) FROM dbo.StatsImportExecution WHERE PreparationID=?) AS n",
                source_id,
                source_id,
                source_id,
                source_id,
            )
            execution = one(cursor)["n"]
        document = json.loads(root["RequestJson"])
        inner = document.get("request", {})
        ConfigurationProducerDAL.validate_read_request(inner)
        generation = json.loads(root["GenerationJson"] or "{}")
        if (
            bytes(root["RequestHash"]) != digest(document)
            or document.get("consumer") != "config"
            or document.get("storage_owner") != self.storage_owner
            or document.get("kvk_no") is not None
            or root["KVK_NO"] is not None
            or not isinstance(generation, dict)
            or set(generation) - {"configuration_continuation"}
            or root["State"] != "unavailable"
            or root["Fence"] != 1
            or root["OwnerID"] is None
            or execution
            or (not generation and root["Version"] != 2)
            or (generation and root["Version"] < 3)
            or any(root[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID"))
        ):
            raise SourceConflict(
                "Exact withdrawn, never-admitted configuration import read required."
            )
        if generation:
            marker = generation["configuration_continuation"]
            if (
                not isinstance(marker, dict)
                or set(marker) - {"export_disposition"}
                != {"action", "token", "reason", "choice", "configuration"}
                or (
                    "export_disposition" in marker
                    and (
                        marker["export_disposition"] != "configuration_only_v1"
                        or marker["choice"] != "retry"
                    )
                )
                or marker["choice"] not in {"keep_prior", "retry"}
                or not isinstance(marker["reason"], str)
                or not isinstance(marker["token"], str)
                or len(marker["token"]) != 64
                or any(c not in "0123456789abcdef" for c in marker["token"])
                or not isinstance(marker["configuration"], dict)
                or not all(
                    isinstance(marker["configuration"].get(k), dict)
                    for k in ("config", "scan_data")
                )
            ):
                raise SourceConflict("Complete saved configuration decision required.")
            identity(marker["action"])
        return root

    def review_context(self, root):
        association = json.loads(root["RequestJson"])["request"]["configuration_import"]
        return dict(
            review_root=dict(
                RequestJson=json.dumps({"request": {"config": association["outputs"]}})
            ),
            original_sources=association["sources"],
            failure_context=dict(
                operation="configuration_import",
                original_export_intent=association["producer"].get(
                    "export_disposition", "not_recorded"
                ),
                operation_id=association["producer"]["operation"],
                input_kind="registered_configuration_sheets",
                original_fault="configuration_read_admission_not_obtained",
                original_read_id=identity(root["PreparationID"]),
                original_created_utc=str(root["CreatedUTC"]),
                original_request_sha256=bytes(root["RequestHash"]).hex(),
                sql_outcome="not_started",
                current_blocker="configuration_continuation_decision_required",
                summary="The configuration import's read was withdrawn before admission. No provider stream, input collection or configuration publication started in this attempt.",
            ),
        )
