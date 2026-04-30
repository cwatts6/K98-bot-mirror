from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from decoraters import _is_admin
from inventory.dal import inventory_reporting_dal
from inventory.inventory_service import (
    get_registered_governors_for_user,
    user_can_import_for_governor,
)
from inventory.models import (
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
    InventoryReportVisibility,
    InventoryResourcePoint,
    InventorySpeedupPoint,
    RegisteredGovernor,
)

logger = logging.getLogger(__name__)

REPORT_RANGE_DAYS = {
    InventoryReportRange.ONE_MONTH: 31,
    InventoryReportRange.THREE_MONTHS: 92,
    InventoryReportRange.SIX_MONTHS: 183,
    InventoryReportRange.TWELVE_MONTHS: 366,
}


def parse_report_range(value: str | None) -> InventoryReportRange:
    normalized = (value or InventoryReportRange.ONE_MONTH.value).strip().upper()
    for item in InventoryReportRange:
        if item.value.upper() == normalized:
            return item
    raise ValueError("Inventory range must be one of: 1M, 3M, 6M, 12M.")


def parse_report_view(value: str | None) -> InventoryReportView:
    normalized = (value or InventoryReportView.ALL.value).strip().lower()
    try:
        return InventoryReportView(normalized)
    except ValueError as exc:
        raise ValueError("Inventory view must be Resources, Speedups, or All.") from exc


def parse_visibility(value: str | None) -> InventoryReportVisibility | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace(" ", "_")
    aliases = {
        "only_me": InventoryReportVisibility.ONLY_ME,
        "me": InventoryReportVisibility.ONLY_ME,
        "private": InventoryReportVisibility.ONLY_ME,
        "public": InventoryReportVisibility.PUBLIC,
        "public_output_channel": InventoryReportVisibility.PUBLIC,
    }
    if normalized not in aliases:
        raise ValueError("Visibility must be Only Me or Public Output Channel.")
    return aliases[normalized]


async def get_visibility_preference(discord_user_id: int) -> InventoryReportVisibility:
    pref = await asyncio.to_thread(
        inventory_reporting_dal.fetch_visibility_preference,
        int(discord_user_id),
    )
    return pref or InventoryReportVisibility.ONLY_ME


async def resolve_visibility(
    *, discord_user_id: int, selected_visibility: InventoryReportVisibility | None
) -> InventoryReportVisibility:
    if selected_visibility is not None:
        await asyncio.to_thread(
            inventory_reporting_dal.upsert_visibility_preference,
            int(discord_user_id),
            selected_visibility,
        )
        return selected_visibility
    return await get_visibility_preference(discord_user_id)


async def resolve_governor_for_report(
    *,
    discord_user_id: int,
    governor_id: int | None,
    discord_user: Any | None = None,
) -> RegisteredGovernor | None:
    governors = await get_registered_governors_for_user(discord_user_id)
    if governor_id is None:
        return governors[0] if len(governors) == 1 else None

    if not await user_can_import_for_governor(
        discord_user_id=discord_user_id,
        governor_id=int(governor_id),
        discord_user=discord_user,
    ):
        raise PermissionError("You can only view inventory for governors registered to you.")

    for item in governors:
        if item.governor_id == int(governor_id):
            return item

    if discord_user is not None and _is_admin(discord_user):
        return RegisteredGovernor(int(governor_id), str(governor_id), "Lookup")
    return None


def _group_resource_points(rows: list[dict[str, Any]]) -> list[InventoryResourcePoint]:
    grouped: dict[Any, dict[str, Any]] = {}
    for row in rows:
        scan = row.get("ScanUtc")
        bucket = grouped.setdefault(scan, {"scan_utc": scan})
        rtype = str(row.get("ResourceType") or "").lower()
        if rtype in {"food", "wood", "stone", "gold"}:
            bucket[rtype] = int(row.get("TotalResourcesValue") or 0)

    points: list[InventoryResourcePoint] = []
    for row in grouped.values():
        if all(key in row for key in ("food", "wood", "stone", "gold")):
            points.append(
                InventoryResourcePoint(
                    scan_utc=row["scan_utc"],
                    food=int(row["food"]),
                    wood=int(row["wood"]),
                    stone=int(row["stone"]),
                    gold=int(row["gold"]),
                )
            )
    return sorted(points, key=lambda item: item.scan_utc)


def _group_speedup_points(rows: list[dict[str, Any]]) -> list[InventorySpeedupPoint]:
    grouped: dict[Any, dict[str, Any]] = {}
    for row in rows:
        scan = row.get("ScanUtc")
        bucket = grouped.setdefault(scan, {"scan_utc": scan})
        stype = str(row.get("SpeedupType") or "").lower()
        if stype in {"building", "research", "training", "healing", "universal"}:
            bucket[f"{stype}_days"] = float(row.get("TotalDaysDecimal") or 0.0)

    points: list[InventorySpeedupPoint] = []
    for row in grouped.values():
        if all(
            key in row
            for key in (
                "building_days",
                "research_days",
                "training_days",
                "healing_days",
                "universal_days",
            )
        ):
            points.append(
                InventorySpeedupPoint(
                    scan_utc=row["scan_utc"],
                    building_days=float(row["building_days"]),
                    research_days=float(row["research_days"]),
                    training_days=float(row["training_days"]),
                    healing_days=float(row["healing_days"]),
                    universal_days=float(row["universal_days"]),
                )
            )
    return sorted(points, key=lambda item: item.scan_utc)


def _filter_points_for_range(points: list[Any], range_key: InventoryReportRange) -> list[Any]:
    cutoff = datetime.now(UTC) - timedelta(days=REPORT_RANGE_DAYS[range_key])
    filtered = []
    for item in points:
        scan = getattr(item, "scan_utc", None)
        if scan is None:
            continue
        if getattr(scan, "tzinfo", None) is None:
            scan = scan.replace(tzinfo=UTC)
        if scan >= cutoff:
            filtered.append(item)
    return filtered or points[-1:]


async def build_inventory_report_payload(
    *,
    discord_user_id: int,
    governor: RegisteredGovernor,
    view: InventoryReportView,
    range_key: InventoryReportRange,
) -> InventoryReportPayload:
    resources: list[InventoryResourcePoint] = []
    speedups: list[InventorySpeedupPoint] = []

    if view in {InventoryReportView.RESOURCES, InventoryReportView.ALL}:
        resource_rows = await asyncio.to_thread(
            inventory_reporting_dal.fetch_resource_rows,
            int(governor.governor_id),
        )
        resources = _filter_points_for_range(_group_resource_points(resource_rows), range_key)

    if view in {InventoryReportView.SPEEDUPS, InventoryReportView.ALL}:
        speedup_rows = await asyncio.to_thread(
            inventory_reporting_dal.fetch_speedup_rows,
            int(governor.governor_id),
        )
        speedups = _filter_points_for_range(_group_speedup_points(speedup_rows), range_key)

    logger.info(
        "inventory_report_payload_built user_id=%s governor_id=%s view=%s range=%s resources=%s speedups=%s",
        discord_user_id,
        governor.governor_id,
        view.value,
        range_key.value,
        len(resources),
        len(speedups),
    )
    return InventoryReportPayload(
        governor_id=int(governor.governor_id),
        governor_name=governor.governor_name,
        view=view,
        range_key=range_key,
        resources=resources,
        speedups=speedups,
        generated_at_utc=datetime.now(UTC),
    )
