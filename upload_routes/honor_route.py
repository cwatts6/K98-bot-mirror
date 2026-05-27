"""KVK Honor workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import os
import re
from typing import Any

from honor_importer import ingest_honor_snapshot, parse_honor_xlsx
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
    send_stats_update_embed: Callable[..., Awaitable[Any]] | None = None
    now_utc: Callable[[], Any] = utcnow
    sql_conn_str_factory: Callable[[], str] | None = None


def _is_test_upload(message: Any, filename: str) -> bool:
    msg_text = (message.content or "").lower()
    return (
        ("[test]" in msg_text)
        or (" test " in f" {msg_text} ")
        or filename.lower().startswith(("test_", "demo_", "sample_"))
    )


def _sql_conn_str_from_env() -> str:
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.environ.get('SQL_SERVER')};DATABASE={os.environ.get('SQL_DATABASE')};UID={os.environ.get('SQL_USERNAME')};PWD={os.environ.get('SQL_PASSWORD')};"
    )


async def _refresh_stats_embed(deps: HonorRouteDeps, is_test: bool) -> None:
    stats_refresh = deps.send_stats_update_embed
    if stats_refresh is None:
        from stats_alerts.interface import send_stats_update_embed as stats_refresh

    sql_conn_str = (
        deps.sql_conn_str_factory() if deps.sql_conn_str_factory else _sql_conn_str_from_env()
    )
    ts = deps.now_utc().strftime("%Y-%m-%d %H:%M UTC")
    await stats_refresh(deps.bot, ts, True, sql_conn_str, is_test=is_test)


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
        try:
            pre_df = await deps.offload_callable(
                parse_honor_xlsx,
                file_bytes,
                name="parse_honor_xlsx",
                prefer_process=True,
                meta={"filename": target.filename},
            )
            row_count = len(pre_df)
        except Exception:
            logger.debug("honor_upload_row_count_parse_failed", exc_info=True)
            row_count = 0

        kvk_no, scan_id = await deps.offload_callable(
            ingest_honor_snapshot,
            file_bytes,
            source_filename=target.filename,
            scan_ts_utc=message.created_at,
            name="ingest_honor_snapshot",
            prefer_process=True,
            meta={"filename": target.filename},
        )

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

        try:
            await _refresh_stats_embed(deps, is_test)
        except Exception:
            logger.debug("Failed to refresh stats embed after KVK Honor import", exc_info=True)
    except Exception as e:
        fields = {
            "Error": f"{type(e).__name__}: {e}",
            "Filename": target.filename,
            **message_source_fields(message),
        }
        await deps.send_embed(notify_ch, "KVK Honor Import ❌", fields, 0xE74C3C)
    return True
