"""
tests/test_kvk_personal_service.py

Unit tests for services.kvk_personal_service.

Tests cover:
- resolve_user_accounts: happy path and registry load failure
- classify_accounts: single, multi, and no accounts
- load_last_kvk_map: cold cache safety
- post_stats_embeds: orig channel success, fallback to kvk channel, all fail → DM
"""

from __future__ import annotations

import asyncio
import types

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class DummyChannel:
    def __init__(self, fail=False, forbidden=False):
        self.sent = []
        self._fail = fail
        self._forbidden = forbidden
        self.id = 999

    async def send(self, *args, **kwargs):
        if self._forbidden:
            import discord

            raise discord.Forbidden(types.SimpleNamespace(status=403), "no perms")
        if self._fail:
            raise RuntimeError("channel send failed")
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="msg")

    @property
    def guild(self):
        return None  # simplifies _can_send check — no guild = True


class DummyUser:
    def __init__(self, uid=42):
        self.id = uid
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="dm")


class DummyCtx:
    def __init__(self, channel=None, user=None):
        self.channel = channel or DummyChannel()
        self.user = user or DummyUser()
        self.author = self.user


class DummyBot:
    def __init__(self, channels=None):
        self._channels = channels or {}

    def get_channel(self, cid):
        return self._channels.get(cid)

    class user:
        id = 1


# ---------------------------------------------------------------------------
# resolve_user_accounts
# ---------------------------------------------------------------------------



@pytest.mark.asyncio
async def test_resolve_user_accounts_happy_path(monkeypatch):
    """Returns the accounts dict for a known user."""
    fake_registry = {
        "42": {"accounts": {"Main": {"GovernorID": "999", "GovernorName": "X"}}}
    }

    def fake_load_registry():
        return fake_registry

    async def fake_to_thread(fn, *a, **kw):
        return fn(*a, **kw)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    import importlib
    import sys

    # Ensure fresh import for module-level patching
    mod_name = "registry.governor_registry"
    orig = sys.modules.get(mod_name)
    stub = types.ModuleType(mod_name)
    stub.load_registry = fake_load_registry
    sys.modules[mod_name] = stub
    try:
        from services import kvk_personal_service

        result = await kvk_personal_service.resolve_user_accounts(42)
        assert result == {"Main": {"GovernorID": "999", "GovernorName": "X"}}
    finally:
        if orig is not None:
            sys.modules[mod_name] = orig
        else:
            del sys.modules[mod_name]



@pytest.mark.asyncio
async def test_resolve_user_accounts_registry_failure(monkeypatch):
    """Registry load failure returns an empty dict."""

    async def fake_to_thread(fn, *a, **kw):
        raise RuntimeError("disk error")

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    from services import kvk_personal_service

    result = await kvk_personal_service.resolve_user_accounts(42)
    assert result == {}


# ---------------------------------------------------------------------------
# classify_accounts
# ---------------------------------------------------------------------------


def test_classify_accounts_no_accounts():
    from services import kvk_personal_service

    kind, gid = kvk_personal_service.classify_accounts({})
    assert kind == "none"
    assert gid is None


def test_classify_accounts_single_account():
    from services import kvk_personal_service

    accounts = {"Main": {"GovernorID": "123", "GovernorName": "Solo"}}
    kind, gid = kvk_personal_service.classify_accounts(accounts)
    assert kind == "single"
    assert gid == "123"


def test_classify_accounts_multi_account():
    from services import kvk_personal_service

    accounts = {
        "Main": {"GovernorID": "100", "GovernorName": "A"},
        "Alt 1": {"GovernorID": "200", "GovernorName": "B"},
    }
    kind, gid = kvk_personal_service.classify_accounts(accounts)
    assert kind == "multi"
    assert gid is None


def test_classify_accounts_empty_governor_ids():
    """Accounts with empty GovernorIDs should count as none."""
    from services import kvk_personal_service

    accounts = {
        "Main": {"GovernorID": "", "GovernorName": "Empty"},
        "Alt 1": {},
    }
    kind, gid = kvk_personal_service.classify_accounts(accounts)
    assert kind == "none"


# ---------------------------------------------------------------------------
# load_last_kvk_map — cold cache safety
# ---------------------------------------------------------------------------



@pytest.mark.asyncio
async def test_load_last_kvk_map_cold_cache(monkeypatch):
    """Returns an empty dict when cache is not warmed."""
    import stats_cache_helpers

    async def fake_load():
        return {}

    monkeypatch.setattr(stats_cache_helpers, "load_last_kvk_map", fake_load)

    from services import kvk_personal_service

    result = await kvk_personal_service.load_last_kvk_map()
    assert isinstance(result, dict)
    assert result == {}


# ---------------------------------------------------------------------------
# post_stats_embeds
# ---------------------------------------------------------------------------



@pytest.mark.asyncio
async def test_post_stats_embeds_orig_channel_succeeds():
    """Happy path: original channel succeeds — returns (True, 'orig_channel')."""
    import bot_config
    import unittest.mock as mock

    channel = DummyChannel()
    ctx = DummyCtx(channel=channel)
    bot = DummyBot()

    embeds = [types.SimpleNamespace()]
    file = None

    with mock.patch.object(bot_config, "KVK_PLAYER_STATS_CHANNEL_ID", 50), mock.patch.object(
        bot_config, "NOTIFY_CHANNEL_ID", 51
    ):
        from services import kvk_personal_service

        posted, used = await kvk_personal_service.post_stats_embeds(bot, ctx, embeds, file)

    assert posted is True
    assert used == "orig_channel"
    assert channel.sent  # message was sent to original channel



@pytest.mark.asyncio
async def test_post_stats_embeds_orig_fails_kvk_succeeds():
    """Orig channel fails → falls back to KVK_PLAYER_STATS_CHANNEL_ID."""
    import bot_config
    import unittest.mock as mock

    orig_ch = DummyChannel(fail=True)
    kvk_ch = DummyChannel()
    ctx = DummyCtx(channel=orig_ch)
    bot = DummyBot(channels={50: kvk_ch})

    embeds = [types.SimpleNamespace()]
    file = None

    with mock.patch.object(bot_config, "KVK_PLAYER_STATS_CHANNEL_ID", 50), mock.patch.object(
        bot_config, "NOTIFY_CHANNEL_ID", 51
    ):
        from services import kvk_personal_service

        posted, used = await kvk_personal_service.post_stats_embeds(bot, ctx, embeds, file)

    assert posted is True
    assert used == "kvk_channel"
    assert kvk_ch.sent



@pytest.mark.asyncio
async def test_post_stats_embeds_all_fail_dm_attempted():
    """All channels fail → DM attempted and result returned."""
    import bot_config
    import unittest.mock as mock

    orig_ch = DummyChannel(fail=True)
    user = DummyUser()
    ctx = DummyCtx(channel=orig_ch, user=user)
    bot = DummyBot()  # no channels registered → get_channel returns None

    embeds = [types.SimpleNamespace()]
    file = None

    with mock.patch.object(bot_config, "KVK_PLAYER_STATS_CHANNEL_ID", 50), mock.patch.object(
        bot_config, "NOTIFY_CHANNEL_ID", 51
    ):
        from services import kvk_personal_service

        posted, used = await kvk_personal_service.post_stats_embeds(bot, ctx, embeds, file)

    # DM was the last resort; user.sent should have been populated
    assert posted is True
    assert used == "dm"
    assert user.sent
