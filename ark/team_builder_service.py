"""Persistence and audit orchestration for Ark team-builder interactions."""

from __future__ import annotations

from ark.ark_draft_service import (
    ArkDraftResult,
    generate_draft_for_match,
    sync_manual_draft,
)
from ark.dal.ark_dal import insert_audit_log


async def assign_player(
    *,
    match_id: int,
    team1_ids: list[int],
    team2_ids: list[int],
    actor_discord_id: int,
) -> bool:
    """Persist a manual assignment; the established contract has no audit row."""
    return await sync_manual_draft(
        match_id=match_id,
        team1_ids=team1_ids,
        team2_ids=team2_ids,
        actor_discord_id=actor_discord_id,
        source="team_builder_assign",
    )


async def remove_player(
    *,
    match_id: int,
    team1_ids: list[int],
    team2_ids: list[int],
    actor_discord_id: int,
    governor_id: int,
    from_team: int,
) -> bool:
    """Persist removal, then write the existing exact removal audit contract."""
    persisted = await sync_manual_draft(
        match_id=match_id,
        team1_ids=team1_ids,
        team2_ids=team2_ids,
        actor_discord_id=actor_discord_id,
        source="team_builder_remove",
    )
    await insert_audit_log(
        action_type="ark_team_remove",
        actor_discord_id=actor_discord_id,
        match_id=match_id,
        governor_id=governor_id,
        details_json={"from_team": from_team},
    )
    return persisted


async def reset_teams(*, match_id: int, actor_discord_id: int) -> bool:
    """Clear draft rows, then write the existing exact reset audit contract."""
    persisted = await sync_manual_draft(
        match_id=match_id,
        team1_ids=[],
        team2_ids=[],
        actor_discord_id=actor_discord_id,
        source="team_builder_reset",
    )
    await insert_audit_log(
        action_type="ark_team_reset",
        actor_discord_id=actor_discord_id,
        match_id=match_id,
        governor_id=None,
        details_json={},
    )
    return persisted


async def auto_balance_teams(
    *,
    match_id: int,
    actor_discord_id: int,
    roster_rows: list[dict],
) -> ArkDraftResult:
    """Generate/persist a draft, then write the existing exact balance audit contract."""
    result = await generate_draft_for_match(
        match_id,
        actor_discord_id=actor_discord_id,
        source="team_builder_button",
        roster_rows=roster_rows,
    )
    await insert_audit_log(
        action_type="ark_team_autobalance",
        actor_discord_id=actor_discord_id,
        match_id=match_id,
        governor_id=None,
        details_json={
            "team1_count": len(result.team1_ids),
            "team2_count": len(result.team2_ids),
            "team1_power": result.team1_power,
            "team2_power": result.team2_power,
            "assigned_by_preference": result.assigned_by_preference,
            "assigned_by_balancer": result.assigned_by_balancer,
        },
    )
    return result
