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
    assert "registered_account_slots" in source
    assert "def _parse_user_id" not in source
