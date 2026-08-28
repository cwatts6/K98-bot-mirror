from __future__ import annotations

import asyncio
import logging
from typing import Any

from decoraters import _is_admin
from inventory.dal import inventory_profile_dal
from inventory.inventory_service import user_can_import_for_governor
from inventory.models import InventoryGovernorProfile
from inventory.vip_levels import normalize_vip_level, persisted_vip_code, vip_label
from registry import registry_service

logger = logging.getLogger(__name__)


def profile_from_row(governor_id: int, row: dict[str, Any] | None) -> InventoryGovernorProfile:
    if not row:
        return InventoryGovernorProfile.default(governor_id)
    code = persisted_vip_code(row.get("VipLevelCode"))
    return InventoryGovernorProfile(
        governor_id=int(row.get("GovernorID") or governor_id),
        vip_level_code=code,
        vip_level_label=vip_label(code),
        updated_by_discord_user_id=(
            int(row["UpdatedByDiscordUserID"]) if row.get("UpdatedByDiscordUserID") else None
        ),
        created_at_utc=row.get("CreatedAtUtc"),
        updated_at_utc=row.get("UpdatedAtUtc"),
    )


async def fetch_inventory_profile(governor_id: int) -> InventoryGovernorProfile:
    try:
        row = await asyncio.to_thread(
            inventory_profile_dal.fetch_inventory_profile,
            int(governor_id),
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "inventory_profile_fetch_failed governor_id=%s using_default=True",
            governor_id,
        )
        return InventoryGovernorProfile.default(int(governor_id))
    return profile_from_row(int(governor_id), row)


async def update_inventory_vip(
    *,
    discord_user_id: int,
    governor_id: int,
    vip_level_code: str | None,
    discord_user: Any | None = None,
    is_admin: bool = False,
) -> InventoryGovernorProfile:
    admin = bool(is_admin or (discord_user is not None and _is_admin(discord_user)))
    if not await user_can_import_for_governor(
        discord_user_id=int(discord_user_id),
        governor_id=int(governor_id),
        discord_user=discord_user,
        is_admin=admin,
    ):
        raise PermissionError("You can only update VIP for governors registered to you.")

    if not admin:
        current_owner = await asyncio.to_thread(
            registry_service.get_discord_user_for_governor,
            int(governor_id),
        )
        if not current_owner or int(current_owner["DiscordUserID"]) != int(discord_user_id):
            raise PermissionError("You can only update VIP for governors registered to you.")

    level = normalize_vip_level(vip_level_code)
    persisted_code = persisted_vip_code(level)
    await asyncio.to_thread(
        inventory_profile_dal.upsert_inventory_vip,
        governor_id=int(governor_id),
        vip_level_code=persisted_code,
        updated_by_discord_user_id=int(discord_user_id),
    )
    logger.info(
        "inventory_vip_updated actor=%s governor_id=%s vip_level=%s",
        discord_user_id,
        governor_id,
        persisted_code or "UNKNOWN",
    )
    return InventoryGovernorProfile(
        governor_id=int(governor_id),
        vip_level_code=persisted_code,
        vip_level_label=vip_label(level),
        updated_by_discord_user_id=int(discord_user_id),
    )
