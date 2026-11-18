from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import daily_KVK_overview_embed as overview


@pytest.mark.asyncio
async def test_daily_overview_is_removed_outside_broad_kvk_window(monkeypatch) -> None:
    monkeypatch.setattr(overview, "is_currently_kvk", lambda: False)
    publish = AsyncMock(return_value="removed")
    monkeypatch.setattr(overview, "_publish_overview", publish)
    bot = object()

    assert await overview.post_or_update_daily_KVK_overview(bot, 123) == "removed"
    publish.assert_awaited_once_with(bot, 123, enabled=False)


@pytest.mark.asyncio
async def test_daily_overview_remains_enabled_inside_broad_window_before_pass4(
    monkeypatch,
) -> None:
    async def unexpected_remove(*_args):
        raise AssertionError("Daily overview must not be removed inside the broad KVK window.")

    monkeypatch.setattr(overview, "is_currently_kvk", lambda: True)
    monkeypatch.setattr(overview, "get_all_upcoming_events", lambda: [])
    monkeypatch.setattr(overview, "remove_daily_KVK_overview_embed", unexpected_remove)

    await overview.post_or_update_daily_KVK_overview(object(), 123)
