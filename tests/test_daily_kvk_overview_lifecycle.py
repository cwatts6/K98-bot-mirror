from __future__ import annotations

import pytest

import daily_KVK_overview_embed as overview


@pytest.mark.asyncio
async def test_daily_overview_is_removed_outside_broad_kvk_window(monkeypatch) -> None:
    removed: list[tuple[object, int]] = []

    async def remove(bot, channel_id):
        removed.append((bot, channel_id))

    monkeypatch.setattr(overview, "is_currently_kvk", lambda: False)
    monkeypatch.setattr(overview, "remove_daily_KVK_overview_embed", remove)
    bot = object()

    await overview.post_or_update_daily_KVK_overview(bot, 123)

    assert removed == [(bot, 123)]


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
