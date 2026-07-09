from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from player_self_service import governor_dashboard_dal as dal, governor_dashboard_service as service
from player_self_service.governor_dashboard_models import (
    GovernorDashboardContext,
    GovernorDashboardDataRow,
)
from scripts import validate_command_registration as command_validator
from services.governor_account_service import summarize_accounts


async def _account_loader(accounts, *, ok: bool = True, error: str | None = None):
    async def load(_discord_user_id: int):
        return summarize_accounts(accounts, ok=ok, error=error)

    return load


def _self_context(governor_id: int = 111) -> GovernorDashboardContext:
    return GovernorDashboardContext(
        viewer_discord_id=42,
        viewer_mode="self",
        selected_governor_id=governor_id,
        selected_governor_name="Linked Gov",
        is_linked_to_viewer=True,
        account_type_for_self_view="Main",
        access_decision=service.GovernorDashboardAccessDecision(
            allowed=True,
            reason="linked governor selected",
        ),
        privacy_profile="self_view",
    )


@pytest.mark.asyncio
async def test_governor_options_list_linked_accounts_in_slot_order() -> None:
    account_loader = await _account_loader(
        {
            "Alt 1": {"GovernorID": "222", "GovernorName": "Alt Gov"},
            "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
        }
    )

    options = await service.get_dashboard_governor_options(42, account_loader=account_loader)

    assert [option.account_type for option in options] == ["Main", "Alt 1"]
    assert [option.governor_id for option in options] == [111, 222]
    assert options[0].is_default is True


