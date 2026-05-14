from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import commands.registry_cmds as registry_cmds
from commands.registry_cmds import _build_my_registrations_embed, _load_my_registrations_summary
from services.governor_account_service import summarize_accounts


def test_registry_cmds_uses_public_governor_lookup_helper() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "target_utils.lookup_governor_row_by_id" in source
    assert "target_utils._name_cache" not in source
    assert "from target_utils import _name_cache" not in source


def test_registry_cmds_uses_shared_account_helpers() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "parse_discord_user_id" in source
    assert "filter_account_slots" in source
    assert "get_account_summary_for_user" in source
    assert "summary.registered_slots" in source
    assert "def _parse_user_id" not in source


def test_registry_cmds_uses_account_summary_directly_for_registry_selection() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "get_accounts_for_user as get_user_accounts_async" not in source
    assert "await asyncio.to_thread(get_user_accounts" not in source
    assert "account_summary.ordered_accounts" in source


def test_registry_autocomplete_falls_back_to_invoking_user_for_self_service() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert 'command_name != "modify_registration"' in source
    assert 'getattr(getattr(ctx, "interaction", None), "user", None)' in source
    assert 'getattr(ctx, "user", None)' not in source


def test_my_registrations_uses_account_summary_display_loader() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "asyncio.to_thread(load_registry)" not in source
    assert "await _load_my_registrations_summary(ctx.user.id)" in source


@pytest.mark.asyncio
async def test_my_registrations_summary_loader_uses_stale_registry_fallback(monkeypatch) -> None:
    async def _failed_summary(_discord_user_id: int):
        return summarize_accounts({}, ok=False, error="SQL down")

    def _stale_registry():
        return {
            "123": {
                "accounts": {
                    "Main": {"GovernorID": "111", "GovernorName": "Stale Main"},
                },
            },
        }

    monkeypatch.setattr(registry_cmds, "get_account_summary_for_user", _failed_summary)
    monkeypatch.setattr(registry_cmds.registry_service, "load_registry_as_dict", _stale_registry)

    summary = await _load_my_registrations_summary(123)

    assert summary.ok is True
    assert summary.ordered_accounts == {"Main": {"GovernorID": "111", "GovernorName": "Stale Main"}}


@pytest.mark.asyncio
async def test_my_registrations_summary_loader_returns_primary_failure_when_no_fallback(
    monkeypatch,
) -> None:
    async def _failed_summary(_discord_user_id: int):
        return summarize_accounts({}, ok=False, error="SQL down")

    def _failed_registry():
        raise RuntimeError("cache unavailable")

    monkeypatch.setattr(registry_cmds, "get_account_summary_for_user", _failed_summary)
    monkeypatch.setattr(registry_cmds.registry_service, "load_registry_as_dict", _failed_registry)

    summary = await _load_my_registrations_summary(123)

    assert summary.ok is False
    assert summary.error == "SQL down"


def test_my_registrations_embed_uses_summary_order_and_copy() -> None:
    summary = summarize_accounts(
        {
            "Farm 1": {"GovernorID": "333", "GovernorName": "Farmhand"},
            "Main": {"GovernorID": "111", "GovernorName": "Main Gov"},
            "Alt 1": {"GovernorID": "222", "GovernorName": "Alt Gov"},
        }
    )

    embed, has_regs = _build_my_registrations_embed(
        summary,
        requested_by=SimpleNamespace(display_name="Tester", name="Fallback"),
    )

    assert has_regs is True
    assert embed.title == "Your Registered Accounts"
    assert embed.description.splitlines() == [
        "• **Main** — **Main Gov** (`111`)",
        "• **Alt 1** — **Alt Gov** (`222`)",
        "• **Farm 1** — **Farmhand** (`333`)",
    ]
    assert embed.footer.text == "Requested by Tester"


def test_my_registrations_embed_preserves_empty_state_copy() -> None:
    summary = summarize_accounts({})

    embed, has_regs = _build_my_registrations_embed(
        summary,
        requested_by=SimpleNamespace(name="No Display"),
    )

    assert has_regs is False
    assert embed.title == "Your Registered Accounts"
    assert embed.description == "You don’t have any accounts registered yet."


def test_registration_audit_fetches_missing_registered_members_before_payload() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "missing_registered_uids" in source
    assert "guild.fetch_member" in source
    assert "build_registration_audit_payload(registry, members_info, sql_rows)" in source


def test_registry_cmds_do_not_import_registry_dal_directly() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "from registry.dal" not in source
