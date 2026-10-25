from __future__ import annotations

import pytest

from core import event_rehydration_lifecycle as lifecycle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "available,stale,status,expected",
    [
        (True, False, "refreshed", 0),
        (True, True, "refreshed", 1),
        (False, False, "pending", 1),
        (False, True, "failed", 1),
    ],
)
async def test_cache_startup_observes_one_owner(monkeypatch, available, stale, status, expected):
    from types import SimpleNamespace

    calls = []

    async def load(_bot):
        return {"original"}

    async def refresh(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status=status)

    monkeypatch.setattr(lifecycle, "load_active_reminders", load)
    monkeypatch.setattr(lifecycle, "load_event_cache", lambda: None)
    monkeypatch.setattr(lifecycle, "is_cache_stale", lambda: stale)
    monkeypatch.setattr(
        lifecycle,
        "get_upcoming_event_cache_snapshot",
        lambda: SimpleNamespace(ok=available, events=(), stale=stale, persistence="saved"),
    )
    monkeypatch.setattr(lifecycle, "refresh_event_cache_result", refresh)
    loaded = await lifecycle.run_ready_event_cache_rehydration(
        bot=object(), schedule_bg=lambda *a, **kw: pytest.fail("second refresh scheduled")
    )
    assert loaded == {"original"}
    assert calls == [{"observation_seconds": 10.0}] * expected


@pytest.mark.asyncio
async def test_empty_loaded_snapshot_is_ready_without_provider(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        lifecycle, "get_upcoming_event_cache_snapshot", lambda: SimpleNamespace(ok=True, events=())
    )
    assert await lifecycle.wait_for_events(1)


@pytest.mark.asyncio
async def test_ready_view_rehydration_helpers_schedule_expected_tasks(monkeypatch):
    calls: list[tuple[str, float]] = []

    def fake_schedule_bg(name, timeout, coro_factory, **observation):
        calls.append((name, timeout))
        assert callable(coro_factory)
        if name == "rehydrate_tracked_views":
            assert observation["cancel_on_deadline"] is False
            assert observation["completion_check"] is lifecycle.restoration_completion
        else:
            assert not observation

    await lifecycle.run_ready_tracked_view_rehydration(bot=object(), schedule_bg=fake_schedule_bg)
    await lifecycle.run_ready_pinned_calendar_rehydration(
        bot=object(), schedule_bg=fake_schedule_bg
    )

    assert calls == [
        ("rehydrate_tracked_views", 10.0),
        ("rehydrate_vote_post_views", 10.0),
        ("rehydrate_survey_post_views", 10.0),
        ("rehydrate_pinned_calendar_view", 8.0),
    ]


@pytest.mark.asyncio
async def test_tracked_view_rehydration_schedule_failure_is_best_effort(caplog):
    def fail_schedule_bg(name, timeout, coro_factory, **observation):
        raise RuntimeError("scheduler unavailable")

    await lifecycle.run_ready_tracked_view_rehydration(
        bot=object(),
        schedule_bg=fail_schedule_bg,
    )

    assert "Failed to start rehydrate_tracked_views" in caplog.text


@pytest.mark.asyncio
async def test_pinned_calendar_rehydration_schedule_failure_is_best_effort(caplog):
    def fail_schedule_bg(name, timeout, coro_factory, **observation):
        raise RuntimeError("scheduler unavailable")

    await lifecycle.run_ready_pinned_calendar_rehydration(
        bot=object(),
        schedule_bg=fail_schedule_bg,
    )

    assert "failed to schedule pinned calendar rehydration" in caplog.text
