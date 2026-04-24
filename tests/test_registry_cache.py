# tests/test_registry_cache.py
"""
Unit tests for registry.registry_cache — in-process TTL cache.

All tests use monkeypatch to isolate module-level state and control time.monotonic().
No SQL connection required.
"""

from __future__ import annotations

import logging
import time

import pytest

import registry.registry_cache as rc
import registry.registry_service as svc
import registry.dal.registry_dal as dal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_cache(monkeypatch):
    """Reset the registry cache to a clean, unpopulated state."""
    monkeypatch.setattr(rc, "_cache_data", None)
    monkeypatch.setattr(rc, "_cache_ts", 0.0)
    monkeypatch.setattr(rc, "_last_invalidation_reason", "test_reset")
    monkeypatch.setattr(rc, "_CACHE_TTL", 45.0)


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


_ACTIVE_ROW = [
    {
        "DiscordUserID": 111,
        "DiscordName": "Alice",
        "GovernorID": 2441482,
        "GovernorName": "Chrislos",
        "AccountType": "Main",
    }
]

_SAMPLE_DICT = {
    "111": {
        "discord_id": "111",
        "discord_name": "Alice",
        "accounts": {
            "Main": {"GovernorID": "2441482", "GovernorName": "Chrislos"},
        },
    }
}

_EXISTING_SLOT = [{"AccountType": "Main", "GovernorID": 2441482, "DiscordUserID": 111}]


# ---------------------------------------------------------------------------
# Basic cache module API tests
# ---------------------------------------------------------------------------


def test_get_cached_or_none_returns_none_when_empty(monkeypatch):
    _reset_cache(monkeypatch)
    assert rc.get_cached_or_none() is None


def test_store_and_retrieve_within_ttl(monkeypatch):
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)
    result = rc.get_cached_or_none()
    assert result is not None
    assert "111" in result


def test_get_cached_or_none_returns_none_after_ttl(monkeypatch):
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 0.001)  # 1ms TTL
    rc.store_cache(_SAMPLE_DICT)
    time.sleep(0.02)  # exceed TTL
    assert rc.get_cached_or_none() is None


def test_invalidate_clears_cache(monkeypatch):
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)
    assert rc.get_cached_or_none() is not None
    rc.invalidate(reason="test")
    assert rc.get_cached_or_none() is None


def test_deep_copy_on_store(monkeypatch):
    """Mutating stored data should not affect cached state."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    data = {"111": {"discord_id": "111", "discord_name": "Alice", "accounts": {}}}
    rc.store_cache(data)
    data["111"]["discord_name"] = "MUTATED"
    result = rc.get_cached_or_none()
    assert result is not None
    assert result["111"]["discord_name"] == "Alice"


def test_deep_copy_on_get(monkeypatch):
    """Mutating the returned dict must not affect cached state."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)
    result = rc.get_cached_or_none()
    assert result is not None
    result["111"]["discord_name"] = "MUTATED"
    # Retrieve again — must be unaffected
    result2 = rc.get_cached_or_none()
    assert result2 is not None
    assert result2["111"]["discord_name"] == "Alice"


def test_get_info_keys(monkeypatch):
    _reset_cache(monkeypatch)
    info = rc.get_info()
    assert "populated" in info
    assert "age_seconds" in info
    assert "ttl_seconds" in info
    assert "last_invalidation_reason" in info


def test_get_info_populated_false_when_empty(monkeypatch):
    _reset_cache(monkeypatch)
    info = rc.get_info()
    assert info["populated"] is False
    assert info["age_seconds"] is None


def test_get_info_populated_true_when_stored(monkeypatch):
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)
    info = rc.get_info()
    assert info["populated"] is True
    assert info["age_seconds"] is not None
    assert info["age_seconds"] >= 0.0


def test_get_info_last_invalidation_reason(monkeypatch):
    _reset_cache(monkeypatch)
    rc.invalidate(reason="my_test_reason")
    info = rc.get_info()
    assert info["last_invalidation_reason"] == "my_test_reason"


def test_invalidate_logs_info(monkeypatch, caplog):
    _reset_cache(monkeypatch)
    with caplog.at_level(logging.INFO, logger="registry.registry_cache"):
        rc.invalidate(reason="log_test")
    assert "log_test" in caplog.text


# ---------------------------------------------------------------------------
# Integration tests via registry_service.load_registry_as_dict()
# ---------------------------------------------------------------------------


def test_first_call_misses_cache_dal_called_once(monkeypatch):
    """First load_registry_as_dict call hits SQL (cache miss)."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    call_count = []

    def _fake_all_active():
        call_count.append(1)
        return _ACTIVE_ROW

    monkeypatch.setattr(dal, "get_all_active", _fake_all_active)
    svc.load_registry_as_dict()
    assert len(call_count) == 1


def test_second_call_within_ttl_hits_cache(monkeypatch):
    """Second call within TTL must NOT call the DAL again."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    call_count = []

    def _fake_all_active():
        call_count.append(1)
        return _ACTIVE_ROW

    monkeypatch.setattr(dal, "get_all_active", _fake_all_active)
    svc.load_registry_as_dict()
    svc.load_registry_as_dict()
    assert len(call_count) == 1, f"Expected 1 DAL call, got {len(call_count)}"


