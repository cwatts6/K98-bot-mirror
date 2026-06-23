from datetime import UTC, datetime, timedelta
import logging
import types

import pytest

from inventory import reporting_service
from inventory.models import (
    InventoryGovernorProfile,
    InventoryReportRange,
    InventoryReportView,
    InventoryReportVisibility,
    RegisteredGovernor,
)


def test_parse_report_inputs_accept_expected_values():
    assert reporting_service.parse_report_view("Resources") == InventoryReportView.RESOURCES
    assert reporting_service.parse_report_view("All") == InventoryReportView.ALL
    assert reporting_service.parse_report_range("3M") == InventoryReportRange.THREE_MONTHS
    assert reporting_service.parse_visibility("Only Me") == InventoryReportVisibility.ONLY_ME
    assert (
        reporting_service.parse_visibility("Public Output Channel")
        == InventoryReportVisibility.PUBLIC
    )


@pytest.mark.asyncio
async def test_resolve_visibility_persists_selected_preference(monkeypatch):
    calls = []

    def _upsert(user_id, visibility):
        calls.append((user_id, visibility))

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "upsert_visibility_preference",
        _upsert,
    )

    visibility = await reporting_service.resolve_visibility(
        discord_user_id=123,
        selected_visibility=InventoryReportVisibility.PUBLIC,
    )

    assert visibility == InventoryReportVisibility.PUBLIC
    assert calls == [(123, InventoryReportVisibility.PUBLIC)]


@pytest.mark.asyncio
async def test_resolve_visibility_defaults_private_when_preference_read_fails(monkeypatch):
    def _fetch(_user_id):
        raise RuntimeError("table missing")

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_visibility_preference",
        _fetch,
    )

    visibility = await reporting_service.resolve_visibility(
        discord_user_id=123,
        selected_visibility=None,
    )

    assert visibility == InventoryReportVisibility.ONLY_ME


@pytest.mark.asyncio
async def test_read_visibility_preference_reports_failure_without_defaulting(monkeypatch, caplog):
    def _fetch(_user_id):
        raise RuntimeError("table missing")

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "fetch_visibility_preference",
        _fetch,
    )

    caplog.set_level(logging.ERROR)
    result = await reporting_service.read_visibility_preference(123)

    assert result.ok is False
    assert result.visibility is None
    assert "RuntimeError" in (result.error or "")
    assert "inventory_report_visibility_pref_read_failed user_id=123" in caplog.text
    assert "defaulting" not in caplog.text


@pytest.mark.asyncio
async def test_resolve_visibility_falls_back_to_private_when_write_fails(monkeypatch):
    def _upsert(_user_id, _visibility):
        raise RuntimeError("db error")

    monkeypatch.setattr(
        reporting_service.inventory_reporting_dal,
        "upsert_visibility_preference",
        _upsert,
    )

    visibility = await reporting_service.resolve_visibility(
        discord_user_id=123,
        selected_visibility=InventoryReportVisibility.PUBLIC,
    )

    assert visibility == InventoryReportVisibility.ONLY_ME


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
