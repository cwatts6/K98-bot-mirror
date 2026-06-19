"""Weekly alliance activity workbook upload route for the legacy listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from upload_routes.common import message_source_fields, resolve_notify_channel, schedule_best_effort
from weekly_activity_importer import ingest_weekly_activity_excel

logger = logging.getLogger(__name__)


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

    try:
        file_bytes = await target.read()
        ok = await deps.ensure_sql_headroom_or_notify(target_ch)
        if not ok:
            return True

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
        if snap_id == 0:
            await deps.send_embed(
                target_ch,
                "Alliance Activity Import",
                {"Status": "Duplicate detected for this week. Skipped."},
                0xF1C40F,
            )
        else:
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
            schedule_best_effort(
                deps.create_task,
                deps.trigger_log_backup_background(),
                logger,
                "Failed to schedule background log-backup trigger",
            )
    except Exception as e:
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
