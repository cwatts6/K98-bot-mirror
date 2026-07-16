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
VisibilityReader = Callable[..., Awaitable[reporting_service.InventoryVisibilityPreferenceRead]]


@dataclass(frozen=True, slots=True)
class PreferenceMutationResult:
    ok: bool
    message: str
    inventory_visibility: str | None = None
    stale: bool = False


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
                "Inventory report visibility could not be saved. Please try again in a moment."
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


async def confirm_inventory_visibility_change(
    discord_user_id: int,
    *,
    expected_visibility: InventoryReportVisibility,
    target_visibility: InventoryReportVisibility,
    reader: VisibilityReader = reporting_service.read_visibility_preference,
    writer: VisibilityWriter = reporting_service.write_visibility_preference,
) -> PreferenceMutationResult:
    try:
        current_result = await reader(int(discord_user_id))
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_inventory_visibility_confirm_read_failed user_id=%s",
            discord_user_id,
        )
        return PreferenceMutationResult(
            ok=False,
            message="Inventory visibility could not be checked. Please reopen Privacy & sharing.",
        )

    if not current_result.ok:
        return PreferenceMutationResult(
            ok=False,
            message="Inventory visibility could not be checked. Please reopen Privacy & sharing.",
        )
    current = current_result.visibility or InventoryReportVisibility.ONLY_ME
    if current != expected_visibility:
        return PreferenceMutationResult(
            ok=False,
            stale=True,
            message=(
                "Inventory visibility changed after this confirmation opened. "
                "Review the current setting and try again."
            ),
        )
    if target_visibility == current:
        return PreferenceMutationResult(
            ok=False,
            stale=True,
            message="Inventory visibility is already set to that state.",
        )
    return await save_inventory_visibility(
        int(discord_user_id),
        target_visibility,
        writer=writer,
    )
