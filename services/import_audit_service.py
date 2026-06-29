"""Best-effort service wrappers for durable import audit writes."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import json
import logging
from typing import Any

from stats.dal import import_audit_dal
from stats.dal.import_audit_dal import ImportAuditBatchRef

logger = logging.getLogger(__name__)

MAX_ERROR_TYPE_LENGTH = 128
MAX_ERROR_TEXT_LENGTH = 2000


def _as_batch_id(batch_ref: ImportAuditBatchRef | int | None) -> int | None:
    if batch_ref is None:
        return None
    if isinstance(batch_ref, ImportAuditBatchRef):
        return batch_ref.import_audit_batch_id
    try:
        return int(batch_ref)
    except Exception:
        return None


def _details_json(details: Any) -> str | None:
    if details is None:
        return None
    return json.dumps(details, ensure_ascii=False, default=str)


def _truncate(value: Any, max_length: int) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text[:max_length]


def start_batch_best_effort(
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
    details: Any = None,
    correlation_id: str | None = None,
    writer: Callable[..., ImportAuditBatchRef] = import_audit_dal.start_import_audit_batch,
) -> ImportAuditBatchRef | None:
    try:
        return writer(
            import_kind=import_kind,
            source_type=source_type,
            source_filename=source_filename,
            source_file_hash_sha256=source_file_hash_sha256,
            source_message_id=source_message_id,
            source_channel_id=source_channel_id,
            actor_discord_id=actor_discord_id,
            queue_name=queue_name,
            queue_channel_id=queue_channel_id,
            external_batch_table=external_batch_table,
            external_batch_id=external_batch_id,
            status=status,
            rows_in_source=rows_in_source,
            details_json=_details_json(details),
            correlation_id=correlation_id,
        )
    except Exception:
        logger.warning(
            "[IMPORT_AUDIT] Failed to start %s audit batch; continuing.",
            import_kind,
            exc_info=True,
        )
        return None


def record_phase_best_effort(
    batch_ref: ImportAuditBatchRef | int | None,
    *,
    phase_name: str,
    phase_status: str,
    started_at_utc: datetime | None = None,
    completed_at_utc: datetime | None = None,
    rows_in: int | None = None,
    rows_out: int | None = None,
    duration_ms: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    details: Any = None,
    set_batch_status: str | None = None,
    writer: Callable[..., int | None] = import_audit_dal.record_import_audit_phase,
) -> int | None:
    import_audit_batch_id = _as_batch_id(batch_ref)
    if import_audit_batch_id is None:
        return None
    try:
        return writer(
            import_audit_batch_id=import_audit_batch_id,
            phase_name=phase_name,
            phase_status=phase_status,
            started_at_utc=started_at_utc,
            completed_at_utc=completed_at_utc,
            rows_in=rows_in,
            rows_out=rows_out,
            duration_ms=duration_ms,
            error_type=_truncate(error_type, MAX_ERROR_TYPE_LENGTH),
            error_text=_truncate(error_text, MAX_ERROR_TEXT_LENGTH),
            details_json=_details_json(details),
            set_batch_status=set_batch_status,
        )
    except Exception:
        logger.warning(
            "[IMPORT_AUDIT] Failed to record %s phase for batch %s; continuing.",
            phase_name,
            import_audit_batch_id,
            exc_info=True,
        )
        return None


def complete_batch_best_effort(
    batch_ref: ImportAuditBatchRef | int | None,
    *,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_table: str | None = None,
    external_batch_id: str | None = None,
    details: Any = None,
    completed_at_utc: datetime | None = None,
    writer: Callable[..., None] = import_audit_dal.complete_import_audit_batch,
) -> bool:
    import_audit_batch_id = _as_batch_id(batch_ref)
    if import_audit_batch_id is None:
        return False
    try:
        writer(
            import_audit_batch_id=import_audit_batch_id,
            status=status,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            external_batch_table=external_batch_table,
            external_batch_id=external_batch_id,
            details_json=_details_json(details),
            completed_at_utc=completed_at_utc,
        )
        return True
    except Exception:
        logger.warning(
            "[IMPORT_AUDIT] Failed to complete audit batch %s; continuing.",
            import_audit_batch_id,
            exc_info=True,
        )
        return False


def fail_batch_best_effort(
    batch_ref: ImportAuditBatchRef | int | None,
    *,
    status: str = "failed",
    error_type: str | None = None,
    error_text: str | None = None,
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_table: str | None = None,
    external_batch_id: str | None = None,
    details: Any = None,
    completed_at_utc: datetime | None = None,
    writer: Callable[..., None] = import_audit_dal.fail_import_audit_batch,
) -> bool:
    import_audit_batch_id = _as_batch_id(batch_ref)
    if import_audit_batch_id is None:
        return False
    try:
        writer(
            import_audit_batch_id=import_audit_batch_id,
            status=status,
            error_type=_truncate(error_type, MAX_ERROR_TYPE_LENGTH),
            error_text=_truncate(error_text, MAX_ERROR_TEXT_LENGTH),
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            external_batch_table=external_batch_table,
            external_batch_id=external_batch_id,
            details_json=_details_json(details),
            completed_at_utc=completed_at_utc,
        )
        return True
    except Exception:
        logger.warning(
            "[IMPORT_AUDIT] Failed to fail audit batch %s; continuing.",
            import_audit_batch_id,
            exc_info=True,
        )
        return False
