from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_accounts_for_user_uses_registry_service(monkeypatch):
    from services import governor_account_service as svc

    def fake_get_user_accounts(discord_user_id):
        assert discord_user_id == 42
        return {"Main": {"GovernorID": "123", "GovernorName": "A"}}

    monkeypatch.setattr(svc.registry_service, "get_user_accounts", fake_get_user_accounts)

    result = await svc.get_accounts_for_user(42)

    assert result.ok is True
    assert result.accounts["Main"]["GovernorID"] == "123"


@pytest.mark.asyncio
async def test_get_accounts_for_user_reports_failure(monkeypatch):
    from services import governor_account_service as svc

    def fake_get_user_accounts(discord_user_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc.registry_service, "get_user_accounts", fake_get_user_accounts)

    result = await svc.get_accounts_for_user(42)

    assert result.ok is False
    assert result.accounts == {}
    assert "db down" in result.error


def test_account_classification_and_free_slots():
    from services import governor_account_service as svc

    assert svc.classify_accounts({}) == ("none", None)
    assert svc.classify_accounts({"Main": {"GovernorID": "1"}}) == ("single", "1")
    assert svc.classify_accounts({"Main": {"GovernorID": "1"}, "Alt 1": {"GovernorID": "2"}}) == (
        "multi",
        None,
    )

    free = svc.free_account_slots({"Main": {"GovernorID": "1"}})
    assert "Main" not in free
    assert "Alt 1" in free
    assert "Farm 20" in free


def test_account_resolution_summary_orders_deduplicates_and_defaults_to_main():
    from services import governor_account_service as svc

    summary = svc.summarize_accounts(
        {
            "Farm 1": {"GovernorID": "300", "GovernorName": "Farm"},
            "Main": {"GovernorID": "100", "GovernorName": "Main"},
            "Alt 1": {"GovernorID": "100", "GovernorName": "Main"},
            "Alt 2": {"GovernorID": "not-a-number", "GovernorName": "Bad"},
        }
    )

    assert summary.ok is True
    assert list(summary.ordered_accounts) == ["Main", "Alt 1", "Alt 2", "Farm 1"]
    assert summary.governor_ids == (100, 300)
    assert summary.governor_id_strings == ("100", "300")
    assert summary.account_names == ("Main", "Farm")
    assert summary.name_to_id == {"Main": 100, "Farm": 300}
    assert summary.default_choice == "Main"
    assert summary.classification == ("multi", None)
    assert summary.contains_governor_id("100")
    assert summary.registered_slots() == ["Main", "Alt 1", "Alt 2", "Farm 1"]
    assert summary.registered_slots("alt") == ["Alt 1", "Alt 2"]


def test_account_resolution_summary_single_classification_handles_unknown_slots():
    from services import governor_account_service as svc

    summary = svc.summarize_accounts({"Custom": {"GovernorID": "987", "GovernorName": "C"}})

    assert list(summary.ordered_accounts) == ["Custom"]
    assert summary.classification == ("single", "987")
    assert summary.first_account is not None
    assert summary.first_account.slot == "Custom"


def test_parse_discord_user_id_accepts_mentions_and_raw_ids():
    from services import governor_account_service as svc

    assert svc.parse_discord_user_id("<@123456789012345678>") == 123456789012345678
    assert svc.parse_discord_user_id("id=987654321098765432") == 987654321098765432
    assert svc.parse_discord_user_id("not an id") is None


def test_account_slot_filters_use_canonical_sql_backed_slots():
    from services import governor_account_service as svc

    slots = svc.all_account_slots()
    assert slots[0] == "Main"
    assert "Farm 20" in slots
    assert svc.filter_account_slots("farm 2") == ["Farm 2", "Farm 20"]
    assert svc.registered_account_slots(
        {
            "Farm 20": {"GovernorID": "20"},
            "Main": {"GovernorID": "1"},
            "Custom": {"GovernorID": "99"},
        }
    ) == ["Main", "Farm 20", "Custom"]


@pytest.mark.asyncio
async def test_resolve_governor_label(monkeypatch):
    from services import governor_account_service as svc

    async def fake_get_account_summary_for_user(discord_user_id):
        return svc.summarize_accounts(
            {"Main": {"GovernorID": "123", "GovernorName": "Ada"}},
        )

    monkeypatch.setattr(svc, "get_account_summary_for_user", fake_get_account_summary_for_user)

    assert await svc.resolve_governor_label(42, "123") == "Ada (123)"
