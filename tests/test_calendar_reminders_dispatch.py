from __future__ import annotations

from datetime import UTC, datetime, timedelta

import discord
import pytest

from event_calendar import reminders as mod


class _FakeUser:
    def __init__(self):
        self.sent: list[dict[str, object]] = []

    async def send(self, content: str = "", embed=None, **kwargs):
        self.sent.append(
            {
                "content": content,
                "embed": embed,
                "kwargs": kwargs,
            }
        )


class _FakeBot:
    def __init__(self, user=None, fetch_user_exc: Exception | None = None):
        self._user = user
        self._fetch_user_exc = fetch_user_exc

    def get_user(self, _user_id: int):
        return self._user

    async def fetch_user(self, _user_id: int):
        if self._fetch_user_exc:
            raise self._fetch_user_exc
        return self._user


class _FakeResponse:
    status = 404
    reason = "Not Found"
    text = "not found"


@pytest.fixture
def fixed_now(monkeypatch):
    now = datetime(2026, 3, 9, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(mod, "_now_utc", lambda: now)
    return now


def _event(instance_id: str, event_type: str, start: datetime):
    return {
        "instance_id": instance_id,
        "title": f"Event {instance_id}",
        "type": event_type,
        "start_utc": start.isoformat(),
        "end_utc": (start + timedelta(hours=1)).isoformat(),
    }


@pytest.mark.asyncio
async def test_dispatch_cache_unavailable(monkeypatch, fixed_now):
    monkeypatch.setattr(mod, "load_runtime_cache", lambda: {"ok": False, "events": []})
    bot = _FakeBot()
    out = await mod.dispatch_due_calendar_reminders(bot)
    assert out.ok is False
    assert out.status == "cache_unavailable"


@pytest.mark.asyncio
async def test_dispatch_no_due_reminders(monkeypatch, fixed_now):
    future = fixed_now + timedelta(days=30)
    cache_state = {"ok": True, "events": [_event("1", "raid", future)]}

    monkeypatch.setattr(mod, "load_runtime_cache", lambda: cache_state)
    monkeypatch.setattr(mod, "filter_events", lambda events, **_k: events)
    monkeypatch.setattr(mod, "list_event_types", lambda _c: ["raid"])
    monkeypatch.setattr(
        mod,
        "load_all_user_prefs",
        lambda: {"123": {"enabled": True, "by_event_type": {"all": ["all"]}}},
    )

    out = await mod.dispatch_due_calendar_reminders(_FakeBot())
    assert out.ok is True
    assert out.status == "no_due_reminders"


@pytest.mark.asyncio
async def test_dispatch_no_opted_in_users(monkeypatch, fixed_now):
    start = fixed_now + timedelta(hours=24)  # due for 24h reminder exactly now
    cache_state = {"ok": True, "events": [_event("1", "raid", start)]}

    monkeypatch.setattr(mod, "load_runtime_cache", lambda: cache_state)
    monkeypatch.setattr(mod, "filter_events", lambda events, **_k: events)
    monkeypatch.setattr(mod, "list_event_types", lambda _c: ["raid"])
    monkeypatch.setattr(mod, "load_all_user_prefs", lambda: {})

    out = await mod.dispatch_due_calendar_reminders(_FakeBot())
    assert out.ok is True
    assert out.status == "no_opted_in_users"


@pytest.mark.asyncio
async def test_dispatch_sends_and_dedupes(monkeypatch, fixed_now, tmp_path):
    start = fixed_now + timedelta(hours=24)  # 24h due now
    cache_state = {"ok": True, "events": [_event("evt-1", "raid", start)]}

    monkeypatch.setattr(mod, "load_runtime_cache", lambda: cache_state)
    monkeypatch.setattr(mod, "filter_events", lambda events, **_k: events)
    monkeypatch.setattr(mod, "list_event_types", lambda _c: ["raid"])
    monkeypatch.setattr(
        mod,
        "load_all_user_prefs",
        lambda: {"123": {"enabled": True, "by_event_type": {"raid": ["24h"]}}},
    )

    from event_calendar import reminder_state as rs_mod

    st_path = tmp_path / "state.json"
    monkeypatch.setattr(rs_mod, "DEFAULT_REMINDER_STATE_PATH", st_path)

    user = _FakeUser()
    bot = _FakeBot(user=user)

    out1 = await mod.dispatch_due_calendar_reminders(bot)
    assert out1.sent == 1
    assert len(user.sent) == 1

    out2 = await mod.dispatch_due_calendar_reminders(bot)
    assert out2.sent == 0
    assert out2.skipped_already_sent >= 1
    assert len(user.sent) == 1


@pytest.mark.asyncio
async def test_dispatch_dry_run_marks_sent(monkeypatch, fixed_now, tmp_path):
    start = fixed_now + timedelta(hours=24)
    cache_state = {"ok": True, "events": [_event("evt-2", "raid", start)]}

    monkeypatch.setattr(mod, "EVENT_CALENDAR_REMINDERS_DRY_RUN", True)
    monkeypatch.setattr(mod, "load_runtime_cache", lambda: cache_state)
    monkeypatch.setattr(mod, "filter_events", lambda events, **_k: events)
    monkeypatch.setattr(mod, "list_event_types", lambda _c: ["raid"])
    monkeypatch.setattr(
        mod,
        "load_all_user_prefs",
        lambda: {"123": {"enabled": True, "by_event_type": {"all": ["24h"]}}},
    )

    from event_calendar import reminder_state as rs_mod

    st_path = tmp_path / "state.json"
    monkeypatch.setattr(rs_mod, "DEFAULT_REMINDER_STATE_PATH", st_path)

    bot = _FakeBot(user=_FakeUser())
    out = await mod.dispatch_due_calendar_reminders(bot)
    assert out.sent == 1
    assert out.attempted == 1


@pytest.mark.asyncio
async def test_dispatch_failure_reason_buckets(monkeypatch, fixed_now, tmp_path):
    start = fixed_now + timedelta(hours=24)
    cache_state = {"ok": True, "events": [_event("evt-3", "raid", start)]}

    monkeypatch.setattr(mod, "EVENT_CALENDAR_REMINDERS_DRY_RUN", False)
    monkeypatch.setattr(mod, "load_runtime_cache", lambda: cache_state)
    monkeypatch.setattr(mod, "filter_events", lambda events, **_k: events)
    monkeypatch.setattr(mod, "list_event_types", lambda _c: ["raid"])
    monkeypatch.setattr(
        mod,
        "load_all_user_prefs",
        lambda: {"123": {"enabled": True, "by_event_type": {"raid": ["24h"]}}},
    )

    from event_calendar import reminder_state as rs_mod

    st_path = tmp_path / "state.json"
    monkeypatch.setattr(rs_mod, "DEFAULT_REMINDER_STATE_PATH", st_path)

    bot = _FakeBot(fetch_user_exc=discord.NotFound(response=_FakeResponse(), message="x"))
    out = await mod.dispatch_due_calendar_reminders(bot)
    assert out.failures == 1
    assert out.failed_not_found == 1
