from __future__ import annotations

from datetime import date, datetime, time

import pytest

from ark.dal import ark_dal
from ui.views.ark_views import AmendArkMatchView


@pytest.mark.asyncio
async def test_amend_match_updates_sql(monkeypatch):
    captured = {}

    async def fake_run_one_async(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return {"MatchId": 123}

    monkeypatch.setattr(ark_dal, "run_one_async", fake_run_one_async)

    ok = await ark_dal.amend_match(
        match_id=123,
        alliance="K98",
        match_day="Sat",
        match_time_utc=time(11, 0),
        signup_close_utc=datetime(2026, 3, 6, 23, 0),
        notes="Updated",
        actor_discord_id=1,
    )

    assert ok is True
    assert "UPDATE dbo.ArkMatches" in captured["sql"]


@pytest.mark.asyncio
async def test_get_roster_filters_active(monkeypatch):
    async def fake_run_query_async(sql, params):
        assert "Status = 'Active'" in sql
        return [{"GovernorId": 1}]

    monkeypatch.setattr(ark_dal, "run_query_async", fake_run_query_async)
    roster = await ark_dal.get_roster(match_id=55)
    assert roster == [{"GovernorId": 1}]


@pytest.mark.asyncio
async def test_amend_view_confirm_state():
    matches = [
        {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": date(2026, 3, 7),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(11, 0),
            "Notes": None,
        }
    ]

    view = AmendArkMatchView(
        author_id=123,
        matches=matches,
        alliances=["K98", "K99"],
        allowed_days=["Saturday", "Sunday"],
        allowed_times_by_day={"Saturday": ["11:00"], "Sunday": ["04:00"]},
        match_alliance_change_allowed={1: True},
        notes_templates=None,
        on_confirm=lambda *_: None,
        on_cancel=None,
    )

    # Initially disabled
    assert view.confirm_btn.disabled is True

    # Simulate match selection
    view.selection.match_id = 1
    view.selection.match_day = "Saturday"
    view.selection.match_time_utc = "11:00"
    view._refresh_confirm_state()

    assert view.confirm_btn.disabled is False
