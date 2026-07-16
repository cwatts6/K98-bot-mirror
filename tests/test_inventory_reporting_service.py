from datetime import UTC, datetime, timedelta
import threading
import time
import types

import pytest

from inventory import reporting_service
from inventory.models import (
    InventoryGovernorProfile,
    InventoryReportRange,
    InventoryReportView,
    RegisteredGovernor,
)


def test_parse_report_inputs_accept_expected_values():
    assert reporting_service.parse_report_view("Resources") == InventoryReportView.RESOURCES
    assert reporting_service.parse_report_view("All") == InventoryReportView.ALL
    assert reporting_service.parse_report_range("3M") == InventoryReportRange.THREE_MONTHS


@pytest.mark.asyncio
async def test_build_inventory_report_payload_groups_resources_and_speedups(monkeypatch):
    now = datetime.now(UTC)

    def _resource_rows(governor_id):
        assert governor_id == 111
        return [
            {
                "ScanUtc": now - timedelta(days=10),
                "ResourceType": "food",
                "TotalResourcesValue": 100,
            },
            {
                "ScanUtc": now - timedelta(days=10),
                "ResourceType": "wood",
                "TotalResourcesValue": 200,
            },
            {
                "ScanUtc": now - timedelta(days=10),
                "ResourceType": "stone",
                "TotalResourcesValue": 300,
            },
            {
                "ScanUtc": now - timedelta(days=10),
                "ResourceType": "gold",
                "TotalResourcesValue": 400,
            },
        ]

    def _speedup_rows(governor_id):
        assert governor_id == 111
        return [
            {"ScanUtc": now, "SpeedupType": "building", "TotalDaysDecimal": 1},
            {"ScanUtc": now, "SpeedupType": "research", "TotalDaysDecimal": 2},
            {"ScanUtc": now, "SpeedupType": "training", "TotalDaysDecimal": 3},
            {"ScanUtc": now, "SpeedupType": "healing", "TotalDaysDecimal": 4},
            {"ScanUtc": now, "SpeedupType": "universal", "TotalDaysDecimal": 5},
        ]

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_resource_rows",
        _resource_rows,
    )
    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_speedup_rows",
        _speedup_rows,
    )
    monkeypatch.setattr(
        reporting_service.inventory_material_dal,
        "fetch_material_rows",
        lambda _governor_id: [],
    )

    async def _profile(governor_id):
        return InventoryGovernorProfile.default(governor_id)

    monkeypatch.setattr(reporting_service.profile_service, "fetch_inventory_profile", _profile)

    payload = await reporting_service.build_inventory_report_payload(
        discord_user_id=42,
        governor=RegisteredGovernor(111, "Gov", "Main"),
        view=InventoryReportView.ALL,
        range_key=InventoryReportRange.ONE_MONTH,
    )

    assert payload.resources[0].total == 1000
    assert payload.speedups[0].training_days == 3
    assert payload.speedups[0].universal_days == 5
    assert payload.materials == []
    assert payload.governor_profile is not None
    assert payload.governor_profile.uses_default_vip is True


@pytest.mark.asyncio
async def test_build_latest_inventory_snapshot_groups_latest_rows(monkeypatch):
    now = datetime.now(UTC)

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_latest_resource_rows",
        lambda governor_id: [
            {"ScanUtc": now, "ResourceType": "food", "TotalResourcesValue": governor_id},
            {"ScanUtc": now, "ResourceType": "wood", "TotalResourcesValue": 2},
            {"ScanUtc": now, "ResourceType": "stone", "TotalResourcesValue": 3},
            {"ScanUtc": now, "ResourceType": "gold", "TotalResourcesValue": 4},
        ],
    )
    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_latest_speedup_rows",
        lambda _governor_id: [
            {"ScanUtc": now, "SpeedupType": "building", "TotalDaysDecimal": 1},
            {"ScanUtc": now, "SpeedupType": "research", "TotalDaysDecimal": 2},
            {"ScanUtc": now, "SpeedupType": "training", "TotalDaysDecimal": 3},
            {"ScanUtc": now, "SpeedupType": "healing", "TotalDaysDecimal": 4},
            {"ScanUtc": now, "SpeedupType": "universal", "TotalDaysDecimal": 5},
        ],
    )
    monkeypatch.setattr(
        reporting_service.inventory_material_dal,
        "fetch_latest_material_rows",
        lambda _governor_id: [],
    )

    snapshot = await reporting_service.build_latest_inventory_snapshot(
        [RegisteredGovernor(111, "Gov", "Main")]
    )

    assert snapshot.governors[0].governor_id == 111
    assert snapshot.resources[0].food == 111
    assert snapshot.speedups[0].universal_days == 5
    assert snapshot.materials == ()


@pytest.mark.asyncio
async def test_build_latest_resource_points_by_governor_reuses_canonical_grouping(monkeypatch):
    now = datetime.now(UTC)
    calls = []

    def bulk(ids):
        calls.append(ids)
        rows = []
        for governor_id in ids:
            for resource_type, value in (
                ("food", governor_id),
                ("wood", 2),
                ("stone", 3),
                ("gold", 4),
            ):
                rows.append(
                    {
                        "GovernorID": governor_id,
                        "ScanUtc": now,
                        "ResourceType": resource_type,
                        "TotalResourcesValue": value,
                    }
                )
        return rows

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_latest_resource_rows_bulk",
        bulk,
    )

    points = await reporting_service.build_latest_resource_points_by_governor((111, 222, 111))

    assert calls == [(111, 222)]
    assert points[111].total == 120
    assert points[222].total == 231


