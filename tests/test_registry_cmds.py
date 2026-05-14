from __future__ import annotations

from pathlib import Path


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


def test_my_registrations_uses_service_loader_not_removed_facade_import() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "asyncio.to_thread(load_registry)" not in source
    assert "registry_service.load_registry_as_dict" in source


def test_registration_audit_fetches_missing_registered_members_before_payload() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "missing_registered_uids" in source
    assert "guild.fetch_member" in source
    assert "build_registration_audit_payload(registry, members_info, sql_rows)" in source


def test_registry_cmds_do_not_import_registry_dal_directly() -> None:
    source = Path("commands/registry_cmds.py").read_text(encoding="utf-8")

    assert "from registry.dal" not in source
