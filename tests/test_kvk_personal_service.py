from __future__ import annotations

import types

import pytest


class DummyChannel:
    def __init__(self, fail=False, forbidden=False):
        self.sent = []
        self._fail = fail
        self._forbidden = forbidden
        self.id = 999

    async def send(self, *args, **kwargs):
        if self._forbidden:
            import discord  # architecture-check: allow

            raise discord.Forbidden(  # architecture-check: allow
                types.SimpleNamespace(status=403), "no perms"
            )
        if self._fail:
            raise RuntimeError("channel send failed")
        self.sent.append({"args": args, "kwargs": kwargs})
        return types.SimpleNamespace(id="msg")

    @property
    def guild(self):
        return None


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


@pytest.mark.asyncio
async def test_load_last_kvk_map_cold_cache(monkeypatch):
    import stats_cache_helpers

    async def fake_load():
        return {}

    monkeypatch.setattr(stats_cache_helpers, "load_last_kvk_map", fake_load)

    from services import kvk_personal_service

    result = await kvk_personal_service.load_last_kvk_map()
    assert isinstance(result, dict)
    assert result == {}


@pytest.mark.asyncio
async def test_post_stats_embeds_orig_channel_succeeds():
    import unittest.mock as mock

    import bot_config

    channel = DummyChannel()
    ctx = DummyCtx(channel=channel)
    bot = DummyBot()

    with (
        mock.patch.object(bot_config, "KVK_PLAYER_STATS_CHANNEL_ID", 50),
        mock.patch.object(bot_config, "NOTIFY_CHANNEL_ID", 51),
    ):
        from commands import kvk_personal_posting

        posted, used = await kvk_personal_posting.post_stats_embeds(
            bot, ctx, [types.SimpleNamespace()], None
        )

    assert posted is True
    assert used == "orig_channel"
    assert channel.sent


@pytest.mark.asyncio
async def test_post_stats_embeds_orig_fails_kvk_succeeds():
    import unittest.mock as mock

    import bot_config

    orig_ch = DummyChannel(fail=True)
    kvk_ch = DummyChannel()
    ctx = DummyCtx(channel=orig_ch)
    bot = DummyBot(channels={50: kvk_ch})

    with (
        mock.patch.object(bot_config, "KVK_PLAYER_STATS_CHANNEL_ID", 50),
        mock.patch.object(bot_config, "NOTIFY_CHANNEL_ID", 51),
    ):
        from commands import kvk_personal_posting

        posted, used = await kvk_personal_posting.post_stats_embeds(
            bot, ctx, [types.SimpleNamespace()], None
        )

    assert posted is True
    assert used == "kvk_channel"
    assert kvk_ch.sent


@pytest.mark.asyncio
async def test_post_stats_embeds_all_fail_dm_attempted():
    import unittest.mock as mock

    import bot_config

    orig_ch = DummyChannel(fail=True)
    user = DummyUser()
    ctx = DummyCtx(channel=orig_ch, user=user)
    bot = DummyBot()

    with (
        mock.patch.object(bot_config, "KVK_PLAYER_STATS_CHANNEL_ID", 50),
        mock.patch.object(bot_config, "NOTIFY_CHANNEL_ID", 51),
    ):
        from commands import kvk_personal_posting

        posted, used = await kvk_personal_posting.post_stats_embeds(
            bot, ctx, [types.SimpleNamespace()], None
        )

    assert posted is True
    assert used == "dm"
    assert user.sent
