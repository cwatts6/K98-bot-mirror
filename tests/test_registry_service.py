# tests/test_registry_service.py
"""
Unit tests for registry.registry_service

All DAL calls are monkeypatched — no SQL connection required.
"""

import pytest

import registry.dal.registry_dal as dal
import registry.registry_service as svc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_dal(
    monkeypatch,
    *,
    insert_result=(0, "OK"),
    soft_delete_result=(0, "OK"),
    by_discord=None,
    by_governor=None,
    all_active=None,
):
    monkeypatch.setattr(dal, "insert", lambda **kw: insert_result)
    monkeypatch.setattr(dal, "soft_delete", lambda **kw: soft_delete_result)
    monkeypatch.setattr(dal, "get_by_discord_id", lambda uid, **kw: by_discord or [])
    monkeypatch.setattr(dal, "get_by_governor_id", lambda gid, **kw: by_governor)
    monkeypatch.setattr(dal, "get_all_active", lambda: all_active or [])


# ---------------------------------------------------------------------------
# register_governor()
# ---------------------------------------------------------------------------


def test_register_governor_success(monkeypatch):
    _patch_dal(monkeypatch, insert_result=(0, "Inserted"))
    ok, err = svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )
    assert ok is True
    assert err is None


def test_register_governor_invalid_governor_id(monkeypatch):
    _patch_dal(monkeypatch)
    ok, err = svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="notanumber",
        governor_name="Test",
    )
    assert ok is False
    assert "Invalid Governor ID" in err


def test_register_governor_duplicate_slot(monkeypatch):
    _patch_dal(monkeypatch, insert_result=(1, "Slot already active"))
    ok, err = svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )
    assert ok is False
    assert "slot" in err.lower() or "registration" in err.lower()


def test_register_governor_duplicate_governor_across_users(monkeypatch):
    _patch_dal(monkeypatch, insert_result=(2, "GovernorID already registered to another user"))
    ok, err = svc.register_governor(
        discord_user_id=222,
        discord_name="Bob",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )
    assert ok is False
    assert "another" in err.lower() or "registered" in err.lower()


def test_register_governor_sql_error(monkeypatch):
    _patch_dal(monkeypatch, insert_result=(9, "Unexpected DB failure"))
    ok, err = svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )
    assert ok is False
    assert err is not None


# ---------------------------------------------------------------------------
# modify_governor()
# ---------------------------------------------------------------------------

_EXISTING_SLOT = [{"AccountType": "Main", "GovernorID": 2441482, "DiscordUserID": 111}]


def test_modify_governor_success(monkeypatch):
    _patch_dal(
        monkeypatch,
        by_discord=_EXISTING_SLOT,
        by_governor=None,
        soft_delete_result=(0, "OK"),
        insert_result=(0, "OK"),
    )
    ok, err = svc.modify_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        new_governor_id="9999999",
        new_governor_name="NewGov",
        updated_by=111,
    )
    assert ok is True
    assert err is None


def test_modify_governor_slot_not_found(monkeypatch):
    _patch_dal(monkeypatch, by_discord=[])
    ok, err = svc.modify_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Alt 1",
        new_governor_id="9999999",
        new_governor_name="NewGov",
    )
    assert ok is False
    assert "no active registration" in err.lower()


def test_modify_governor_new_id_claimed_by_other(monkeypatch):
    claimed = {"DiscordUserID": 999, "AccountType": "Main"}
    _patch_dal(monkeypatch, by_discord=_EXISTING_SLOT, by_governor=claimed)
    ok, err = svc.modify_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        new_governor_id="9999999",
        new_governor_name="Taken",
    )
    assert ok is False
    assert "another" in err.lower()


def test_modify_governor_partial_failure_logged(monkeypatch, caplog):
    """
    If soft_delete succeeds but insert fails, the error must be logged at ERROR
    level so an admin can detect and correct.
    """
    import logging

    _patch_dal(
        monkeypatch,
        by_discord=_EXISTING_SLOT,
        by_governor=None,
        soft_delete_result=(0, "OK"),
        insert_result=(9, "DB write failed"),
    )
    with caplog.at_level(logging.ERROR, logger="registry.registry_service"):
        ok, err = svc.modify_governor(
            discord_user_id=111,
            discord_name="Alice",
            account_type="Main",
            new_governor_id="9999999",
            new_governor_name="X",
        )
    assert ok is False
    assert "PARTIAL" in caplog.text or "partial" in caplog.text.lower()


# ---------------------------------------------------------------------------
# remove_governor()
# ---------------------------------------------------------------------------


def test_remove_governor_success(monkeypatch):
    _patch_dal(monkeypatch, soft_delete_result=(0, "Removed"))
    ok, err = svc.remove_governor(discord_user_id=111, account_type="Main", removed_by=111)
    assert ok is True
    assert err is None


