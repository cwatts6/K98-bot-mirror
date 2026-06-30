"""Rally Forts workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import os
import re
from typing import Any

from services.rally_forts_import_audit_service import (
    RALLY_FORTS_AUDIT_ALLTIME_INGEST_PHASE,
    RALLY_FORTS_AUDIT_ATTACHMENT_SAVE_PHASE,
    RALLY_FORTS_AUDIT_BACKUP_PHASE,
    RALLY_FORTS_AUDIT_DAILY_INGEST_PHASE,
    RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE,
    RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE,
    RallyFortsImportAuditContext,
    audit_duration_ms,
    audit_timestamp_utc,
    complete_rally_forts_audit_batch,
    fail_rally_forts_audit_batch,
    rally_forts_audit_details,
    rally_forts_external_batch_id,
    record_rally_forts_audit_phase,
    start_rally_forts_audit_batch,
)
from upload_routes.common import resolve_notify_channel, schedule_best_effort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RallyFortsRouteDeps:
    fort_rally_channel_id: int
    log_dir: str
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    importer_loader: Callable[[], tuple[Callable[..., Any], Callable[..., Any]]] | None = None
    start_audit_batch: Callable[..., Awaitable[Any]] = start_rally_forts_audit_batch
    record_audit_phase: Callable[..., Awaitable[None]] = record_rally_forts_audit_phase
    complete_audit_batch: Callable[..., Awaitable[None]] = complete_rally_forts_audit_batch
    fail_audit_batch: Callable[..., Awaitable[None]] = fail_rally_forts_audit_batch
    now_utc: Callable[[], Any] = audit_timestamp_utc


def is_rally_daily(filename: str) -> bool:
    return re.search(r"^Rally_data_\d{2}-\d{2}-\d{4}\.xlsx$", filename, re.I) is not None


def is_rally_alltime(filename: str) -> bool:
    return re.search(r"Rally[_\s]?data.*all[\s_]?time.*\.xlsx$", filename, re.I) is not None


def _load_importers() -> tuple[Callable[..., Any], Callable[..., Any]]:
    from forts_ingest import import_rally_alltime_xlsx, import_rally_daily_xlsx

    return import_rally_alltime_xlsx, import_rally_daily_xlsx


def _maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _message_int_attr(obj: Any, name: str) -> int | None:
    return _maybe_int(getattr(obj, name, None))


def _result_rows(result: Any) -> int | None:
    if isinstance(result, dict):
        rows = _maybe_int(result.get("rows"))
        if rows is not None:
            return rows
        if str(result.get("reason") or "").lower() == "no rows":
            return 0
    return None


def _result_ingestion_external_id(result: Any) -> str | None:
    if not isinstance(result, dict):
        return None
    ingestion_id = _maybe_int(result.get("ingestion_id"))
    if ingestion_id is None:
        return None
    return rally_forts_external_batch_id(ingestion_id)


def _result_reason(result: Any) -> str | None:
    if isinstance(result, dict) and result.get("reason") is not None:
        return str(result.get("reason"))
    return None


def _is_skipped_result(result: Any) -> bool:
    return isinstance(result, dict) and result.get("status") == "skipped"


async def handle_rally_forts_upload(message: Any, deps: RallyFortsRouteDeps) -> bool:
    """Handle Rally Forts XLSX imports from the configured Fort Rally channel."""
    if (
        not deps.fort_rally_channel_id
        or message.channel.id != deps.fort_rally_channel_id
        or not message.attachments
    ):
        return False

    notify_ch = await resolve_notify_channel(
        deps.get_notify_channel,
        message.channel,
        logger,
        "rally_forts_upload",
    )

    try:
        importer_loader = deps.importer_loader or _load_importers
        import_rally_alltime_xlsx, import_rally_daily_xlsx = importer_loader()
    except Exception as e:
        await deps.send_embed(
            notify_ch,
            "Rally Forts Import \u274c",
            {
                "Error": f"Import failure: {type(e).__name__}: {e}",
                "Hint": "Ensure forts_ingest.py and its dependencies (pandas, pyodbc) are installed in the venv.",
            },
            0xE74C3C,
        )
        return True

    downloads_dir = os.path.join(deps.log_dir, "downloads")
    try:
        os.makedirs(downloads_dir, exist_ok=True)
    except Exception:
        pass

    results: list[tuple[str, str, Any]] = []
    matched_any = False
    for attachment in message.attachments:
        if not attachment.filename.lower().endswith(".xlsx"):
            continue

        filename = attachment.filename
        audit_context = RallyFortsImportAuditContext(
            source_filename=filename,
            source_message_id=_message_int_attr(message, "id"),
            source_channel_id=_message_int_attr(message.channel, "id"),
            actor_discord_id=_message_int_attr(message.author, "id"),
        )
        audit_ref: Any = await deps.start_audit_batch(context=audit_context)
        audit_terminal_recorded = False

        if "/" in filename or "\\" in filename:
            logger.warning(
                "[RALLY] Rejecting unsafe filename with path components: %s",
                filename,
            )
            details = rally_forts_audit_details(
                audit_context,
                error="Invalid filename: path separators not allowed",
            )
            await deps.record_audit_phase(
                audit_ref,
                phase_name=RALLY_FORTS_AUDIT_ATTACHMENT_SAVE_PHASE,
                phase_status="failed",
                error_type="UnsafeFilename",
                error_text="Invalid filename: path separators not allowed",
                details=details,
            )
            await deps.fail_audit_batch(
                audit_ref,
                error_type="UnsafeFilename",
                error_text="Invalid filename: path separators not allowed",
                rows_written=0,
                details=details,
            )
            audit_terminal_recorded = True
            results.append(("err", filename, "Invalid filename: path separators not allowed"))
            continue

        safe_filename = os.path.basename(filename)
        local_path = os.path.join(downloads_dir, safe_filename)
        current_phase = RALLY_FORTS_AUDIT_ATTACHMENT_SAVE_PHASE
        current_file_kind: str | None = None
        phase_started = deps.now_utc()
        try:
            save_started = phase_started
            await attachment.save(local_path)
            logger.info("[RALLY] Saved %s to %s", filename, local_path)
            await deps.record_audit_phase(
                audit_ref,
                phase_name=RALLY_FORTS_AUDIT_ATTACHMENT_SAVE_PHASE,
                phase_status="completed",
                started_at_utc=save_started.replace(tzinfo=None),
                rows_out=1,
                duration_ms=audit_duration_ms(save_started),
                details=rally_forts_audit_details(audit_context),
            )

            if is_rally_alltime(filename):
                matched_any = True
                current_file_kind = "alltime"
                logger.info("[RALLY] Detected ALL-TIME file: %s", filename)
                classify_started = deps.now_utc()
                current_phase = RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE
                phase_started = classify_started
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE,
                    phase_status="completed",
                    started_at_utc=classify_started.replace(tzinfo=None),
                    rows_in=1,
                    rows_out=1,
                    duration_ms=audit_duration_ms(classify_started),
                    details=rally_forts_audit_details(audit_context, file_kind="alltime"),
                )
                preflight_started = deps.now_utc()
                current_phase = RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE
                phase_started = preflight_started
                ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
                if not ok:
                    details = rally_forts_audit_details(
                        audit_context,
                        file_kind="alltime",
                        error="SQL log headroom insufficient",
                    )
                    await deps.record_audit_phase(
                        audit_ref,
                        phase_name=RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE,
                        phase_status="failed",
                        started_at_utc=preflight_started.replace(tzinfo=None),
                        duration_ms=audit_duration_ms(preflight_started),
                        error_type="SqlHeadroomInsufficient",
                        error_text="SQL log headroom insufficient",
                        details=details,
                    )
                    await deps.fail_audit_batch(
                        audit_ref,
                        error_type="SqlHeadroomInsufficient",
                        error_text="SQL log headroom insufficient",
                        rows_written=0,
                        details=details,
                    )
                    audit_terminal_recorded = True
                    results.append(("err", filename, "Aborted: SQL log headroom insufficient"))
                    continue
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE,
                    phase_status="completed",
                    started_at_utc=preflight_started.replace(tzinfo=None),
                    duration_ms=audit_duration_ms(preflight_started),
                    details=rally_forts_audit_details(audit_context, file_kind="alltime"),
                )

                ingest_started = deps.now_utc()
                current_phase = RALLY_FORTS_AUDIT_ALLTIME_INGEST_PHASE
                phase_started = ingest_started
                result = await deps.offload_callable(
                    import_rally_alltime_xlsx,
                    local_path,
                    name="import_rally_alltime_xlsx",
                    prefer_process=True,
                    meta={"path": local_path},
                )
                rows = _result_rows(result)
                ingestion_id = (
                    _maybe_int(result.get("ingestion_id")) if isinstance(result, dict) else None
                )
                status = "skipped" if _is_skipped_result(result) else "completed"
                rows_written = 0 if status == "skipped" else rows
                rows_skipped = rows if status == "skipped" else 0
                details = rally_forts_audit_details(
                    audit_context,
                    file_kind="alltime",
                    rows_parsed=rows,
                    rows_staged=rows if status == "completed" else 0,
                    rows_written=rows_written,
                    rows_skipped=rows_skipped,
                    ingestion_id=ingestion_id,
                    reason=_result_reason(result),
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_ALLTIME_INGEST_PHASE,
                    phase_status=status,
                    started_at_utc=ingest_started.replace(tzinfo=None),
                    rows_in=rows,
                    rows_out=rows_written,
                    duration_ms=audit_duration_ms(ingest_started),
                    details=details,
                    set_batch_status="procedure_started" if status == "completed" else "skipped",
                )
                results.append(("ok", filename, result))
                backup_started = deps.now_utc()
                backup_error = schedule_best_effort(
                    deps.create_task,
                    deps.trigger_log_backup_background(),
                    logger,
                    "Failed to schedule background log-backup trigger",
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_BACKUP_PHASE,
                    phase_status="failed" if backup_error else "completed",
                    started_at_utc=backup_started.replace(tzinfo=None),
                    rows_in=rows,
                    rows_out=rows,
                    duration_ms=audit_duration_ms(backup_started),
                    error_type=type(backup_error).__name__ if backup_error else None,
                    error_text=str(backup_error) if backup_error else None,
                    details=details,
                )
                external_batch_id = (
                    _result_ingestion_external_id(result) if status == "completed" else None
                )
                await deps.complete_audit_batch(
                    audit_ref,
                    status=status,
                    rows_in_source=rows,
                    rows_staged=rows if status == "completed" else 0,
                    rows_written=rows_written,
                    rows_skipped=rows_skipped,
                    external_batch_id=external_batch_id,
                    details=details,
                )
                audit_terminal_recorded = True
            elif is_rally_daily(filename):
                matched_any = True
                current_file_kind = "daily"
                logger.info("[RALLY] Detected DAILY file: %s", filename)
                classify_started = deps.now_utc()
                current_phase = RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE
                phase_started = classify_started
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE,
                    phase_status="completed",
                    started_at_utc=classify_started.replace(tzinfo=None),
                    rows_in=1,
                    rows_out=1,
                    duration_ms=audit_duration_ms(classify_started),
                    details=rally_forts_audit_details(audit_context, file_kind="daily"),
                )
                preflight_started = deps.now_utc()
                current_phase = RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE
                phase_started = preflight_started
                ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
                if not ok:
                    details = rally_forts_audit_details(
                        audit_context,
                        file_kind="daily",
                        error="SQL log headroom insufficient",
                    )
                    await deps.record_audit_phase(
                        audit_ref,
                        phase_name=RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE,
                        phase_status="failed",
                        started_at_utc=preflight_started.replace(tzinfo=None),
                        duration_ms=audit_duration_ms(preflight_started),
                        error_type="SqlHeadroomInsufficient",
                        error_text="SQL log headroom insufficient",
                        details=details,
                    )
                    await deps.fail_audit_batch(
                        audit_ref,
                        error_type="SqlHeadroomInsufficient",
                        error_text="SQL log headroom insufficient",
                        rows_written=0,
                        details=details,
                    )
                    audit_terminal_recorded = True
                    results.append(("err", filename, "Aborted: SQL log headroom insufficient"))
                    continue
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_SQL_PREFLIGHT_PHASE,
                    phase_status="completed",
                    started_at_utc=preflight_started.replace(tzinfo=None),
                    duration_ms=audit_duration_ms(preflight_started),
                    details=rally_forts_audit_details(audit_context, file_kind="daily"),
                )

                ingest_started = deps.now_utc()
                current_phase = RALLY_FORTS_AUDIT_DAILY_INGEST_PHASE
                phase_started = ingest_started
                result = await deps.offload_callable(
                    import_rally_daily_xlsx,
                    local_path,
                    name="import_rally_daily_xlsx",
                    prefer_process=True,
                    meta={"path": local_path},
                )
                rows = _result_rows(result)
                ingestion_id = (
                    _maybe_int(result.get("ingestion_id")) if isinstance(result, dict) else None
                )
                status = "skipped" if _is_skipped_result(result) else "completed"
                rows_written = 0 if status == "skipped" else rows
                rows_skipped = rows if status == "skipped" else 0
                as_of = (
                    str(result.get("as_of"))
                    if isinstance(result, dict) and result.get("as_of")
                    else None
                )
                details = rally_forts_audit_details(
                    audit_context,
                    file_kind="daily",
                    rows_parsed=rows,
                    rows_staged=rows if status == "completed" else 0,
                    rows_written=rows_written,
                    rows_skipped=rows_skipped,
                    as_of=as_of,
                    ingestion_id=ingestion_id,
                    reason=_result_reason(result),
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_DAILY_INGEST_PHASE,
                    phase_status=status,
                    started_at_utc=ingest_started.replace(tzinfo=None),
                    rows_in=rows,
                    rows_out=rows_written,
                    duration_ms=audit_duration_ms(ingest_started),
                    details=details,
                    set_batch_status="procedure_started" if status == "completed" else "skipped",
                )
                results.append(("ok", filename, result))
                backup_started = deps.now_utc()
                backup_error = schedule_best_effort(
                    deps.create_task,
                    deps.trigger_log_backup_background(),
                    logger,
                    "Failed to schedule background log-backup trigger",
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_BACKUP_PHASE,
                    phase_status="failed" if backup_error else "completed",
                    started_at_utc=backup_started.replace(tzinfo=None),
                    rows_in=rows,
                    rows_out=rows,
                    duration_ms=audit_duration_ms(backup_started),
                    error_type=type(backup_error).__name__ if backup_error else None,
                    error_text=str(backup_error) if backup_error else None,
                    details=details,
                )
                external_batch_id = (
                    _result_ingestion_external_id(result) if status == "completed" else None
                )
                await deps.complete_audit_batch(
                    audit_ref,
                    status=status,
                    rows_in_source=rows,
                    rows_staged=rows if status == "completed" else 0,
                    rows_written=rows_written,
                    rows_skipped=rows_skipped,
                    external_batch_id=external_batch_id,
                    details=details,
                )
                audit_terminal_recorded = True
            else:
                details = rally_forts_audit_details(
                    audit_context,
                    reason="Unrecognized rally filename",
                )
                classify_started = deps.now_utc()
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=RALLY_FORTS_AUDIT_FILE_CLASSIFY_PHASE,
                    phase_status="skipped",
                    started_at_utc=classify_started.replace(tzinfo=None),
                    rows_in=1,
                    rows_out=0,
                    duration_ms=audit_duration_ms(classify_started),
                    details=details,
                    set_batch_status="skipped",
                )
                await deps.complete_audit_batch(
                    audit_ref,
                    status="skipped",
                    rows_in_source=0,
                    rows_staged=0,
                    rows_written=0,
                    rows_skipped=0,
                    details=details,
                )
                audit_terminal_recorded = True
                results.append(("skip", filename, "Unrecognized rally filename"))
        except Exception as e:
            if not audit_terminal_recorded:
                details = rally_forts_audit_details(
                    audit_context,
                    file_kind=current_file_kind,
                    error=str(e),
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=current_phase,
                    phase_status="failed",
                    started_at_utc=phase_started.replace(tzinfo=None),
                    duration_ms=audit_duration_ms(phase_started),
                    error_type=type(e).__name__,
                    error_text=str(e),
                    details=details,
                )
                await deps.fail_audit_batch(
                    audit_ref,
                    error_type=type(e).__name__,
                    error_text=str(e),
                    rows_written=0,
                    details=details,
                )
            logger.exception("[RALLY] Error processing attachment %s", attachment.filename)
            results.append(("err", attachment.filename, f"{type(e).__name__}: {e}"))

    if not matched_any and not results:
        await deps.send_embed(
            notify_ch,
            "Rally Forts Import \u26a0\ufe0f",
            {
                "Info": "No rally .xlsx attachments matched expected patterns.",
                "Expected Daily": "Rally_data_DD-MM-YYYY.xlsx",
                "Expected All-Time": "Rally_data_All_Time*.xlsx",
            },
            0xE67E22,
        )
        return True

    fields = {
        "Source Channel": f"#{message.channel.name} ({message.channel.id})",
        "Uploaded By": f"{message.author} ({message.author.id})",
    }
    oks = [result for result in results if result[0] == "ok"]
    errs = [result for result in results if result[0] == "err"]
    skips = [result for result in results if result[0] == "skip"]

    for _, filename, result in oks[:5]:
        if isinstance(result, dict):
            rows = result.get("rows")
            as_of = result.get("as_of")
            extra = f"rows={rows}" + (f"; as_of={as_of}" if as_of else "")
        else:
            extra = str(result)
        fields[f"\u2705 {filename}"] = extra or "ok"

    for _, filename, why in skips[:5]:
        fields[f"\u23ed\ufe0f {filename}"] = why

    for _, filename, err in errs[:5]:
        fields[f"\u274c {filename}"] = err

    color = 0x2ECC71 if oks and not errs else (0xE67E22 if oks and errs else 0xE74C3C)
    title = "Rally Forts Import" + (
        " \u2705" if oks and not errs else " \u26a0\ufe0f" if oks and errs else " \u274c"
    )

    try:
        await deps.send_embed(notify_ch, title, fields, color)
    except Exception:
        logger.exception("Failed to send Rally Forts import embed")

    return True
