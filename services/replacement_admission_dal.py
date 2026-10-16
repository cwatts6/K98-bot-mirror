"""Read-only explanation of the exact replacement-verification admission gates."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, transaction
from services.export_coordination_dal import identity


def _owner(cursor, account, kind, key):
    key = identity(key)
    if kind == "job":
        cursor.execute(
            "SELECT State,Version FROM dbo.ExportJob WHERE JobID=? AND AccountKey=?", key, account
        )
        route = "export_job"
    elif kind == "rollover":
        cursor.execute(
            "SELECT State,Version FROM KVK.SourceOutputOperation WHERE OperationID=? AND AccountKey=?",
            key,
            account,
        )
        route = "export_rollover"
    else:
        cursor.execute(
            "SELECT p.State,p.Version,p.ConsumerKind,"
            "JSON_VALUE(p.RequestJson,'$.request.producer.kind') AS ProducerKind,"
            "p.RequestJson,p.RequestHash,p.StorageOwner,"
            "e.PreparationID AS ExecutionID,c.JobID,c.OutputOperationID "
            "FROM dbo.ExportPreparation p "
            "LEFT JOIN dbo.StatsImportExecution e ON e.PreparationID=p.PreparationID "
            "LEFT JOIN dbo.ExportReplacementVerification v ON v.PreparationID=p.PreparationID "
            "LEFT JOIN dbo.ExportReplacementPlan plan_row ON plan_row.ReplacementID=v.ReplacementID AND plan_row.AccountKey=p.AccountKey "
            "LEFT JOIN dbo.ExportTargetContainment c ON c.ContainmentID=plan_row.ContainmentID AND c.AccountKey=p.AccountKey "
            "WHERE p.PreparationID=? AND p.AccountKey=?",
            key,
            account,
        )
        row = one(cursor)
        if row is None:
            return None
        job, operation = row["JobID"], row["OutputOperationID"]
        if job is not None or operation is not None:
            if job is not None and operation is not None:
                raise SourceConflict("The blocking read has ambiguous recovery ownership.")
            return _owner(cursor, account, "job" if job else "rollover", job or operation)
        route = {
            "config": "configuration_read",
            "all_kvk": "all_kvk_capture",
            "scan_data": "stats_import",
        }.get(row["ConsumerKind"])
        if row["ProducerKind"] == "player_stats_report":
            route = "player_report"
        elif row["ProducerKind"] == "configuration_import":
            route = "configuration_producer"
        elif row["ProducerKind"] == "stats_import" and row["ExecutionID"] is None:
            route = "producer_refusal"
            document = json.loads(row["RequestJson"])
            producer = document["request"]["producer"]
            if producer.get("parent") is not None:
                parent_id = identity(producer["parent"])
                cursor.execute(
                    "SELECT RequestJson,RequestHash,StorageOwner,ConsumerKind FROM dbo.ExportPreparation "
                    "WHERE PreparationID=? AND AccountKey=?",
                    parent_id,
                    account,
                )
                parent = one(cursor)
                if parent is None:
                    raise SourceConflict(
                        "The blocking continuation's original recovery is unavailable."
                    )
                original = json.loads(parent["RequestJson"])
                original_producer = original.get("request", {}).get("producer", {})
                if (
                    parent["ConsumerKind"] != "scan_data"
                    or parent["StorageOwner"] != row["StorageOwner"]
                    or bytes(parent["RequestHash"]) != digest(original)
                    or bytes(row["RequestHash"]) != digest(document)
                    or original_producer.get("kind") != "stats_import"
                    or original_producer.get("parent") is not None
                    or original_producer.get("inputs") != producer.get("inputs")
                    or not original_producer.get("inputs")
                ):
                    raise SourceConflict(
                        "The blocking continuation differs from its original recovery."
                    )
                key = parent_id
        if route is None:
            raise SourceConflict("The blocking preparation has no typed recovery route.")
        return dict(kind=route, source_id=key, state=row["State"], version=row["Version"])
    row = one(cursor)
    return (
        dict(kind=route, source_id=key, state=row["State"], version=row["Version"]) if row else None
    )


def admission_blocker(connect, *, account, replacement_id):
    """Return one exact blocker at a time; final SQL admission remains authoritative.

    No age-based release, mutations or private request data. Rechecking advances
    to the next owner after settlement, keeping Discord's button count bounded.
    """
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT ReplacementID FROM dbo.ExportReplacementPlan WHERE ReplacementID=? AND AccountKey=?",
            identity(replacement_id),
            account,
        )
        if one(cursor) is None:
            raise SourceConflict("Replacement proposal is outside registered custody.")
        cursor.execute(
            "SELECT TOP (1) r.ResourceKey,r.Version,r.ActiveJobID,r.ActivePreparationID,r.ActiveOutputOperationID "
            "FROM dbo.ExportResource r WHERE (r.ResourceKey=? OR r.ResourceKey IN "
            "(SELECT 'destination:'+NewFileID FROM dbo.ExportReplacementTarget WHERE ReplacementID=?)) "
            "AND (r.OwnerID IS NOT NULL OR r.ActiveJobID IS NOT NULL OR r.ActivePreparationID IS NOT NULL "
            "OR r.ActiveOutputOperationID IS NOT NULL OR r.BlockedReason IS NOT NULL) ORDER BY r.ResourceKey",
            "account:" + account,
            identity(replacement_id),
        )
        resource = one(cursor)
        if resource:
            owners = [
                (kind, resource[column])
                for kind, column in (
                    ("job", "ActiveJobID"),
                    ("rollover", "ActiveOutputOperationID"),
                    ("preparation", "ActivePreparationID"),
                )
                if resource[column] is not None
            ]
            if len(owners) > 1:
                raise SourceConflict("The blocking resource has ambiguous ownership.")
            owner = _owner(cursor, account, *owners[0]) if owners else None
            # Cross-account identifiers and blocked-reason text never leave DAL.
            return dict(reason="reserved", version=resource["Version"], owner=owner)
        cursor.execute(
            "SELECT TOP (1) Kind,SourceID FROM ("
            "SELECT 'preparation' AS Kind,p.PreparationID AS SourceID,p.EnqueueSequence AS Ticket FROM dbo.ExportPreparation p "
            "WHERE p.AccountKey=? AND p.State IN ('pending','preflight','sql_pending','writing','committed','uncertain') "
            "UNION ALL SELECT 'job',j.JobID,j.EnqueueSequence FROM dbo.ExportJob j WHERE j.AccountKey=? AND j.State IN ('ready','running','uncertain') "
            "AND NOT EXISTS(SELECT 1 FROM dbo.ExportJobResource m JOIN dbo.ExportContainedTarget t ON m.ResourceKey='destination:'+t.FileID WHERE m.JobID=j.JobID) "
            "UNION ALL SELECT 'rollover',o.OperationID,o.EnqueueSequence FROM KVK.SourceOutputOperation o WHERE o.AccountKey=? AND o.State IN ('closing','ready','running','uncertain') "
            "AND NOT EXISTS(SELECT 1 FROM dbo.ExportTargetContainment c WHERE c.OutputOperationID=o.OperationID AND c.AccountKey=o.AccountKey)"
            ") pending_owner ORDER BY Ticket,Kind,SourceID",
            account,
            account,
            account,
        )
        queued = one(cursor)
        if queued:
            return dict(
                reason="priority", owner=_owner(cursor, account, queued["Kind"], queued["SourceID"])
            )
        cursor.execute(
            "SELECT StreamID,Version,JobID,PreparationID,OutputOperationID FROM dbo.ExportExecutionStream WHERE ActiveAccountKey=?",
            account,
        )
        stream = one(cursor)
        if stream:
            owners = [
                (kind, stream[column])
                for kind, column in (
                    ("job", "JobID"),
                    ("rollover", "OutputOperationID"),
                    ("preparation", "PreparationID"),
                )
                if stream[column] is not None
            ]
            if len(owners) != 1:
                raise SourceConflict("The active stream has ambiguous recovery ownership.")
            return dict(
                reason="active_stream",
                version=stream["Version"],
                owner=_owner(cursor, account, *owners[0]),
            )
    return None