def test_remove_governor_not_found(monkeypatch):
    _patch_dal(monkeypatch, soft_delete_result=(3, "No active row found"))
    ok, err = svc.remove_governor(discord_user_id=111, account_type="Alt 1")
    assert ok is False
    assert "not currently registered" in err.lower()


# ---------------------------------------------------------------------------
# admin_register_or_replace()
# ---------------------------------------------------------------------------


def test_admin_register_new_slot(monkeypatch):
    _patch_dal(monkeypatch, by_discord=[], by_governor=None, insert_result=(0, "OK"))
    ok, err = svc.admin_register_or_replace(
        target_discord_user_id=222,
        target_discord_name="Bob",
        account_type="Main",
        governor_id="9999999",
        governor_name="NewGov",
        admin_discord_id=1,
    )
    assert ok is True
    assert err is None


def test_admin_register_overwrites_existing_slot(monkeypatch):
    """Existing slot must be superseded then a new row inserted."""
    _patch_dal(
        monkeypatch,
        by_discord=_EXISTING_SLOT,
        by_governor=None,
        soft_delete_result=(0, "Superseded"),
        insert_result=(0, "OK"),
    )
    ok, err = svc.admin_register_or_replace(
        target_discord_user_id=111,
        target_discord_name="Alice",
        account_type="Main",
        governor_id="9999999",
        governor_name="Replacement",
        admin_discord_id=1,
    )
    assert ok is True


def test_admin_register_rejects_governor_claimed_by_other(monkeypatch):
    claimed = {"DiscordUserID": 999, "AccountType": "Alt 1"}
    _patch_dal(monkeypatch, by_discord=_EXISTING_SLOT, by_governor=claimed)
    ok, err = svc.admin_register_or_replace(
        target_discord_user_id=111,
        target_discord_name="Alice",
        account_type="Main",
        governor_id="9999999",
        governor_name="Taken",
        admin_discord_id=1,
    )
    assert ok is False
    assert "already registered" in err.lower()


# ---------------------------------------------------------------------------
# load_registry_as_dict()
# ---------------------------------------------------------------------------


def test_load_registry_as_dict_shape(monkeypatch):
    rows = [
        {
            "DiscordUserID": 111,
            "DiscordName": "Alice",
            "GovernorID": 2441482,
            "GovernorName": "Chrislos",
            "AccountType": "Main",
        },
        {
            "DiscordUserID": 111,
            "DiscordName": "Alice",
            "GovernorID": 46718337,
            "GovernorName": "Kurisulos",
            "AccountType": "Alt 1",
        },
    ]
    _patch_dal(monkeypatch, all_active=rows)
    result = svc.load_registry_as_dict()
    assert "111" in result
    assert "Main" in result["111"]["accounts"]
    assert result["111"]["accounts"]["Main"]["GovernorID"] == "2441482"
    assert "Alt 1" in result["111"]["accounts"]


def test_load_registry_as_dict_propagates_sql_exception(monkeypatch):
    """
    Phase 6 requirement: exception must propagate, not be swallowed.
    """
    monkeypatch.setattr(
        dal, "get_all_active", lambda: (_ for _ in ()).throw(RuntimeError("DB down"))
    )
    with pytest.raises(RuntimeError, match="DB down"):
        svc.load_registry_as_dict()


def test_get_user_accounts_propagates_sql_exception(monkeypatch):
    monkeypatch.setattr(
        dal, "get_by_discord_id", lambda uid, **kw: (_ for _ in ()).throw(RuntimeError("timeout"))
    )
    with pytest.raises(RuntimeError, match="timeout"):
        svc.get_user_accounts(111)


# ---------------------------------------------------------------------------
# VALID_ACCOUNT_TYPES
# ---------------------------------------------------------------------------


def test_valid_account_types_contains_main():
    assert "Main" in svc.VALID_ACCOUNT_TYPES


def test_valid_account_types_contains_all_alts():
    for i in range(1, 6):
        assert f"Alt {i}" in svc.VALID_ACCOUNT_TYPES


def test_valid_account_types_contains_all_farms():
    for i in range(1, 21):
        assert f"Farm {i}" in svc.VALID_ACCOUNT_TYPES


def test_valid_account_types_total_count():
    assert len(svc.VALID_ACCOUNT_TYPES) == 26  # 1 Main + 5 Alts + 20 Farms


# ---------------------------------------------------------------------------
# Cache integration tests
# ---------------------------------------------------------------------------


def _reset_cache(monkeypatch):
    """Reset the registry cache to a clean state."""
    import registry.registry_cache as rc

    monkeypatch.setattr(rc, "_cache_data", None)
    monkeypatch.setattr(rc, "_cache_ts", 0.0)
    monkeypatch.setattr(rc, "_last_invalidation_reason", "test_reset")


