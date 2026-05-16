"""Player-location CSV upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from location_importer import load_staging_and_replace, parse_output_csv
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
        rows = parse_output_csv(csv_bytes)

        if not rows:
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

        ok = await deps.ensure_sql_headroom_or_notify(target_ch)
        if not ok:
            return True

        staging_rows, total_tracked = await deps.offload_callable(
            load_staging_and_replace,
            rows,
            name="load_staging_and_replace",
            prefer_process=True,
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

        signal_location_refresh_complete()

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
    finally:
        return True
