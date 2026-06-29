"""Player-location CSV upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from location_importer import load_staging_and_replace, parse_output_csv
from services.location_import_service import (
    LOCATION_AUDIT_PARSE_PHASE,
    LOCATION_AUDIT_REFRESH_PHASE,
    LOCATION_AUDIT_REPLACE_PHASE,
    LocationImportAuditContext,
    complete_location_audit_batch,
    fail_location_audit_batch,
    record_location_audit_phase,
    start_location_audit_batch,
)
from services.location_refresh_signal import signal_location_refresh_complete

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlayerLocationRouteDeps:
    player_location_channel_id: int
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    warm_profile_cache: Callable[[], None] | None = None


async def handle_player_location_upload(message: Any, deps: PlayerLocationRouteDeps) -> bool:
    """Handle automatic `scan_1198.csv` imports from the location upload channel."""
    if message.channel.id != deps.player_location_channel_id or not message.attachments:
        return False

    target = next((a for a in message.attachments if a.filename.lower() == "scan_1198.csv"), None)
    if not target:
        return False

    target_ch = message.channel
    try:
        notify_ch = await deps.get_notify_channel()
        if notify_ch:
            target_ch = notify_ch
    except Exception:
        logger.debug("Failed to resolve notify channel for player location upload", exc_info=True)

    try:
        csv_bytes = await target.read()
        audit_context = LocationImportAuditContext(
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
            entry_point="location_auto_upload",
            sql_operation="replace",
        )
        audit_ref = await start_location_audit_batch(
            context=audit_context,
            csv_bytes=csv_bytes,
        )

        try:
            rows = parse_output_csv(csv_bytes)
        except Exception as exc:
            await record_location_audit_phase(
                audit_ref,
                phase_name=LOCATION_AUDIT_PARSE_PHASE,
                phase_status="failed",
                error_type=type(exc).__name__,
                error_text=str(exc),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "error": str(exc),
                },
            )
            await fail_location_audit_batch(
                audit_ref,
                error_type=type(exc).__name__,
                error_text=str(exc),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "error": str(exc),
                },
            )
            raise

        if not rows:
            await record_location_audit_phase(
                audit_ref,
                phase_name=LOCATION_AUDIT_PARSE_PHASE,
                phase_status="skipped",
                rows_out=0,
                error_type="NoValidLocationRows",
                error_text="No valid rows found in CSV.",
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": 0,
                },
            )
            await fail_location_audit_batch(
                audit_ref,
                status="skipped",
                error_type="NoValidLocationRows",
                error_text="No valid rows found in CSV.",
                rows_skipped=0,
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": 0,
                },
            )
            await deps.send_embed(
                target_ch,
                "Player Location Import",
                {
                    "Status": "No valid rows found in CSV.",
                    "Source Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploaded By": f"{message.author} ({message.author.id})",
                },
                0xE74C3C,
            )
            return True

        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_PARSE_PHASE,
            phase_status="completed",
            rows_out=len(rows),
            details={
                "entry_point": audit_context.entry_point,
                "sql_operation": audit_context.sql_operation,
                "rows_parsed": len(rows),
            },
        )

        ok = await deps.ensure_sql_headroom_or_notify(target_ch)
        if not ok:
            await fail_location_audit_batch(
                audit_ref,
                status="skipped",
                error_type="SqlHeadroomUnavailable",
                error_text="SQL headroom preflight rejected location import.",
                rows_skipped=len(rows),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": len(rows),
                },
            )
            return True

        try:
            staging_rows, total_tracked = await deps.offload_callable(
                load_staging_and_replace,
                rows,
                name="load_staging_and_replace",
                prefer_process=True,
            )
        except Exception as exc:
            await record_location_audit_phase(
                audit_ref,
                phase_name=LOCATION_AUDIT_REPLACE_PHASE,
                phase_status="failed",
                rows_in=len(rows),
                error_type=type(exc).__name__,
                error_text=str(exc),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": len(rows),
                    "error": str(exc),
                },
            )
            await fail_location_audit_batch(
                audit_ref,
                error_type=type(exc).__name__,
                error_text=str(exc),
                rows_staged=0,
                rows_written=0,
                rows_skipped=len(rows),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": len(rows),
                    "error": str(exc),
                },
            )
            raise

        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_REPLACE_PHASE,
            phase_status="completed",
            rows_in=len(rows),
            rows_out=staging_rows,
            details={
                "entry_point": audit_context.entry_point,
                "sql_operation": audit_context.sql_operation,
                "rows_parsed": len(rows),
                "staging_rows": staging_rows,
                "total_tracked": total_tracked,
            },
            set_batch_status="staged",
        )

        await deps.send_embed(
            target_ch,
            "Player Location Import ✅",
            {
                "Imported Rows": str(staging_rows),
                "Total Tracked": str(total_tracked),
                "Source Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploaded By": f"{message.author} ({message.author.id})",
            },
            0x2ECC71,
        )

        try:
            deps.create_task(deps.trigger_log_backup_background())
        except Exception:
            logger.exception("Failed to schedule background log-backup trigger")

        try:
            if deps.warm_profile_cache is None:
                from profile_cache import warm_cache as warm_profile_cache
            else:
                warm_profile_cache = deps.warm_profile_cache
            warm_profile_cache()
        except Exception:
            logger.debug("Failed to warm profile cache after player location import", exc_info=True)

        try:
            signal_location_refresh_complete()
        except Exception as exc:
            await record_location_audit_phase(
                audit_ref,
                phase_name=LOCATION_AUDIT_REFRESH_PHASE,
                phase_status="failed",
                rows_in=staging_rows,
                rows_out=staging_rows,
                error_type=type(exc).__name__,
                error_text=str(exc),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": len(rows),
                    "staging_rows": staging_rows,
                    "total_tracked": total_tracked,
                    "error": str(exc),
                },
            )
            await fail_location_audit_batch(
                audit_ref,
                error_type=type(exc).__name__,
                error_text=str(exc),
                rows_staged=staging_rows,
                rows_written=staging_rows,
                rows_skipped=max(0, len(rows) - int(staging_rows or 0)),
                details={
                    "entry_point": audit_context.entry_point,
                    "sql_operation": audit_context.sql_operation,
                    "rows_parsed": len(rows),
                    "staging_rows": staging_rows,
                    "total_tracked": total_tracked,
                    "error": str(exc),
                },
            )
            raise

        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_REFRESH_PHASE,
            phase_status="completed",
            rows_in=staging_rows,
            rows_out=staging_rows,
            details={
                "entry_point": audit_context.entry_point,
                "sql_operation": audit_context.sql_operation,
                "rows_parsed": len(rows),
                "staging_rows": staging_rows,
                "total_tracked": total_tracked,
            },
        )
        await complete_location_audit_batch(
            audit_ref,
            rows_staged=staging_rows,
            rows_written=staging_rows,
            rows_skipped=max(0, len(rows) - int(staging_rows or 0)),
            details={
                "entry_point": audit_context.entry_point,
                "sql_operation": audit_context.sql_operation,
                "rows_parsed": len(rows),
                "staging_rows": staging_rows,
                "total_tracked": total_tracked,
            },
        )

    except Exception as e:
        await deps.send_embed(
            target_ch,
            "Player Location Import ❌",
            {
                "Error": f"{type(e).__name__}: {e}",
                "Source Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploaded By": f"{message.author} ({message.author.id})",
            },
            0xE74C3C,
            mention=None,
        )
    return True
