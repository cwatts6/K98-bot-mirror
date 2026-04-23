"""Tests for services/kvk_personal_stats_service.py"""
from __future__ import annotations

import os
import sys
import types

import pytest

pytestmark = pytest.mark.asyncio

os.environ.setdefault("OUR_KINGDOM", "1234")


def _ensure_service_importable():
    """Stub any heavy deps that might be pulled in transitively."""
    stubs = [
        "pyodbc",
        "gspread",
        "google", "google.auth", "google.auth.transport",
        "google.auth.transport.requests", "google.oauth2",
        "google.oauth2.service_account", "googleapiclient",
        "googleapiclient.discovery",
        "rapidfuzz", "rapidfuzz.fuzz", "rapidfuzz.process",
        "unidecode", "pandas",
    ]
    for mod in stubs:
        if mod not in sys.modules:
            m = types.ModuleType(mod)
            sys.modules[mod] = m


_ensure_service_importable()


# ---------------------------------------------------------------------------
# resolve_governor_accounts tests
# ---------------------------------------------------------------------------

async def test_resolve_manual_valid():
    from services.kvk_personal_stats_service import resolve_governor_accounts

    result = await resolve_governor_accounts(user_id=1, manual_governor_id="12345")
    assert result["mode"] == "manual"
    assert result["governor_id"] == "12345"
    assert result["accounts"] == []


async def test_resolve_manual_invalid():
    from services.kvk_personal_stats_service import resolve_governor_accounts

    result = await resolve_governor_accounts(user_id=1, manual_governor_id="not-a-number")
    assert result["mode"] == "none"
    assert result["governor_id"] is None


async def test_resolve_no_accounts():
    from services.kvk_personal_stats_service import resolve_governor_accounts

    registry = {"1": {"accounts": {}}}
    result = await resolve_governor_accounts(user_id=1, registry=registry)
    assert result["mode"] == "none"


async def test_resolve_single_account():
    from services.kvk_personal_stats_service import resolve_governor_accounts

    registry = {"1": {"accounts": {"Main": {"GovernorID": "999"}}}}
    result = await resolve_governor_accounts(user_id=1, registry=registry)
    assert result["mode"] == "single"
    assert len(result["accounts"]) == 1


async def test_resolve_multi_account():
    from services.kvk_personal_stats_service import resolve_governor_accounts

    registry = {
        "1": {
            "accounts": {
                "Main": {"GovernorID": "1"},
                "Alt 1": {"GovernorID": "2"},
            }
        }
    }
    result = await resolve_governor_accounts(user_id=1, registry=registry)
    assert result["mode"] == "multi"
    assert len(result["accounts"]) == 2


# ---------------------------------------------------------------------------
# load_target_data tests
# ---------------------------------------------------------------------------

async def test_load_target_data_success(monkeypatch):
    from services import kvk_personal_stats_service as svc

    async def fake_run_target_lookup(gid):
        return {"status": "found", "data": {"GovernorID": gid}}

    fake_target_utils = types.ModuleType("target_utils")
    fake_target_utils.run_target_lookup = fake_run_target_lookup
    monkeypatch.setitem(sys.modules, "target_utils", fake_target_utils)

    result = await svc.load_target_data("12345")
    assert result is not None
    assert result["status"] == "found"


async def test_load_target_data_failure(monkeypatch):
    from services import kvk_personal_stats_service as svc

    async def bad_lookup(gid):
        raise RuntimeError("DB down")

    fake_target_utils = types.ModuleType("target_utils")
    fake_target_utils.run_target_lookup = bad_lookup
    monkeypatch.setitem(sys.modules, "target_utils", fake_target_utils)

    result = await svc.load_target_data("12345")
    assert result is None


# ---------------------------------------------------------------------------
# load_stats_data tests
# ---------------------------------------------------------------------------

async def test_load_stats_data_cache_hit(monkeypatch):
    from services import kvk_personal_stats_service as svc

    fake_utils = types.ModuleType("utils")
    fake_utils.load_stat_row = lambda gid: {"GovernorID": gid, "kills": 1000}
    monkeypatch.setitem(sys.modules, "utils", fake_utils)

    async def fake_load_last_kvk_map():
        return {"99999": {"last_kills": 500}}

    fake_cache_helpers = types.ModuleType("stats_cache_helpers")
    fake_cache_helpers.load_last_kvk_map = fake_load_last_kvk_map
    monkeypatch.setitem(sys.modules, "stats_cache_helpers", fake_cache_helpers)

    result = await svc.load_stats_data("99999")
    assert result["row"] is not None
    assert result["row"]["GovernorID"] == "99999"
    assert isinstance(result["last_kvk_map"], dict)


async def test_load_stats_data_cache_miss(monkeypatch):
    from services import kvk_personal_stats_service as svc

    fake_utils = types.ModuleType("utils")
    fake_utils.load_stat_row = lambda gid: None
    monkeypatch.setitem(sys.modules, "stats_cache_helpers", fake_utils)

    async def fake_load_last_kvk_map():
        return {}

    fake_cache_helpers = types.ModuleType("stats_cache_helpers")
    fake_cache_helpers.load_last_kvk_map = fake_load_last_kvk_map
    monkeypatch.setitem(sys.modules, "stats_cache_helpers", fake_cache_helpers)

    fake_utils2 = types.ModuleType("utils")
    fake_utils2.load_stat_row = lambda gid: None
    monkeypatch.setitem(sys.modules, "utils", fake_utils2)

    result = await svc.load_stats_data("00000")
    assert result["row"] is None
    assert result["last_kvk_map"] == {}


# ---------------------------------------------------------------------------
# decide_post_channel tests
# ---------------------------------------------------------------------------

def test_decide_post_channel_no_guild():
    from services.kvk_personal_stats_service import decide_post_channel

    result = decide_post_channel(None, ["1234", "5678"])
    assert result is None


def test_decide_post_channel_first_match():
    from services.kvk_personal_stats_service import decide_post_channel

    fake_channel = types.SimpleNamespace(id=1234)

    class FakeGuild:
        def get_channel(self, cid):
            if cid == 1234:
                return fake_channel
            return None

    result = decide_post_channel(FakeGuild(), [1234, 5678])
    assert result is fake_channel


def test_decide_post_channel_fallback():
    from services.kvk_personal_stats_service import decide_post_channel

    fake_channel = types.SimpleNamespace(id=5678)

    class FakeGuild:
        def get_channel(self, cid):
            if cid == 5678:
                return fake_channel
            return None

    result = decide_post_channel(FakeGuild(), [1234, 5678])
    assert result is fake_channel


def test_decide_post_channel_none_found():
    from services.kvk_personal_stats_service import decide_post_channel

    class FakeGuild:
        def get_channel(self, cid):
            return None

    result = decide_post_channel(FakeGuild(), [1234, 5678])
    assert result is None
