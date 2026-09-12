from __future__ import annotations

import asyncio
import csv
from datetime import UTC, datetime
import logging
from pathlib import Path
import tempfile
from typing import Any

from inventory.dal import inventory_export_dal, inventory_material_dal
from inventory.inventory_service import user_can_import_for_governor
from inventory.models import InventoryExportFile, InventoryExportFormat, InventoryReportView

logger = logging.getLogger(__name__)

EXPORT_COLUMNS = [
    "RecordKind",
    "ImportBatchID",
    "GovernorID",
    "VipLevelCode",
    "VipLevelLabel",
    "DiscordUserID",
    "FlowType",
    "ApprovedAtUtc",
    "ScanUtc",
    "ItemType",
    "FromItemsValue",
    "TotalResourcesValue",
    "TotalMinutes",
    "TotalHours",
    "TotalDaysDecimal",
    "MaterialKind",
    "Rarity",
    "Quantity",
    "LegendaryEquivalent",
    "SourceImageIndex",
]


async def resolve_export_governor_ids(
    *,
    discord_user_id: int,
    governor_id: int,
) -> list[int]:
    if not await user_can_import_for_governor(
        discord_user_id=int(discord_user_id),
        governor_id=int(governor_id),
        is_admin=False,
    ):
        raise PermissionError("You can only export inventory for governors registered to you.")
    return [int(governor_id)]


def _dt(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _resource_export_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "RecordKind": "resource",
            "ImportBatchID": row.get("ImportBatchID"),
            "GovernorID": row.get("GovernorID"),
            "VipLevelCode": row.get("VipLevelCode") or "",
            "VipLevelLabel": row.get("VipLevelLabel") or "",
            "DiscordUserID": row.get("DiscordUserID"),
            "FlowType": row.get("FlowType"),
            "ApprovedAtUtc": _dt(row.get("ApprovedAtUtc")),
            "ScanUtc": _dt(row.get("ScanUtc")),
            "ItemType": row.get("ResourceType"),
            "FromItemsValue": row.get("FromItemsValue"),
            "TotalResourcesValue": row.get("TotalResourcesValue"),
            "TotalMinutes": "",
            "TotalHours": "",
            "TotalDaysDecimal": "",
            "MaterialKind": "",
            "Rarity": "",
            "Quantity": "",
            "LegendaryEquivalent": "",
            "SourceImageIndex": "",
        }
        for row in rows
    ]


def _speedup_export_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "RecordKind": "speedup",
            "ImportBatchID": row.get("ImportBatchID"),
            "GovernorID": row.get("GovernorID"),
            "VipLevelCode": row.get("VipLevelCode") or "",
            "VipLevelLabel": row.get("VipLevelLabel") or "",
            "DiscordUserID": row.get("DiscordUserID"),
            "FlowType": row.get("FlowType"),
            "ApprovedAtUtc": _dt(row.get("ApprovedAtUtc")),
            "ScanUtc": _dt(row.get("ScanUtc")),
            "ItemType": row.get("SpeedupType"),
            "FromItemsValue": "",
            "TotalResourcesValue": "",
            "TotalMinutes": row.get("TotalMinutes"),
            "TotalHours": row.get("TotalHours"),
            "TotalDaysDecimal": row.get("TotalDaysDecimal"),
            "MaterialKind": "",
            "Rarity": "",
            "Quantity": "",
            "LegendaryEquivalent": "",
            "SourceImageIndex": "",
        }
        for row in rows
    ]


def _material_export_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "RecordKind": "material",
            "ImportBatchID": row.get("ImportBatchID"),
            "GovernorID": row.get("GovernorID"),
            "VipLevelCode": row.get("VipLevelCode") or "",
            "VipLevelLabel": row.get("VipLevelLabel") or "",
            "DiscordUserID": row.get("DiscordUserID"),
            "FlowType": row.get("FlowType"),
            "ApprovedAtUtc": _dt(row.get("ApprovedAtUtc")),
            "ScanUtc": _dt(row.get("ScanUtc")),
            "ItemType": row.get("MaterialKind"),
            "FromItemsValue": "",
            "TotalResourcesValue": "",
            "TotalMinutes": "",
            "TotalHours": "",
            "TotalDaysDecimal": "",
            "MaterialKind": row.get("MaterialKind"),
            "Rarity": row.get("Rarity"),
            "Quantity": row.get("Quantity"),
            "LegendaryEquivalent": row.get("LegendaryEquivalent"),
            "SourceImageIndex": row.get("SourceImageIndex") or "",
        }
        for row in rows
    ]


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_xlsx(rows: list[dict[str, Any]], path: Path) -> None:
    import pandas as pd

    df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(
            {
                "Info": [
                    "Inventory Export",
                    "Approved Resources, Speedups, and Materials only.",
                    "Image/debug references are available through admin audit where retained.",
                ]
            }
        ).to_excel(writer, index=False, sheet_name="README")
        df.to_excel(writer, index=False, sheet_name="RAW_INVENTORY")


async def build_inventory_export_file(
    *,
    discord_user_id: int,
    username: str,
    export_format: InventoryExportFormat,
    view: InventoryReportView,
    governor_id: int,
    lookback_days: int = 366,
) -> InventoryExportFile:
    governor_ids = await resolve_export_governor_ids(
        discord_user_id=int(discord_user_id),
        governor_id=governor_id,
    )

    resources: list[dict[str, Any]] = []
    speedups: list[dict[str, Any]] = []
    materials: list[dict[str, Any]] = []
    if view == InventoryReportView.RESOURCES:
        resources = await asyncio.to_thread(
            inventory_export_dal.fetch_resource_export_rows,
            governor_ids,
            lookback_days=lookback_days,
        )
    elif view == InventoryReportView.SPEEDUPS:
        speedups = await asyncio.to_thread(
            inventory_export_dal.fetch_speedup_export_rows,
            governor_ids,
            lookback_days=lookback_days,
        )
    elif view == InventoryReportView.MATERIALS:
        materials = await asyncio.to_thread(
            inventory_material_dal.fetch_material_export_rows,
            governor_ids,
            lookback_days=lookback_days,
        )

    export_rows = (
        _resource_export_rows(resources)
        + _speedup_export_rows(speedups)
        + _material_export_rows(materials)
    )
    if not export_rows:
        raise ValueError("No approved inventory records found for the selected export.")

    safe_username = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in username)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    suffix = ".csv" if export_format == InventoryExportFormat.CSV else ".xlsx"
    temp_dir = Path(tempfile.mkdtemp(prefix="inventory_export_"))
    path = temp_dir / f"inventory_{safe_username}_{timestamp}{suffix}"

    if export_format == InventoryExportFormat.CSV:
        await asyncio.to_thread(_write_csv, export_rows, path)
    else:
        await asyncio.to_thread(_write_xlsx, export_rows, path)

    logger.info(
        "inventory_export_built user_id=%s governors=%s format=%s rows=%s",
        discord_user_id,
        governor_ids,
        export_format.value,
        len(export_rows),
    )
    return InventoryExportFile(
        path=path,
        filename=path.name,
        format=export_format,
        row_count=len(export_rows),
        governor_ids=tuple(governor_ids),
    )


def cleanup_export_file(export_file: InventoryExportFile | None) -> None:
    if export_file is None:
        return
    try:
        export_file.path.unlink(missing_ok=True)
    except Exception:
        logger.warning("inventory_export_file_cleanup_failed path=%s", export_file.path)
    try:
        export_file.path.parent.rmdir()
    except Exception:
        logger.debug("inventory_export_dir_cleanup_skipped path=%s", export_file.path.parent)
