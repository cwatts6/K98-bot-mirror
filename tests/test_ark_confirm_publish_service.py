from __future__ import annotations

import pytest

from ark import confirm_publish_service as service


@pytest.mark.asyncio
async def test_load_team_review_state_prefers_final(monkeypatch):
    async def _get_match(_match_id):
        return {"MatchId": 44, "Alliance": "K98", "Status": "Locked"}

    async def _get_roster(_match_id):
        return [
            {"GovernorId": 101, "Status": "Active", "SlotType": "Player"},
            {"GovernorId": 102, "Status": "Active", "SlotType": "Player"},
            {"GovernorId": 103, "Status": "Active", "SlotType": "Player"},
        ]

    async def _list_rows(*, match_id, draft_only):
        assert match_id == 44
        assert draft_only is False
        return [
            {"GovernorId": 101, "TeamNumber": 1, "IsDraft": 1, "IsFinal": 0},
            {"GovernorId": 102, "TeamNumber": 2, "IsDraft": 1, "IsFinal": 0},
            {"GovernorId": 103, "TeamNumber": 2, "IsDraft": 0, "IsFinal": 1},
            {"GovernorId": 102, "TeamNumber": 1, "IsDraft": 0, "IsFinal": 1},
        ]

    monkeypatch.setattr(service, "get_match", _get_match)
    monkeypatch.setattr(service, "get_roster", _get_roster)
    monkeypatch.setattr(service, "list_match_team_rows", _list_rows)

    state = await service.load_team_review_state(44)
    assert state.is_finalized is True
    assert state.team1_ids == [102]
    assert state.team2_ids == [103]


@pytest.mark.asyncio
async def test_load_team_review_state_uses_draft_when_no_final(monkeypatch):
    async def _get_match(_match_id):
        return {"MatchId": 45, "Alliance": "K98", "Status": "Locked"}

    async def _get_roster(_match_id):
        return [
            {"GovernorId": 201, "Status": "Active", "SlotType": "Player"},
            {"GovernorId": 202, "Status": "Active", "SlotType": "Player"},
        ]

    async def _list_rows(*, match_id, draft_only):
        assert match_id == 45
        assert draft_only is False
        return [
            {"GovernorId": 202, "TeamNumber": 2, "IsDraft": 1, "IsFinal": 0},
            {"GovernorId": 201, "TeamNumber": 1, "IsDraft": 1, "IsFinal": 0},
        ]

    monkeypatch.setattr(service, "get_match", _get_match)
    monkeypatch.setattr(service, "get_roster", _get_roster)
    monkeypatch.setattr(service, "list_match_team_rows", _list_rows)

    state = await service.load_team_review_state(45)
    assert state.is_finalized is False
    assert state.team1_ids == [201]
    assert state.team2_ids == [202]
