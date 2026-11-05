from __future__ import annotations

import pytest

from ark.ark_draft_service import ArkDraftResult
from ark.team_builder_service import (
    assign_player,
    auto_balance_teams,
    remove_player,
    reset_teams,
)


@pytest.mark.asyncio
async def test_assign_player_preserves_source_and_writes_no_audit(monkeypatch):
    calls = []

    async def _sync(**kwargs):
        calls.append(("persist", kwargs))
        return True

    async def _unexpected_audit(**kwargs):
        calls.append(("audit", kwargs))

    monkeypatch.setattr("ark.team_builder_service.sync_manual_draft", _sync)
    monkeypatch.setattr("ark.team_builder_service.insert_audit_log", _unexpected_audit)

    persisted = await assign_player(
        match_id=7,
        team1_ids=[11],
        team2_ids=[22],
        actor_discord_id=33,
    )

    assert persisted is True
    assert calls == [
        (
            "persist",
            {
                "match_id": 7,
                "team1_ids": [11],
                "team2_ids": [22],
                "actor_discord_id": 33,
                "source": "team_builder_assign",
            },
        )
    ]


@pytest.mark.asyncio
async def test_remove_player_persists_before_exact_audit(monkeypatch):
    calls = []

    async def _sync(**kwargs):
        calls.append(("persist", kwargs))
        return True

    async def _audit(**kwargs):
        calls.append(("audit", kwargs))
        return 1

    monkeypatch.setattr("ark.team_builder_service.sync_manual_draft", _sync)
    monkeypatch.setattr("ark.team_builder_service.insert_audit_log", _audit)

    persisted = await remove_player(
        match_id=7,
        team1_ids=[],
        team2_ids=[22],
        actor_discord_id=33,
        governor_id=11,
        from_team=1,
    )

    assert persisted is True
    assert [name for name, _ in calls] == ["persist", "audit"]
    assert calls[0][1]["source"] == "team_builder_remove"
    assert calls[1][1] == {
        "action_type": "ark_team_remove",
        "actor_discord_id": 33,
        "match_id": 7,
        "governor_id": 11,
        "details_json": {"from_team": 1},
    }


@pytest.mark.asyncio
async def test_reset_teams_persists_before_exact_audit(monkeypatch):
    calls = []

    async def _sync(**kwargs):
        calls.append(("persist", kwargs))
        return True

    async def _audit(**kwargs):
        calls.append(("audit", kwargs))
        return 1

    monkeypatch.setattr("ark.team_builder_service.sync_manual_draft", _sync)
    monkeypatch.setattr("ark.team_builder_service.insert_audit_log", _audit)

    persisted = await reset_teams(match_id=7, actor_discord_id=33)

    assert persisted is True
    assert [name for name, _ in calls] == ["persist", "audit"]
    assert calls[0][1] == {
        "match_id": 7,
        "team1_ids": [],
        "team2_ids": [],
        "actor_discord_id": 33,
        "source": "team_builder_reset",
    }
    assert calls[1][1] == {
        "action_type": "ark_team_reset",
        "actor_discord_id": 33,
        "match_id": 7,
        "governor_id": None,
        "details_json": {},
    }


@pytest.mark.asyncio
async def test_auto_balance_persists_before_exact_audit(monkeypatch):
    calls = []
    result = ArkDraftResult(
        match_id=7,
        team1_ids=[11, 12],
        team2_ids=[22],
        team1_power=100,
        team2_power=90,
        assigned_by_preference=1,
        assigned_by_balancer=2,
        preference_count=1,
        eligible_count=3,
    )

    async def _generate(*args, **kwargs):
        calls.append(("persist", {"args": args, **kwargs}))
        return result

    async def _audit(**kwargs):
        calls.append(("audit", kwargs))
        return 1

    monkeypatch.setattr("ark.team_builder_service.generate_draft_for_match", _generate)
    monkeypatch.setattr("ark.team_builder_service.insert_audit_log", _audit)

    actual = await auto_balance_teams(
        match_id=7,
        actor_discord_id=33,
        roster_rows=[{"GovernorId": 11}],
    )

    assert actual is result
    assert [name for name, _ in calls] == ["persist", "audit"]
    assert calls[0][1] == {
        "args": (7,),
        "actor_discord_id": 33,
        "source": "team_builder_button",
        "roster_rows": [{"GovernorId": 11}],
    }
    assert calls[1][1] == {
        "action_type": "ark_team_autobalance",
        "actor_discord_id": 33,
        "match_id": 7,
        "governor_id": None,
        "details_json": {
            "team1_count": 2,
            "team2_count": 1,
            "team1_power": 100,
            "team2_power": 90,
            "assigned_by_preference": 1,
            "assigned_by_balancer": 2,
        },
    }