_ACTIVE_ROW = [
    {
        "DiscordUserID": 111,
        "DiscordName": "Alice",
        "GovernorID": 2441482,
        "GovernorName": "Chrislos",
        "AccountType": "Main",
    }
]


def test_load_registry_as_dict_uses_cache_on_second_call(monkeypatch):
    """Second call within TTL must not call the DAL again."""
    _reset_cache(monkeypatch)
    call_count = []

    def _fake_get_all_active():
        call_count.append(1)
        return _ACTIVE_ROW

    monkeypatch.setattr(dal, "get_all_active", _fake_get_all_active)

    # Prime TTL to 9999 seconds so cache does not expire
    import registry.registry_cache as rc

    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)

    svc.load_registry_as_dict()
    svc.load_registry_as_dict()

    assert len(call_count) == 1, f"DAL called {len(call_count)} times — expected 1 (cache should hit)"


def test_load_registry_as_dict_bypasses_cache_with_use_cache_false(monkeypatch):
    """use_cache=False must always call the DAL."""
    _reset_cache(monkeypatch)
    call_count = []

    def _fake_get_all_active():
        call_count.append(1)
        return _ACTIVE_ROW

    monkeypatch.setattr(dal, "get_all_active", _fake_get_all_active)

    import registry.registry_cache as rc

    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)

    svc.load_registry_as_dict(use_cache=False)
    svc.load_registry_as_dict(use_cache=False)

    assert len(call_count) == 2, f"DAL called {len(call_count)} times — expected 2 (cache bypassed)"


def test_register_governor_success_invalidates_cache(monkeypatch):
    """Successful register must invalidate the cache."""
    import registry.registry_cache as rc

    _reset_cache(monkeypatch)
    # Prime the cache
    rc.store_cache({"111": {"discord_id": "111", "discord_name": "Alice", "accounts": {}}})
    assert rc.get_cached_or_none() is not None, "cache should be populated before test"

    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    _patch_dal(monkeypatch, insert_result=(0, "Inserted"))

    svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )

    # After successful write, cache_ts must be 0 (invalidated)
    with rc._cache_lock:
        assert rc._cache_ts == 0.0, "cache_ts must be 0 after successful register_governor"


def test_modify_governor_success_invalidates_cache(monkeypatch):
    """Successful modify must invalidate the cache."""
    import registry.registry_cache as rc

    _reset_cache(monkeypatch)
    rc.store_cache({"111": {"discord_id": "111", "discord_name": "Alice", "accounts": {}}})
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)

    _patch_dal(
        monkeypatch,
        by_discord=_EXISTING_SLOT,
        by_governor=None,
        soft_delete_result=(0, "OK"),
        insert_result=(0, "OK"),
    )
    svc.modify_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        new_governor_id="9999999",
        new_governor_name="NewGov",
        updated_by=111,
    )

    with rc._cache_lock:
        assert rc._cache_ts == 0.0


def test_remove_governor_success_invalidates_cache(monkeypatch):
    """Successful remove must invalidate the cache."""
    import registry.registry_cache as rc

    _reset_cache(monkeypatch)
    rc.store_cache({"111": {"discord_id": "111", "discord_name": "Alice", "accounts": {}}})
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)

    _patch_dal(monkeypatch, soft_delete_result=(0, "Removed"))
    svc.remove_governor(discord_user_id=111, account_type="Main", removed_by=111)

    with rc._cache_lock:
        assert rc._cache_ts == 0.0


def test_admin_register_success_invalidates_cache(monkeypatch):
    """Successful admin register must invalidate the cache."""
    import registry.registry_cache as rc

    _reset_cache(monkeypatch)
    rc.store_cache({"222": {"discord_id": "222", "discord_name": "Bob", "accounts": {}}})
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)

    _patch_dal(monkeypatch, by_discord=[], by_governor=None, insert_result=(0, "OK"))
    svc.admin_register_or_replace(
        target_discord_user_id=222,
        target_discord_name="Bob",
        account_type="Main",
        governor_id="9999999",
        governor_name="NewGov",
        admin_discord_id=1,
    )

    with rc._cache_lock:
        assert rc._cache_ts == 0.0


def test_failed_write_does_not_invalidate_cache(monkeypatch):
    """RC_DUPE_SLOT must NOT invalidate the cache."""
    import registry.registry_cache as rc

    _reset_cache(monkeypatch)
    rc.store_cache({"111": {"discord_id": "111", "discord_name": "Alice", "accounts": {}}})
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)

    _patch_dal(monkeypatch, insert_result=(1, "Slot already active"))
    svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )

    # cache_ts must NOT be 0 — cache should remain populated
    with rc._cache_lock:
        assert rc._cache_ts != 0.0, "cache must remain populated after a failed write"
