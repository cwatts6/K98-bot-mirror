from __future__ import annotations

from pathlib import Path

import pytest

from player_self_service import account_service
from services.governor_account_service import summarize_accounts
from services.governor_lookup_service import GovernorLookupResult


async def _found_governor(_query: str) -> GovernorLookupResult:
    return GovernorLookupResult(
        status="found",
        query="123",
        governor_id="123",
        governor_name="New Gov",
    )


def test_build_state_from_summary_lists_registered_and_free_slots() -> None:
    state = account_service.build_state_from_summary(
        summarize_accounts(
            {
                "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
                "Alt 1": {"GovernorID": "222", "GovernorName": "Alt Gov"},
            }
        )
    )

    assert state.ok is True
    assert state.linked_count == 2
    assert state.main_label == "Main Gov (111)"
    assert [slot.slot for slot in state.registered_slots] == ["Main", "Alt 1"]
    assert "Alt 2" in state.free_slots


def test_build_state_reports_unavailable_source() -> None:
    state = account_service.build_state_from_summary(
        summarize_accounts({}, ok=False, error="SQL down")
    )

    assert state.ok is False
    assert state.error == "SQL down"
    assert state.can_register is False


@pytest.mark.asyncio
async def test_prepare_register_confirmation_rejects_used_slot() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})

    confirmation, error = await account_service.prepare_register_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
    )

    assert confirmation is None
    assert "already registered" in error


@pytest.mark.asyncio
async def test_prepare_register_confirmation_rejects_claimed_governor() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({})

    confirmation, error = await account_service.prepare_register_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
        claim_checker=lambda _gid, _uid: True,
    )

    assert confirmation is None
    assert "another Discord user" in error


@pytest.mark.asyncio
async def test_prepare_register_confirmation_returns_payload() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({})

    confirmation, error = await account_service.prepare_register_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
        claim_checker=lambda _gid, _uid: False,
    )

    assert error is None
    assert confirmation is not None
    assert confirmation.action == "register"
    assert confirmation.account_type == "Main"
    assert confirmation.governor_id == "123"
    assert "Register Main" in confirmation.title


@pytest.mark.asyncio
async def test_prepare_replace_confirmation_requires_existing_slot() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({})

    confirmation, error = await account_service.prepare_replace_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
    )

    assert confirmation is None
    assert "not currently registered" in error


@pytest.mark.asyncio
async def test_prepare_replace_confirmation_rejects_same_current_governor() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "123", "GovernorName": "Main Gov"}})

    confirmation, error = await account_service.prepare_replace_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
        claim_checker=lambda _gid, _uid: False,
    )

    assert confirmation is None
    assert "already linked" in error


@pytest.mark.asyncio
async def test_prepare_replace_confirmation_rejects_governor_linked_to_other_slot() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts(
            {
                "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
                "Alt 1": {"GovernorID": "123", "GovernorName": "Alt Gov"},
            }
        )

    confirmation, error = await account_service.prepare_replace_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
        claim_checker=lambda _gid, _uid: False,
    )

    assert confirmation is None
    assert "another slot" in error


@pytest.mark.asyncio
async def test_prepare_replace_confirmation_returns_current_and_new_values() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})

    confirmation, error = await account_service.prepare_replace_confirmation(
        42,
        "Main",
        "123",
        account_loader=account_loader,
        resolver=_found_governor,
        claim_checker=lambda _gid, _uid: False,
    )

    assert error is None
    assert confirmation is not None
    assert confirmation.action == "replace"
    assert confirmation.current_governor_id == "111"
    assert confirmation.governor_name == "New Gov"
    assert "Replace Main" in confirmation.title


@pytest.mark.asyncio
async def test_prepare_remove_confirmation_returns_current_values() -> None:
    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})

    confirmation, error = await account_service.prepare_remove_confirmation(
        42,
        "Main",
        account_loader=account_loader,
    )

    assert error is None
    assert confirmation is not None
    assert confirmation.action == "remove"
    assert confirmation.current_governor_id == "111"
    assert "Remove Main" in confirmation.title