@pytest.mark.asyncio
async def test_build_latest_inventory_snapshot_fetches_governors_with_bounded_concurrency(
    monkeypatch,
):
    now = datetime.now(UTC)
    lock = threading.Lock()
    active_fetches_by_governor: dict[int, int] = {}
    max_active_governors = 0

    def _track_fetch(governor_id: int) -> None:
        nonlocal max_active_governors
        with lock:
            active_fetches_by_governor[governor_id] = (
                active_fetches_by_governor.get(governor_id, 0) + 1
            )
            max_active_governors = max(
                max_active_governors,
                len(active_fetches_by_governor),
            )
        time.sleep(0.05)
        with lock:
            remaining = active_fetches_by_governor[governor_id] - 1
            if remaining:
                active_fetches_by_governor[governor_id] = remaining
            else:
                del active_fetches_by_governor[governor_id]

    def _fetch_resource_rows(governor_id):
        _track_fetch(governor_id)
        return [
            {"ScanUtc": now, "ResourceType": "food", "TotalResourcesValue": governor_id},
            {"ScanUtc": now, "ResourceType": "wood", "TotalResourcesValue": 1},
            {"ScanUtc": now, "ResourceType": "stone", "TotalResourcesValue": 1},
            {"ScanUtc": now, "ResourceType": "gold", "TotalResourcesValue": 1},
        ]

    def _fetch_empty_rows(governor_id):
        _track_fetch(governor_id)
        return []

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_latest_resource_rows",
        _fetch_resource_rows,
    )
    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_latest_speedup_rows",
        _fetch_empty_rows,
    )
    monkeypatch.setattr(
        reporting_service.inventory_material_dal,
        "fetch_latest_material_rows",
        _fetch_empty_rows,
    )

    snapshot = await reporting_service.build_latest_inventory_snapshot(
        [
            RegisteredGovernor(governor_id, f"Gov {governor_id}", "Alt")
            for governor_id in range(101, 107)
        ]
    )

    assert len(snapshot.resources) == 6
    assert max_active_governors > 1
    assert max_active_governors <= reporting_service._LATEST_INVENTORY_SNAPSHOT_CONCURRENCY


@pytest.mark.asyncio
async def test_build_inventory_report_payload_includes_stored_vip(monkeypatch):
    now = datetime.now(UTC)

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_resource_rows",
        lambda _governor_id: [
            {"ScanUtc": now, "ResourceType": "food", "TotalResourcesValue": 100},
            {"ScanUtc": now, "ResourceType": "wood", "TotalResourcesValue": 100},
            {"ScanUtc": now, "ResourceType": "stone", "TotalResourcesValue": 100},
            {"ScanUtc": now, "ResourceType": "gold", "TotalResourcesValue": 100},
        ],
    )
    monkeypatch.setattr(
        reporting_service.inventory_material_dal,
        "fetch_material_rows",
        lambda _governor_id: [],
    )

    async def _profile(governor_id):
        return InventoryGovernorProfile(
            governor_id=governor_id,
            vip_level_code="VIP_18",
            vip_level_label="VIP 18",
        )

    monkeypatch.setattr(reporting_service.profile_service, "fetch_inventory_profile", _profile)

    payload = await reporting_service.build_inventory_report_payload(
        discord_user_id=42,
        governor=RegisteredGovernor(111, "Gov", "Main"),
        view=InventoryReportView.RESOURCES,
        range_key=InventoryReportRange.ONE_MONTH,
    )

    assert payload.governor_profile is not None
    assert payload.governor_profile.vip_level_code == "VIP_18"


@pytest.mark.asyncio
async def test_resolve_governor_for_report_rejects_unregistered_governor(monkeypatch):
    async def _can_import(**_kwargs):
        return False

    async def _governors(_uid):
        return []

    monkeypatch.setattr(reporting_service, "user_can_import_for_governor", _can_import)
    monkeypatch.setattr(reporting_service, "get_registered_governors_for_user", _governors)

    with pytest.raises(PermissionError):
        await reporting_service.resolve_governor_for_report(
            discord_user_id=42,
            governor_id=999,
            discord_user=types.SimpleNamespace(id=42),
        )


@pytest.mark.asyncio
async def test_self_service_report_payload_rechecks_governor_before_fetch(monkeypatch):
    governor = RegisteredGovernor(111, "Main Gov", "Main")
    calls = []

    async def governors(_user_id):
        calls.append("access")
        return [governor]

    async def payload(**kwargs):
        calls.append(("payload", kwargs))
        return object()

    monkeypatch.setattr(reporting_service, "get_registered_governors_for_user", governors)
    monkeypatch.setattr(reporting_service, "build_inventory_report_payload", payload)

    result = await reporting_service.build_self_service_inventory_report_payload(
        discord_user_id=42,
        governor_id=111,
        view=InventoryReportView.RESOURCES,
        range_key=InventoryReportRange.ONE_MONTH,
    )

    assert result is not None
    assert calls[0] == "access"
    assert calls[1][1]["governor"] == governor


@pytest.mark.asyncio
async def test_self_service_report_payload_denies_unlinked_before_fetch(monkeypatch):
    async def governors(_user_id):
        return [RegisteredGovernor(111, "Main Gov", "Main")]

    async def payload(**_kwargs):
        raise AssertionError("denied report must not fetch payload")

    monkeypatch.setattr(reporting_service, "get_registered_governors_for_user", governors)
    monkeypatch.setattr(reporting_service, "build_inventory_report_payload", payload)

    with pytest.raises(PermissionError):
        await reporting_service.build_self_service_inventory_report_payload(
            discord_user_id=42,
            governor_id=999,
            view=InventoryReportView.RESOURCES,
            range_key=InventoryReportRange.ONE_MONTH,
        )
