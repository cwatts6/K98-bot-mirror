from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import logging
from typing import Any

from inventory.dal import inventory_material_dal
from inventory.material_calculations import (
    MATERIAL_KINDS,
    MATERIAL_RARITIES,
    MaterialMergeResult,
    choice_chest_total,
    fixed_material_total,
    material_totals,
    merge_material_value_sets,
    normalize_material_values,
    parse_material_quantity,
    total_legendary_equivalent,
)
from inventory.models import InventoryAnalysisSummary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MaterialReviewSummary:
    values: dict[str, dict[str, int]]
    warnings: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    screenshot_count: int = 1

    @property
    def can_approve(self) -> bool:
        return not self.conflicts and any(
            quantity > 0 for rarities in self.values.values() for quantity in rarities.values()
        )


def normalize_summary_materials(summary: InventoryAnalysisSummary) -> dict[str, dict[str, int]]:
    return normalize_material_values(summary.values)


def build_material_review_from_summaries(
    summaries: list[InventoryAnalysisSummary],
) -> MaterialReviewSummary:
    normalized_sets = [normalize_summary_materials(summary) for summary in summaries]
    merged: MaterialMergeResult = merge_material_value_sets(normalized_sets)
    warnings = []
    for summary in summaries:
        warnings.extend(summary.warnings)
    warnings.extend(merged.warnings)
    return MaterialReviewSummary(
        values=merged.values,
        warnings=list(dict.fromkeys(item for item in warnings if item)),
        conflicts=merged.conflicts,
        screenshot_count=sum(_summary_screenshot_count(summary) for summary in summaries),
    )


def _summary_screenshot_count(summary: InventoryAnalysisSummary) -> int:
    raw_json = summary.raw_json if isinstance(summary.raw_json, dict) else {}
    try:
        return max(1, int(raw_json.get("screenshot_count") or 1))
    except (TypeError, ValueError):
        return 1


def apply_material_corrections(
    values: dict[str, Any], material_kind: str, corrections: dict[str, Any]
) -> dict[str, Any]:
    normalized = normalize_material_values({"materials": values.get("materials", values)})
    kind = material_kind
    from inventory.material_calculations import normalize_material_kind

    kind = normalize_material_kind(kind)
    for rarity in MATERIAL_RARITIES:
        if rarity in corrections:
            normalized[kind][rarity] = parse_material_quantity(corrections[rarity])
    return {"materials": normalized}


def summarize_material_values(values: dict[str, dict[str, int]]) -> dict[str, float]:
    totals = material_totals(values)
    return {
        **totals,
        "fixed_total": fixed_material_total(values),
        "choice_chest_total": choice_chest_total(values),
        "total": total_legendary_equivalent(values),
    }


async def approve_material_import(
    *,
    import_batch_id: int,
    governor_id: int,
    values: dict[str, Any],
    corrected_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_material_values(values)
    if not any(quantity > 0 for rarities in normalized.values() for quantity in rarities.values()):
        raise ValueError("At least one material quantity is required before approval.")

    final_payload = {"materials": normalized}
    await asyncio.to_thread(
        inventory_material_dal.approve_material_batch,
        import_batch_id=int(import_batch_id),
        governor_id=int(governor_id),
        scan_utc=datetime.now(UTC),
        materials=normalized,
        corrected_json=(
            json.dumps(corrected_values, ensure_ascii=False, sort_keys=True)
            if corrected_values is not None
            else None
        ),
        final_json=json.dumps(final_payload, ensure_ascii=False, sort_keys=True),
    )
    logger.info(
        "inventory_material_import_approved batch_id=%s governor_id=%s total_legendary=%.4f",
        import_batch_id,
        governor_id,
        total_legendary_equivalent(normalized),
    )
    return final_payload


def format_material_review_lines(values: dict[str, dict[str, int]]) -> list[str]:
    totals = material_totals(values)
    labels = {
        "animal_bone": "Bone",
        "leather": "Leather",
        "ebony": "Ebony",
        "iron_ore": "Iron",
        "choice_chests": "Choice Chests",
    }
    lines = [f"{labels[kind]}: `{totals[kind]:,.2f}` legendary" for kind in MATERIAL_KINDS]
    lines.append(f"Total: `{total_legendary_equivalent(values):,.2f}` legendary")
    return lines
