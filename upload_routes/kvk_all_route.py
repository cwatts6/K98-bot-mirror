"""KVK all-kingdom workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import os
from typing import Any

from kvk_all_importer import ingest_kvk_all_excel
from services.kvk_all_import_audit_service import (
    KVK_ALL_AUDIT_ATTACHMENT_READ_PHASE,
    KVK_ALL_AUDIT_AUTO_EXPORT_PHASE,
    KVK_ALL_AUDIT_DIAGNOSTIC_TABLE,
    KVK_ALL_AUDIT_INGEST_PHASE,
    KVK_ALL_AUDIT_NEGATIVE_PHASE,
    KVK_ALL_AUDIT_PARSE_PHASE,
    KVK_ALL_AUDIT_RECOMPUTE_PHASE,
    KVK_ALL_AUDIT_SQL_PREFLIGHT_PHASE,
    KVK_ALL_AUDIT_STAGE_PHASE,
    KvkAllImportAuditContext,
    audit_duration_ms,
    audit_timestamp_utc,
    complete_kvk_all_audit_batch,
    fail_kvk_all_audit_batch,
    kvk_all_audit_details,
    kvk_all_diagnostic_external_batch_id,
    kvk_all_external_batch_id,
    kvk_all_source_type,
    record_kvk_all_audit_phase,
    start_kvk_all_audit_batch,
)

logger = logging.getLogger(__name__)

ACCEPTED_KVK_ALL_EXTENSIONS = (".xlsx", ".xls", ".csv")


@dataclass(frozen=True)
class KvkAllRouteDeps:
    prokingdom_channel_id: int
    bot: Any
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    auto_export_enabled: bool
    auto_export_scheduler: Callable[[int, Any, Any], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    get_sheet_id: Callable[[], str | None] | None = None
    embed_factory: Callable[..., Any] | None = None
    view_factory: Callable[[], Any] | None = None
    button_factory: Callable[..., Any] | None = None
    button_style_link: Any | None = None
    custom_avatar_url: str | None = None
    start_audit_batch: Callable[..., Awaitable[Any]] = start_kvk_all_audit_batch
    record_audit_phase: Callable[..., Awaitable[None]] = record_kvk_all_audit_phase
    complete_audit_batch: Callable[..., Awaitable[None]] = complete_kvk_all_audit_batch
    fail_audit_batch: Callable[..., Awaitable[None]] = fail_kvk_all_audit_batch
    now_utc: Callable[[], Any] = audit_timestamp_utc


def _default_embed_factory(**kwargs: Any) -> Any:
    import discord

    return discord.Embed(**kwargs)


def _default_view_factory() -> Any:
    import discord

    return discord.ui.View()


def _default_button_factory(**kwargs: Any) -> Any:
    import discord

    return discord.ui.Button(**kwargs)


def _default_button_style_link() -> Any:
    import discord

    return discord.ButtonStyle.link


def _resolve_custom_avatar_url(deps: KvkAllRouteDeps) -> str | None:
    if deps.custom_avatar_url is not None:
        return deps.custom_avatar_url
    try:
        from constants import CUSTOM_AVATAR_URL

        return CUSTOM_AVATAR_URL
    except Exception:
        return None


def _resolve_sheet_id(deps: KvkAllRouteDeps) -> str | None:
    if deps.get_sheet_id is not None:
        return deps.get_sheet_id()
    return os.environ.get("KVK_SHEET_ID") or os.environ.get("ALL_KVK_SHEET_ID")


def _build_result_embed(
    deps: KvkAllRouteDeps, title: str, color: int, fields: dict[str, str]
) -> Any:
    embed_factory = deps.embed_factory or _default_embed_factory
    embed = embed_factory(title=title, color=color)
    for key, value in fields.items():
        embed.add_field(name=key, value=str(value), inline=True)

    avatar_url = _resolve_custom_avatar_url(deps)
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    return embed


def _build_sheet_view(deps: KvkAllRouteDeps) -> Any | None:
    try:
        sheet_id = _resolve_sheet_id(deps)
        if not sheet_id:
            return None
        view_factory = deps.view_factory or _default_view_factory
        button_factory = deps.button_factory or _default_button_factory
        button_style_link = (
            deps.button_style_link
            if deps.button_style_link is not None
            else _default_button_style_link()
        )
        view = view_factory()
        view.add_item(
            button_factory(
                label="\U0001f4c4 Open KVK_ALLPLAYER_OUTPUT",
                url=f"https://docs.google.com/spreadsheets/d/{sheet_id}",
                style=button_style_link,
            )
        )
        return view
    except Exception:
        logger.info("[KVK EXPORT] ALL KVK SHEET ID INVALID")
        return None


def _maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _structured_error_type(result: dict[str, Any]) -> str:
    validation_error = result.get("validation_error")
    if isinstance(validation_error, dict) and validation_error.get("code"):
        return str(validation_error["code"])
    if result.get("missing_stage_columns"):
        return "MissingStageColumns"
    if result.get("diagnostic_id") is not None:
        return "KvkDetailsTimestampRejected"
    return "KvkAllImportFailed"


def _diagnostic_external_id(result: dict[str, Any]) -> str | None:
    diagnostic_id = _maybe_int(result.get("diagnostic_id"))
    if diagnostic_id is None:
        return None
    return kvk_all_diagnostic_external_batch_id(diagnostic_id)


def _exception_error_type(exc: Exception, diagnostic_id: int | None) -> str:
    if diagnostic_id is not None:
        return "KvkDetailsTimestampRejected"
    return type(exc).__name__


async def _record_structured_failure_audit(
    deps: KvkAllRouteDeps,
    audit_ref: Any,
    audit_context: KvkAllImportAuditContext,
    result: dict[str, Any],
) -> None:
    error_text = str(result.get("error") or "KVK_ALL import failed")
    error_type = _structured_error_type(result)
    rows_staged = _maybe_int(result.get("staged_rows") or result.get("row_count"))
    diagnostic_id = _maybe_int(result.get("diagnostic_id"))
    details = kvk_all_audit_details(
        audit_context,
        rows_parsed=rows_staged,
        rows_staged=rows_staged,
        diagnostic_id=diagnostic_id,
        sheet=result.get("sheet"),
        schema_version=result.get("schema_version"),
        error=error_text,
    )

    if result.get("prepare_ms") is not None:
        await deps.record_audit_phase(
            audit_ref,
            phase_name=KVK_ALL_AUDIT_PARSE_PHASE,
            phase_status="completed",
            rows_out=rows_staged,
            duration_ms=_maybe_int(float(result.get("prepare_ms", 0))),
            details=details,
        )

    if result.get("missing_stage_columns"):
        await deps.record_audit_phase(
            audit_ref,
            phase_name=KVK_ALL_AUDIT_STAGE_PHASE,
            phase_status="failed",
            rows_in=rows_staged,
            duration_ms=0,
            error_type=error_type,
            error_text=error_text,
            details=details,
        )
    elif result.get("stage_insert_ms") is not None:
        await deps.record_audit_phase(
            audit_ref,
            phase_name=KVK_ALL_AUDIT_STAGE_PHASE,
            phase_status="completed",
            rows_in=rows_staged,
            rows_out=rows_staged,
            duration_ms=_maybe_int(float(result.get("stage_insert_ms", 0))),
            details=details,
            set_batch_status="staged",
        )
        await deps.record_audit_phase(
            audit_ref,
            phase_name=KVK_ALL_AUDIT_INGEST_PHASE,
            phase_status="failed",
            rows_in=rows_staged,
            duration_ms=_maybe_int(float(result.get("precheck_ms", 0))),
            error_type=error_type,
            error_text=error_text,
            details=details,
        )
    else:
        await deps.record_audit_phase(
            audit_ref,
            phase_name=KVK_ALL_AUDIT_PARSE_PHASE,
            phase_status="failed",
            rows_out=0,
            error_type=error_type,
            error_text=error_text,
            details=details,
        )

    external_id = _diagnostic_external_id(result)
    await deps.fail_audit_batch(
        audit_ref,
        error_type=error_type,
        error_text=error_text,
        rows_in_source=rows_staged,
        rows_staged=rows_staged,
        rows_written=0,
        rows_skipped=rows_staged,
        external_batch_table=KVK_ALL_AUDIT_DIAGNOSTIC_TABLE if external_id else None,
        external_batch_id=external_id,
        details=details,
    )


async def handle_kvk_all_upload(message: Any, deps: KvkAllRouteDeps) -> bool:
    """Handle KVK all-kingdom uploads from the configured Pro Kingdom channel."""
    if message.channel.id != deps.prokingdom_channel_id or not message.attachments:
        return False

    notify_ch = await deps.get_notify_channel() or message.channel

    try:
        logger.info(
            "[KVK] msg=%s attachments=%s",
            message.id,
            [attachment.filename for attachment in message.attachments],
        )
    except Exception:
        pass

    excel_attachments = [
        attachment
        for attachment in message.attachments
        if attachment.filename.lower().strip().endswith(ACCEPTED_KVK_ALL_EXTENSIONS)
    ]

    if not excel_attachments:
        await deps.send_embed(
            notify_ch,
            "KVK All-Kingdom Import \u26a0\ufe0f",
            {
                "Info": "No .xlsx/.xls/.csv attachment found.",
                "Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploader": f"{message.author} ({message.author.id})",
            },
            0xE67E22,
        )
        return True

    for attachment in excel_attachments:
        audit_context: KvkAllImportAuditContext | None = None
        audit_ref: Any = None
        audit_terminal_recorded = False
        kvk_no: int | None = None
        scan_id: int | None = None
        rows: int | None = None
        staged: int | None = None
        neg: int | None = None
        external_batch_id: str | None = None
        try:
            logger.info(
                "[KVK] Reading attachment: %s (%s bytes)",
                attachment.filename,
                getattr(attachment, "size", None),
            )
            read_started = deps.now_utc()
            file_bytes = await attachment.read()
            audit_context = KvkAllImportAuditContext(
                source_filename=attachment.filename,
                source_type=kvk_all_source_type(attachment.filename),
                source_message_id=(
                    int(message.id) if getattr(message, "id", None) is not None else None
                ),
                source_channel_id=(
                    int(message.channel.id)
                    if getattr(message.channel, "id", None) is not None
                    else None
                ),
                actor_discord_id=(
                    int(message.author.id)
                    if getattr(message.author, "id", None) is not None
                    else None
                ),
            )
            audit_ref = await deps.start_audit_batch(
                context=audit_context,
                content=file_bytes,
            )
            await deps.record_audit_phase(
                audit_ref,
                phase_name=KVK_ALL_AUDIT_ATTACHMENT_READ_PHASE,
                phase_status="completed",
                started_at_utc=read_started.replace(tzinfo=None),
                rows_out=1,
                duration_ms=audit_duration_ms(read_started),
                details=kvk_all_audit_details(audit_context),
            )

            preflight_started = deps.now_utc()
            ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
            if not ok:
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=KVK_ALL_AUDIT_SQL_PREFLIGHT_PHASE,
                    phase_status="failed",
                    started_at_utc=preflight_started.replace(tzinfo=None),
                    duration_ms=audit_duration_ms(preflight_started),
                    error_type="SqlHeadroomInsufficient",
                    error_text="SQL log headroom insufficient",
                    details=kvk_all_audit_details(
                        audit_context,
                        error="SQL log headroom insufficient",
                    ),
                )
                await deps.fail_audit_batch(
                    audit_ref,
                    error_type="SqlHeadroomInsufficient",
                    error_text="SQL log headroom insufficient",
                    rows_written=0,
                    details=kvk_all_audit_details(
                        audit_context,
                        error="SQL log headroom insufficient",
                    ),
                )
                audit_terminal_recorded = True
                continue
            await deps.record_audit_phase(
                audit_ref,
                phase_name=KVK_ALL_AUDIT_SQL_PREFLIGHT_PHASE,
                phase_status="completed",
                started_at_utc=preflight_started.replace(tzinfo=None),
                duration_ms=audit_duration_ms(preflight_started),
                details=kvk_all_audit_details(audit_context),
            )

            result = await deps.offload_callable(
                ingest_kvk_all_excel,
                content=file_bytes,
                source_filename=attachment.filename,
                uploader_id=message.author.id,
                scan_ts_utc=message.created_at,
                server=os.environ.get("SQL_SERVER"),
                database=os.environ.get("SQL_DATABASE"),
                username=os.environ.get("SQL_USERNAME"),
                password=os.environ.get("SQL_PASSWORD"),
                name="ingest_kvk_all_excel",
                prefer_process=True,
                meta={"filename": attachment.filename},
            )

            if isinstance(result, dict) and not result.get("success", True):
                logger.info(
                    "[KVK] Import failed for %s: %s", attachment.filename, result.get("error")
                )
                if audit_context is not None:
                    await _record_structured_failure_audit(
                        deps,
                        audit_ref,
                        audit_context,
                        result,
                    )
                    audit_terminal_recorded = True
                await deps.send_embed(
                    notify_ch,
                    "KVK All-Kingdom Import \u274c",
                    {
                        "Filename": attachment.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                        "Error": result.get("error"),
                        "Sheet": result.get("sheet", "unknown"),
                    },
                    0xE74C3C,
                )
                continue

            kvk_no = int(result["kvk_no"])
            scan_id = int(result["scan_id"])
            rows = int(result["row_count"])
            neg = int(result["negatives"])
            dur_s = float(result["duration_s"])
            staged = int(result.get("staged_rows", rows))
            proc_ms = float(result.get("proc_ms", max(0.0, dur_s * 1000.0)))
            io_ms = max(0.0, dur_s * 1000.0 - proc_ms)
            recompute_ms = float(result.get("recompute_ms", 0.0))
            sheet_used = result.get("sheet", "unknown")
            external_batch_id = kvk_all_external_batch_id(kvk_no, scan_id)

            if audit_context is not None:
                success_details = kvk_all_audit_details(
                    audit_context,
                    rows_parsed=staged,
                    rows_staged=staged,
                    rows_written=rows,
                    negatives=neg,
                    kvk_no=kvk_no,
                    scan_id=scan_id,
                    sheet=sheet_used,
                    schema_version=result.get("schema_version"),
                    auto_export_enabled=deps.auto_export_enabled,
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=KVK_ALL_AUDIT_PARSE_PHASE,
                    phase_status="completed",
                    rows_out=staged,
                    duration_ms=_maybe_int(float(result.get("prepare_ms", 0))),
                    details=success_details,
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=KVK_ALL_AUDIT_STAGE_PHASE,
                    phase_status="completed",
                    rows_in=staged,
                    rows_out=staged,
                    duration_ms=_maybe_int(float(result.get("stage_insert_ms", 0))),
                    details=success_details,
                    set_batch_status="staged",
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=KVK_ALL_AUDIT_INGEST_PHASE,
                    phase_status="completed",
                    rows_in=staged,
                    rows_out=rows,
                    duration_ms=_maybe_int(float(result.get("ingest_ms", proc_ms))),
                    details=success_details,
                    set_batch_status="procedure_started",
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=KVK_ALL_AUDIT_RECOMPUTE_PHASE,
                    phase_status="completed",
                    rows_in=rows,
                    rows_out=rows,
                    duration_ms=_maybe_int(recompute_ms),
                    details=success_details,
                    set_batch_status="downstream_rebuild_started",
                )
                await deps.record_audit_phase(
                    audit_ref,
                    phase_name=KVK_ALL_AUDIT_NEGATIVE_PHASE,
                    phase_status="completed",
                    rows_in=rows,
                    rows_out=neg,
                    duration_ms=_maybe_int(float(result.get("negative_count_ms", 0))),
                    details=success_details,
                )

            neg_badge = "0" if neg == 0 else f"{neg} \u26a0\ufe0f"
            color = 0x2ECC71 if neg == 0 else 0xE67E22
            title = (
                "KVK All-Kingdom Import \u2705"
                if neg == 0
                else "KVK All-Kingdom Import \u26a0\ufe0f"
            )

            fields = {
                "KVK": str(kvk_no),
                "ScanID": str(scan_id),
                "Rows": str(rows),
                "Staged": str(staged),
                "Negative Corrections": neg_badge,
                "Duration": f"{dur_s:.2f}s",
                "Health": (
                    f"proc `{proc_ms:.0f}ms` \u2022 I/O `{io_ms:.0f}ms`"
                    + (f" \u2022 recompute `{recompute_ms:.0f}ms`" if recompute_ms > 0 else "")
                ),
                "File": attachment.filename,
                "Sheet": sheet_used,
                "Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploader": f"{message.author} ({message.author.id})",
            }

            embed = _build_result_embed(deps, title, color, fields)
            view = _build_sheet_view(deps)
            await notify_ch.send(embed=embed, view=view)

            if deps.auto_export_enabled:
                export_started = deps.now_utc()
                logger.info(
                    "[KVK_EXPORT] Scheduling auto-export for KVK %s (Scan %s)",
                    kvk_no,
                    scan_id,
                )
                deps.create_task(
                    deps.auto_export_scheduler(
                        kvk_no,
                        notify_ch,
                        deps.bot.loop,
                    )
                )
                if audit_context is not None:
                    await deps.record_audit_phase(
                        audit_ref,
                        phase_name=KVK_ALL_AUDIT_AUTO_EXPORT_PHASE,
                        phase_status="completed",
                        started_at_utc=export_started.replace(tzinfo=None),
                        rows_in=rows,
                        rows_out=rows,
                        duration_ms=audit_duration_ms(export_started),
                        details=success_details,
                    )
            if audit_context is not None:
                await deps.complete_audit_batch(
                    audit_ref,
                    rows_in_source=staged,
                    rows_staged=staged,
                    rows_written=rows,
                    rows_skipped=0,
                    external_batch_id=external_batch_id,
                    details=success_details,
                )
                audit_terminal_recorded = True
        except Exception as exc:
            if audit_ref is not None and audit_context is not None and not audit_terminal_recorded:
                diagnostic_id = _maybe_int(getattr(exc, "kvk_diagnostic_id", None))
                diagnostic_external_id = (
                    kvk_all_diagnostic_external_batch_id(diagnostic_id)
                    if diagnostic_id is not None
                    else None
                )
                staged_from_exc = _maybe_int(getattr(exc, "kvk_staged_rows", None))
                error_type = _exception_error_type(exc, diagnostic_id)
                terminal_details = kvk_all_audit_details(
                    audit_context,
                    rows_parsed=staged if staged is not None else staged_from_exc,
                    rows_staged=staged if staged is not None else staged_from_exc,
                    rows_written=rows,
                    negatives=neg,
                    kvk_no=kvk_no,
                    scan_id=scan_id,
                    diagnostic_id=diagnostic_id,
                    error=str(exc),
                )
                if external_batch_id is not None and rows is not None:
                    await deps.complete_audit_batch(
                        audit_ref,
                        rows_in_source=staged,
                        rows_staged=staged,
                        rows_written=rows,
                        rows_skipped=0,
                        external_batch_id=external_batch_id,
                        details=terminal_details,
                    )
                else:
                    await deps.fail_audit_batch(
                        audit_ref,
                        error_type=error_type,
                        error_text=str(exc),
                        rows_in_source=staged if staged is not None else staged_from_exc,
                        rows_staged=staged if staged is not None else staged_from_exc,
                        rows_written=rows if rows is not None else 0,
                        rows_skipped=0 if rows is not None else staged_from_exc,
                        external_batch_table=(
                            KVK_ALL_AUDIT_DIAGNOSTIC_TABLE if diagnostic_external_id else None
                        ),
                        external_batch_id=diagnostic_external_id,
                        details=terminal_details,
                    )
                audit_terminal_recorded = True
            logger.exception("[KVK] Import failed for %s: %s", attachment.filename, exc)
            await deps.send_embed(
                notify_ch,
                "KVK All-Kingdom Import \u274c",
                {
                    "Error": f"{type(exc).__name__}: {exc}",
                    "File": attachment.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE74C3C,
            )
    return True
