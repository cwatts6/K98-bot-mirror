from __future__ import annotations

from datetime import datetime

import pytest

from ark.dal import ark_dal
from ark.reminders import cancel_match_reminders
from ark.state.ark_state import ArkJsonState, ArkReminderState


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


@pytest.mark.asyncio
async def test_cancel_match_reminders_clears_state(monkeypatch):
    state = ArkJsonState()
    state.reminders = {
        "77|111|24h": ArkReminderState(sent_at_utc=datetime.utcnow()),
        "88|111|24h": ArkReminderState(sent_at_utc=datetime.utcnow()),
    }

    async def fake_load_async():
        return None

    async def fake_save_async():
        return None

    monkeypatch.setattr(state, "load_async", fake_load_async)
    monkeypatch.setattr(state, "save_async", fake_save_async)

    monkeypatch.setattr("ark.reminders.ArkJsonState", lambda: state)

    changed = await cancel_match_reminders(77)

    assert changed is True
    assert "77|111|24h" not in state.reminders
    assert "88|111|24h" in state.reminders
