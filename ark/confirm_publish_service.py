from __future__ import annotations

from dataclasses import dataclass
import logging

from ark.dal.ark_dal import (
    clear_match_final_rows,
    get_alliance,
    get_config,
    get_match,
    get_roster,
    insert_audit_log,
    list_match_team_rows,
    promote_match_draft_to_final,
)
from ark.team_publish import publish_ark_teams

logger = logging.getLogger(__name__)


class ArkPublishPreconditionError(RuntimeError):
    """Raised when Ark team publish preconditions fail."""


@dataclass(frozen=True)
class ArkPublishResult:
    match_id: int
    team1_count: int
    team2_count: int
    confirmation_channel_id: int


@dataclass(frozen=True)
class ArkTeamReviewState:
    match: dict
    player_rows: list[dict]
    team1_ids: list[int]
    team2_ids: list[int]
    is_finalized: bool
    draft_count: int
    final_count: int


async def _load_draft_assignments(match_id: int) -> dict[int, int]:
    """
    Load current draft assignments for a match as a governor_id → team_number map.

    Ownership: ark/confirm_publish_service.py
    Reads: IsDraft=1, IsFinal=0 rows only.
    """
    rows = await list_match_team_rows(match_id=int(match_id), draft_only=True)
    assignments: dict[int, int] = {}
    for row in rows or []:
        gid = row.get("GovernorId")
        team_no = row.get("TeamNumber")
        if gid is None or team_no is None:
            continue
        gid_i = int(gid)
        team_i = int(team_no)
        if team_i not in (1, 2):
            continue
        if gid_i in assignments:
            logger.warning(
                "[ARK_PUBLISH] duplicate_draft_assignment match_id=%s governor_id=%s",
                int(match_id),
                gid_i,
            )
            raise ArkPublishPreconditionError("Duplicate governor assignment detected in draft.")
        assignments[gid_i] = team_i

    logger.info(
        "[ARK_PUBLISH] load_draft_assignments match_id=%s draft_assignments=%s",
        int(match_id),
        len(assignments),
    )
    return assignments


async def load_team_review_state(match_id: int) -> ArkTeamReviewState:
    """
    Load SQL-backed team review state for a match.

    Ownership: ark/confirm_publish_service.py
    Source priority: final rows first, draft rows as fallback.
    Player rows: active Player-slot signups only.
    """
    match = await get_match(int(match_id))
    if not match:
        raise ArkPublishPreconditionError("Match not found.")

    roster = await get_roster(int(match_id))
    player_rows = [
        r
        for r in (roster or [])
        if (r.get("Status") or "").lower() == "active"
        and (r.get("SlotType") or "").lower() == "player"
        and r.get("GovernorId") is not None
    ]
    roster_ids = {int(r["GovernorId"]) for r in player_rows}

    all_rows = await list_match_team_rows(match_id=int(match_id), draft_only=False)
    final_rows = [r for r in (all_rows or []) if int(r.get("IsFinal") or 0) == 1]
    draft_rows = [
        r
        for r in (all_rows or [])
        if int(r.get("IsDraft") or 0) == 1 and int(r.get("IsFinal") or 0) == 0
    ]
    source_rows = final_rows or draft_rows
    using = "final" if final_rows else "draft"

    team1_ids: list[int] = []
    team2_ids: list[int] = []
    seen: set[int] = set()
    for row in source_rows:
        gid = row.get("GovernorId")
        team_no = row.get("TeamNumber")
        if gid is None or team_no is None:
            continue
        gid_i = int(gid)
        if gid_i in seen or gid_i not in roster_ids:
            continue
        seen.add(gid_i)
        if int(team_no) == 1:
            team1_ids.append(gid_i)
        elif int(team_no) == 2:
            team2_ids.append(gid_i)

    logger.info(
        "[ARK_PUBLISH] load_review_state match_id=%s roster_players=%s "
        "draft_rows=%s final_rows=%s using=%s team1=%s team2=%s",
        int(match_id),
        len(player_rows),
        len(draft_rows),
        len(final_rows),
        using,
        len(team1_ids),
        len(team2_ids),
    )

    return ArkTeamReviewState(
        match=match,
        player_rows=player_rows,
        team1_ids=team1_ids,
        team2_ids=team2_ids,
        is_finalized=bool(final_rows),
        draft_count=len(draft_rows),
        final_count=len(final_rows),
    )


