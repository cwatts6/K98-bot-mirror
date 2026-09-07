"""Data access helpers for durable import audit records."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from constants import _conn_trusted
from file_utils import fetch_one_dict


@dataclass(frozen=True, slots=True)
class ImportAuditBatchRef:
    import_audit_batch_id: int
    correlation_id: str


def _enable_autocommit(conn: Any) -> None:
    try:
        conn.autocommit = True
    except Exception:
        pass


def start_import_audit_batch(
    *,
    import_kind: str,
    source_type: str | None = None,
    source_filename: str | None = None,
    source_file_hash_sha256: str | None = None,
    source_message_id: int | None = None,
    source_channel_id: int | None = None,
    actor_discord_id: int | None = None,
    queue_name: str | None = None,
    queue_channel_id: int | None = None,
    external_batch_table: str | None = None,
    external_batch_id: str | None = None,
    status: str = "started",
    rows_in_source: int | None = None,
    details_json: str | None = None,
    correlation_id: str | None = None,
    connection_factory: Callable[[], Any] = _conn_trusted,
) -> ImportAuditBatchRef:
    """Create a durable import audit batch via the SQL-owned writer procedure."""
    with connection_factory() as conn:
        _enable_autocommit(conn)
        cur = conn.cursor()
        cur.execute(
            """
            EXEC dbo.usp_ImportAudit_StartBatch
                @ImportKind = ?,
                @SourceType = ?,
                @SourceFilename = ?,
                @SourceFileHashSha256 = ?,
                @SourceMessageId = ?,
                @SourceChannelId = ?,
                @ActorDiscordId = ?,
                @QueueName = ?,
                @QueueChannelId = ?,
                @ExternalBatchTable = ?,
                @ExternalBatchId = ?,
                @Status = ?,
                @RowsInSource = ?,
                @DetailsJson = ?,
                @CorrelationId = ?;
            """,
            import_kind,
            source_type,
            source_filename,
            source_file_hash_sha256,
            source_message_id,
            source_channel_id,
            actor_discord_id,
            queue_name,
            queue_channel_id,
            external_batch_table,
            external_batch_id,
            status,
            rows_in_source,
            details_json,
            correlation_id,
        )
        row = fetch_one_dict(cur)
        if not row:
            raise RuntimeError("dbo.usp_ImportAudit_StartBatch returned no row.")
        return ImportAuditBatchRef(
            import_audit_batch_id=int(row["ImportAuditBatchId"]),
            correlation_id=str(row["CorrelationId"]),
        )


def record_import_audit_phase(
    *,
    import_audit_batch_id: int,
    phase_name: str,
    phase_status: str,
    started_at_utc: Any = None,
    completed_at_utc: Any = None,
    rows_in: int | None = None,
    rows_out: int | None = None,
    duration_ms: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    details_json: str | None = None,
    set_batch_status: str | None = None,
    connection_factory: Callable[[], Any] = _conn_trusted,
) -> int | None:
    """Record one import phase through the SQL-owned writer procedure."""
    with connection_factory() as conn:
        _enable_autocommit(conn)
        cur = conn.cursor()
        cur.execute(
            """
            EXEC dbo.usp_ImportAudit_RecordPhase
                @ImportAuditBatchId = ?,
                @PhaseName = ?,
                @PhaseStatus = ?,
                @StartedAtUtc = ?,
                @CompletedAtUtc = ?,
                @RowsIn = ?,
                @RowsOut = ?,
                @DurationMs = ?,
                @ErrorType = ?,
                @ErrorText = ?,
                @DetailsJson = ?,
                @SetBatchStatus = ?;
            """,
            import_audit_batch_id,
            phase_name,
            phase_status,
            started_at_utc,
            completed_at_utc,
            rows_in,
            rows_out,
            duration_ms,
            error_type,
            error_text,
            details_json,
            set_batch_status,
        )
        row = fetch_one_dict(cur)
        return int(row["ImportAuditPhaseId"]) if row else None


def fetch_import_audit_batch_by_external_id(
    *,
    import_kind: str,
    external_batch_table: str,
    external_batch_id: str,
    connection_factory: Callable[[], Any] = _conn_trusted,
) -> ImportAuditBatchRef | None:
    """Fetch the latest durable audit batch for a domain batch correlation."""
    with connection_factory() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP (1)
                   ImportAuditBatchId,
                   CorrelationId
            FROM dbo.ImportAuditBatch
            WHERE ImportKind = ?
              AND ExternalBatchTable = ?
              AND ExternalBatchId = ?
            ORDER BY StartedAtUtc DESC, ImportAuditBatchId DESC;
            """,
            import_kind,
            external_batch_table,
            external_batch_id,
        )
        row = fetch_one_dict(cur)
        if not row:
            return None
        return ImportAuditBatchRef(
            import_audit_batch_id=int(row["ImportAuditBatchId"]),
            correlation_id=str(row["CorrelationId"]),
        )


def complete_import_audit_batch(
    *,
    import_audit_batch_id: int,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_table: str | None = None,
    external_batch_id: str | None = None,
    details_json: str | None = None,
    completed_at_utc: Any = None,
    connection_factory: Callable[[], Any] = _conn_trusted,
) -> None:
    """Mark an import audit batch complete through the SQL-owned writer procedure."""
    with connection_factory() as conn:
        _enable_autocommit(conn)
        cur = conn.cursor()
        cur.execute(
            """
            EXEC dbo.usp_ImportAudit_CompleteBatch
                @ImportAuditBatchId = ?,
                @Status = ?,
                @RowsInSource = ?,
                @RowsStaged = ?,
                @RowsWritten = ?,
                @RowsSkipped = ?,
                @ExternalBatchTable = ?,
                @ExternalBatchId = ?,
                @DetailsJson = ?,
                @CompletedAtUtc = ?;
            """,
            import_audit_batch_id,
            status,
            rows_in_source,
            rows_staged,
            rows_written,
            rows_skipped,
            external_batch_table,
            external_batch_id,
            details_json,
            completed_at_utc,
        )
        fetch_one_dict(cur)


def fail_import_audit_batch(
    *,
    import_audit_batch_id: int,
    status: str = "failed",
    rows_in_source: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_table: str | None = None,
    external_batch_id: str | None = None,
    details_json: str | None = None,
    completed_at_utc: Any = None,
    connection_factory: Callable[[], Any] = _conn_trusted,
) -> None:
    """Mark an import audit batch failed through the SQL-owned writer procedure."""
    with connection_factory() as conn:
        _enable_autocommit(conn)
        cur = conn.cursor()
        cur.execute(
            """
            EXEC dbo.usp_ImportAudit_FailBatch
                @ImportAuditBatchId = ?,
                @Status = ?,
                @RowsInSource = ?,
                @ErrorType = ?,
                @ErrorText = ?,
                @RowsStaged = ?,
                @RowsWritten = ?,
                @RowsSkipped = ?,
                @ExternalBatchTable = ?,
                @ExternalBatchId = ?,
                @DetailsJson = ?,
                @CompletedAtUtc = ?;
            """,
            import_audit_batch_id,
            status,
            rows_in_source,
            error_type,
            error_text,
            rows_staged,
            rows_written,
            rows_skipped,
            external_batch_table,
            external_batch_id,
            details_json,
            completed_at_utc,
        )
        fetch_one_dict(cur)
