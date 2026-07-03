"""Preference mutation service for the /me command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from inventory import reporting_service
from inventory.models import InventoryReportVisibility

logger = logging.getLogger(__name__)

VisibilityWriter = Callable[..., Awaitable[reporting_service.InventoryVisibilityPreferenceWrite]]


@dataclass(frozen=True, slots=True)
class PreferenceMutationResult:
    ok: bool
    message: str
    inventory_visibility: str | None = None


def _visibility_label(visibility: InventoryReportVisibility) -> str:
    if visibility == InventoryReportVisibility.PUBLIC:
        return "public"
    return "private"


async def save_inventory_visibility(
    discord_user_id: int,
    visibility: InventoryReportVisibility,
    *,
    writer: VisibilityWriter = reporting_service.write_visibility_preference,
) -> PreferenceMutationResult:
    try:
        result = await writer(int(discord_user_id), visibility)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_inventory_visibility_save_failed user_id=%s selected=%s",
            discord_user_id,
            visibility.value,
        )
        return PreferenceMutationResult(
            ok=False,
            message=(
                "Inventory report visibility could not be saved. " "Please try again in a moment."
            ),
        )

    if not result.ok or result.visibility != visibility:
        return PreferenceMutationResult(
            ok=False,
            message=(
                "Inventory report visibility could not be saved. "
                "Your previous setting is unchanged."
            ),
        )

    label = _visibility_label(visibility)
    logger.info(
        "player_self_service_inventory_visibility_saved user_id=%s visibility=%s",
        discord_user_id,
        visibility.value,
    )
    return PreferenceMutationResult(
        ok=True,
        message=f"Inventory report visibility saved as {label}.",
        inventory_visibility=label,
    )
