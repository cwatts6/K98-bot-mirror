from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import (
    ArkSchedulerState,
    _post_initial_registration,
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
    called = {"lock": False, "ensure": False, "auto_create": False}
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

    async def _list_completed():
        return []

    async def _lock(*_a, **_k):
        called["lock"] = True

    async def _ensure(*_a, **_k):
        called["ensure"] = True

    async def _run_match_dispatch(*_a, **_k):
        return None

    async def _auto_create(**_kwargs):
        called["auto_create"] = True
        return type(
            "R",
            (),
            {
                "scanned": 1,
                "created": 0,
                "existing": 0,
                "skipped_cancelled_match": 0,
                "invalid_title": 0,
                "errors": 0,
            },
        )()

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.list_completed_matches_pending_completion", _list_completed
    )
    monkeypatch.setattr("ark.ark_scheduler.lock_match_and_post_confirmation", _lock)
    monkeypatch.setattr("ark.ark_scheduler.ensure_confirmation_message", _ensure)
    monkeypatch.setattr("ark.ark_scheduler.sync_ark_matches_from_calendar", _auto_create)
    monkeypatch.setattr("ark.ark_scheduler._run_match_reminder_dispatch", _run_match_dispatch)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert called["lock"] is False
    assert called["ensure"] is True
    assert called["auto_create"] is True


@pytest.mark.asyncio
async def test_scheduler_updates_match_complete_immediately(monkeypatch):
    called = {"complete": False, "mark": False}
    now = datetime(2026, 3, 7, 12, 0, tzinfo=UTC)
    match_dt = now - timedelta(hours=2)

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return []

    async def _list_completed():
        return [
            {
                "MatchId": 42,
                "Alliance": "K98",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": now - timedelta(days=1),
                "Status": "Completed",
            }
        ]

    async def _ensure(*_a, **_k):
        called["complete"] = True
        return True

    async def _mark(_mid):
        called["mark"] = True
        return True

    async def _auto_create(**_kwargs):
        return type(
            "R",
            (),
            {
                "scanned": 0,
                "created": 0,
                "existing": 0,
                "skipped_cancelled_match": 0,
                "invalid_title": 0,
                "errors": 0,
            },
        )()

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.list_completed_matches_pending_completion", _list_completed
    )
    monkeypatch.setattr("ark.ark_scheduler.ensure_confirmation_message", _ensure)
    monkeypatch.setattr("ark.ark_scheduler.mark_match_completion_posted", _mark)
    monkeypatch.setattr("ark.ark_scheduler.sync_ark_matches_from_calendar", _auto_create)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert called["complete"] is True
    assert called["mark"] is True


@pytest.mark.asyncio
async def test_scheduler_schedules_match_complete(monkeypatch):
    scheduled = {"key": None, "when": None}
    now = datetime(2026, 3, 7, 10, 0, tzinfo=UTC)
    match_dt = now + timedelta(minutes=30)
    complete_at = match_dt + timedelta(hours=1)

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return []

    async def _list_completed():
        return [
            {
                "MatchId": 99,
                "Alliance": "K98",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": now - timedelta(days=1),
                "Status": "Completed",
            }
        ]

    async def _schedule_once(*, state, key, when, coro_factory):
        scheduled["key"] = key
        scheduled["when"] = when

    async def _auto_create(**_kwargs):
        return type(
            "R",
            (),
            {
                "scanned": 0,
                "created": 0,
                "existing": 0,
                "skipped_cancelled_match": 0,
                "invalid_title": 0,
                "errors": 0,
            },
        )()

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.list_completed_matches_pending_completion", _list_completed
    )
    monkeypatch.setattr("ark.ark_scheduler._schedule_once", _schedule_once)
    monkeypatch.setattr("ark.ark_scheduler.sync_ark_matches_from_calendar", _auto_create)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert scheduled["key"] == _task_key(99, "complete")
    assert scheduled["when"] == complete_at


def _make_auto_create_result():
    return type(
        "AutoCreateResult",
        (),
        {
            "scanned": 0,
            "created": 0,
            "existing": 0,
            "skipped_cancelled_match": 0,
            "invalid_title": 0,
            "errors": 0,
        },
    )()


@pytest.mark.asyncio
async def test_scheduler_schedules_reg_post_for_future_scheduled_match(monkeypatch):
    """Scheduler schedules reg_post task at match_dt when no registration message exists yet."""
    scheduled = {}
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    match_dt = now + timedelta(days=12)  # future event

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return [
            {
                "MatchId": 20,
                "Alliance": "k98A",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": match_dt - timedelta(days=1),
                "Status": "Scheduled",
                "RegistrationMessageId": None,
                "RegistrationChannelId": None,
            }
        ]

    async def _list_completed():
        return []

    async def _schedule_once_stub(*, state, key, when, coro_factory):
        scheduled[key] = when

    async def _run_match_dispatch(*_a, **_k):
        return None

    async def _auto_create(**_kwargs):
        return _make_auto_create_result()

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.list_completed_matches_pending_completion", _list_completed
    )
    monkeypatch.setattr("ark.ark_scheduler._schedule_once", _schedule_once_stub)
    monkeypatch.setattr("ark.ark_scheduler.sync_ark_matches_from_calendar", _auto_create)
    monkeypatch.setattr("ark.ark_scheduler._run_match_reminder_dispatch", _run_match_dispatch)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert _task_key(20, "reg_post") in scheduled
    assert scheduled[_task_key(20, "reg_post")] == match_dt


