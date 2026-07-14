from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from inventory.models import InventoryResourcePoint
from player_self_service import accounts_service
from player_self_service.accounts_models import AccountsScanRow
from services.governor_account_service import summarize_accounts


def _accounts(**slots):
    return {
        slot: {"GovernorID": governor_id, "GovernorName": name}
        for slot, (governor_id, name) in slots.items()
    }


@pytest.mark.asyncio
async def test_build_accounts_portfolio_uses_distinct_ids_and_canonical_rss(monkeypatch) -> None:
    latest = datetime(2026, 7, 14, 8, 0)
    resolution = summarize_accounts(
        _accounts(Main=(111, "Registered Main"), **{"Alt 1": (222, "Alt")})
    )

    async def account_summary(_user_id):
        return resolution

    def scan_rows(ids):
        assert ids == (111, 222)
        return tuple(
            AccountsScanRow(
                governor_id=gid,
                governor_name="Current Main" if gid == 111 else "Alt",
                power=gid * 10,
                troop_power=gid,
                t4_kills=gid,
                t5_kills=gid * 2,
                scan_date=latest,
                latest_scan_date=latest,
            )
            for gid in ids
        )

    async def inventory(ids):
        assert ids == (111, 222)
        return {
            gid: InventoryResourcePoint(latest.replace(tzinfo=UTC), gid, 2, 3, 4)
            for gid in ids
        }

    monkeypatch.setattr(
        accounts_service.governor_account_service,
        "get_account_summary_for_user",
        account_summary,
    )
    monkeypatch.setattr(accounts_service.accounts_dal, "fetch_latest_accounts_scan_rows", scan_rows)
    monkeypatch.setattr(
        accounts_service.reporting_service,
        "build_latest_resource_points_by_governor",
        inventory,
    )

    payload = await accounts_service.build_accounts_portfolio(42)

    assert payload.state == "READY"
    assert [row.slot for row in payload.rows] == ["Main", "Alt 1"]
    assert payload.power.value == 3330
    assert payload.t4_t5_kills.value == 999
    assert payload.rss_total.value == (111 + 9) + (222 + 9)
    assert payload.role_counts == (("Main", 1), ("Alt", 1), ("Farm", 0))
    assert payload.rows[0].registered_name == "Registered Main"
    assert payload.rows[0].current_governor_name == "Current Main"
    assert payload.rows[0].rss_total == 120


@pytest.mark.asyncio
async def test_duplicate_ids_are_review_and_totals_do_not_double_count(monkeypatch) -> None:
    latest = datetime(2026, 7, 14, 8, 0)
    resolution = summarize_accounts(
        _accounts(Main=(111, "Main"), **{"Alt 1": (111, "Duplicate")})
    )

    async def account_summary(_user_id):
        return resolution

    async def inventory(_ids):
        return {111: InventoryResourcePoint(latest, 25, 25, 25, 25)}

    monkeypatch.setattr(
        accounts_service.governor_account_service,
        "get_account_summary_for_user",
        account_summary,
    )
    monkeypatch.setattr(
        accounts_service.accounts_dal,
        "fetch_latest_accounts_scan_rows",
        lambda _ids: (
            AccountsScanRow(
                governor_id=111,
                power=500,
                t4_kills=10,
                t5_kills=20,
                scan_date=latest,
                latest_scan_date=latest,
            ),
        ),
    )
    monkeypatch.setattr(
        accounts_service.reporting_service,
        "build_latest_resource_points_by_governor",
        inventory,
    )

    payload = await accounts_service.build_accounts_portfolio(42)

    assert payload.state == "REVIEW"
    assert payload.power.value == 500
    assert payload.power.reporting_count == 1
    assert payload.power.expected_count == 2
    assert payload.rss_total.value == 100
    assert all(row.duplicate_governor_id for row in payload.rows)
    assert payload.insight.startswith("Duplicate Governor IDs")


@pytest.mark.asyncio
async def test_scan_states_and_inventory_coverage_are_independent(monkeypatch) -> None:
    latest = datetime(2026, 7, 14, 8, 0)
    resolution = summarize_accounts(
        {
            "Main": {"GovernorID": 111, "GovernorName": "Main"},
            "Alt 1": {"GovernorID": 222, "GovernorName": "Alt"},
            "Farm 1": {"GovernorID": "bad", "GovernorName": "Broken"},
        }
    )

    async def account_summary(_user_id):
        return resolution

    async def failing_inventory(_ids):
        raise RuntimeError("inventory unavailable")

    monkeypatch.setattr(
        accounts_service.governor_account_service,
        "get_account_summary_for_user",
        account_summary,
    )
    monkeypatch.setattr(
        accounts_service.accounts_dal,
        "fetch_latest_accounts_scan_rows",
        lambda _ids: (
            AccountsScanRow(
                governor_id=111,
                power=1,
                scan_date=latest,
                latest_scan_date=latest,
            ),
            AccountsScanRow(
                governor_id=222,
                scan_date=latest - timedelta(days=1),
                latest_scan_date=latest,
            ),
        ),
    )
    monkeypatch.setattr(
        accounts_service.reporting_service,
        "build_latest_resource_points_by_governor",
        failing_inventory,
    )

    payload = await accounts_service.build_accounts_portfolio(42)

    assert [row.data_state for row in payload.rows] == ["CURRENT", "STALE", "UNRESOLVED"]
    assert payload.state == "REVIEW"
    assert payload.rss_total.value is None
    assert payload.rss_total.reporting_count == 0
    assert payload.rss_total.expected_count == 3
    assert "Inventory coverage" in payload.warnings[-1]


@pytest.mark.asyncio
async def test_registry_failure_is_review_not_false_setup(monkeypatch) -> None:
    async def account_summary(_user_id):
        return summarize_accounts({}, ok=False, error="database unavailable")

    monkeypatch.setattr(
        accounts_service.governor_account_service,
        "get_account_summary_for_user",
        account_summary,
    )

    payload = await accounts_service.build_accounts_portfolio(42)

    assert payload.state == "REVIEW"
    assert payload.linked_count == 0
    assert payload.warnings == ("Registry data is temporarily unavailable.",)
    assert payload.insight.startswith("Account registry data is temporarily unavailable")


def test_summary_pagination_supports_hundreds_and_section_change_resets_externally() -> None:
    from dataclasses import replace

    from player_self_service.accounts_models import (
        AccountMetricTotal,
        AccountPortfolioRow,
        AccountsPortfolioPayload,
    )

    rows = tuple(
        AccountPortfolioRow(
            slot="Main" if index == 0 else f"Farm {index}",
            role="Main" if index == 0 else "Farm",
            registered_name=f"Gov {index}",
            governor_id=1000 + index,
            data_state="CURRENT",
        )
        for index in range(205)
    )
    empty_metric = AccountMetricTotal(None, 0, len(rows))
    payload = AccountsPortfolioPayload(
        discord_user_id=42,
        state="READY",
        rows=rows,
        linked_count=len(rows),
        main_row=rows[0],
        role_counts=(("Main", 1), ("Alt", 0), ("Farm", 204)),
        power=empty_metric,
        troop_power=empty_metric,
        t4_t5_kills=empty_metric,
        rss_total=empty_metric,
        insight="All current.",
        refreshed_at_utc=datetime.now(UTC),
    )

    page = accounts_service.build_account_summary_page(payload, section="combat", page=26)

    assert page.page_count == 26
    assert page.page == 26
    assert len(page.rows) == 5
    assert page.rows[0].governor_id == 1200
    assert accounts_service.build_account_summary_page(
        replace(payload), section="economy", page=1
    ).page == 1
