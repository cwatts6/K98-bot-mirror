"""Scoped historical export closeout; never change a resource or provider stream."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.config_read_containment import stream_wire
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity


class FailedExportCloseoutDAL:
    def __init__(self, connect, *, account, storage_owner):
        self.connect, self.account, self.storage_owner = connect, account, storage_owner

    def _snapshot(self, cursor, job_id):
        _mutex(cursor, "account:" + self.account)
        cursor.execute(
            "SELECT * FROM dbo.ExportJob WITH(UPDLOCK,HOLDLOCK) WHERE JobID=? "
            "AND AccountKey=? AND StorageOwner=? AND ConsumerKind IN ('scan_data','all_kvk')",
            identity(job_id),
            self.account,
            self.storage_owner,
        )
        job = one(cursor)
        if job is None:
            raise SourceConflict("Failed export is outside registered recovery custody.")
        cursor.execute(
            "SELECT ResourceKey FROM dbo.ExportJobResource WITH(UPDLOCK,HOLDLOCK) "
            "WHERE JobID=? ORDER BY ResourceKey",
            job_id,
        )
        membership = [r["ResourceKey"] for r in rows(cursor)]
        cursor.execute(
            "SELECT * FROM dbo.ExportResource WITH(UPDLOCK,HOLDLOCK) WHERE ActiveJobID=? "
            "ORDER BY ResourceKey",
            job_id,
        )
        held = rows(cursor)
        cursor.execute(
            "SELECT * FROM dbo.ExportAttempt WITH(UPDLOCK,HOLDLOCK) WHERE JobID=? ORDER BY AttemptID",
            job_id,
        )
        attempts = rows(cursor)
        cursor.execute(
            "SELECT * FROM dbo.ExportExecutionStream WITH(UPDLOCK,HOLDLOCK) WHERE JobID=? "
            "ORDER BY CONVERT(varchar(36),StreamID)",
            job_id,
        )
        streams = [stream_wire(r) for r in rows(cursor)]
        cursor.execute(
            "SELECT SessionID,AuthorityPrincipal FROM dbo.ExportExecutionSession WHERE SessionID IN "
            "(SELECT SessionID FROM dbo.ExportExecutionStream WHERE JobID=?) ORDER BY SessionID",
            job_id,
        )
        sessions = rows(cursor)
        cursor.execute("SELECT USER_NAME() AS principal")
        return _wire(
            dict(
                job=job,
                membership=membership,
                held=held,
                attempts=attempts,
                streams=streams,
                sessions=sessions,
                principal=one(cursor)["principal"],
            )
        )

    def snapshot(self, job_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, identity(job_id))

    def retire(self, expected, receipt):
        with transaction(self.connect) as cursor:
            job = expected["job"]
            current = self._snapshot(cursor, job["JobID"])
            if (
                current != expected
                or job["State"] != "failed"
                or current["held"]
                or current["attempts"]
            ):
                raise SourceConflict("Failed export changed; no closeout was recorded.")
            provenance = json.loads(job["ProvenanceJson"])
            if provenance.get("failed_export_retired") or provenance.get("safe_retry", {}).get(
                "requested"
            ):
                raise SourceConflict("Another decision already exists for this failed export.")
            provenance["failed_export_retired"] = receipt
            _cas(
                cursor,
                "UPDATE dbo.ExportJob SET ProvenanceJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE JobID=? AND Version=? AND State='failed' AND OwnerID=? AND Fence=?",
                bounded_json(provenance),
                job["JobID"],
                job["Version"],
                job["OwnerID"],
                job["Fence"],
            )
