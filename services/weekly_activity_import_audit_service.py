"""Service helpers for best-effort weekly activity import audit writes."""

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

WEEKLY_ACTIVITY_AUDIT_IMPORT_KIND = "weekly_activity"
WEEKLY_ACTIVITY_AUDIT_SOURCE_TYPE = "discord_upload_xlsx"
WEEKLY_ACTIVITY_AUDIT_PARSE_PHASE = "weekly_activity_xlsx_parse"
WEEKLY_ACTIVITY_AUDIT_INGEST_PHASE = "weekly_activity_sql_ingest"
WEEKLY_ACTIVITY_AUDIT_BACKUP_PHASE = "weekly_activity_post_import_backup"
WEEKLY_ACTIVITY_AUDIT_EXTERNAL_TABLE = "dbo.AllianceActivitySnapshotHeader"

AuditThreadRunner = Callable[..., Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class WeeklyActivityImportAuditContext:
    source_filename: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    entry_point: str = "weekly_activity_upload"


def audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def audit_duration_ms(started: datetime) -> int:
    started_utc = started.replace(tzinfo=UTC) if started.tzinfo is None else started.astimezone(UTC)
    return max(0, int((datetime.now(UTC) - started_utc).total_seconds() * 1000))


def weekly_activity_external_batch_id(snapshot_id: int) -> str:
    return str(int(snapshot_id))


def weekly_activity_audit_details(
    context: WeeklyActivityImportAuditContext,
    *,
    rows_parsed: int | None = None,
    snapshot_id: int | None = None,
    delta_rows: int | None = None,
    duplicate: bool | None = None,
    error: str | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {
        "entry_point": context.entry_point,
    }
    if rows_parsed is not None:
        details["rows_parsed"] = int(rows_parsed)
    if snapshot_id is not None:
        details["snapshot_id"] = int(snapshot_id)
    if delta_rows is not None:
        details["delta_rows"] = int(delta_rows)
    if duplicate is not None:
        details["duplicate"] = duplicate
    if error:
        details["error"] = error
    return details


def _sha256_hex(content: bytes | None) -> str | None:
    if content is None:
        return None
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception:
        logger.debug("weekly_activity_audit_hash_failed", exc_info=True)
        return None


def _start_weekly_activity_audit_batch_sync(
    context: WeeklyActivityImportAuditContext,
    xlsx_bytes: bytes | None,
):
    return import_audit_service.start_batch_best_effort(
        import_kind=WEEKLY_ACTIVITY_AUDIT_IMPORT_KIND,
        source_type=WEEKLY_ACTIVITY_AUDIT_SOURCE_TYPE,
        source_filename=context.source_filename,
        source_file_hash_sha256=_sha256_hex(xlsx_bytes),
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        details=weekly_activity_audit_details(context),
    )


async def start_weekly_activity_audit_batch(
    *,
    context: WeeklyActivityImportAuditContext,
    xlsx_bytes: bytes | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(
            _start_weekly_activity_audit_batch_sync,
            context,
            xlsx_bytes,
        )
    except Exception:
        logger.warning("weekly_activity_audit_start_failed; continuing import", exc_info=True)
        return None


async def record_weekly_activity_audit_phase(
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
            "weekly_activity_audit_phase_failed phase=%s; continuing import",
            phase_name,
            exc_info=True,
        )


async def complete_weekly_activity_audit_batch(
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
            external_batch_table=(
                WEEKLY_ACTIVITY_AUDIT_EXTERNAL_TABLE if external_batch_id else None
            ),
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("weekly_activity_audit_complete_failed; continuing import", exc_info=True)


async def fail_weekly_activity_audit_batch(
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
            external_batch_table=(
                WEEKLY_ACTIVITY_AUDIT_EXTERNAL_TABLE if external_batch_id else None
            ),
            external_batch_id=external_batch_id,
            details=details,
        )
    except Exception:
        logger.warning("weekly_activity_audit_fail_failed; continuing import", exc_info=True)
