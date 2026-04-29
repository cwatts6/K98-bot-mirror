from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from ark.ark_preference_service import get_all_active_preferences
from ark.dal.ark_dal import (
    get_governor_power_bulk,
    get_match,
    list_match_team_rows,
    replace_match_draft_rows,
)
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)


class ArkDraftError(RuntimeError):
    """Raised when draft generation cannot complete."""


class ArkDraftPreconditionError(ArkDraftError):
    """Raised when preconditions (time/finalization) are not met."""


@dataclass(frozen=True)
class ArkDraftResult:
    match_id: int
    team1_ids: list[int]
    team2_ids: list[int]
    team1_power: int
    team2_power: int
    assigned_by_preference: int
    assigned_by_balancer: int
    preference_count: int
    eligible_count: int


@dataclass(frozen=True)
class _Player:
    governor_id: int
    power: int


def _match_registration_closed(match: dict, *, now_utc: datetime) -> bool:
    close = match.get("SignupCloseUtc")
    if close is None:
        return False
    return ensure_aware_utc(now_utc) >= ensure_aware_utc(close)


def _deterministic_unassigned(players: list[_Player]) -> list[_Player]:
    return sorted(players, key=lambda p: (-p.power, p.governor_id))


def _safe_int_power(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0


async def _load_existing_draft(match_id: int) -> tuple[list[int], list[int]]:
    rows = await list_match_team_rows(match_id=match_id, draft_only=True)
    team1: list[int] = []
    team2: list[int] = []
    for row in rows or []:
        gid = row.get("GovernorId")
        team_no = row.get("TeamNumber")
        if gid is None or team_no is None:
            continue
        gid_int = int(gid)
        if int(team_no) == 1:
            team1.append(gid_int)
        elif int(team_no) == 2:
            team2.append(gid_int)
    return sorted(set(team1)), sorted(set(team2))


async def generate_draft_for_match(
    match_id: int,
    *,
    actor_discord_id: int,
    source: str,
    roster_rows: list[dict] | None = None,
) -> ArkDraftResult:
    """
    Generate and persist a deterministic Ark draft for a single match.

    Ownership: ark/ark_draft_service.py
    Persistence: delegated entirely to ark/dal/ark_dal.replace_match_draft_rows.

    Raises:
        ArkDraftPreconditionError: Registration not yet closed, or teams already finalized.
        ArkDraftError: Persistence failed after generation.
    """
    logger.info(
        "[ARK_DRAFT] generate_start match_id=%s actor_discord_id=%s source=%s "
        "roster_rows_provided=%s",
        int(match_id),
        int(actor_discord_id),
        str(source),
        len(roster_rows or []),
    )

    match = await get_match(int(match_id))
    if not match:
        raise ArkDraftError(f"Match {match_id} not found.")

    if not _match_registration_closed(match, now_utc=utcnow()):
        raise ArkDraftPreconditionError("Drafting is blocked until registration closes.")

    # Guard: abort early if teams are already finalized.
    finalize_guard = await replace_match_draft_rows(
        match_id=int(match_id),
        assignments=[],
        actor_discord_id=int(actor_discord_id),
        source=str(source),
        check_finalized_only=True,
    )
    if not finalize_guard:
        raise ArkDraftPreconditionError(
            "Teams are finalized. Unpublish/reset before regenerating draft."
        )

    rows = roster_rows or []
    if not rows:
        from ark.dal.ark_dal import get_roster  # local import to avoid cycles

        rows = await get_roster(int(match_id))

    eligible: list[int] = []
    for row in rows or []:
        gid = row.get("GovernorId")
        if gid is None:
            continue
        if str(row.get("Status") or "").lower() != "active":
            continue
        if str(row.get("SlotType") or "").lower() != "player":
            continue
        eligible.append(int(gid))

    eligible = sorted(set(eligible))
    logger.info(
        "[ARK_DRAFT] eligible_players match_id=%s eligible=%s",
        int(match_id),
        len(eligible),
    )

    if not eligible:
        persisted = await replace_match_draft_rows(
            match_id=int(match_id),
            assignments=[],
            actor_discord_id=int(actor_discord_id),
            source=str(source),
            check_finalized_only=False,
        )
        logger.info(
            "[ARK_DRAFT] empty_roster_cleared match_id=%s persisted=%s",
            int(match_id),
            persisted,
        )
        return ArkDraftResult(
            match_id=int(match_id),
            team1_ids=[],
            team2_ids=[],
            team1_power=0,
            team2_power=0,
            assigned_by_preference=0,
            assigned_by_balancer=0,
            preference_count=0,
            eligible_count=0,
        )

    preferences = await get_all_active_preferences()
    power_map = await get_governor_power_bulk(eligible)

    players = [
        _Player(governor_id=gid, power=_safe_int_power(power_map.get(gid, 0))) for gid in eligible
    ]
    player_by_gid = {p.governor_id: p for p in players}

    preferred_team1 = sorted(
        [gid for gid in eligible if int(preferences.get(gid, 0)) == 1],
        key=lambda g: g,
    )
    preferred_team2 = sorted(
        [gid for gid in eligible if int(preferences.get(gid, 0)) == 2],
        key=lambda g: g,
    )

    assigned = set(preferred_team1) | set(preferred_team2)
    remaining = _deterministic_unassigned([p for p in players if p.governor_id not in assigned])

    team1_ids = list(preferred_team1)
    team2_ids = list(preferred_team2)
    team1_power = sum(player_by_gid[gid].power for gid in team1_ids if gid in player_by_gid)
    team2_power = sum(player_by_gid[gid].power for gid in team2_ids if gid in player_by_gid)

    for p in remaining:
        if team1_power < team2_power:
            target = 1
        elif team2_power < team1_power:
            target = 2
        else:
            if len(team1_ids) < len(team2_ids):
                target = 1
            elif len(team2_ids) < len(team1_ids):
                target = 2
            else:
                target = 1

        if target == 1:
            team1_ids.append(p.governor_id)
            team1_power += p.power
        else:
            team2_ids.append(p.governor_id)
            team2_power += p.power

    assignments = [(gid, 1) for gid in team1_ids] + [(gid, 2) for gid in team2_ids]

    logger.info(
        "[ARK_DRAFT] persisting match_id=%s assignments=%s team1=%s team2=%s "
        "pref_assigned=%s balanced_assigned=%s",
        int(match_id),
        len(assignments),
        len(team1_ids),
        len(team2_ids),
        len(preferred_team1) + len(preferred_team2),
        len(remaining),
    )

    persisted = await replace_match_draft_rows(
        match_id=int(match_id),
        assignments=assignments,
        actor_discord_id=int(actor_discord_id),
        source=str(source),
        check_finalized_only=False,
    )
    if not persisted:
        logger.error(
            "[ARK_DRAFT] persist_failed match_id=%s actor_discord_id=%s source=%s "
            "assignments=%s team1=%s team2=%s",
            int(match_id),
            int(actor_discord_id),
            str(source),
            len(assignments),
            len(team1_ids),
            len(team2_ids),
        )
        raise ArkDraftError("Failed to persist draft teams.")

    logger.info(
        "[ARK_DRAFT] generated match_id=%s source=%s eligible=%s preferences=%s "
        "pref_assigned=%s balanced_assigned=%s team1_count=%s team2_count=%s "
        "team1_power=%s team2_power=%s",
        int(match_id),
        source,
        len(eligible),
        len(preferences),
        len(preferred_team1) + len(preferred_team2),
        len(remaining),
        len(team1_ids),
        len(team2_ids),
        team1_power,
        team2_power,
    )

    return ArkDraftResult(
        match_id=int(match_id),
        team1_ids=team1_ids,
        team2_ids=team2_ids,
        team1_power=team1_power,
        team2_power=team2_power,
        assigned_by_preference=len(preferred_team1) + len(preferred_team2),
        assigned_by_balancer=len(remaining),
        preference_count=len(preferences),
        eligible_count=len(eligible),
    )


async def sync_manual_draft(
    *,
    match_id: int,
    team1_ids: list[int],
    team2_ids: list[int],
    actor_discord_id: int,
    source: str,
) -> bool:
    """
    Persist a manually-adjusted draft snapshot to SQL draft rows.

    Ownership: ark/ark_draft_service.py
    Returns True on success, False if blocked by finalization.
    Raises ArkDraftPreconditionError if teams are finalized.
    """
    logger.info(
        "[ARK_DRAFT] sync_manual_start match_id=%s actor_discord_id=%s source=%s "
        "team1_ids=%s team2_ids=%s",
        int(match_id),
        int(actor_discord_id),
        str(source),
        len(team1_ids or []),
        len(team2_ids or []),
    )

    # Guard: abort if finalized.
    finalize_guard = await replace_match_draft_rows(
        match_id=int(match_id),
        assignments=[],
        actor_discord_id=int(actor_discord_id),
        source=str(source),
        check_finalized_only=True,
    )
    if not finalize_guard:
        raise ArkDraftPreconditionError("Teams are finalized. Unpublish/reset first.")

    seen: set[int] = set()
    assignments: list[tuple[int, int]] = []
    for gid in team1_ids or []:
        g = int(gid)
        if g in seen:
            continue
        seen.add(g)
        assignments.append((g, 1))
    for gid in team2_ids or []:
        g = int(gid)
        if g in seen:
            continue
        seen.add(g)
        assignments.append((g, 2))

    persisted = await replace_match_draft_rows(
        match_id=int(match_id),
        assignments=assignments,
        actor_discord_id=int(actor_discord_id),
        source=str(source),
        check_finalized_only=False,
    )

    logger.info(
        "[ARK_DRAFT] sync_manual_done match_id=%s actor_discord_id=%s source=%s "
        "assignments=%s persisted=%s",
        int(match_id),
        int(actor_discord_id),
        str(source),
        len(assignments),
        bool(persisted),
    )
    return persisted


async def load_persisted_draft(match_id: int) -> tuple[list[int], list[int]]:
    """Load persisted SQL draft rows for a match, by team."""
    return await _load_existing_draft(int(match_id))
