"""Service helpers for best-effort Rally Forts import audit writes."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import logging
from typing import Any

from services import import_audit_service

logger = logging.getLogger(__name__)

RALLY_FORTS_AUDIT_IMPORT_KIND = "rally_forts"
RALLY_FORTS_AUDIT_SOURCE_TYPE = "discord_upload_xlsx"
RALLY_FORTS_AUDIT_ATTACHMENT_SAVE_PHASE = "rally_forts_attachment_save"
RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE = "rally_forts_file_classify"
RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE = "rally_forts_sql_preflight"
RALLY_FORTS_AUDIT_DAILY_INGEST_PHASE = "rally_forts_daily_ingest"
RALLY_FORTS_AUDIT_ALLTIME_INGEST_PHASE = "rally_forts_alltime_ingest"
RALLY_FORTS_AUDIT_BACKUP_PHASE = "rally_forts_log_backup_schedule"
RALLY_FORTS_AUDIT_EXTERNAL_TABLE = "dbo.IngestionLog"

AuditThreadRunner = Callable[..., Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class RallyFortsImportAuditContext:
    source_filename: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    entry_point: str = "rally_forts_upload"


def audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def audit_duration_ms(started: datetime) -> int:
    started_utc = started.replace(tzinfo=UTC) if started.tzinfo is None else started.astimezone(UTC)
    return max(0, int((datetime.now(UTC) - started_utc).total_seconds() * 1000))


def rally_forts_external_batch_id(ingestion_id: int) -> str:
    return str(int(ingestion_id))


def rally_forts_audit_details(
    context: RallyFortsImportAuditContext,
    *,
    file_kind: str | None = None,
    rows_parsed: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    as_of: str | None = None,
    ingestion_id: int | None = None,
    reason: str | None = None,
    error: str | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {"entry_point": context.entry_point}
    if file_kind:
        details["file_kind"] = file_kind
    if rows_parsed is not None:
        details["rows_parsed"] = int(rows_parsed)
    if rows_staged is not None:
        details["rows_staged"] = int(rows_staged)
    if rows_written is not None:
        details["rows_written"] = int(rows_written)
    if rows_skipped is not None:
        details["rows_skipped"] = int(rows_skipped)
    if as_of:
        details["as_of"] = as_of
    if ingestion_id is not None:
        details["ingestion_id"] = int(ingestion_id)
    if reason:
        details["reason"] = reason
    if error:
        details["error"] = error
    return details


def _sha256_file(path: str | None) -> str | None:
    if not path:
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        logger.debug("rally_forts_audit_hash_failed", exc_info=True)
        return None


def _start_rally_forts_audit_batch_sync(
    context: RallyFortsImportAuditContext,
    local_path: str | None,
):
    return import_audit_service.start_batch_best_effort(
        import_kind=RALLY_FORTS_AUDIT_IMPORT_KIND,
        source_type=RALLY_FORTS_AUDIT_SOURCE_TYPE,
        source_filename=context.source_filename,
        source_file_hash_sha256=_sha256_file(local_path),
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        details=rally_forts_audit_details(context),
    )


async def start_rally_forts_audit_batch(
    *,
    context: RallyFortsImportAuditContext,
    local_path: str | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(_start_rally_forts_audit_batch_sync, context, local_path)
    except Exception:
        logger.warning("rally_forts_audit_start_failed; continuing import", exc_info=True)
        return None


async def record_rally_forts_audit_phase(
    batch_ref,
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
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.record_phase_best_effort,
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
            "rally_forts_audit_phase_failed phase=%s; continuing import",
            phase_name,
            exc_info=True,
        )


async def complete_rally_forts_audit_batch(
    batch_ref,
    *,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_id: str | None = None,
    details: object = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.complete_batch_best_effort,
            batch_ref,
            status=status,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            external_batch_table=RALLY_FORTS_AUDIT_EXTERNAL_TABLE if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("rally_forts_audit_complete_failed; continuing import", exc_info=True)


async def fail_rally_forts_audit_batch(
    batch_ref,
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
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.fail_batch_best_effort,
            batch_ref,
            status=status,
            error_type=error_type,
            error_text=error_text,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            external_batch_table=RALLY_FORTS_AUDIT_EXTERNAL_TABLE if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("rally_forts_audit_fail_failed; continuing import", exc_info=True)
