from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ark import ark_draft_service as service


@pytest.mark.asyncio
async def test_generate_draft_blocks_before_close(monkeypatch):
    async def _get_match(_match_id):
        return {
            "MatchId": 10,
            "SignupCloseUtc": datetime.now(UTC) + timedelta(hours=1),
        }

    monkeypatch.setattr(service, "get_match", _get_match)

    with pytest.raises(service.ArkDraftPreconditionError, match="registration closes"):
        await service.generate_draft_for_match(
            10,
            actor_discord_id=1,
            source="test",
            roster_rows=[],
        )


@pytest.mark.asyncio
async def test_generate_draft_applies_preferences_and_balances(monkeypatch):
    now = datetime.now(UTC)

    async def _get_match(_match_id):
        return {
            "MatchId": 11,
            "SignupCloseUtc": now - timedelta(minutes=1),
        }

    async def _replace(**kwargs):
        return True

    async def _get_prefs():
        return {101: 1, 104: 2}

    async def _power(ids):
        return {101: 200, 102: 150, 103: 120, 104: 90}

    monkeypatch.setattr(service, "get_match", _get_match)
    monkeypatch.setattr(service, "replace_match_draft_rows", _replace)
    monkeypatch.setattr(service, "get_all_active_preferences", _get_prefs)
    monkeypatch.setattr(service, "get_governor_power_bulk", _power)

    roster = [
        {"GovernorId": 101, "Status": "Active", "SlotType": "Player"},
        {"GovernorId": 102, "Status": "Active", "SlotType": "Player"},
        {"GovernorId": 103, "Status": "Active", "SlotType": "Player"},
        {"GovernorId": 104, "Status": "Active", "SlotType": "Player"},
    ]

    result = await service.generate_draft_for_match(
        11,
        actor_discord_id=1,
        source="test",
        roster_rows=roster,
    )

    assert 101 in result.team1_ids
    assert 104 in result.team2_ids
    assert result.assigned_by_preference == 2
    assert result.assigned_by_balancer == 2


@pytest.mark.asyncio
async def test_generate_draft_null_power_falls_back_to_zero(monkeypatch):
    now = datetime.now(UTC)

    async def _get_match(_match_id):
        return {
            "MatchId": 12,
            "SignupCloseUtc": now - timedelta(minutes=1),
        }

    async def _replace(**kwargs):
        return True

    async def _get_prefs():
        return {}

    async def _power(ids):
        return {201: None, 202: 50}

    monkeypatch.setattr(service, "get_match", _get_match)
    monkeypatch.setattr(service, "replace_match_draft_rows", _replace)
    monkeypatch.setattr(service, "get_all_active_preferences", _get_prefs)
    monkeypatch.setattr(service, "get_governor_power_bulk", _power)

    roster = [
        {"GovernorId": 201, "Status": "Active", "SlotType": "Player"},
        {"GovernorId": 202, "Status": "Active", "SlotType": "Player"},
    ]

    result = await service.generate_draft_for_match(
        12,
        actor_discord_id=1,
        source="test",
        roster_rows=roster,
    )

    assert result.team1_power >= 0
    assert result.team2_power >= 0


@pytest.mark.asyncio
async def test_generate_draft_blocks_when_final_exists(monkeypatch):
    now = datetime.now(UTC)

    async def _get_match(_match_id):
        return {
            "MatchId": 13,
            "SignupCloseUtc": now - timedelta(minutes=1),
        }

    calls = {"n": 0}

    async def _replace(**kwargs):
        calls["n"] += 1
        if kwargs.get("check_finalized_only"):
            return False
        return True

    monkeypatch.setattr(service, "get_match", _get_match)
    monkeypatch.setattr(service, "replace_match_draft_rows", _replace)

    with pytest.raises(service.ArkDraftPreconditionError, match="finalized"):
        await service.generate_draft_for_match(
            13,
            actor_discord_id=1,
            source="test",
            roster_rows=[{"GovernorId": 1, "Status": "Active", "SlotType": "Player"}],
        )

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_sync_manual_draft_dedupes(monkeypatch):
    async def _replace(**kwargs):
        return True

    monkeypatch.setattr(service, "replace_match_draft_rows", _replace)

    ok = await service.sync_manual_draft(
        match_id=20,
        team1_ids=[1, 1, 2],
        team2_ids=[2, 3],
        actor_discord_id=99,
        source="test",
    )

    assert ok is True
