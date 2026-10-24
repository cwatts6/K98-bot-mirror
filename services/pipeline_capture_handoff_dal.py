"""Read exact pipeline lineage without rewriting producer or delivery receipts."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, rows, transaction
from services.export_coordination_dal import identity


class PipelineCaptureHandoffDAL:
    def __init__(self, runtime):
        self.runtime = runtime

    def inspect(self, prep):
        if prep.get("ConsumerKind") != "scan_data" or prep.get("JobID"):
            return None
        producer = (
            json.loads(prep.get("RequestJson") or "{}").get("request", {}).get("producer", {})
        )
        operation = producer.get("operation")
        if not operation:
            return None
        with transaction(self.runtime.dal.connect) as cursor:
            cursor.execute(
                "SELECT r.RunID,r.RegistrationJson,s.Stage,p.Version AS SourceVersion,"
                "e.State AS ExportState,e.EvidenceJson,t.PreparationID AS TargetID,"
                "t.State AS TargetState,t.JobID,t.SpoolKey,t.SpoolBytes,t.SpoolHash,"
                "t.RequestJson AS TargetRequest,j.State AS JobState,j.InputHash,"
                "j.SpoolKey AS JobSpoolKey,j.SpoolBytes AS JobSpoolBytes,j.DestinationSetHash "
                "FROM dbo.ExportPreparation p "
                "JOIN dbo.ProcessingPipelineStage s ON LOWER(CONVERT(varchar(36),s.OperationID))=? "
                "JOIN dbo.ProcessingPipelineRun r ON r.RunID=s.RunID "
                "JOIN dbo.ProcessingPipelineStage e ON e.RunID=r.RunID AND e.Stage='export' "
                "JOIN dbo.ProcessingPipelineStage c ON c.RunID=r.RunID AND c.Stage='configuration' "
                "LEFT JOIN dbo.ExportPreparation t ON LOWER(CONVERT(varchar(36),t.PreparationID))="
                "JSON_VALUE(e.EvidenceJson,'$.preparation_id') AND t.AccountKey=r.AccountKey "
                "AND t.StorageOwner=r.StorageOwner AND t.ConsumerKind='scan_data' "
                "AND JSON_VALUE(t.RequestJson,'$.request.producer.operation')=LOWER(CONVERT(varchar(36),c.OperationID)) "
                "LEFT JOIN dbo.ExportJob j ON j.JobID=t.JobID AND j.AccountKey=r.AccountKey "
                "AND j.StorageOwner=r.StorageOwner AND j.ConsumerKind='scan_data' "
                "WHERE p.PreparationID=? AND p.AccountKey=r.AccountKey AND p.StorageOwner=r.StorageOwner "
                "AND JSON_VALUE(p.RequestJson,'$.request.producer.operation')=LOWER(CONVERT(varchar(36),s.OperationID)) "
                "AND s.Stage IN ('import','player_cache','configuration') "
                "AND r.AccountKey=? AND r.StorageOwner=?",
                identity(operation),
                identity(prep["PreparationID"]),
                self.runtime.account,
                self.runtime.store.storage_owner,
            )
            found = rows(cursor)
        if not found:
            return None
        if len(found) != 1 or found[0]["SourceVersion"] != prep["Version"]:
            raise SourceConflict("Pipeline capture association changed or is ambiguous.")
        row = found[0]
        link = dict(pipeline_id=identity(row["RunID"]), job_id=None)
        # A pending pipeline also owns its queue decision. Never independently
        # enqueue its intermediate snapshots while final admission is unconfirmed.
        if row["ExportState"] != "observed":
            return link
        evidence = json.loads(row["EvidenceJson"] or "{}")
        registration = json.loads(row["RegistrationJson"])
        if (
            evidence.get("outcome") != "queued"
            or not row["JobID"]
            or row["TargetState"] != "materialized"
            or not row["JobState"]
            or identity(evidence.get("job_id")) != identity(row["JobID"])
            or registration != json.loads(self.runtime.configuration)
            or json.loads(row["TargetRequest"])["request"]["config"] != registration["scan_data"]
            or bytes(row["SpoolHash"]) != bytes(row["InputHash"])
            or row["SpoolKey"] != row["JobSpoolKey"]
            or row["SpoolBytes"] != row["JobSpoolBytes"]
            or bytes(row["DestinationSetHash"])
            != digest(tuple(sorted(set(registration["scan_data"]["destinations"]))))
        ):
            raise SourceConflict(
                "Pipeline export linkage requires verification; no independent queue action."
            )
        target, _, _ = self.runtime.verified_snapshot(identity(row["TargetID"]))
        if identity(target["JobID"]) != identity(row["JobID"]):
            raise SourceConflict("Pipeline export capture changed during verification.")
        return dict(link, job_id=identity(row["JobID"]))
