from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from server_status.member_count_channel import (
    format_member_count_channel_name,
    update_member_count_channel_once,
)
from server_status.utc_clock_channel import (
    format_utc_clock_channel_name,
    update_utc_clock_channel_once,
)


def test_format_utc_clock_channel_name_uses_utc():
    dt = datetime(2026, 4, 28, 21, 0, tzinfo=UTC)
    assert format_utc_clock_channel_name(dt) == "Tue 28 Apr 21:00 UTC"


def test_format_member_count_channel_name():
    assert format_member_count_channel_name(2123) == "Members: 2,123"


@pytest.mark.asyncio
async def test_utc_clock_update_skips_unchanged_name(monkeypatch):
    fixed_dt = datetime(2026, 4, 28, 21, 30, tzinfo=UTC)
    monkeypatch.setattr("server_status.utc_clock_channel.SERVER_STATUS_ENABLED", True)
    monkeypatch.setattr("server_status.utc_clock_channel.UTC_CLOCK_CHANNEL_ID", 123)

    class _FakeDatetime:
        @staticmethod
        def now(tz=None):
            return fixed_dt

    monkeypatch.setattr("server_status.utc_clock_channel.datetime", _FakeDatetime)

    class Channel:
        name = format_utc_clock_channel_name(fixed_dt)

        async def edit(self, **_kwargs):
            raise AssertionError("edit should not be called for unchanged channel name")

    bot = SimpleNamespace(get_channel=lambda _cid: Channel())
    assert await update_utc_clock_channel_once(bot) is False


@pytest.mark.asyncio
async def test_member_count_update_renames_when_changed(monkeypatch):
    monkeypatch.setattr("server_status.member_count_channel.SERVER_STATUS_ENABLED", True)
    monkeypatch.setattr("server_status.member_count_channel.MEMBER_COUNT_CHANNEL_ID", 456)

    calls = []

    class Channel:
        name = "Members: 1"
        guild = SimpleNamespace(member_count=2123)

        async def edit(self, **kwargs):
            calls.append(kwargs)
            self.name = kwargs["name"]

    bot = SimpleNamespace(get_channel=lambda _cid: Channel())
    assert await update_member_count_channel_once(bot) is True
    assert calls[0]["name"] == "Members: 2,123"
