from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ark.dal import ark_dal
from ark.reminder_state import ArkReminderState
from ark.reminders import cancel_match_reminders


@pytest.mark.asyncio
async def test_cancel_match_updates_sql(monkeypatch):
    captured = {}

    async def fake_run_one_async(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return {"MatchId": 99}

    monkeypatch.setattr(ark_dal, "run_one_async", fake_run_one_async)

    ok = await ark_dal.cancel_match(match_id=99, actor_discord_id=1)

    assert ok is True
    assert "UPDATE dbo.ArkMatches" in captured["sql"]


def test_cancel_match_reminders_clears_state(monkeypatch):
    state = ArkReminderState()
    state.reminders = {
        "77|111|24h": datetime.now(UTC).isoformat(),
        "88|111|24h": datetime.now(UTC).isoformat(),
    }

    def fake_load():
        return state

    def fake_save():
        return None

    monkeypatch.setattr("ark.reminders.ArkReminderState.load", fake_load)
    monkeypatch.setattr(state, "save", fake_save)

    changed = cancel_match_reminders(77)

    assert changed is True
    assert "77|111|24h" not in state.reminders
    assert "88|111|24h" in state.reminders


@pytest.mark.asyncio
async def test_create_match_includes_calendar_lineage_fields(monkeypatch):
    captured = {}

    async def fake_run_one_async(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return {"MatchId": 101}

    monkeypatch.setattr(ark_dal, "run_one_async", fake_run_one_async)

    match_id = await ark_dal.create_match(
        ark_dal.ArkMatchCreateRequest(
            alliance="k98A",
            ark_weekend_date=datetime(2026, 4, 4).date(),
            match_day="Sat",
            match_time_utc=datetime(2026, 4, 4, 20, 0).time(),
            registration_starts_at_utc=datetime(2026, 4, 4, 20, 0),
            signup_close_utc=datetime(2026, 4, 3, 18, 0),
            notes=None,
            actor_discord_id=1,
            calendar_instance_id=16464,
            created_source="calendar_auto",
        )
    )

    assert match_id == 101
    assert "CalendarInstanceId" in captured["sql"]
    assert "CreatedSource" in captured["sql"]
    assert "RegistrationStartsAtUtc" in captured["sql"]
    assert captured["params"][-2:] == (16464, "calendar_auto")
