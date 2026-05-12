from __future__ import annotations

import pytest

from services import stats_account_service


def test_summarize_accounts_orders_ids_names_and_default_main() -> None:
    accounts = {
        "Farm 1": {"GovernorID": "300", "GovernorName": "Farm"},
        "Main": {"GovernorID": "100", "GovernorName": "Main"},
        "Alt 1": {"GovernorID": "200", "GovernorName": "Alt"},
    }

    summary = stats_account_service.summarize_accounts(accounts)

    assert list(summary.ordered_accounts) == ["Main", "Alt 1", "Farm 1"]
    assert summary.governor_ids == [100, 200, 300]
    assert summary.account_names == ["Main", "Alt", "Farm"]
    assert summary.name_to_id == {"Main": 100, "Alt": 200, "Farm": 300}
    assert summary.default_choice == "Main"


@pytest.mark.asyncio
async def test_get_account_summary_uses_registry_service(monkeypatch) -> None:
    called = {}

    def fake_get_user_accounts(discord_user_id: int):
        called["discord_user_id"] = discord_user_id
        return {"Main": {"GovernorID": "123", "GovernorName": "Player"}}

    monkeypatch.setattr(
        stats_account_service.registry_service,
        "get_user_accounts",
        fake_get_user_accounts,
    )

    summary = await stats_account_service.get_account_summary_for_user(42)

    assert called == {"discord_user_id": 42}
    assert summary.ok is True
    assert summary.governor_ids == [123]


@pytest.mark.asyncio
async def test_get_account_summary_returns_error_on_registry_failure(monkeypatch) -> None:
    def fake_get_user_accounts(_discord_user_id: int):
        raise RuntimeError("db down")

    monkeypatch.setattr(
        stats_account_service.registry_service,
        "get_user_accounts",
        fake_get_user_accounts,
    )

    summary = await stats_account_service.get_account_summary_for_user(42)

    assert summary.ok is False
    assert summary.governor_ids == []
    assert "RuntimeError" in (summary.error or "")
