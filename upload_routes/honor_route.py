"""KVK Honor workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import re
from typing import Any

from honor_importer import ingest_honor_snapshot, parse_honor_xlsx
from services.honor_import_audit_service import (
    HONOR_AUDIT_INGEST_PHASE,
    HONOR_AUDIT_PARSE_PHASE,
    HONOR_AUDIT_REFRESH_PHASE,
    HonorImportAuditContext,
    audit_duration_ms,
    honor_audit_details,
    honor_external_batch_id,
    complete_honor_audit_batch,
    fail_honor_audit_batch,
    record_honor_audit_phase,
    start_honor_audit_batch,
)
from upload_routes.common import message_source_fields, resolve_notify_channel, schedule_best_effort
from utils import utcnow

logger = logging.getLogger(__name__)

HONOR_NAME_RX = re.compile(
    r"^(?:test_|demo_|sample_)?1198[_\s-]*honor.*\.xlsx$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HonorRouteDeps:
    honor_channel_id: int
    bot: Any
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    start_audit_batch: Callable[..., Awaitable[Any]] = start_honor_audit_batch
    record_audit_phase: Callable[..., Awaitable[None]] = record_honor_audit_phase
    complete_audit_batch: Callable[..., Awaitable[None]] = complete_honor_audit_batch
    fail_audit_batch: Callable[..., Awaitable[None]] = fail_honor_audit_batch
    send_stats_update_embed: Callable[..., Awaitable[Any]] | None = None
    now_utc: Callable[[], Any] = utcnow


def _is_test_upload(message: Any, filename: str) -> bool:
    msg_text = (message.content or "").lower()
    return (
        ("[test]" in msg_text)
        or (" test " in f" {msg_text} ")
        or filename.lower().startswith(("test_", "demo_", "sample_"))
    )


async def _refresh_stats_embed(deps: HonorRouteDeps, is_test: bool) -> None:
    stats_refresh = deps.send_stats_update_embed
    if stats_refresh is None:
        from stats_alerts.interface import send_stats_update_embed as stats_refresh

    ts = deps.now_utc().strftime("%Y-%m-%d %H:%M UTC")
    await stats_refresh(deps.bot, ts, True, is_test=is_test)


async def handle_honor_upload(message: Any, deps: HonorRouteDeps) -> bool:
    """Handle KVK Honor workbook imports from the configured upload channel."""
    if message.channel.id != deps.honor_channel_id or not message.attachments:
        return False

    notify_ch = await resolve_notify_channel(
        deps.get_notify_channel,
        message.channel,
        logger,
        "honor_upload",
    )

    target = next(
        (a for a in message.attachments if HONOR_NAME_RX.match(a.filename.strip())),
        None,
    )
    if not target:
        fields = {
            "Info": "No matching file found.",
            "Expected": "1198_honor.xlsx  • also accepts *1198_honor*.xlsx with optional TEST_/DEMO_/SAMPLE_ prefix",
            **message_source_fields(message),
        }
        await deps.send_embed(notify_ch, "KVK Honor Import ⚠️", fields, 0xE67E22)
        return True

    try:
        is_test = _is_test_upload(message, target.filename)

        ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
        if not ok:
            return True

        file_bytes = await target.read()
        audit_context = HonorImportAuditContext(
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
            is_test=is_test,
        )
        audit_ref = await deps.start_audit_batch(
            context=audit_context,
            xlsx_bytes=file_bytes,
        )

        parse_succeeded = False
        parse_started = deps.now_utc()
        try:
            pre_df = await deps.offload_callable(
                parse_honor_xlsx,
                file_bytes,
                name="parse_honor_xlsx",
                prefer_process=True,
                meta={"filename": target.filename},
            )
            row_count = len(pre_df)
            parse_succeeded = True
            await deps.record_audit_phase(
                audit_ref,
                phase_name=HONOR_AUDIT_PARSE_PHASE,
                phase_status="completed",
                started_at_utc=parse_started.replace(tzinfo=None),
                rows_out=row_count,
                duration_ms=audit_duration_ms(parse_started),
                details=honor_audit_details(audit_context, rows_parsed=row_count),
            )
        except Exception as exc:
            logger.debug("honor_upload_row_count_parse_failed", exc_info=True)
            row_count = 0
            await deps.record_audit_phase(
                audit_ref,
                phase_name=HONOR_AUDIT_PARSE_PHASE,
                phase_status="failed",
                started_at_utc=parse_started.replace(tzinfo=None),
                duration_ms=audit_duration_ms(parse_started),
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=honor_audit_details(audit_context, error=str(exc)),
            )

        ingest_started = deps.now_utc()
        external_batch_id = None
        try:
            kvk_no, scan_id = await deps.offload_callable(
                ingest_honor_snapshot,
                file_bytes,
                source_filename=target.filename,
                scan_ts_utc=message.created_at,
                name="ingest_honor_snapshot",
                prefer_process=True,
                meta={"filename": target.filename},
            )
            external_batch_id = honor_external_batch_id(kvk_no, scan_id)
            await deps.record_audit_phase(
                audit_ref,
                phase_name=HONOR_AUDIT_INGEST_PHASE,
                phase_status="completed",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=row_count if parse_succeeded else None,
                rows_out=row_count if parse_succeeded else None,
                duration_ms=audit_duration_ms(ingest_started),
                details=honor_audit_details(
                    audit_context,
                    rows_parsed=row_count if parse_succeeded else None,
                    kvk_no=kvk_no,
                    scan_id=scan_id,
                ),
                set_batch_status="staged",
            )
        except Exception as exc:
            await deps.record_audit_phase(
                audit_ref,
                phase_name=HONOR_AUDIT_INGEST_PHASE,
                phase_status="failed",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=row_count if parse_succeeded else None,
                duration_ms=audit_duration_ms(ingest_started),
                error_type=type(exc).__name__,
                error_text=str(exc),
                details=honor_audit_details(
                    audit_context,
                    rows_parsed=row_count if parse_succeeded else None,
                    error=str(exc),
                ),
            )
            await deps.fail_audit_batch(
                audit_ref,
                error_type=type(exc).__name__,
                error_text=str(exc),
                rows_in_source=row_count if parse_succeeded else None,
                rows_staged=0 if parse_succeeded else None,
                rows_written=0 if parse_succeeded else None,
                rows_skipped=row_count if parse_succeeded else None,
                details=honor_audit_details(
                    audit_context,
                    rows_parsed=row_count if parse_succeeded else None,
                    error=str(exc),
                ),
            )
            raise

        fields = {
            "KVK": str(kvk_no),
            "ScanID": str(scan_id),
            "Rows": str(row_count),
            "Filename": target.filename,
            **message_source_fields(message),
        }
        await deps.send_embed(
            notify_ch,
            "KVK Honor Import ✅" + (" (TEST)" if is_test else ""),
            fields,
            0x2ECC71,
        )

        schedule_best_effort(
            deps.create_task,
            deps.trigger_log_backup_background(),
            logger,
            "Failed to schedule background log-backup trigger",
        )

        refresh_failed: Exception | None = None
        refresh_started = deps.now_utc()
        try:
            await _refresh_stats_embed(deps, is_test)
        except Exception as exc:
            refresh_failed = exc
            logger.debug("Failed to refresh stats embed after KVK Honor import", exc_info=True)
        await deps.record_audit_phase(
            audit_ref,
            phase_name=HONOR_AUDIT_REFRESH_PHASE,
            phase_status="failed" if refresh_failed else "completed",
            started_at_utc=refresh_started.replace(tzinfo=None),
            rows_in=row_count if parse_succeeded else None,
            rows_out=row_count if parse_succeeded else None,
            duration_ms=audit_duration_ms(refresh_started),
            error_type=type(refresh_failed).__name__ if refresh_failed else None,
            error_text=str(refresh_failed) if refresh_failed else None,
            details=honor_audit_details(
                audit_context,
                rows_parsed=row_count if parse_succeeded else None,
                kvk_no=kvk_no,
                scan_id=scan_id,
                error=str(refresh_failed) if refresh_failed else None,
                refresh_failed=refresh_failed is not None,
            ),
        )
        await deps.complete_audit_batch(
            audit_ref,
            status="failed" if refresh_failed else "completed",
            rows_in_source=row_count if parse_succeeded else None,
            rows_staged=row_count if parse_succeeded else None,
            rows_written=row_count if parse_succeeded else None,
            rows_skipped=0 if parse_succeeded else None,
            external_batch_id=external_batch_id,
            details=honor_audit_details(
                audit_context,
                rows_parsed=row_count if parse_succeeded else None,
                kvk_no=kvk_no,
                scan_id=scan_id,
                error=str(refresh_failed) if refresh_failed else None,
                refresh_failed=refresh_failed is not None,
            ),
        )
    except Exception as e:
        fields = {
            "Error": f"{type(e).__name__}: {e}",
            "Filename": target.filename,
            **message_source_fields(message),
        }
        await deps.send_embed(notify_ch, "KVK Honor Import ❌", fields, 0xE74C3C)
    return True
