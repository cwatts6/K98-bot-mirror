from datetime import UTC, datetime

import pytest

from inventory.capacity_calculations import (
    rss_healing_capacity,
    rss_training_capacity,
    speedup_healing_capacity,
    speedup_training_capacity,
)
from inventory.models import InventoryResourcePoint, InventorySpeedupPoint
from inventory.vip_levels import InventoryVipLevel


def _resource_point() -> InventoryResourcePoint:
    return InventoryResourcePoint(
        scan_utc=datetime.now(UTC),
        food=1_066_000_000,
        wood=1_066_000_000,
        stone=800_000_000,
        gold=800_000_000,
    )


def _speedup_point() -> InventorySpeedupPoint:
    return InventorySpeedupPoint(
        scan_utc=datetime.now(UTC),
        building_days=0,
        research_days=0,
        training_days=80,
        healing_days=70,
        universal_days=20,
    )


def test_rss_training_capacity_does_not_change_by_vip():
    point = _resource_point()

    default = rss_training_capacity(point)
    vip19 = rss_training_capacity(point)

    assert default.troops_millions == 2.0
    assert vip19 == default


def test_rss_healing_capacity_defaults_to_vip_15_or_less_when_unknown():
    capacity = rss_healing_capacity(_resource_point(), None)

    assert capacity.troops_millions == 4.9
    assert capacity.limiting_resource == "Food"
    assert capacity.vip_note == "VIP: default"


def test_rss_healing_capacity_uses_vip_16_17_costs():
    capacity = rss_healing_capacity(_resource_point(), InventoryVipLevel.VIP_17)

    assert capacity.troops_millions == 5.5
    assert capacity.vip_note == "VIP: 17"


def test_rss_healing_capacity_uses_vip_18_plus_costs():
    capacity = rss_healing_capacity(_resource_point(), InventoryVipLevel.SVIP)

    assert capacity.troops_millions == 5.8
    assert capacity.vip_note == "VIP: SVIP"


def test_speedup_training_capacity_defaults_to_vip_14_or_less():
    capacity = speedup_training_capacity(_speedup_point(), None)

    assert capacity.source_days == 100
    assert capacity.troops == 133_000
    assert capacity.power_millions == 1.33
    assert capacity.mge_points_millions == 13.3


def test_speedup_training_capacity_uses_vip_15_baseline():
    capacity = speedup_training_capacity(_speedup_point(), InventoryVipLevel.VIP_15)

    assert capacity.troops == 136_000
    assert capacity.power_millions == 1.36
    assert capacity.mge_points_millions == 13.6


def test_speedup_training_capacity_uses_vip_16_17_baseline():
    capacity = speedup_training_capacity(_speedup_point(), InventoryVipLevel.VIP_16)

    assert capacity.troops == 140_000
    assert capacity.power_millions == 1.4
    assert capacity.mge_points_millions == 14.0


def test_speedup_training_capacity_uses_vip_18_plus_baseline():
    capacity = speedup_training_capacity(_speedup_point(), InventoryVipLevel.VIP_18)

    assert capacity.troops == 144_000
    assert capacity.power_millions == 1.44
    assert capacity.mge_points_millions == 14.4


def test_speedup_healing_capacity_defaults_to_vip_14_or_less():
    capacity = speedup_healing_capacity(_speedup_point(), None)

    assert capacity.source_days == 90
    assert capacity.healed_millions == 3.69
    assert capacity.kills_millions == 3.69
    assert capacity.kill_points_millions == 73.8


def test_speedup_healing_capacity_uses_vip_15_16_baseline():
    capacity = speedup_healing_capacity(_speedup_point(), InventoryVipLevel.VIP_16)

    assert capacity.healed_millions == 5.04
    assert capacity.kills_millions == 5.04
    assert capacity.kill_points_millions == 100.8


def test_speedup_healing_capacity_uses_vip_17_plus_baseline():
    capacity = speedup_healing_capacity(_speedup_point(), InventoryVipLevel.VIP_19)

    assert capacity.healed_millions == 5.13
    assert capacity.kills_millions == 5.13
    assert capacity.kill_points_millions == pytest.approx(102.6)
