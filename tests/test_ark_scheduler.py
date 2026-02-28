from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import (
    ArkSchedulerState,
    _schedule_once,
    _task_key,
    ensure_confirmation_message,
    schedule_ark_lifecycle,
)


class DummyClient:
    guild_id = 123456789012345678

    def get_channel(self, _cid):
        class _Channel:
            async def send(self, *_a, **_k):
                class _Msg:
                    id = 100
                    channel = type("C", (), {"id": 200})()

                return _Msg()

        return _Channel()

    def get_user(self, _uid):
        return None

    async def fetch_user(self, _uid):
        class _U:
            async def send(self, _content):
                return None

        return _U()


@pytest.mark.asyncio
async def test_schedule_once_runs_immediately(monkeypatch):
    state = ArkSchedulerState()
    called = {"ran": False}

    async def _noop_sleep(_):
        return None

    async def _work():
        called["ran"] = True

    monkeypatch.setattr("ark.ark_scheduler._sleep_until", _noop_sleep)

    when = datetime.now(UTC) - timedelta(seconds=1)
    await _schedule_once(
        state=state,
        key=_task_key(1, "lock"),
        when=when,
        coro_factory=_work,
    )

    task = state.tasks[_task_key(1, "lock")]
    await task

    assert called["ran"] is True
    assert _task_key(1, "lock") not in state.tasks


@pytest.mark.asyncio
async def test_check_in_activation_refreshes_confirmation(monkeypatch):
    called = {"refresh": False}

    async def _get_match(match_id):
        return {
            "MatchId": 5,
            "Alliance": "K98",
            "ArkWeekendDate": datetime(2026, 3, 7, tzinfo=UTC).date(),
            "MatchDay": "Sat",
            "MatchTimeUtc": datetime(2026, 3, 7, 11, 0, tzinfo=UTC).time(),
            "SignupCloseUtc": datetime.now(UTC) + timedelta(hours=1),
            "Status": "Locked",
        }

    async def _get_alliance(_alliance):
        return {"ConfirmationChannelId": 123}

    async def _refresh(*_a, **_k):
        called["refresh"] = True
        return True

    monkeypatch.setattr("ark.ark_scheduler.get_match", _get_match)
    monkeypatch.setattr("ark.ark_scheduler.get_alliance", _get_alliance)
    monkeypatch.setattr(
        "ark.ark_scheduler.ArkConfirmationController.refresh_confirmation_message", _refresh
    )

    ok = await ensure_confirmation_message(
        client=DummyClient(),
        match_id=5,
        config={"PlayersCap": 30, "SubsCap": 15},
        show_check_in=True,
    )

    assert ok is True
    assert called["refresh"] is True


@pytest.mark.asyncio
async def test_scheduler_does_not_relock_locked_matches(monkeypatch):
    called = {"lock": False, "ensure": False}
    now = datetime.now(UTC)
    match_dt = now + timedelta(hours=1)

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return [
            {
                "MatchId": 7,
                "Alliance": "K98",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": now + timedelta(hours=2),
                "Status": "Locked",
            }
        ]

    async def _lock(*_a, **_k):
        called["lock"] = True

    async def _ensure(*_a, **_k):
        called["ensure"] = True

    async def _run_match_dispatch(*_a, **_k):
        return None

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr("ark.ark_scheduler.lock_match_and_post_confirmation", _lock)
    monkeypatch.setattr("ark.ark_scheduler.ensure_confirmation_message", _ensure)
    monkeypatch.setattr("ark.ark_scheduler._run_match_reminder_dispatch", _run_match_dispatch)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert called["lock"] is False
    assert called["ensure"] is True
