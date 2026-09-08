from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

MATERIAL_KINDS = ("choice_chests", "animal_bone", "leather", "ebony", "iron_ore")
FIXED_MATERIAL_KINDS = ("animal_bone", "leather", "ebony", "iron_ore")
MATERIAL_RARITIES = ("normal", "advanced", "elite", "epic", "legendary")
RARITY_LEGENDARY_DIVISORS = {
    "normal": 256,
    "advanced": 64,
    "elite": 16,
    "epic": 4,
    "legendary": 1,
}

_KIND_ALIASES = {
    "choice_chest": "choice_chests",
    "choice_chests": "choice_chests",
    "choice chest": "choice_chests",
    "choice chests": "choice_chests",
    "equipment_material_choice_chest": "choice_chests",
    "equipment materials chest": "choice_chests",
    "animal_bone": "animal_bone",
    "animal bone": "animal_bone",
    "bone": "animal_bone",
    "leather": "leather",
    "ebony": "ebony",
    "iron": "iron_ore",
    "iron_ore": "iron_ore",
    "iron ore": "iron_ore",
}

_RARITY_ALIASES = {
    "normal": "normal",
    "grey": "normal",
    "gray": "normal",
    "advanced": "advanced",
    "green": "advanced",
    "elite": "elite",
    "blue": "elite",
    "epic": "epic",
    "purple": "epic",
    "legendary": "legendary",
    "orange": "legendary",
}


@dataclass(frozen=True)
class MaterialMergeResult:
    values: dict[str, dict[str, int]]
    warnings: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    @property
    def can_approve(self) -> bool:
        return not self.conflicts and any(
            quantity > 0 for rarities in self.values.values() for quantity in rarities.values()
        )


def normalize_material_kind(value: Any) -> str:
    key = str(value or "").strip().lower().replace("-", "_")
    key = " ".join(key.replace("_", " ").split())
    normalized = _KIND_ALIASES.get(key) or _KIND_ALIASES.get(key.replace(" ", "_"))
    if normalized not in MATERIAL_KINDS:
        raise ValueError(f"Unknown material kind: {value!r}.")
    return normalized


def normalize_material_rarity(value: Any) -> str:
    key = str(value or "").strip().lower().replace("-", "_")
    key = " ".join(key.replace("_", " ").split())
    normalized = _RARITY_ALIASES.get(key) or _RARITY_ALIASES.get(key.replace(" ", "_"))
    if normalized not in MATERIAL_RARITIES:
        raise ValueError(f"Unknown material rarity: {value!r}.")
    return normalized


def parse_material_quantity(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid material quantities.")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Negative material quantities are not allowed.")
        return value
    if isinstance(value, float):
        if value < 0 or not value.is_integer():
            raise ValueError("Material quantities must be whole non-negative numbers.")
        return int(value)
    text = str(value).replace(",", "").strip()
    if text == "":
        return 0
    if not text.isdigit():
        raise ValueError(f"Invalid material quantity: {value!r}.")
    return int(text)


def empty_material_values() -> dict[str, dict[str, int]]:
    return {kind: {rarity: 0 for rarity in MATERIAL_RARITIES} for kind in MATERIAL_KINDS}


def legendary_equivalent(quantity: Any, rarity: Any) -> float:
    normalized_rarity = normalize_material_rarity(rarity)
    parsed = parse_material_quantity(quantity)
    return parsed / RARITY_LEGENDARY_DIVISORS[normalized_rarity]


def row_legendary_equivalent(rarities: dict[str, Any]) -> float:
    total = 0.0
    for rarity in MATERIAL_RARITIES:
        total += legendary_equivalent(rarities.get(rarity), rarity)
    return total


def normalize_material_values(values: dict[str, Any]) -> dict[str, dict[str, int]]:
    materials = values.get("materials") if isinstance(values, dict) else None
    if not isinstance(materials, dict):
        raise ValueError("Missing materials section.")

    normalized = empty_material_values()
    for raw_kind, raw_row in materials.items():
        if raw_kind in {"material_screen_type", "unreadable_items", "duplicate_candidates"}:
            continue
        kind = normalize_material_kind(raw_kind)
        if not isinstance(raw_row, dict):
            raise ValueError(f"Missing material row: {kind}.")
        for rarity in MATERIAL_RARITIES:
            normalized[kind][rarity] = parse_material_quantity(raw_row.get(rarity))
    return normalized


def material_totals(values: dict[str, dict[str, int]]) -> dict[str, float]:
    return {kind: row_legendary_equivalent(row) for kind, row in values.items()}


def fixed_material_total(values: dict[str, dict[str, int]]) -> float:
    totals = material_totals(values)
    return sum(totals[kind] for kind in FIXED_MATERIAL_KINDS)


def choice_chest_total(values: dict[str, dict[str, int]]) -> float:
    return material_totals(values)["choice_chests"]


def total_legendary_equivalent(values: dict[str, dict[str, int]]) -> float:
    return fixed_material_total(values) + choice_chest_total(values)


def merge_material_value_sets(
    value_sets: Iterable[dict[str, dict[str, int]]],
) -> MaterialMergeResult:
    merged = empty_material_values()
    warnings: list[str] = []
    conflicts: list[str] = []
    seen: dict[tuple[str, str], int] = {}

    for values in value_sets:
        for raw_kind, rarities in values.items():
            kind = normalize_material_kind(raw_kind)
            for raw_rarity, raw_quantity in rarities.items():
                rarity = normalize_material_rarity(raw_rarity)
                quantity = parse_material_quantity(raw_quantity)
                if quantity <= 0:
                    continue
                key = (kind, rarity)
                if key in seen:
                    previous = seen[key]
                    label = f"{kind}/{rarity}"
                    if previous == quantity:
                        warnings.append(f"Duplicate {label} value detected; kept {quantity:,}.")
                    else:
                        conflicts.append(
                            f"Conflicting {label} values detected; kept {previous:,} and ignored {quantity:,}."
                        )
                    continue
                seen[key] = quantity
                merged[kind][rarity] = quantity

    return MaterialMergeResult(
        values=merged,
        warnings=list(dict.fromkeys(warnings)),
        conflicts=list(dict.fromkeys(conflicts)),
    )
