from __future__ import annotations

from pathlib import Path
import re


def _source() -> str:
    return Path("commands/registry_cmds.py").read_text(encoding="utf-8")


def test_registry_cmds_uses_public_governor_lookup_helper() -> None:
    source = _source()

    assert "target_utils.lookup_governor_row_by_id" in source
    assert "target_utils._name_cache" not in source
    assert "from target_utils import _name_cache" not in source


def test_registry_cmds_uses_shared_account_helpers() -> None:
    source = _source()

    assert "parse_discord_user_id" in source
    assert "filter_account_slots" in source
    assert "get_account_summary_for_user" in source
    assert "summary.registered_slots" in source
    assert "def _parse_user_id" not in source


def test_registry_cmds_uses_account_summary_directly_for_registry_selection() -> None:
    source = _source()

    assert "get_accounts_for_user as get_user_accounts_async" not in source
    assert "await asyncio.to_thread(get_user_accounts" not in source
    assert "account_summary.ordered_accounts" in source


def test_registry_autocomplete_falls_back_to_invoking_user_for_self_service() -> None:
    source = _source()

    assert 'command_name != "modify_registration"' in source
    assert 'getattr(getattr(ctx, "interaction", None), "user", None)' in source
    assert 'getattr(ctx, "user", None)' not in source


def test_legacy_player_account_commands_redirect_to_me_accounts() -> None:
    source = _source()

    for old_path in ("/register_governor", "/modify_registration", "/my_registrations"):
        assert re.search(rf"old_path\s*=\s*['\"]{re.escape(old_path)}['\"]", source)
    assert len(re.findall(r"new_path\s*=\s*['\"]/me accounts['\"]", source)) >= 3


def test_deprecated_account_redirect_options_are_optional() -> None:
    source = _source()

    assert (
        len(
            re.findall(
                r"required\s*=\s*False\s*,\s*default\s*=\s*['\"]['\"]",
                source,
            )
        )
        >= 4
    )


def test_my_registrations_legacy_helpers_removed_from_command_module() -> None:
    source = _source()

    assert "_load_my_registrations_summary" not in source
    assert "_build_my_registrations_embed" not in source
    assert "MyRegsActionView" not in source
    assert "RegisterGovernorView" not in source
    assert "ModifyGovernorView" not in source
    assert "ConfirmRemoveView" not in source


def test_registration_audit_fetches_missing_registered_members_before_payload() -> None:
    source = _source()

    assert "missing_registered_uids" in source
    assert "guild.fetch_member" in source
    assert "build_registration_audit_payload(registry, members_info, sql_rows)" in source


def test_registry_cmds_do_not_import_registry_dal_directly() -> None:
    source = _source()

    assert "from registry.dal" not in source
