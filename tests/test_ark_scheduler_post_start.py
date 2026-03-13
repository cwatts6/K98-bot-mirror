import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from ark.ark_scheduler import schedule_ark_lifecycle


class DummyClient:
    guild_id = 123456789012345678


@pytest.mark.asyncio
async def test_scheduler_post_start_refresh(monkeypatch):
    called = {"refresh": False}

    now = datetime.now(UTC)
    match_dt = now - timedelta(minutes=31)

    async def _get_config():
        return {"PlayersCap": 30, "SubsCap": 15, "CheckInActivationOffsetHours": 12}

    async def _list_open_matches():
        return [
            {
                "MatchId": 5,
                "Alliance": "K98",
                "ArkWeekendDate": match_dt.date(),
                "MatchDay": "Sat",
                "MatchTimeUtc": match_dt.time().replace(microsecond=0),
                "SignupCloseUtc": now - timedelta(hours=1),
                "Status": "Locked",
            }
        ]

    async def _ensure_confirmation_message(*_a, **_k):
        called["refresh"] = True
        return True

    async def _run_match_dispatch(*_a, **_k):
        return None

    async def _sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr("ark.ark_scheduler.get_config", _get_config)
    monkeypatch.setattr("ark.ark_scheduler.list_open_matches", _list_open_matches)
    monkeypatch.setattr(
        "ark.ark_scheduler.ensure_confirmation_message", _ensure_confirmation_message
    )
    monkeypatch.setattr("ark.ark_scheduler._run_match_reminder_dispatch", _run_match_dispatch)
    monkeypatch.setattr("ark.ark_scheduler.asyncio.sleep", _sleep)

    with pytest.raises(asyncio.CancelledError):
        await schedule_ark_lifecycle(DummyClient(), poll_interval_seconds=1)

    assert called["refresh"] is True