@pytest.mark.asyncio
async def test_scheduler_posts_reg_immediately_when_match_dt_passed(monkeypatch):
    """Scheduler posts registration immediately if match_dt is already past and no message exists."""
    called = {"reg_post": False}
    now = datetime(2026, 4, 4, 21, 0, tzinfo=UTC)
    match_dt = now - timedelta(hours=1)  # match_dt is in the past

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return [
            {
                "MatchId": 20,
                "Alliance": "k98A",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": match_dt + timedelta(hours=2),
                "Status": "Scheduled",
                "RegistrationMessageId": None,
                "RegistrationChannelId": None,
            }
        ]

    async def _list_completed():
        return []

    async def _post_initial_reg(**_kw):
        called["reg_post"] = True

    async def _run_match_dispatch(*_a, **_k):
        return None

    async def _auto_create(**_kwargs):
        return _make_auto_create_result()

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.list_completed_matches_pending_completion", _list_completed
    )
    monkeypatch.setattr("ark.ark_scheduler._post_initial_registration", _post_initial_reg)
    monkeypatch.setattr("ark.ark_scheduler.sync_ark_matches_from_calendar", _auto_create)
    monkeypatch.setattr("ark.ark_scheduler._run_match_reminder_dispatch", _run_match_dispatch)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert called["reg_post"] is True


@pytest.mark.asyncio
async def test_scheduler_skips_reg_post_when_message_already_exists(monkeypatch):
    """Scheduler does not schedule or call reg_post when RegistrationMessageId is already set."""
    scheduled = {}
    called = {"reg_post": False}
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    match_dt = now + timedelta(days=12)

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return [
            {
                "MatchId": 20,
                "Alliance": "k98A",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": match_dt - timedelta(days=1),
                "Status": "Scheduled",
                "RegistrationMessageId": 99999,
                "RegistrationChannelId": 11111,
            }
        ]

    async def _list_completed():
        return []

    async def _schedule_once_stub(*, state, key, when, coro_factory):
        scheduled[key] = when

    async def _post_initial_reg(**_kw):
        called["reg_post"] = True

    async def _run_match_dispatch(*_a, **_k):
        return None

    async def _auto_create(**_kwargs):
        return _make_auto_create_result()

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler._utcnow", lambda: now)
    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.list_completed_matches_pending_completion", _list_completed
    )
    monkeypatch.setattr("ark.ark_scheduler._schedule_once", _schedule_once_stub)
    monkeypatch.setattr("ark.ark_scheduler._post_initial_registration", _post_initial_reg)
    monkeypatch.setattr("ark.ark_scheduler.sync_ark_matches_from_calendar", _auto_create)
    monkeypatch.setattr("ark.ark_scheduler._run_match_reminder_dispatch", _run_match_dispatch)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert _task_key(20, "reg_post") not in scheduled
    assert called["reg_post"] is False


@pytest.mark.asyncio
async def test_post_initial_registration_calls_ensure_with_announce_true(monkeypatch):
    """_post_initial_registration calls ensure_registration_message with announce=True."""
    import ark.ark_scheduler as sched

    captured = {}

    async def _get_match(_mid):
        return {
            "MatchId": 20,
            "Alliance": "k98A",
            "RegistrationMessageId": None,
        }

    async def _get_alliance(_alliance):
        return {"RegistrationChannelId": 111}

    class _Controller:
        def __init__(self, *, match_id, config):
            captured["match_id"] = match_id

        async def ensure_registration_message(self, **kwargs):
            captured["kwargs"] = kwargs
            return type("Ref", (), {"channel_id": 111, "message_id": 999})()

    monkeypatch.setattr(sched, "get_match", _get_match)
    monkeypatch.setattr(sched, "get_alliance", _get_alliance)
    monkeypatch.setattr(sched, "ArkRegistrationController", _Controller)

    await _post_initial_registration(
        client=DummyClient(),
        match_id=20,
        config={"PlayersCap": 30, "SubsCap": 15},
    )

    assert captured["kwargs"]["announce"] is True
    assert captured["kwargs"]["force_announce"] is False
    assert captured["kwargs"]["target_channel_id"] == 111


@pytest.mark.asyncio
async def test_post_initial_registration_skips_if_already_posted(monkeypatch):
    """_post_initial_registration is a no-op when RegistrationMessageId is already set."""
    import ark.ark_scheduler as sched

    called = {"controller": False}

    async def _get_match(_mid):
        return {
            "MatchId": 20,
            "Alliance": "k98A",
            "RegistrationMessageId": 88888,
        }

    class _Controller:
        def __init__(self, **_kw):
            called["controller"] = True

    monkeypatch.setattr(sched, "get_match", _get_match)
    monkeypatch.setattr(sched, "ArkRegistrationController", _Controller)

    await _post_initial_registration(
        client=DummyClient(),
        match_id=20,
        config={"PlayersCap": 30, "SubsCap": 15},
    )

    assert called["controller"] is False
