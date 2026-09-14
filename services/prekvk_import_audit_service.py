"""Service helpers for best-effort PreKvK import audit writes."""

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

PREKVK_AUDIT_IMPORT_KIND = "prekvk"
PREKVK_AUDIT_SOURCE_TYPE = "discord_upload_xlsx"
PREKVK_AUDIT_PARSE_PHASE = "prekvk_xlsx_parse"
PREKVK_AUDIT_INGEST_PHASE = "prekvk_sql_ingest"
PREKVK_AUDIT_REFRESH_PHASE = "prekvk_post_import_refresh"
PREKVK_AUDIT_SCAN_TABLE = "dbo.PreKvk_Scan"
PREKVK_AUDIT_HISTORY_TABLE = "dbo.PreKvk_ImportHistory"

AuditThreadRunner = Callable[..., Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class PreKvkImportAuditContext:
    source_filename: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    kvk_no: int | None = None
    entry_point: str = "prekvk_upload"


def audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def audit_duration_ms(started: datetime) -> int:
    started_utc = started.replace(tzinfo=UTC) if started.tzinfo is None else started.astimezone(UTC)
    return max(0, int((datetime.now(UTC) - started_utc).total_seconds() * 1000))


def prekvk_scan_external_batch_id(kvk_no: int, scan_id: int) -> str:
    return f"{int(kvk_no)}:{int(scan_id)}"


def prekvk_audit_details(
    context: PreKvkImportAuditContext,
    *,
    rows_parsed: int | None = None,
    kvk_no: int | None = None,
    scan_id: int | None = None,
    history_id: int | None = None,
    importer_status: str | None = None,
    importer_phase: str | None = None,
    error: str | None = None,
    refresh_failed: bool | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {
        "entry_point": context.entry_point,
    }
    resolved_kvk_no = kvk_no if kvk_no is not None else context.kvk_no
    if resolved_kvk_no is not None:
        details["kvk_no"] = int(resolved_kvk_no)
    if rows_parsed is not None:
        details["rows_parsed"] = int(rows_parsed)
    if scan_id is not None:
        details["scan_id"] = int(scan_id)
    if history_id is not None:
        details["history_id"] = int(history_id)
    if importer_status:
        details["importer_status"] = importer_status
    if importer_phase:
        details["importer_phase"] = importer_phase
    if error:
        details["error"] = error
    if refresh_failed is not None:
        details["refresh_failed"] = refresh_failed
    return details


def _sha256_hex(content: bytes | None) -> str | None:
    if content is None:
        return None
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception:
        logger.debug("prekvk_audit_hash_failed", exc_info=True)
        return None


def _start_prekvk_audit_batch_sync(
    context: PreKvkImportAuditContext,
    xlsx_bytes: bytes | None,
):
    return import_audit_service.start_batch_best_effort(
        import_kind=PREKVK_AUDIT_IMPORT_KIND,
        source_type=PREKVK_AUDIT_SOURCE_TYPE,
        source_filename=context.source_filename,
        source_file_hash_sha256=_sha256_hex(xlsx_bytes),
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        details=prekvk_audit_details(context),
    )


async def start_prekvk_audit_batch(
    *,
    context: PreKvkImportAuditContext,
    xlsx_bytes: bytes | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(
            _start_prekvk_audit_batch_sync,
            context,
            xlsx_bytes,
        )
    except Exception:
        logger.warning("prekvk_audit_start_failed; continuing import", exc_info=True)
        return None


async def record_prekvk_audit_phase(
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
            "prekvk_audit_phase_failed phase=%s; continuing import",
            phase_name,
            exc_info=True,
        )


async def complete_prekvk_audit_batch(
    batch_ref,
    *,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    external_batch_table: str | None = None,
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
            external_batch_table=external_batch_table if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("prekvk_audit_complete_failed; continuing import", exc_info=True)


async def fail_prekvk_audit_batch(
    batch_ref,
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
            external_batch_table=external_batch_table if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("prekvk_audit_fail_failed; continuing import", exc_info=True)
