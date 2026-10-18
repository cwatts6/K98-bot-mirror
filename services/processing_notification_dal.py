"""Read exact correlated export evidence. No provider calls or state mutations."""

import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from services.export_coordination_dal import identity


def read_export_outcome(runtime, run):
    scope = (runtime.account, runtime.store.storage_owner, "scan_data")
    if (run["account"], run["storage_owner"], "scan_data") != scope:
        raise SourceConflict("Notification belongs to another protected runtime.")
    with transaction(runtime.dal.connect) as cursor:
        cursor.execute(
            "SELECT AccountKey,StorageOwner,ConsumerKind,JobID FROM dbo.ExportPreparation WHERE PreparationID=?",
            identity(run["preparation_id"]),
        )
        prep = one(cursor)
        if not prep or (prep["AccountKey"], prep["StorageOwner"], prep["ConsumerKind"]) != scope:
            raise SourceConflict("Exact preparation scope differs.")
        if prep["JobID"] is None:
            return dict(state="pending", job_id=None, links=[])
        job_id = identity(prep["JobID"])
        if run.get("job_id") and job_id != run["job_id"]:
            raise SourceConflict("Preparation job differs from its registered notification.")
        cursor.execute("SELECT * FROM dbo.ExportJob WHERE JobID=?", job_id)
        job = one(cursor)
        if not job or (job["AccountKey"], job["StorageOwner"], job["ConsumerKind"]) != scope:
            raise SourceConflict("Exact export job scope differs.")
        result = dict(state=job["State"], job_id=job_id, links=[])
        if job["State"] != "confirmed":
            return result
        cursor.execute(
            "SELECT * FROM dbo.ExportAttempt WHERE JobID=? AND Phase='published' AND OwnerID=? AND Fence=?",
            job_id,
            job["OwnerID"],
            job["Fence"],
        )
        attempts = rows(cursor)
        if len(attempts) != 1:
            raise SourceConflict("Exact published attempt receipt required.")
        attempt = attempts[0]
        cursor.execute(
            "SELECT FileID,VerificationState,QuarantineState,AclState FROM dbo.ExportAttemptPart WHERE AttemptID=? ORDER BY PartNo",
            attempt["AttemptID"],
        )
        parts = rows(cursor)
        receipt = json.loads(attempt["ReceiptJson"])
        if (
            len(parts) != attempt["PartCount"]
            or receipt.get("attempt_id") != identity(attempt["AttemptID"])
            or receipt.get("fence") != job["Fence"]
            or receipt.get("files") != [p["FileID"] for p in parts]
            or any(
                p["VerificationState"] != "verified" or p["QuarantineState"] != "none"
                for p in parts
            )
        ):
            raise SourceConflict("Published export evidence is incomplete.")
        # Only public outputs get public analysis links. Never publish private IDs.
        links = [
            "https://docs.google.com/spreadsheets/d/" + p["FileID"]
            for p in parts
            if p["AclState"] in {"public_viewer", "public_editor"}
            and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", p["FileID"])
        ]
        result["links"] = links[:20]
        if len(links) > 20:
            result["additional_links"] = len(links) - 20
        return result
