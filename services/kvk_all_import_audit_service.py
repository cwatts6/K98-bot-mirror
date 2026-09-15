"""Service helpers for best-effort KVK_ALL import audit writes."""

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

KVK_ALL_AUDIT_IMPORT_KIND = "kvk_all"
KVK_ALL_AUDIT_ATTACHMENT_READ_PHASE = "kvk_all_attachment_read"
KVK_ALL_AUDIT_SQL_PREFLIGHT_PHASE = "kvk_all_sql_preflight"
KVK_ALL_AUDIT_PARSE_PHASE = "kvk_all_schema_parse"
KVK_ALL_AUDIT_STAGE_PHASE = "kvk_all_stage_insert"
KVK_ALL_AUDIT_INGEST_PHASE = "kvk_all_sql_ingest"
KVK_ALL_AUDIT_RECOMPUTE_PHASE = "kvk_all_recompute_windows"
KVK_ALL_AUDIT_NEGATIVE_PHASE = "kvk_all_negative_check"
KVK_ALL_AUDIT_AUTO_EXPORT_PHASE = "kvk_all_auto_export_schedule"
KVK_ALL_AUDIT_EXTERNAL_TABLE = "KVK.KVK_Scan"
KVK_ALL_AUDIT_DIAGNOSTIC_TABLE = "KVK.KVK_Ingest_Diagnostics"

AuditThreadRunner = Callable[..., Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class KvkAllImportAuditContext:
    source_filename: str | None = None
    source_type: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    entry_point: str = "kvk_all_upload"


def audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def audit_duration_ms(started: datetime) -> int:
    started_utc = started.replace(tzinfo=UTC) if started.tzinfo is None else started.astimezone(UTC)
    return max(0, int((datetime.now(UTC) - started_utc).total_seconds() * 1000))


def kvk_all_source_type(filename: str) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix in {"xlsx", "xls", "csv"}:
        return f"discord_upload_{suffix}"
    return "discord_upload"


def kvk_all_external_batch_id(kvk_no: int, scan_id: int) -> str:
    return f"{int(kvk_no)}:{int(scan_id)}"


def kvk_all_diagnostic_external_batch_id(diagnostic_id: int) -> str:
    return str(int(diagnostic_id))


def kvk_all_audit_details(
    context: KvkAllImportAuditContext,
    *,
    rows_parsed: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    negatives: int | None = None,
    kvk_no: int | None = None,
    scan_id: int | None = None,
    diagnostic_id: int | None = None,
    sheet: str | None = None,
    schema_version: str | None = None,
    error: str | None = None,
    auto_export_enabled: bool | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {"entry_point": context.entry_point}
    if rows_parsed is not None:
        details["rows_parsed"] = int(rows_parsed)
    if rows_staged is not None:
        details["rows_staged"] = int(rows_staged)
    if rows_written is not None:
        details["rows_written"] = int(rows_written)
    if negatives is not None:
        details["negatives"] = int(negatives)
    if kvk_no is not None:
        details["kvk_no"] = int(kvk_no)
    if scan_id is not None:
        details["scan_id"] = int(scan_id)
    if diagnostic_id is not None:
        details["diagnostic_id"] = int(diagnostic_id)
    if sheet:
        details["sheet"] = sheet
    if schema_version:
        details["schema_version"] = schema_version
    if error:
        details["error"] = error
    if auto_export_enabled is not None:
        details["auto_export_enabled"] = auto_export_enabled
    return details


def _sha256_hex(content: bytes | None) -> str | None:
    if content is None:
        return None
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception:
        logger.debug("kvk_all_audit_hash_failed", exc_info=True)
        return None


def _start_kvk_all_audit_batch_sync(
    context: KvkAllImportAuditContext,
    content: bytes | None,
):
    return import_audit_service.start_batch_best_effort(
        import_kind=KVK_ALL_AUDIT_IMPORT_KIND,
        source_type=context.source_type,
        source_filename=context.source_filename,
        source_file_hash_sha256=_sha256_hex(content),
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        details=kvk_all_audit_details(context),
    )


async def start_kvk_all_audit_batch(
    *,
    context: KvkAllImportAuditContext,
    content: bytes | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(_start_kvk_all_audit_batch_sync, context, content)
    except Exception:
        logger.warning("kvk_all_audit_start_failed; continuing import", exc_info=True)
        return None


async def record_kvk_all_audit_phase(
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
            "kvk_all_audit_phase_failed phase=%s; continuing import",
            phase_name,
            exc_info=True,
        )


async def complete_kvk_all_audit_batch(
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
            external_batch_table=KVK_ALL_AUDIT_EXTERNAL_TABLE if external_batch_id else None,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("kvk_all_audit_complete_failed; continuing import", exc_info=True)


async def fail_kvk_all_audit_batch(
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
            external_batch_table=external_batch_table,
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("kvk_all_audit_fail_failed; continuing import", exc_info=True)