def test_call_after_ttl_expiry_hits_sql(monkeypatch):
    """Call after TTL expiry must call the DAL again."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 0.001)  # 1ms
    call_count = []

    def _fake_all_active():
        call_count.append(1)
        return _ACTIVE_ROW

    monkeypatch.setattr(dal, "get_all_active", _fake_all_active)
    svc.load_registry_as_dict()
    time.sleep(0.02)  # exceed TTL
    svc.load_registry_as_dict()
    assert len(call_count) == 2, f"Expected 2 DAL calls after TTL expiry, got {len(call_count)}"


def test_invalidate_forces_reload(monkeypatch):
    """After invalidate(), next call must reload from SQL even within TTL."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    call_count = []

    def _fake_all_active():
        call_count.append(1)
        return _ACTIVE_ROW

    monkeypatch.setattr(dal, "get_all_active", _fake_all_active)
    svc.load_registry_as_dict()
    rc.invalidate(reason="test_forced_reload")
    svc.load_registry_as_dict()
    assert len(call_count) == 2


def test_register_governor_success_invalidates_cache(monkeypatch):
    """Successful register_governor() invalidates the cache."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)

    _patch_dal(monkeypatch, insert_result=(0, "Inserted"))

    svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )

    with rc._cache_lock:
        assert rc._cache_ts == 0.0


def test_modify_governor_success_invalidates_cache(monkeypatch):
    """Successful modify_governor() invalidates the cache."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)

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
    )

    with rc._cache_lock:
        assert rc._cache_ts == 0.0


def test_remove_governor_success_invalidates_cache(monkeypatch):
    """Successful remove_governor() invalidates the cache."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)

    _patch_dal(monkeypatch, soft_delete_result=(0, "Removed"))

    svc.remove_governor(discord_user_id=111, account_type="Main", removed_by=111)

    with rc._cache_lock:
        assert rc._cache_ts == 0.0


def test_admin_register_success_invalidates_cache(monkeypatch):
    """Successful admin_register_or_replace() invalidates the cache."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)

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


def test_failed_write_rc_dupe_slot_does_not_invalidate_cache(monkeypatch):
    """RC_DUPE_SLOT must NOT invalidate the cache."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    rc.store_cache(_SAMPLE_DICT)

    # Record the ts before the failed write
    with rc._cache_lock:
        ts_before = rc._cache_ts

    _patch_dal(monkeypatch, insert_result=(1, "Slot already active"))

    svc.register_governor(
        discord_user_id=111,
        discord_name="Alice",
        account_type="Main",
        governor_id="2441482",
        governor_name="Chrislos",
    )

    with rc._cache_lock:
        assert rc._cache_ts == ts_before, "cache must NOT be invalidated after RC_DUPE_SLOT"


def test_sql_failure_with_stale_cache_allow_stale_true(monkeypatch, caplog):
    """SQL failure with populated cache + allow_stale_on_error=True → stale returned, WARNING logged."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 0.001)  # Let TTL expire to simulate stale state

    # First populate the cache
    monkeypatch.setattr(dal, "get_all_active", lambda: _ACTIVE_ROW)
    svc.load_registry_as_dict()

    # Now force TTL to 0 so get_cached_or_none returns None (cache miss path)
    # but _cache_data is still populated (stale)
    time.sleep(0.02)

    # Now make SQL fail
    monkeypatch.setattr(
        dal, "get_all_active", lambda: (_ for _ in ()).throw(RuntimeError("DB down"))
    )

    with caplog.at_level(logging.WARNING, logger="registry.registry_service"):
        result = svc.load_registry_as_dict(allow_stale_on_error=True)

    assert result is not None
    assert "111" in result
    assert "stale" in caplog.text.lower() or "warning" in caplog.text.lower() or caplog.records


def test_sql_failure_with_stale_cache_allow_stale_false(monkeypatch):
    """SQL failure with populated cache + allow_stale_on_error=False → raises."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 0.001)

    monkeypatch.setattr(dal, "get_all_active", lambda: _ACTIVE_ROW)
    svc.load_registry_as_dict()
    time.sleep(0.02)

    monkeypatch.setattr(
        dal, "get_all_active", lambda: (_ for _ in ()).throw(RuntimeError("DB down"))
    )

    with pytest.raises(RuntimeError, match="DB down"):
        svc.load_registry_as_dict(allow_stale_on_error=False)


def test_sql_failure_empty_cache_allow_stale_true_raises(monkeypatch):
    """SQL failure with empty cache + allow_stale_on_error=True → raises (nothing stale)."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(
        dal, "get_all_active", lambda: (_ for _ in ()).throw(RuntimeError("DB down"))
    )

    with pytest.raises(RuntimeError, match="DB down"):
        svc.load_registry_as_dict(allow_stale_on_error=True)


def test_caller_mutating_dict_does_not_affect_cache(monkeypatch):
    """Mutating the returned dict must not corrupt cached state."""
    _reset_cache(monkeypatch)
    monkeypatch.setattr(rc, "_CACHE_TTL", 9999.0)
    monkeypatch.setattr(dal, "get_all_active", lambda: _ACTIVE_ROW)

    result = svc.load_registry_as_dict()
    result["111"]["discord_name"] = "HACKED"

    result2 = svc.load_registry_as_dict()
    assert result2["111"]["discord_name"] == "Alice", (
        "Mutating the returned dict must not affect the cached state"
    )


def test_get_registry_cache_info_returns_expected_keys(monkeypatch):
    """get_registry_cache_info() must return the expected diagnostic keys."""
    _reset_cache(monkeypatch)
    info = svc.get_registry_cache_info()
    assert "populated" in info
    assert "age_seconds" in info
    assert "ttl_seconds" in info
    assert "last_invalidation_reason" in info
