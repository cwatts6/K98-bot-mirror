"""Weekly alliance activity workbook upload route for the legacy listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from services.weekly_activity_import_audit_service import (
    WEEKLY_ACTIVITY_AUDIT_BACKUP_PHASE,
    WEEKLY_ACTIVITY_AUDIT_INGEST_PHASE,
    WEEKLY_ACTIVITY_AUDIT_PARSE_PHASE,
    WeeklyActivityImportAuditContext,
    audit_duration_ms,
    complete_weekly_activity_audit_batch,
    fail_weekly_activity_audit_batch,
    record_weekly_activity_audit_phase,
    start_weekly_activity_audit_batch,
    weekly_activity_audit_details,
    weekly_activity_external_batch_id,
)
from upload_routes.common import message_source_fields, resolve_notify_channel, schedule_best_effort
from utils import utcnow
from weekly_activity_importer import ingest_weekly_activity_excel, parse_activity_excel

logger = logging.getLogger(__name__)


async def count_weekly_activity_source_rows(content: bytes) -> int:
    """Parse weekly activity workbook bytes off the event loop and return source rows."""
    parsed_df = await asyncio.to_thread(parse_activity_excel, content)
    return len(parsed_df)


@dataclass(frozen=True)
class WeeklyActivityRouteDeps:
    activity_upload_channel_id: int
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    server: str | None
    database: str | None
    username: str | None
    password: str | None
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    count_source_rows: Callable[[bytes], Awaitable[int]] = count_weekly_activity_source_rows
    start_audit_batch: Callable[..., Awaitable[Any]] = start_weekly_activity_audit_batch
    record_audit_phase: Callable[..., Awaitable[None]] = record_weekly_activity_audit_phase
    complete_audit_batch: Callable[..., Awaitable[None]] = complete_weekly_activity_audit_batch
    fail_audit_batch: Callable[..., Awaitable[None]] = fail_weekly_activity_audit_batch
    now_utc: Callable[[], Any] = utcnow


def _is_weekly_activity_filename(filename: str) -> bool:
    return filename.lower().endswith("1198_alliance_activity.xlsx")


async def handle_weekly_activity_upload(message: Any, deps: WeeklyActivityRouteDeps) -> bool:
    """Handle weekly alliance activity workbooks from the configured upload channel."""
    if message.channel.id != deps.activity_upload_channel_id or not message.attachments:
        return False

    target = next(
        (a for a in message.attachments if _is_weekly_activity_filename(a.filename)),
        None,
    )
    if target is None:
        return False

    target_ch = await resolve_notify_channel(
        deps.get_notify_channel,
        message.channel,
        logger,
        "weekly_activity_upload",
    )

    audit_context: WeeklyActivityImportAuditContext | None = None
    audit_ref: Any = None
    audit_terminal_recorded = False
    parse_succeeded = False
    rows_parsed: int | None = None
    snap_id: int | None = None
    row_count: int | None = None
    external_batch_id: str | None = None

    try:
        file_bytes = await target.read()
        ok = await deps.ensure_sql_headroom_or_notify(target_ch)
        if not ok:
            return True

        audit_context = WeeklyActivityImportAuditContext(
            source_filename=target.filename,
            source_message_id=int(message.id) if getattr(message, "id", None) is not None else None,
            source_channel_id=(
                int(message.channel.id)
                if getattr(message.channel, "id", None) is not None
                else None
            ),
            actor_discord_id=(
                int(message.author.id) if getattr(message.author, "id", None) is not None else None
            ),
        )
        audit_ref = await deps.start_audit_batch(
            context=audit_context,
            xlsx_bytes=file_bytes,
        )

        parse_started = deps.now_utc()
        try:
            rows_parsed = await deps.count_source_rows(file_bytes)
            parse_succeeded = True
            await deps.record_audit_phase(
                audit_ref,
                phase_name=WEEKLY_ACTIVITY_AUDIT_PARSE_PHASE,
                phase_status="completed",
                started_at_utc=parse_started.replace(tzinfo=None),
                rows_out=rows_parsed,
                duration_ms=audit_duration_ms(parse_started),
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                ),
            )
        except Exception as exc:
            rows_parsed = 0
            await deps.record_audit_phase(
                audit_ref,
                phase_name=WEEKLY_ACTIVITY_AUDIT_PARSE_PHASE,
                phase_status="failed",
                started_at_utc=parse_started.replace(tzinfo=None),
                rows_out=0,
                duration_ms=audit_duration_ms(parse_started),
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=0,
                    error=str(exc),
                ),
            )
            await deps.fail_audit_batch(
                audit_ref,
                error_type=type(exc).__name__,
                error_text=str(exc),
                rows_in_source=0,
                rows_staged=0,
                rows_written=0,
                rows_skipped=0,
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=0,
                    error=str(exc),
                ),
            )
            audit_terminal_recorded = True
            raise

        ingest_started = deps.now_utc()
        try:
            snap_id, row_count = await deps.offload_callable(
                ingest_weekly_activity_excel,
                content=file_bytes,
                snapshot_ts_utc=message.created_at,
                message_id=message.id,
                channel_id=message.channel.id,
                server=deps.server,
                database=deps.database,
                username=deps.username,
                password=deps.password,
                source_filename=target.filename,
                name="ingest_weekly_activity_excel",
                prefer_process=True,
                meta={"filename": target.filename},
            )
        except Exception as exc:
            await deps.record_audit_phase(
                audit_ref,
                phase_name=WEEKLY_ACTIVITY_AUDIT_INGEST_PHASE,
                phase_status="failed",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=rows_parsed,
                duration_ms=audit_duration_ms(ingest_started),
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                    error=str(exc),
                ),
            )
            raise
        if snap_id == 0:
            await deps.record_audit_phase(
                audit_ref,
                phase_name=WEEKLY_ACTIVITY_AUDIT_INGEST_PHASE,
                phase_status="duplicate",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=rows_parsed,
                rows_out=0,
                duration_ms=audit_duration_ms(ingest_started),
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                    delta_rows=0,
                    duplicate=True,
                ),
                set_batch_status="duplicate",
            )
            await deps.complete_audit_batch(
                audit_ref,
                status="duplicate",
                rows_in_source=rows_parsed,
                rows_staged=0,
                rows_written=0,
                rows_skipped=rows_parsed,
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                    delta_rows=0,
                    duplicate=True,
                ),
            )
            audit_terminal_recorded = True
            try:
                await deps.send_embed(
                    target_ch,
                    "Alliance Activity Import",
                    {"Status": "Duplicate detected for this week. Skipped."},
                    0xF1C40F,
                )
            except Exception:
                logger.exception("weekly_activity_duplicate_notification_failed")
        else:
            external_batch_id = weekly_activity_external_batch_id(snap_id)
            await deps.record_audit_phase(
                audit_ref,
                phase_name=WEEKLY_ACTIVITY_AUDIT_INGEST_PHASE,
                phase_status="completed",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=rows_parsed,
                rows_out=row_count,
                duration_ms=audit_duration_ms(ingest_started),
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                    snapshot_id=snap_id,
                    delta_rows=row_count,
                ),
                set_batch_status="staged",
            )
            backup_started = deps.now_utc()
            backup_schedule_error = schedule_best_effort(
                deps.create_task,
                deps.trigger_log_backup_background(),
                logger,
                "Failed to schedule background log-backup trigger",
            )
            backup_phase_status = "failed" if backup_schedule_error is not None else "completed"
            await deps.record_audit_phase(
                audit_ref,
                phase_name=WEEKLY_ACTIVITY_AUDIT_BACKUP_PHASE,
                phase_status=backup_phase_status,
                started_at_utc=backup_started.replace(tzinfo=None),
                rows_in=rows_parsed,
                rows_out=row_count if backup_schedule_error is None else None,
                duration_ms=audit_duration_ms(backup_started),
                error_type=(
                    type(backup_schedule_error).__name__
                    if backup_schedule_error is not None
                    else None
                ),
                error_text=(
                    str(backup_schedule_error) if backup_schedule_error is not None else None
                ),
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                    snapshot_id=snap_id,
                    delta_rows=row_count,
                    error=str(backup_schedule_error) if backup_schedule_error is not None else None,
                ),
            )
            await deps.complete_audit_batch(
                audit_ref,
                status="completed",
                rows_in_source=rows_parsed,
                rows_staged=rows_parsed,
                rows_written=row_count,
                rows_skipped=0,
                external_batch_id=external_batch_id,
                details=weekly_activity_audit_details(
                    audit_context,
                    rows_parsed=rows_parsed,
                    snapshot_id=snap_id,
                    delta_rows=row_count,
                ),
            )
            audit_terminal_recorded = True
            try:
                await deps.send_embed(
                    target_ch,
                    "Alliance Activity Import \u2705",
                    {
                        "SnapshotId": str(snap_id),
                        "Rows": str(row_count),
                        "Filename": target.filename,
                        **message_source_fields(message),
                        "Note": "",
                    },
                    0x2ECC71,
                )
            except Exception:
                logger.exception("weekly_activity_success_notification_failed")
    except Exception as e:
        if audit_ref is not None and not audit_terminal_recorded:
            await deps.fail_audit_batch(
                audit_ref,
                error_type=type(e).__name__,
                error_text=str(e),
                rows_in_source=rows_parsed if parse_succeeded else None,
                rows_staged=rows_parsed if parse_succeeded and snap_id not in (None, 0) else None,
                rows_written=row_count if parse_succeeded and snap_id not in (None, 0) else None,
                rows_skipped=0 if parse_succeeded and snap_id not in (None, 0) else None,
                external_batch_id=external_batch_id,
                details=(
                    weekly_activity_audit_details(
                        audit_context,
                        rows_parsed=rows_parsed,
                        snapshot_id=snap_id if snap_id not in (None, 0) else None,
                        delta_rows=row_count,
                        error=str(e),
                    )
                    if audit_context is not None
                    else None
                ),
            )
            audit_terminal_recorded = True
        try:
            await deps.send_embed(
                target_ch,
                "Alliance Activity Import \u274c",
                {
                    "Error": f"{type(e).__name__}: {e}",
                    "Filename": target.filename,
                    **message_source_fields(message),
                },
                0xE74C3C,
                mention=None,
            )
        except Exception:
            logger.exception("weekly_activity_error_notification_failed")
    return True
