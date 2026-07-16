from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from decoraters import _is_admin
from inventory import profile_service
from inventory.dal import inventory_material_dal, inventory_reporting_dal
from inventory.inventory_service import (
    get_registered_governors_for_user,
    user_can_import_for_governor,
)
from inventory.material_calculations import (
    choice_chest_total,
    empty_material_values,
    material_totals,
)
from inventory.models import (
    InventoryMaterialPoint,
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
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

_LATEST_INVENTORY_SNAPSHOT_CONCURRENCY = 4


@dataclass(frozen=True, slots=True)
class LatestInventorySnapshot:
    governors: tuple[RegisteredGovernor, ...]
    resources: tuple[InventoryResourcePoint, ...] = ()
    speedups: tuple[InventorySpeedupPoint, ...] = ()
    materials: tuple[InventoryMaterialPoint, ...] = ()


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
        raise ValueError("Inventory view must be Resources, Speedups, Materials, or All.") from exc


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


async def resolve_self_service_governor_for_report(
    *,
    discord_user_id: int,
    governor_id: int,
) -> RegisteredGovernor:
    """Resolve a report governor without the legacy administrator override."""
    governors = await get_registered_governors_for_user(int(discord_user_id))
    selected = next(
        (item for item in governors if int(item.governor_id) == int(governor_id)),
        None,
    )
    if selected is None:
        raise PermissionError("You can only view inventory for governors registered to you.")
    return selected


async def build_self_service_inventory_report_payload(
    *,
    discord_user_id: int,
    governor_id: int,
    view: InventoryReportView,
    range_key: InventoryReportRange,
) -> InventoryReportPayload:
    """Recheck self-service access and assemble one existing report payload."""
    governor = await resolve_self_service_governor_for_report(
        discord_user_id=int(discord_user_id),
        governor_id=int(governor_id),
    )
    return await build_inventory_report_payload(
        discord_user_id=int(discord_user_id),
        governor=governor,
        view=view,
        range_key=range_key,
    )


async def build_latest_inventory_snapshot(
    governors: list[RegisteredGovernor] | tuple[RegisteredGovernor, ...],
) -> LatestInventorySnapshot:
    governor_tuple = tuple(governors)
    resource_points: list[InventoryResourcePoint] = []
    speedup_points: list[InventorySpeedupPoint] = []
    material_points: list[InventoryMaterialPoint] = []
    if not governor_tuple:
        return LatestInventorySnapshot(governors=())

    semaphore = asyncio.Semaphore(min(_LATEST_INVENTORY_SNAPSHOT_CONCURRENCY, len(governor_tuple)))
    results = await asyncio.gather(
        *(
            _build_latest_inventory_points_for_governor(governor, semaphore)
            for governor in governor_tuple
        )
    )

    for resource_point, speedup_point, material_point in results:
        if resource_point is not None:
            resource_points.append(resource_point)
        if speedup_point is not None:
            speedup_points.append(speedup_point)
        if material_point is not None:
            material_points.append(material_point)

    return LatestInventorySnapshot(
        governors=governor_tuple,
        resources=tuple(resource_points),
        speedups=tuple(speedup_points),
        materials=tuple(material_points),
    )


async def build_latest_resource_points_by_governor(
    governor_ids: list[int] | tuple[int, ...],
) -> dict[int, InventoryResourcePoint]:
    """Return canonical current-RSS points via one bulk DAL read for the requested governors."""
    ids = tuple(dict.fromkeys(int(value) for value in governor_ids if int(value) > 0))
    if not ids:
        return {}
    rows = await asyncio.to_thread(
        inventory_reporting_dal.fetch_latest_resource_rows_bulk,
        ids,
    )
    rows_by_governor: dict[int, list[dict[str, Any]]] = {governor_id: [] for governor_id in ids}
    for row in rows:
        try:
            governor_id = int(row.get("GovernorID"))
        except (TypeError, ValueError):
            continue
        if governor_id in rows_by_governor:
            rows_by_governor[governor_id].append(row)

    points: dict[int, InventoryResourcePoint] = {}
    for governor_id, governor_rows in rows_by_governor.items():
        grouped = _group_resource_points(governor_rows)
        if grouped:
            points[governor_id] = grouped[-1]
    return points


async def _build_latest_inventory_points_for_governor(
    governor: RegisteredGovernor,
    semaphore: asyncio.Semaphore,
) -> tuple[
    InventoryResourcePoint | None, InventorySpeedupPoint | None, InventoryMaterialPoint | None
]:
    async with semaphore:
        resource_rows, speedup_rows, material_rows = await asyncio.gather(
            asyncio.to_thread(
                inventory_reporting_dal.fetch_latest_resource_rows,
                int(governor.governor_id),
            ),
            asyncio.to_thread(
                inventory_reporting_dal.fetch_latest_speedup_rows,
                int(governor.governor_id),
            ),
            asyncio.to_thread(
                inventory_material_dal.fetch_latest_material_rows,
                int(governor.governor_id),
            ),
        )

    grouped_resources = _group_resource_points(resource_rows)
    grouped_speedups = _group_speedup_points(speedup_rows)
    grouped_materials = _group_material_points(material_rows)
    return (
        grouped_resources[-1] if grouped_resources else None,
        grouped_speedups[-1] if grouped_speedups else None,
        grouped_materials[-1] if grouped_materials else None,
    )


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


def _group_material_points(rows: list[dict[str, Any]]) -> list[InventoryMaterialPoint]:
    grouped: dict[Any, dict[str, Any]] = {}
    for row in rows:
        scan = row.get("ScanUtc")
        bucket = grouped.setdefault(scan, empty_material_values())
        kind = str(row.get("MaterialKind") or "").lower()
        rarity = str(row.get("Rarity") or "").lower()
        if kind in bucket and rarity in bucket[kind]:
            bucket[kind][rarity] = int(row.get("Quantity") or 0)

    points: list[InventoryMaterialPoint] = []
    for scan, values in grouped.items():
        totals = material_totals(values)
        points.append(
            InventoryMaterialPoint(
                scan_utc=scan,
                animal_bone_legendary=totals["animal_bone"],
                leather_legendary=totals["leather"],
                ebony_legendary=totals["ebony"],
                iron_ore_legendary=totals["iron_ore"],
                choice_chest_legendary=choice_chest_total(values),
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
    return filtered


async def build_inventory_report_payload(
    *,
    discord_user_id: int,
    governor: RegisteredGovernor,
    view: InventoryReportView,
    range_key: InventoryReportRange,
) -> InventoryReportPayload:
    resources: list[InventoryResourcePoint] = []
    speedups: list[InventorySpeedupPoint] = []
    materials: list[InventoryMaterialPoint] = []
    governor_profile = await profile_service.fetch_inventory_profile(int(governor.governor_id))

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

    if view in {InventoryReportView.MATERIALS, InventoryReportView.ALL}:
        material_rows = await asyncio.to_thread(
            inventory_material_dal.fetch_material_rows,
            int(governor.governor_id),
        )
        materials = _filter_points_for_range(_group_material_points(material_rows), range_key)

    logger.info(
        "inventory_report_payload_built user_id=%s governor_id=%s view=%s range=%s resources=%s speedups=%s materials=%s",
        discord_user_id,
        governor.governor_id,
        view.value,
        range_key.value,
        len(resources),
        len(speedups),
        len(materials),
    )
    return InventoryReportPayload(
        governor_id=int(governor.governor_id),
        governor_name=governor.governor_name,
        view=view,
        range_key=range_key,
        governor_profile=governor_profile,
        resources=resources,
        speedups=speedups,
        materials=materials,
        generated_at_utc=datetime.now(UTC),
    )
