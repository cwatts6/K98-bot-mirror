"""PreKvK workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import re
from typing import Any

from prekvk_importer import import_prekvk_bytes
from services.prekvk_import_audit_service import (
    PREKVK_AUDIT_HISTORY_TABLE,
    PREKVK_AUDIT_INGEST_PHASE,
    PREKVK_AUDIT_PARSE_PHASE,
    PREKVK_AUDIT_REFRESH_PHASE,
    PREKVK_AUDIT_SCAN_TABLE,
    PreKvkImportAuditContext,
    audit_duration_ms,
    complete_prekvk_audit_batch,
    fail_prekvk_audit_batch,
    prekvk_audit_details,
    prekvk_scan_external_batch_id,
    record_prekvk_audit_phase,
    start_prekvk_audit_batch,
)
from utils import utcnow

logger = logging.getLogger(__name__)

PREKVK_NAME_RX = re.compile(
    r"^(?:1198_prekvk|PreKvK_Rankings_[^\\/:*?\"<>|]+)\.xlsx$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PreKvkRouteDeps:
    prekvk_channel_id: int
    bot: Any
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    start_audit_batch: Callable[..., Awaitable[Any]] = start_prekvk_audit_batch
    record_audit_phase: Callable[..., Awaitable[None]] = record_prekvk_audit_phase
    complete_audit_batch: Callable[..., Awaitable[None]] = complete_prekvk_audit_batch
    fail_audit_batch: Callable[..., Awaitable[None]] = fail_prekvk_audit_batch
    current_kvk_metadata: Callable[[], Any] | None = None
    run_blocking_in_thread: Callable[..., Awaitable[Any]] | None = None
    send_stats_update_embed: Callable[..., Awaitable[Any]] | None = None
    now_utc: Callable[[], Any] = utcnow


async def _load_current_kvk_metadata(deps: PreKvkRouteDeps) -> dict[str, Any] | None:
    metadata_func = deps.current_kvk_metadata
    if metadata_func is None:
        import stats_alerts.kvk_meta as kvk_meta

        metadata_func = kvk_meta.get_latest_kvk_metadata_sql

    run_blocking_in_thread = deps.run_blocking_in_thread
    if run_blocking_in_thread is None:
        try:
            from file_utils import run_blocking_in_thread as imported_runner

            run_blocking_in_thread = imported_runner
        except Exception:
            run_blocking_in_thread = None

    if run_blocking_in_thread is not None:
        return await run_blocking_in_thread(
            metadata_func,
            name="get_latest_kvk_metadata_sql_dlbot",
        )
    return await asyncio.to_thread(metadata_func)


async def _refresh_stats_embed(deps: PreKvkRouteDeps) -> None:
    stats_refresh = deps.send_stats_update_embed
    if stats_refresh is None:
        from stats_alerts.interface import send_stats_update_embed as stats_refresh

    ts = deps.now_utc().strftime("%Y-%m-%d %H:%M UTC")
    await stats_refresh(deps.bot, ts, True, is_test=False)


def _metadata_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, tuple) and len(result) >= 4 and isinstance(result[3], dict):
        return result[3]
    return {}


def _metadata_int(metadata: dict[str, Any], key: str) -> int | None:
    value = metadata.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _metadata_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _external_batch_from_metadata(
    metadata: dict[str, Any],
) -> tuple[str | None, str | None]:
    status = (_metadata_text(metadata, "status") or "").lower()
    kvk_no = _metadata_int(metadata, "kvk_no")
    scan_id = _metadata_int(metadata, "scan_id")
    history_id = _metadata_int(metadata, "history_id")
    if status == "accepted" and kvk_no is not None and scan_id is not None:
        return PREKVK_AUDIT_SCAN_TABLE, prekvk_scan_external_batch_id(kvk_no, scan_id)
    if history_id is not None:
        return PREKVK_AUDIT_HISTORY_TABLE, str(history_id)
    return None, None


async def _record_importer_audit_phases(
    deps: PreKvkRouteDeps,
    audit_ref: Any,
    audit_context: PreKvkImportAuditContext,
    metadata: dict[str, Any],
    *,
    import_started: Any,
    elapsed_ms: int,
    note: str,
) -> None:
    if audit_ref is None or not metadata:
        return

    status = (_metadata_text(metadata, "status") or "").lower()
    importer_phase = _metadata_text(metadata, "phase")
    rows_in_source = _metadata_int(metadata, "rows_in_source")
    rows_written = _metadata_int(metadata, "rows_written")
    scan_id = _metadata_int(metadata, "scan_id")
    history_id = _metadata_int(metadata, "history_id")
    error_type = _metadata_text(metadata, "error_type")
    error_text = _metadata_text(metadata, "error_text") or (
        note if status in {"rejected", "failed"} else None
    )
    parsed = rows_in_source is not None and (
        status in {"accepted", "duplicate"}
        or str(importer_phase or "").startswith("db")
    )

    await deps.record_audit_phase(
        audit_ref,
        phase_name=PREKVK_AUDIT_PARSE_PHASE,
        phase_status="completed" if parsed else "failed",
        started_at_utc=import_started.replace(tzinfo=None),
        rows_in=rows_in_source,
        rows_out=rows_in_source if parsed else 0,
        error_type=error_type if not parsed else None,
        error_text=error_text if not parsed else None,
        details=prekvk_audit_details(
            audit_context,
            rows_parsed=rows_in_source,
            scan_id=scan_id,
            history_id=history_id,
            importer_status=status or None,
            importer_phase=importer_phase,
            error=error_text if not parsed else None,
        ),
    )

    if not parsed:
        return

    if status == "accepted":
        ingest_status = "completed"
        set_batch_status = "staged"
        ingest_error_type = None
        ingest_error_text = None
    elif status == "duplicate":
        ingest_status = "duplicate"
        set_batch_status = "duplicate"
        ingest_error_type = None
        ingest_error_text = None
    else:
        ingest_status = "failed"
        set_batch_status = None
        ingest_error_type = error_type
        ingest_error_text = error_text

    await deps.record_audit_phase(
        audit_ref,
        phase_name=PREKVK_AUDIT_INGEST_PHASE,
        phase_status=ingest_status,
        started_at_utc=import_started.replace(tzinfo=None),
        rows_in=rows_in_source,
        rows_out=rows_written,
        duration_ms=elapsed_ms,
        error_type=ingest_error_type,
        error_text=ingest_error_text,
        details=prekvk_audit_details(
            audit_context,
            rows_parsed=rows_in_source,
            scan_id=scan_id,
            history_id=history_id,
            importer_status=status or None,
            importer_phase=importer_phase,
            error=ingest_error_text,
        ),
        set_batch_status=set_batch_status,
    )


async def handle_prekvk_upload(message: Any, deps: PreKvkRouteDeps) -> bool:
    """Handle PreKvK workbook imports from the configured upload channel."""
    if message.channel.id != deps.prekvk_channel_id or not message.attachments:
        return False

    notify_ch = await deps.get_notify_channel() or message.channel

    target = next(
        (a for a in message.attachments if PREKVK_NAME_RX.match(a.filename.strip())),
        None,
    )

    if not target:
        await deps.send_embed(
            notify_ch,
            "Pre-KVK Import ⚠️",
            {
                "Info": "No matching file found.",
                "Expected": "1198_prekvk.xlsx or PreKvK_Rankings_*.xlsx",
                "Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploader": f"{message.author} ({message.author.id})",
            },
            0xE67E22,
        )
        return True

    audit_context: PreKvkImportAuditContext | None = None
    audit_ref: Any = None
    audit_terminal_recorded = False
    metadata: dict[str, Any] = {}
    external_batch_table: str | None = None
    external_batch_id: str | None = None

    try:
        file_bytes = await target.read()

        ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
        if not ok:
            return True

        meta = None
        try:
            meta = await _load_current_kvk_metadata(deps)
        except Exception:
            logger.exception("[DL_BOT] Failed to determine current KVK metadata")

        detected_kvk_no = None
        try:
            if meta and meta.get("kvk_no") is not None:
                detected_kvk_no = int(meta.get("kvk_no"))
        except Exception:
            detected_kvk_no = None

        if detected_kvk_no is None:
            logger.error("[DL_BOT] Could not determine current KVK number; aborting Pre-KVK import")
            await deps.send_embed(
                notify_ch,
                "Pre-KVK Import ❌",
                {
                    "Error": "Could not determine current KVK number (kvk_no). Import aborted.",
                    "Filename": target.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE74C3C,
            )
            return True

        audit_context = PreKvkImportAuditContext(
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
            kvk_no=detected_kvk_no,
        )
        audit_ref = await deps.start_audit_batch(
            context=audit_context,
            xlsx_bytes=file_bytes,
        )

        import_started = deps.now_utc()
        result = await deps.offload_callable(
            import_prekvk_bytes,
            file_bytes,
            target.filename,
            kvk_no=detected_kvk_no,
            uploader_discord_id=(
                int(message.author.id) if getattr(message.author, "id", None) is not None else None
            ),
            channel_id=(
                int(message.channel.id)
                if getattr(message.channel, "id", None) is not None
                else None
            ),
            message_id=int(message.id) if getattr(message, "id", None) is not None else None,
            return_metadata=True,
            name="import_prekvk_bytes",
            prefer_process=True,
            meta={"filename": target.filename, "kvk_no": detected_kvk_no},
        )
        ok, note, rows = result[0], result[1], result[2]
        metadata = _metadata_dict(result)
        external_batch_table, external_batch_id = _external_batch_from_metadata(metadata)
        rows_in_source = _metadata_int(metadata, "rows_in_source")
        rows_written = _metadata_int(metadata, "rows_written")
        scan_id = _metadata_int(metadata, "scan_id")
        history_id = _metadata_int(metadata, "history_id")
        elapsed_ms = audit_duration_ms(import_started)

        await _record_importer_audit_phases(
            deps,
            audit_ref,
            audit_context,
            metadata,
            import_started=import_started,
            elapsed_ms=elapsed_ms,
            note=note,
        )

        if ok:
            duplicate_skip = "duplicate file skipped" in (note or "").lower()
            await deps.send_embed(
                notify_ch,
                ("Pre-KVK Snapshot Skipped" if duplicate_skip else "Pre-KVK Snapshot Imported ✅"),
                {
                    "KVK": str(detected_kvk_no),
                    "Rows": str(rows),
                    "Filename": target.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                    "Note": note,
                },
                0xF1C40F if duplicate_skip else 0x2ECC71,
            )

            if not duplicate_skip:
                try:
                    deps.create_task(deps.trigger_log_backup_background())
                except Exception:
                    logger.exception("Failed to schedule background log-backup trigger")

                refresh_error: Exception | None = None
                refresh_started = deps.now_utc()
                try:
                    await _refresh_stats_embed(deps)
                except Exception as exc:
                    refresh_error = exc
                    logger.debug(
                        "Failed to refresh stats embed after Pre-KVK import", exc_info=True
                    )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=PREKVK_AUDIT_REFRESH_PHASE,
                    phase_status="failed" if refresh_error else "completed",
                    started_at_utc=refresh_started.replace(tzinfo=None),
                    rows_in=rows_in_source,
                    rows_out=rows_written if rows_written is not None else rows,
                    duration_ms=audit_duration_ms(refresh_started),
                    error_type=type(refresh_error).__name__ if refresh_error else None,
                    error_text=str(refresh_error) if refresh_error else None,
                    details=prekvk_audit_details(
                        audit_context,
                        rows_parsed=rows_in_source,
                        scan_id=scan_id,
                        history_id=history_id,
                        importer_status=_metadata_text(metadata, "status"),
                        importer_phase=_metadata_text(metadata, "phase"),
                        error=str(refresh_error) if refresh_error else None,
                        refresh_failed=refresh_error is not None,
                    ),
                )
                await deps.complete_audit_batch(
                    audit_ref,
                    status="failed" if refresh_error else "completed",
                    rows_in_source=rows_in_source,
                    rows_staged=rows_written if rows_written is not None else rows,
                    rows_written=rows_written if rows_written is not None else rows,
                    rows_skipped=0,
                    external_batch_table=external_batch_table,
                    external_batch_id=external_batch_id,
                    details=prekvk_audit_details(
                        audit_context,
                        rows_parsed=rows_in_source,
                        scan_id=scan_id,
                        history_id=history_id,
                        importer_status=_metadata_text(metadata, "status"),
                        importer_phase=_metadata_text(metadata, "phase"),
                        error=str(refresh_error) if refresh_error else None,
                        refresh_failed=refresh_error is not None,
                    ),
                )
                audit_terminal_recorded = True
            else:
                rows_skipped = rows_in_source if rows_in_source is not None else rows
                await deps.complete_audit_batch(
                    audit_ref,
                    status="duplicate",
                    rows_in_source=rows_in_source,
                    rows_staged=0,
                    rows_written=0,
                    rows_skipped=rows_skipped,
                    external_batch_table=external_batch_table,
                    external_batch_id=external_batch_id,
                    details=prekvk_audit_details(
                        audit_context,
                        rows_parsed=rows_in_source,
                        history_id=history_id,
                        importer_status=_metadata_text(metadata, "status"),
                        importer_phase=_metadata_text(metadata, "phase"),
                    ),
                )
                audit_terminal_recorded = True
        else:
            rows_skipped = rows_in_source if rows_in_source is not None else rows
            await deps.fail_audit_batch(
                audit_ref,
                error_type=_metadata_text(metadata, "error_type") or "PreKvkImportFailed",
                error_text=note or "Unknown",
                rows_in_source=rows_in_source,
                rows_staged=0,
                rows_written=0,
                rows_skipped=rows_skipped,
                external_batch_table=external_batch_table,
                external_batch_id=external_batch_id,
                details=prekvk_audit_details(
                    audit_context,
                    rows_parsed=rows_in_source,
                    history_id=history_id,
                    importer_status=_metadata_text(metadata, "status"),
                    importer_phase=_metadata_text(metadata, "phase"),
                    error=note or "Unknown",
                ),
            )
            audit_terminal_recorded = True
            await deps.send_embed(
                notify_ch,
                "Pre-KVK Import ❌",
                {
                    "Filename": target.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                    "Error": note or "Unknown",
                },
                0xE74C3C,
            )
    except Exception as e:
        if audit_ref is not None and not audit_terminal_recorded:
            await deps.fail_audit_batch(
                audit_ref,
                error_type=type(e).__name__,
                error_text=str(e),
                external_batch_table=external_batch_table,
                external_batch_id=external_batch_id,
                details=(
                    prekvk_audit_details(
                        audit_context,
                        scan_id=_metadata_int(metadata, "scan_id"),
                        history_id=_metadata_int(metadata, "history_id"),
                        importer_status=_metadata_text(metadata, "status"),
                        importer_phase=_metadata_text(metadata, "phase"),
                        error=str(e),
                    )
                    if audit_context is not None
                    else None
                ),
            )
            audit_terminal_recorded = True
        await deps.send_embed(
            notify_ch,
            "Pre-KVK Import ❌",
            {
                "Error": f"{type(e).__name__}: {e}",
                "Filename": target.filename,
                "Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploader": f"{message.author} ({message.author.id})",
            },
            0xE74C3C,
        )
    return True