async def publish_reviewed_teams(
    *, client, match_id: int, actor_discord_id: int
) -> ArkPublishResult:
    """
    Publish reviewed Ark teams by promoting persisted draft rows to final rows.

    Ownership: ark/confirm_publish_service.py
    Flow:
      1. Validate match exists and is not cancelled.
      2. Load draft assignments — fail loudly if empty.
      3. Validate all draft governors are in active player roster.
      4. Promote draft → final via DAL.
      5. Refresh confirmation message.
      6. Post team embed.
      7. Audit log.
    """
    match_id_i = int(match_id)
    actor_i = int(actor_discord_id)

    logger.info(
        "[ARK_PUBLISH] publish_start match_id=%s actor_discord_id=%s",
        match_id_i,
        actor_i,
    )

    match = await get_match(match_id_i)
    if not match:
        raise ArkPublishPreconditionError("Match not found.")

    status = str(match.get("Status") or "").strip().lower()
    if status in {"cancelled"}:
        raise ArkPublishPreconditionError("Cannot publish teams for a cancelled match.")

    alliance_name = str(match.get("Alliance") or "").strip()
    alliance_row = await get_alliance(alliance_name)
    confirmation_channel_id = int((alliance_row or {}).get("ConfirmationChannelId") or 0)
    if not confirmation_channel_id:
        raise ArkPublishPreconditionError("Alliance confirmation channel is not configured.")

    roster = await get_roster(match_id_i)
    active_player_ids = {
        int(r["GovernorId"])
        for r in (roster or [])
        if r.get("GovernorId") is not None
        and str(r.get("Status") or "").lower() == "active"
        and str(r.get("SlotType") or "").lower() == "player"
    }
    logger.info(
        "[ARK_PUBLISH] active_player_ids match_id=%s count=%s",
        match_id_i,
        len(active_player_ids),
    )

    assignments = await _load_draft_assignments(match_id_i)
    if not assignments:
        raise ArkPublishPreconditionError(
            "Draft teams are empty. Generate/review teams before publish."
        )

    assigned_ids = set(assignments.keys())
    stale_ids = assigned_ids - active_player_ids
    if stale_ids:
        logger.warning(
            "[ARK_PUBLISH] stale_draft_governors match_id=%s stale_count=%s stale_ids=%s",
            match_id_i,
            len(stale_ids),
            sorted(stale_ids),
        )
        raise ArkPublishPreconditionError(
            f"Draft contains {len(stale_ids)} governor(s) not in active player roster. "
            "Re-open review and save again."
        )

    team1_count = sum(1 for t in assignments.values() if t == 1)
    team2_count = sum(1 for t in assignments.values() if t == 2)
    if team1_count + team2_count == 0:
        raise ArkPublishPreconditionError("No valid team assignments to publish.")

    logger.info(
        "[ARK_PUBLISH] promoting_draft match_id=%s draft_count=%s team1=%s team2=%s",
        match_id_i,
        len(assignments),
        team1_count,
        team2_count,
    )

    promoted = await promote_match_draft_to_final(
        match_id=match_id_i,
        actor_discord_id=actor_i,
        source="confirm_publish",
    )
    if not promoted:
        raise ArkPublishPreconditionError(
            "Failed to finalize teams from draft rows. "
            "Draft rows may be missing — try Auto-Balance or Assign first."
        )

    logger.info(
        "[ARK_PUBLISH] draft_promoted match_id=%s team1=%s team2=%s",
        match_id_i,
        team1_count,
        team2_count,
    )

    config = await get_config()
    if not config:
        raise ArkPublishPreconditionError(
            "Ark config is missing; cannot publish confirmation message."
        )

    from ark.confirmation_flow import ArkConfirmationController

    controller = ArkConfirmationController(match_id=match_id_i, config=config)
    refreshed = await controller.refresh_confirmation_message(
        client=client,
        target_channel_id=confirmation_channel_id,
        show_check_in=False,
    )
    if not refreshed:
        logger.warning(
            "[ARK_PUBLISH] confirmation_refresh_failed match_id=%s channel_id=%s",
            match_id_i,
            confirmation_channel_id,
        )
        raise ArkPublishPreconditionError("Failed to create/update confirmation message.")

    published_embed_ok = await publish_ark_teams(
        client=client,
        match_id=match_id_i,
        target_channel_id=int(confirmation_channel_id),
        actor_discord_id=actor_i,
    )

    await insert_audit_log(
        action_type="ark_team_publish",
        actor_discord_id=actor_i,
        match_id=match_id_i,
        governor_id=None,
        details_json={
            "confirmation_channel_id": confirmation_channel_id,
            "team1_count": team1_count,
            "team2_count": team2_count,
            "status": status,
            "published_embed_ok": bool(published_embed_ok),
        },
    )

    logger.info(
        "[ARK_PUBLISH] publish_complete match_id=%s actor_discord_id=%s channel_id=%s "
        "team1=%s team2=%s published_embed_ok=%s",
        match_id_i,
        actor_i,
        confirmation_channel_id,
        team1_count,
        team2_count,
        bool(published_embed_ok),
    )

    return ArkPublishResult(
        match_id=match_id_i,
        team1_count=team1_count,
        team2_count=team2_count,
        confirmation_channel_id=confirmation_channel_id,
    )


async def unpublish_final_teams(*, match_id: int, actor_discord_id: int) -> int:
    """
    Clear final Ark team rows so draft can be edited again.

    Ownership: ark/confirm_publish_service.py
    Returns the count of final rows removed.
    A return value of 0 means no final rows existed — not an error, but worth noting.
    """
    match_id_i = int(match_id)
    actor_i = int(actor_discord_id)

    logger.info(
        "[ARK_PUBLISH] unpublish_start match_id=%s actor_discord_id=%s",
        match_id_i,
        actor_i,
    )

    removed = await clear_match_final_rows(match_id=match_id_i)

    if removed == 0:
        logger.warning(
            "[ARK_PUBLISH] unpublish_no_rows_removed match_id=%s — no IsFinal=1 rows existed; "
            "teams may not have been published or were already unpublished",
            match_id_i,
        )
    else:
        logger.info(
            "[ARK_PUBLISH] unpublish_complete match_id=%s removed_final_rows=%s",
            match_id_i,
            removed,
        )

    await insert_audit_log(
        action_type="ark_team_unpublish",
        actor_discord_id=actor_i,
        match_id=match_id_i,
        governor_id=None,
        details_json={"removed_final_rows": removed},
    )

    return removed
