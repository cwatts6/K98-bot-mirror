"""Atomic configuration publication using the admitted business connection."""

from kvk.dal.new_source_import_dal import SourceConflict
from services.legacy_export_snapshot_service import current_owner, record_writer_completion


def latest_season(cursor):
    # Read our uncommitted configuration on the same connection; a separate
    # metadata connection could wait indefinitely for this transaction's locks.
    cursor.execute("SELECT MAX(KVK_NO) FROM dbo.KVK_Details WHERE KVK_NO IS NOT NULL")
    row = cursor.fetchone()
    while cursor.nextset():
        pass
    return int(row[0]) if row and row[0] is not None else None


def publish(cursor, latest_kvk):
    owner = current_owner()
    if owner is None or owner.kind != "scan_data":
        raise SourceConflict("Atomic configuration publication requires its admitted owner.")
    cursor.execute(
        "EXEC dbo.sp_TARGETS_MASTER @KVK=?, @ExportPreparationID=?",
        latest_kvk,
        owner.claim.preparation_id,
    )
    while cursor.nextset():
        pass
    # A dropped reply after commit can be recovered from this same-transaction
    # receipt. No in-memory success flag authorizes capture or release.
    record_writer_completion(
        cursor=cursor, procedure="ProcConfig and sp_TARGETS_MASTER", atomic_checkpoint=1
    )
