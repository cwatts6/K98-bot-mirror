"""MGE results workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from upload_routes.common import message_source_fields, resolve_notify_channel, schedule_best_effort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MgeResultsRouteDeps:
    mge_data_channel_id: int
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task


def _load_import_results_auto() -> Callable[..., dict[str, Any]]:
    from mge.mge_results_import import import_results_auto

    return import_results_auto


async def handle_mge_results_upload(message: Any, deps: MgeResultsRouteDeps) -> bool:
    """Handle automatic MGE results imports from the configured data channel."""
    if message.channel.id != deps.mge_data_channel_id or not message.attachments:
        return False

    notify_ch = await resolve_notify_channel(
        deps.get_notify_channel,
        message.channel,
        logger,
        "mge_results_upload",
    )

    target = next(
        (a for a in message.attachments if a.filename.lower().endswith(".xlsx")),
        None,
    )
    if not target:
        fields = {
            "Info": "No .xlsx file found.",
            "Expected": "mge_rankings_kd####_YYYYMMDD.xlsx",
            **message_source_fields(message),
        }
        await deps.send_embed(notify_ch, "MGE Results Import ⚠️", fields, 0xE67E22)
        return True

    try:
        file_bytes = await target.read()

        ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
        if not ok:
            return True

        result = await deps.offload_callable(
            _load_import_results_auto(),
            file_bytes,
            target.filename,
            message.author.id,
            name="import_results_auto",
            prefer_process=True,
            meta={"filename": target.filename, "channel_id": message.channel.id},
        )

        fields = {
            "EventId": str(result["event_id"]),
            "Mode": str(result["event_mode"]),
            "Rows": str(result["rows"]),
            "ImportId": str(result["import_id"]),
            "File": target.filename,
        }

        report = result.get("report") or {}
        if report.get("type") == "open_top15":
            fields["Report"] = "Open Top-15 generated"
        elif report.get("type") == "controlled_awarded_vs_actual":
            fields["Awarded"] = str(report.get("awarded_total", 0))
            fields["Matched"] = str(report.get("matched_actual_total", 0))

        await deps.send_embed(notify_ch, "MGE Results Import ✅", fields, 0x2ECC71)
        schedule_best_effort(
            deps.create_task,
            deps.trigger_log_backup_background(),
            logger,
            "Failed to schedule background log-backup trigger",
        )
    except Exception as e:
        fields = {
            "Error": f"{type(e).__name__}: {e}",
            "File": target.filename,
            **message_source_fields(message),
        }
        await deps.send_embed(notify_ch, "MGE Results Import ❌", fields, 0xE74C3C)
    return True
