import pytest

from ark.dal import ark_dal


@pytest.mark.asyncio
async def test_set_match_result(monkeypatch):
    async def _run_one_async(_sql, _params):
        return {"MatchId": 7}

    monkeypatch.setattr(ark_dal, "run_one_async", _run_one_async)

    ok = await ark_dal.set_match_result(
        match_id=7,
        result="Win",
        notes="Great win",
        actor_discord_id=123,
    )
    assert ok is True


@pytest.mark.asyncio
async def test_mark_no_show(monkeypatch):
    async def _run_one_async(_sql, _params):
        return {"SignupId": 99}

    monkeypatch.setattr(ark_dal, "run_one_async", _run_one_async)

    ok = await ark_dal.mark_no_show(
        match_id=7,
        governor_id=555,
        actor_discord_id=123,
    )
    assert ok is True


@pytest.mark.asyncio
async def test_list_player_report_rows(monkeypatch):
    async def _run_query_async(_sql, _params=None):
        return [{"GovernorId": 1, "GovernorName": "Test"}]

    monkeypatch.setattr(ark_dal, "run_query_async", _run_query_async)

    rows = await ark_dal.list_player_report_rows()
    assert rows
