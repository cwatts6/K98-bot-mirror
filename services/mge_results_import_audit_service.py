"""Service helpers for best-effort MGE results import audit writes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import logging
from typing import Any

from services import import_audit_service

logger = logging.getLogger(__name__)

MGE_RESULTS_AUDIT_IMPORT_KIND = "mge_results"
MGE_RESULTS_AUDIT_SOURCE_TYPE = "discord_upload_xlsx"
MGE_RESULTS_AUDIT_PRECHECK_PHASE = "mge_results_precheck"
MGE_RESULTS_AUDIT_PARSE_PHASE = "mge_results_xlsx_parse"
MGE_RESULTS_AUDIT_INGEST_PHASE = "mge_results_sql_ingest"
MGE_RESULTS_AUDIT_BACKUP_PHASE = "mge_results_post_import_backup"
MGE_RESULTS_AUDIT_EXTERNAL_TABLE = "dbo.MGE_ResultImports"


@dataclass(frozen=True, slots=True)
class MgeResultsImportAuditContext:
    source_filename: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    event_id: int | None = None
    event_mode: str | None = None
    source: str = "auto"
    entry_point: str = "mge_results_upload"


def audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def audit_duration_ms(started: datetime) -> int:
    started_utc = started.replace(tzinfo=UTC) if started.tzinfo is None else started.astimezone(UTC)
    return max(0, int((datetime.now(UTC) - started_utc).total_seconds() * 1000))


def mge_results_external_batch_id(import_id: int) -> str:
    return str(int(import_id))


def mge_results_audit_details(
    context: MgeResultsImportAuditContext,
    *,
    event_id: int | None = None,
    event_mode: str | None = None,
    import_id: int | None = None,
    rows_parsed: int | None = None,
    rows_written: int | None = None,
    duplicate_reason: str | None = None,
    overwrite_confirmed: bool | None = None,
    report_type: str | None = None,
    backup_failed: bool | None = None,
    error: str | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {
        "entry_point": context.entry_point,
        "source": context.source,
    }
    resolved_event_id = event_id if event_id is not None else context.event_id
    resolved_event_mode = event_mode if event_mode is not None else context.event_mode
    if resolved_event_id is not None:
        details["event_id"] = int(resolved_event_id)
    if resolved_event_mode:
        details["event_mode"] = resolved_event_mode
    if import_id is not None:
        details["import_id"] = int(import_id)
    if rows_parsed is not None:
        details["rows_parsed"] = int(rows_parsed)
    if rows_written is not None:
        details["rows_written"] = int(rows_written)
    if duplicate_reason:
        details["duplicate_reason"] = duplicate_reason
    if overwrite_confirmed is not None:
        details["overwrite_confirmed"] = overwrite_confirmed
    if report_type:
        details["report_type"] = report_type
    if backup_failed is not None:
        details["backup_failed"] = backup_failed
    if error:
        details["error"] = error
    return details


def _sha256_hex(content: bytes | None) -> str | None:
    if content is None:
        return None
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception:
        logger.debug("mge_results_audit_hash_failed", exc_info=True)
        return None


def start_mge_results_audit_batch(
    context: MgeResultsImportAuditContext,
    xlsx_bytes: bytes | None,
    *,
    source_file_hash_sha256: str | None = None,
):
    try:
        return import_audit_service.start_batch_best_effort(
            import_kind=MGE_RESULTS_AUDIT_IMPORT_KIND,
            source_type=MGE_RESULTS_AUDIT_SOURCE_TYPE,
            source_filename=context.source_filename,
            source_file_hash_sha256=source_file_hash_sha256 or _sha256_hex(xlsx_bytes),
            source_message_id=context.source_message_id,
            source_channel_id=context.source_channel_id,
            actor_discord_id=context.actor_discord_id,
            details=mge_results_audit_details(context),
        )
    except Exception:
        logger.warning("mge_results_audit_start_failed; continuing import", exc_info=True)
        return None


def record_mge_results_audit_phase(
    batch_ref: Any,
    *,
    phase_name: str,
    phase_status: str,
    started_at_utc: datetime | None = None,
    rows_in: int | None = None,
    rows_out: int | None = None,
    duration_ms: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    details: object = None,
    set_batch_status: str | None = None,
) -> None:
    if batch_ref is None:
        return
    try:
        import_audit_service.record_phase_best_effort(
            batch_ref,
            phase_name=phase_name,
            phase_status=phase_status,
            started_at_utc=started_at_utc,
            completed_at_utc=audit_timestamp_utc(),
            rows_in=rows_in,
            rows_out=rows_out,
            duration_ms=duration_ms,
            error_type=error_type,
            error_text=error_text,
            details=details,
            set_batch_status=set_batch_status,
        )
    except Exception:
        logger.warning(
            "mge_results_audit_phase_failed phase=%s; continuing import",
            phase_name,
            exc_info=True,
        )


def complete_mge_results_audit_batch(
    batch_ref: Any,
    *,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_id: str | None = None,
    details: object = None,
) -> None:
    if batch_ref is None:
        return
    try:
        import_audit_service.complete_batch_best_effort(
            batch_ref,
            status=status,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            external_batch_table=MGE_RESULTS_AUDIT_EXTERNAL_TABLE if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("mge_results_audit_complete_failed; continuing import", exc_info=True)


def fail_mge_results_audit_batch(
    batch_ref: Any,
    *,
    status: str = "failed",
    error_type: str | None = None,
    error_text: str | None = None,
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_id: str | None = None,
    details: object = None,
) -> None:
    if batch_ref is None:
        return
    try:
        import_audit_service.fail_batch_best_effort(
            batch_ref,
            status=status,
            error_type=error_type,
            error_text=error_text,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            external_batch_table=MGE_RESULTS_AUDIT_EXTERNAL_TABLE if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("mge_results_audit_fail_failed; continuing import", exc_info=True)