@pytest.mark.asyncio
async def test_resolve_dashboard_context_represents_no_one_and_multiple_states() -> None:
    no_accounts_loader = await _account_loader({})
    one_account_loader = await _account_loader(
        {"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}}
    )
    multiple_accounts_loader = await _account_loader(
        {
            "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
            "Alt 1": {"GovernorID": "222", "GovernorName": "Alt Gov"},
        }
    )

    no_accounts = await service.resolve_dashboard_context(
        42,
        account_loader=no_accounts_loader,
    )
    one_account = await service.resolve_dashboard_context(
        42,
        account_loader=one_account_loader,
    )
    multiple_accounts = await service.resolve_dashboard_context(
        42,
        account_loader=multiple_accounts_loader,
    )

    assert no_accounts.state == "requires_setup"
    assert no_accounts.options == ()
    assert one_account.state == "selected"
    assert one_account.context is not None
    assert one_account.context.selected_governor_id == 111
    assert multiple_accounts.state == "requires_selection"
    assert multiple_accounts.context is None
    assert multiple_accounts.default_option is not None
    assert multiple_accounts.default_option.governor_id == 111


@pytest.mark.asyncio
async def test_assert_dashboard_governor_access_denies_unlinked_self_service_governor() -> None:
    account_loader = await _account_loader(
        {"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}}
    )

    with pytest.raises(service.GovernorDashboardAccessDenied):
        await service.assert_dashboard_governor_access(
            42,
            999,
            account_loader=account_loader,
        )

    denied = await service.resolve_dashboard_context(
        42,
        999,
        account_loader=account_loader,
    )
    assert denied.state == "denied"
    assert denied.context is not None
    assert denied.context.access_allowed is False
    assert denied.context.is_linked_to_viewer is False


@pytest.mark.asyncio
async def test_payload_assembles_approved_fields_and_self_view_data() -> None:
    scan = datetime(2026, 7, 9, 12, 30, tzinfo=UTC)

    async def data_loader(_governor_id: int):
        return GovernorDashboardDataRow(
            governor_id=111,
            governor_name="SQL Gov",
            alliance="KD98",
            power=123456789,
            kill_points=987654321,
            dead=12345,
            helps=6789,
            healed=55555,
            highest_acclaim=88,
            ark_joined=10,
            ark_won=7,
            times_named_autarch=3,
            conduct=94.5,
            civilization="France",
            updated_at_utc=scan,
            scan_order=456,
        )

    async def vip_loader(_governor_id: int):
        return SimpleNamespace(vip_level_label="VIP 19")

    payload = await service.build_governor_dashboard_payload(
        _self_context(),
        data_loader=data_loader,
        vip_profile_loader=vip_loader,
    )

    assert payload.identity.governor_name == "SQL Gov"
    assert payload.identity.governor_id == 111
    assert payload.identity.alliance == "KD98"
    assert payload.identity.civilisation == "France"
    assert payload.latest_metrics.power == 123456789
    assert payload.latest_metrics.kill_points == 987654321
    assert payload.latest_metrics.dead == 12345
    assert payload.latest_metrics.helps == 6789
    assert payload.latest_metrics.healed == 55555
    assert payload.historical_highlights.highest_acclaim == 88
    assert payload.historical_highlights.times_named_autarch == 3
    assert payload.activity_honours.ark_joined == 10
    assert payload.activity_honours.ark_won == 7
    assert payload.activity_honours.ark_win_ratio == pytest.approx(0.7)
    assert payload.activity_honours.ark_win_ratio_label == "70%"
    assert payload.profile_status.conduct_score == 94.5
    assert payload.profile_status.conduct_source_field == "Conduct"
    assert payload.profile_status.civilisation_source_field == "Civilization"
    assert payload.profile_status.civilisation_label == "Civilisation"
    assert payload.freshness.updated_at_utc == scan
    assert payload.freshness.scan_order == 456
    assert payload.self_view is not None
    assert payload.self_view.account_type == "Main"
    assert payload.self_view.vip_level_label == "VIP 19"
    assert payload.missing_fields == ()


@pytest.mark.asyncio
async def test_payload_handles_missing_values_missing_vip_and_zero_ark_joined() -> None:
    async def data_loader(_governor_id: int):
        return GovernorDashboardDataRow(
            governor_id=111,
            ark_joined=0,
            ark_won=0,
        )

    async def vip_loader(_governor_id: int):
        return SimpleNamespace(vip_level_label="Unknown / not set")

    payload = await service.build_governor_dashboard_payload(
        _self_context(),
        data_loader=data_loader,
        vip_profile_loader=vip_loader,
    )

    assert payload.identity.governor_name == "Linked Gov"
    assert payload.activity_honours.ark_win_ratio is None
    assert payload.activity_honours.ark_win_ratio_label == "N/A"
    assert payload.self_view is not None
    assert payload.self_view.vip_level_label is None
    assert "vip_level_label" in payload.missing_fields
    assert "alliance" in payload.missing_fields
    assert "conduct_score" in payload.missing_fields
    assert "updated_at_utc" in payload.missing_fields


@pytest.mark.asyncio
async def test_inspect_mode_payload_excludes_self_view_only_data() -> None:
    context = GovernorDashboardContext(
        viewer_discord_id=42,
        viewer_mode="inspect",
        selected_governor_id=999,
        selected_governor_name=None,
        is_linked_to_viewer=False,
        account_type_for_self_view=None,
        access_decision=service.GovernorDashboardAccessDecision(
            allowed=True,
            reason="inspect mode",
        ),
        privacy_profile="inspect_safe",
    )

    async def data_loader(_governor_id: int):
        return GovernorDashboardDataRow(governor_id=999, governor_name="Inspect Gov")

    async def vip_loader(_governor_id: int):
        raise AssertionError("inspect mode must not read self-view VIP")

    payload = await service.build_governor_dashboard_payload(
        context,
        data_loader=data_loader,
        vip_profile_loader=vip_loader,
    )

    assert payload.self_view is None
    assert payload.available_actions == ()
    assert payload.identity.governor_name == "Inspect Gov"


@pytest.mark.asyncio
async def test_inspect_mode_requested_governor_does_not_require_account_registry() -> None:
    account_loader = await _account_loader({}, ok=False, error="registry unavailable")

    resolution = await service.resolve_dashboard_context(
        42,
        999,
        viewer_mode="inspect",
        account_loader=account_loader,
    )

    assert resolution.state == "selected"
    assert resolution.options == ()
    assert resolution.context is not None
    assert resolution.context.access_allowed is True
    assert resolution.context.selected_governor_id == 999
    assert resolution.context.is_linked_to_viewer is False
    assert resolution.context.account_type_for_self_view is None


@pytest.mark.asyncio
async def test_default_dashboard_data_fetch_degrades_to_empty_payload(monkeypatch) -> None:
    def broken_fetch(_governor_id: int):
        raise RuntimeError("sql timeout")

    async def vip_loader(_governor_id: int):
        return SimpleNamespace(vip_level_label=None)

    monkeypatch.setattr(
        service.governor_dashboard_dal, "fetch_governor_dashboard_data", broken_fetch
    )

    payload = await service.build_governor_dashboard_payload(
        _self_context(555),
        vip_profile_loader=vip_loader,
    )

    assert payload.identity.governor_id == 555
    assert payload.identity.governor_name == "Linked Gov"
    assert payload.latest_metrics.power is None
    assert "power" in payload.missing_fields


def test_dashboard_dal_int_mapping_preserves_large_decimal_values() -> None:
    value = Decimal("12345678901234567890")

    assert dal._to_int(value) == 12345678901234567890


@pytest.mark.asyncio
async def test_payload_excludes_olympia_fields_entirely() -> None:
    async def data_loader(_governor_id: int):
        return GovernorDashboardDataRow(governor_id=111, governor_name="Main Gov")

    async def vip_loader(_governor_id: int):
        return SimpleNamespace(vip_level_label=None)

    payload = await service.build_governor_dashboard_payload(
        _self_context(),
        data_loader=data_loader,
        vip_profile_loader=vip_loader,
    )

    serialized = str(asdict(payload)).casefold()
    assert "olympia" not in serialized


def test_governor_dashboard_foundation_does_not_change_command_surface() -> None:
    names, grouped = command_validator.collect_primary_inventory()

    assert len(names) == 42
    assert len(grouped["me"]) == 6
    assert {
        "dashboard",
        "accounts",
        "reminders",
        "preferences",
        "inventory",
        "exports",
    }.issubset(grouped["me"])


def test_governor_dashboard_service_has_no_ui_framework_dependency() -> None:
    source = Path("player_self_service/governor_dashboard_service.py").read_text(encoding="utf-8")
    framework_name = "dis" + "cord"

    assert f"import {framework_name}" not in source
    assert f"{framework_name}." not in source
