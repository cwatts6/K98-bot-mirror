"""Recovery of the report-only producer whose output and checkpoint commit together."""

import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.all_kvk_capture_recovery_dal import AllKvkCaptureRecoveryDAL
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL


class PlayerReportRecoveryDAL(AllKvkCaptureRecoveryDAL):
    consumer = "scan_data"
    producer_kind = "player_stats_report"
    closure_key = "report_cancelled"
    cancel_action = "cancel_report"
    export_dispositions = frozenset({"cache_only_v1", "pipeline_export_v1"})

    @classmethod
    def producer_fields(cls, producer):
        fields = {"kind", "atomic_checkpoint", "operation"}
        if "export_disposition" in producer:
            if (
                type(producer["export_disposition"]) is not str
                or producer["export_disposition"] not in cls.export_dispositions
            ):
                raise SourceConflict("The original report export intent is invalid.")
            fields |= {"export_disposition"}
        return fields

    @classmethod
    def request(cls, prep):
        request = json.loads(prep["RequestJson"])
        inner = request.get("request", {})
        producer = inner.get("producer", {})
        if (
            bytes(prep["RequestHash"]) != digest(request)
            or request.get("consumer") != "scan_data"
            or request.get("storage_owner") != prep["StorageOwner"]
            or request.get("kvk_no") is not None
            or prep["KVK_NO"] is not None
            or inner.get("kind") != "scan_data"
            or not isinstance(producer, dict)
            or set(producer) != cls.producer_fields(producer)
            or producer.get("kind") != cls.producer_kind
            or type(producer.get("atomic_checkpoint")) is not int
            or producer["atomic_checkpoint"] != 1
            or identity(producer["operation"]) != inner.get("operation")
        ):
            raise SourceConflict("The exact atomic report request could not be verified.")
        return request

    @staticmethod
    def _snapshot(cursor, preparation_id):
        prep, _, resources = AllKvkCaptureRecoveryDAL._snapshot(cursor, preparation_id)
        cursor.execute(
            "SELECT * FROM dbo.StatsImportExecution WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
            preparation_id,
        )
        return prep, one(cursor), resources

    @classmethod
    def action(cls, prep, execution, resources):
        cls.request(prep)
        if execution:
            raise SourceConflict("An import receipt cannot be treated as a report-only attempt.")
        generation = json.loads(prep["GenerationJson"] or "{}")
        if generation.get(cls.closure_key):
            if prep["State"] != "unavailable" or resources or prep["JobID"] or prep["SpoolKey"]:
                raise SourceConflict("The report closure has not verified its release.")
            return "cancelled"
        if generation:
            return super().action(prep, execution, resources)
        if prep["JobID"] or prep["SpoolKey"] or prep["SpoolHash"] or prep["SpoolBytes"]:
            raise SourceConflict("Retained output requires its own verified capture recovery.")
        expected = {
            "pending": (),
            "preflight": ("account:" + prep["AccountKey"],),
            "sql_pending": (),
            "writing": ("sql_snapshot:legacy_outputs",),
            "uncertain": ("sql_snapshot:legacy_outputs",),
            "unavailable": (),
        }.get(prep["State"])
        if expected is None or tuple(r["ResourceKey"] for r in resources) != expected:
            raise SourceConflict("Exact report reservation ownership is required.")
        for resource in resources:
            if (
                identity(resource["OwnerID"]),
                resource["Fence"],
                resource["ActiveJobID"],
                resource["ActiveOutputOperationID"],
            ) != (identity(prep["OwnerID"]), prep["Fence"], None, None):
                raise SourceConflict("Report reservation ownership changed.")
        return cls.cancel_action

    def pending_recovery(self, *, after=None, limit=20):
        if type(limit) is not int or not 1 <= limit <= 25:
            raise ValueError("Bounded recovery discovery required.")
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) PreparationID FROM dbo.ExportPreparation p "
                "WHERE AccountKey=? AND StorageOwner=? AND ConsumerKind='scan_data' "
                "AND JSON_VALUE(RequestJson,'$.request.producer.kind')=? "
                "AND State IN ('pending','preflight','sql_pending','writing','committed','uncertain','captured','unavailable') "
                "AND JobID IS NULL AND JSON_VALUE(GenerationJson,?) IS NULL "
                # A completed no-export decision is reconciled through its durable
                # incident/action. Do not keep rediscovering routine cache history.
                # Inconsistent state, missing receipt or retained ownership stays visible.
                "AND NOT (State='unavailable' "
                "AND JSON_VALUE(GenerationJson,'$.capture_abandoned.actor') IS NOT NULL "
                "AND JSON_VALUE(GenerationJson,'$.capture_abandoned.token') IS NOT NULL "
                "AND NOT EXISTS (SELECT 1 FROM dbo.ExportResource r "
                "WHERE r.ActivePreparationID=p.PreparationID)) "
                "AND UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()) "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                limit,
                self.account,
                self.storage_owner,
                self.producer_kind,
                "$." + self.closure_key + ".actor",
                identity(after) if after else None,
            )
            return [identity(r["PreparationID"]) for r in rows(cursor)]

    def cancel(self, source_id, token, actor, reason):
        if (
            not isinstance(actor, str)
            or not 1 <= len(actor) <= 128
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise ValueError("A bounded recovery actor and reason are required.")
        source_id = identity(source_id)
        marker = dict(token=token, actor=actor, reason=reason)
        # The independent producer session AND the actual transaction's row locks
        # must have ended. A lost guard session does not permit a late SQL commit.
        with ImportCaptureRecoveryDAL(self, stats_execution=False).session(source_id) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                _mutex(cursor, "account:" + self.account)
                prep, execution, resources = self._snapshot(cursor, source_id)
                self._scope(prep)
                action = self.action(prep, execution, resources)
                if (
                    action == "cancelled"
                    and json.loads(prep["GenerationJson"])[self.closure_key] == marker
                ):
                    cursor.execute("COMMIT TRANSACTION")
                    return
                if action != self.cancel_action or self.token(prep, execution, resources) != token:
                    raise SourceConflict("Report evidence changed; review the current incident.")
                cursor.execute(
                    "SELECT TOP (1) StreamID FROM dbo.ExportExecutionStream WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
                    source_id,
                )
                if one(cursor):
                    raise SourceConflict("Provider execution evidence requires separate recovery.")
                if any(r["ResourceKey"] == "account:" + self.account for r in resources):
                    from services.export_execution_dal import ExportExecutionDAL

                    ExportExecutionDAL.assert_no_active_stream(cursor, self.account)
                for resource in resources:
                    _cas(
                        cursor,
                        "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,Version=Version+1 "
                        "OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? "
                        "AND ActiveJobID IS NULL AND ActiveOutputOperationID IS NULL",
                        resource["ResourceKey"],
                        resource["Version"],
                        source_id,
                        prep["OwnerID"],
                        prep["Fence"],
                    )
                _cas(
                    cursor,
                    "UPDATE dbo.ExportPreparation SET State='unavailable',OwnerID=COALESCE(OwnerID,?),Fence=Fence+1,Version=Version+1,GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() "
                    "OUTPUT inserted.Version WHERE PreparationID=? AND Version=? AND Fence=? AND GenerationJson IS NULL AND JobID IS NULL AND SpoolKey IS NULL",
                    str(uuid4()),
                    bounded_json({self.closure_key: marker}),
                    source_id,
                    prep["Version"],
                    prep["Fence"],
                )
                cursor.execute("COMMIT TRANSACTION")
            except BaseException:
                try:
                    cursor.execute("IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
                except Exception:
                    pass
                raise
            finally:
                cursor.close()