@pytest.mark.asyncio
async def test_confirm_register_hands_off_to_registry_writer() -> None:
    calls = []
    confirmation = account_service.AccountConfirmation(
        action="register",
        account_type="Main",
        governor_id="123",
        governor_name="New Gov",
    )

    def writer(*args, **kwargs):
        calls.append((args, kwargs))
        return True, None

    result = await account_service.confirm_register(
        42,
        "Tester",
        confirmation,
        writer=writer,
    )

    assert result.ok is True
    assert "Registered Main" in result.message
    assert calls[0][0][:5] == (42, "Tester", "Main", "123", "New Gov")
    assert calls[0][1]["created_by"] == 42


@pytest.mark.asyncio
async def test_confirm_replace_revalidates_current_governor_before_writer() -> None:
    calls = []
    confirmation = account_service.AccountConfirmation(
        action="replace",
        account_type="Main",
        governor_id="123",
        governor_name="New Gov",
        current_governor_id="111",
        current_governor_name="Old Gov",
    )

    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "222", "GovernorName": "Other Gov"}})

    def writer(*args, **kwargs):
        calls.append((args, kwargs))
        return True, None

    result = await account_service.confirm_replace(
        42,
        "Tester",
        confirmation,
        account_loader=account_loader,
        writer=writer,
    )

    assert result.ok is False
    assert "stale" in result.message
    assert calls == []


@pytest.mark.asyncio
async def test_confirm_replace_hands_off_to_registry_writer_after_revalidation() -> None:
    calls = []
    confirmation = account_service.AccountConfirmation(
        action="replace",
        account_type="Main",
        governor_id="123",
        governor_name="New Gov",
        current_governor_id="111",
        current_governor_name="Old Gov",
    )

    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Old Gov"}})

    def writer(*args, **kwargs):
        calls.append((args, kwargs))
        return True, None

    result = await account_service.confirm_replace(
        42,
        "Tester",
        confirmation,
        account_loader=account_loader,
        writer=writer,
    )

    assert result.ok is True
    assert "Replaced Main" in result.message
    writer_args, writer_kwargs = calls[0]
    assert writer_args == (42, "Tester", "Main", "123", "New Gov")
    assert writer_kwargs["updated_by"] == 42


@pytest.mark.asyncio
async def test_confirm_remove_revalidates_current_governor_before_writer() -> None:
    calls = []
    confirmation = account_service.AccountConfirmation(
        action="remove",
        account_type="Main",
        current_governor_id="111",
        current_governor_name="Old Gov",
    )

    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "222", "GovernorName": "New Gov"}})

    def writer(*args, **kwargs):
        calls.append((args, kwargs))
        return True, None

    result = await account_service.confirm_remove(
        42,
        confirmation,
        account_loader=account_loader,
        writer=writer,
    )

    assert result.ok is False
    assert "stale" in result.message
    assert calls == []


@pytest.mark.asyncio
async def test_confirm_remove_hands_off_to_registry_writer_after_revalidation() -> None:
    calls = []
    confirmation = account_service.AccountConfirmation(
        action="remove",
        account_type="Main",
        current_governor_id="111",
        current_governor_name="Main Gov",
    )

    async def account_loader(_user_id: int):
        return summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Main Gov"}})

    def writer(*args, **kwargs):
        calls.append((args, kwargs))
        return True, None

    result = await account_service.confirm_remove(
        42,
        confirmation,
        account_loader=account_loader,
        writer=writer,
    )

    assert result.ok is True
    assert "Removed Main" in result.message
    assert calls[0][0] == (42, "Main")
    assert calls[0][1]["removed_by"] == 42


def test_account_service_has_no_ui_framework_dependency() -> None:
    source = Path("player_self_service/account_service.py").read_text(encoding="utf-8")
    framework_name = "dis" + "cord"

    assert f"import {framework_name}" not in source
    assert f"{framework_name}." not in source
