"""PreKvK workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import re
from typing import Any

from prekvk_importer import import_prekvk_bytes
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

        ok, note, rows = await deps.offload_callable(
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
            name="import_prekvk_bytes",
            prefer_process=True,
            meta={"filename": target.filename, "kvk_no": detected_kvk_no},
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

                try:
                    await _refresh_stats_embed(deps)
                except Exception:
                    logger.debug(
                        "Failed to refresh stats embed after Pre-KVK import", exc_info=True
                    )
        else:
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
