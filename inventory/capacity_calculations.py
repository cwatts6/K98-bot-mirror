from __future__ import annotations

from dataclasses import dataclass

from inventory.models import InventoryResourcePoint, InventorySpeedupPoint
from inventory.vip_levels import InventoryVipLevel, normalize_vip_level, vip_note


@dataclass(frozen=True)
class ResourceCapacity:
    troops_millions: float
    limiting_resource: str
    power_millions: float
    mge_points_millions: float
    kills_millions: float | None = None
    kill_points_millions: float | None = None
    vip_note: str = ""


@dataclass(frozen=True)
class SpeedupCapacity:
    source_days: float
    troops: float | None = None
    power_millions: float | None = None
    mge_points_millions: float | None = None
    healed_millions: float | None = None
    kills_millions: float | None = None
    kill_points_millions: float | None = None
    vip_note: str = ""


TRAINING_RESOURCE_COSTS = {
    "food": 533_000_000,
    "wood": 533_000_000,
    "stone": 400_000_000,
    "gold": 400_000_000,
}

HEALING_RESOURCE_COSTS_DEFAULT = {
    "food": 213_300_000,
    "wood": 213_300_000,
    "stone": 160_000_000,
    "gold": 160_000_000,
}

HEALING_RESOURCE_COSTS_VIP_16_17 = {
    "food": 192_000_000,
    "wood": 192_000_000,
    "stone": 144_000_000,
    "gold": 144_000_000,
}

HEALING_RESOURCE_COSTS_VIP_18_PLUS = {
    "food": 181_300_000,
    "wood": 181_300_000,
    "stone": 136_000_000,
    "gold": 136_000_000,
}


def _capacity_from_costs(
    point: InventoryResourcePoint, costs: dict[str, int]
) -> tuple[float, str]:
    capacities = {
        "Food": point.food / costs["food"],
        "Wood": point.wood / costs["wood"],
        "Stone": point.stone / costs["stone"],
        "Gold": point.gold / costs["gold"],
    }
    limiting = min(capacities, key=capacities.get)
    return int(capacities[limiting] * 10) / 10, limiting


def rss_training_capacity(point: InventoryResourcePoint) -> ResourceCapacity:
    troops_m, limiting = _capacity_from_costs(point, TRAINING_RESOURCE_COSTS)
    return ResourceCapacity(
        troops_millions=troops_m,
        limiting_resource=limiting,
        power_millions=troops_m * 10,
        mge_points_millions=troops_m * 100,
    )


def _healing_resource_costs(vip_level: str | InventoryVipLevel | None) -> dict[str, int]:
    level = normalize_vip_level(vip_level)
    if level in {InventoryVipLevel.VIP_16, InventoryVipLevel.VIP_17}:
        return HEALING_RESOURCE_COSTS_VIP_16_17
    if level in {
        InventoryVipLevel.VIP_18,
        InventoryVipLevel.VIP_19,
        InventoryVipLevel.SVIP,
    }:
        return HEALING_RESOURCE_COSTS_VIP_18_PLUS
    return HEALING_RESOURCE_COSTS_DEFAULT


def rss_healing_capacity(
    point: InventoryResourcePoint, vip_level: str | InventoryVipLevel | None
) -> ResourceCapacity:
    troops_m, limiting = _capacity_from_costs(point, _healing_resource_costs(vip_level))
    return ResourceCapacity(
        troops_millions=troops_m,
        limiting_resource=limiting,
        kills_millions=troops_m * 5,
        kill_points_millions=troops_m * 20,
        power_millions=0,
        mge_points_millions=0,
        vip_note=vip_note(vip_level),
    )


def _speedup_training_baseline(
    vip_level: str | InventoryVipLevel | None,
) -> tuple[int, float, float]:
    level = normalize_vip_level(vip_level)
    if level == InventoryVipLevel.VIP_15:
        return 136_000, 1.36, 13.6
    if level in {InventoryVipLevel.VIP_16, InventoryVipLevel.VIP_17}:
        return 140_000, 1.4, 14.0
    if level in {
        InventoryVipLevel.VIP_18,
        InventoryVipLevel.VIP_19,
        InventoryVipLevel.SVIP,
    }:
        return 144_000, 1.44, 14.4
    return 133_000, 1.33, 13.3


def speedup_training_capacity(
    point: InventorySpeedupPoint, vip_level: str | InventoryVipLevel | None
) -> SpeedupCapacity:
    source_days = float(point.training_days) + float(point.universal_days)
    scale = source_days / 100
    troops, power_m, mge_m = _speedup_training_baseline(vip_level)
    return SpeedupCapacity(
        source_days=source_days,
        troops=scale * troops,
        power_millions=scale * power_m,
        mge_points_millions=scale * mge_m,
        vip_note=vip_note(vip_level),
    )


def _speedup_healing_baseline(vip_level: str | InventoryVipLevel | None) -> tuple[float, float]:
    level = normalize_vip_level(vip_level)
    if level in {InventoryVipLevel.VIP_15, InventoryVipLevel.VIP_16}:
        return 5.6, 112
    if level in {
        InventoryVipLevel.VIP_17,
        InventoryVipLevel.VIP_18,
        InventoryVipLevel.VIP_19,
        InventoryVipLevel.SVIP,
    }:
        return 5.7, 114
    return 4.1, 82


def speedup_healing_capacity(
    point: InventorySpeedupPoint, vip_level: str | InventoryVipLevel | None
) -> SpeedupCapacity:
    source_days = float(point.healing_days) + float(point.universal_days)
    scale = source_days / 100
    healed_m, kp_m = _speedup_healing_baseline(vip_level)
    return SpeedupCapacity(
        source_days=source_days,
        healed_millions=scale * healed_m,
        kills_millions=scale * healed_m,
        kill_points_millions=scale * kp_m,
        vip_note=vip_note(vip_level),
    )
