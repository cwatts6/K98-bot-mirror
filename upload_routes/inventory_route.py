"""Inventory upload-first route for the legacy Discord message listener."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InventoryRouteDeps:
    inventory_upload_channel_id: int
    bot: Any
    upload_handler: Callable[[Any, Any], Awaitable[bool]] | None = None


async def _default_upload_handler(message: Any, bot: Any) -> bool:
    from ui.views.inventory_views import handle_inventory_upload_message

    return await handle_inventory_upload_message(message, bot)


async def handle_inventory_upload(message: Any, deps: InventoryRouteDeps) -> bool:
    """Delegate inventory image uploads through the upload route boundary."""
    if (
        not deps.inventory_upload_channel_id
        or message.channel.id != deps.inventory_upload_channel_id
        or not message.attachments
    ):
        return False

    handler = deps.upload_handler or _default_upload_handler
    try:
        return await handler(message, deps.bot)
    except Exception:
        logger.exception(
            "inventory_upload_first_route_failed message_id=%s channel_id=%s",
            getattr(message, "id", None),
            getattr(getattr(message, "channel", None), "id", None),
        )
        try:
            await message.channel.send(
                f"<@{message.author.id}> Inventory import failed unexpectedly. Please try again.",
                delete_after=120,
            )
        except Exception:
            logger.debug("inventory_upload_first_error_notice_failed", exc_info=True)
        return True
