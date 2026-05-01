"""Leadership-facing simplified-flow service helpers for MGE."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from embed_utils import fmt_short
from mge import mge_roster_service
from mge.dal import mge_publish_dal, mge_roster_dal
from mge.mge_constants import DEFAULT_TARGET_DECREMENT_SCORE
from mge.mge_simplified_flow_service import (
    evaluate_publish_readiness,
    get_ordered_leadership_rows,
    normalize_priority,
)

logger = logging.getLogger(__name__)

_ROW_LIMIT = 30


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_text(value: Any) -> str:
    return str(value or "").replace("<", "‹").replace(">", "›").strip()


def _display_name(row: dict[str, Any]) -> str:
    return (
        _safe_text(
            row.get("GovernorNameDisplay")
            or row.get("GovernorNameSnapshot")
            or row.get("GovernorName")
            or "Unknown"
        )
        or "Unknown"
    )


def _priority_display(value: Any) -> str:
    priority = normalize_priority(value)
    return priority.title() if priority != "unknown" else "Unknown"


def _fmt_kvk_rank(value: Any) -> str:
    parsed = _to_int(value, default=-1)
    return f"R{parsed}" if parsed >= 0 else "—"


def _fmt_short_number(value: Any) -> str:
    parsed = _to_int(value, default=-1)
    if parsed < 0:
        return "—"
    try:
        return fmt_short(parsed)
    except Exception:
        return f"{parsed:,}"


def _fmt_percent(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "—"
    try:
        numeric = float(value)
    except Exception:
        return str(value)
    if numeric <= 1:
        numeric *= 100
    return f"{numeric:.0f}%"


def _leadership_rank_label(row: dict[str, Any]) -> str:
    status = str(row.get("SimplifiedStatus") or "").strip().lower()
    if status == "roster":
        return f"#{_to_int(row.get('ComputedAwardedRank') or row.get('AwardedRank') or 0) or '?'}"
    if status == "waitlist":
        return (
            f"W{_to_int(row.get('ComputedWaitlistOrder') or row.get('WaitlistOrder') or 0) or '?'}"
        )
    if status == "rejected":
        return "R"
    return "—"


def build_leadership_display_row(row: dict[str, Any]) -> str:
    """Render a single leadership row line for embed display."""
    return (
        f"{_leadership_rank_label(row)} • "
        f"{_display_name(row)} • "
        f"{_priority_display(row.get('RequestPriority'))} • "
        f"KVK {_fmt_kvk_rank(row.get('LatestKVKRank'))} • "
        f"KVK Kills: {_fmt_short_number(row.get('LatestT4T5Kills'))} • "
        f"KVK Act: {_fmt_percent(row.get('LatestPercentOfKillTarget'))} • "
        f"MGE Target: {_fmt_short_number(row.get('TargetScore'))}"
    )


def _chunk_lines(lines: list[str], limit: int = 1024) -> list[str]:
    if not lines:
        return ["None"]

    chunks: list[str] = []
    current: list[str] = []
    used = 0
    for line in lines:
        line_len = len(line) + (1 if current else 0)
        if current and used + line_len > limit:
            chunks.append("\n".join(current))
            current = [line]
            used = len(line)
        else:
            current.append(line)
            used += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks


def _maybe_regenerate_targets(
    event_id: int,
    actor_discord_id: int,
    now: datetime,
) -> bool:
    """Auto-regenerate targets if any roster rows already have targets set.

    Must be called AFTER rank/order changes are persisted.
    Returns True if regen was attempted and succeeded, False otherwise.
    Failures are logged as warnings and do NOT propagate.
    """
    try:
        dataset = get_ordered_leadership_rows(event_id)
        roster_rows = [
            r for r in dataset.get("roster_rows", []) if _to_int(r.get("AwardId"), 0) > 0
        ]
        if not roster_rows:
            return False

        # Only regenerate if targets already exist for this event
        has_targets = any(
            r.get("TargetScore") is not None and _to_int(r.get("TargetScore"), -1) >= 0
            for r in roster_rows
        )
        if not has_targets:
            return False

        # Find rank1 target from the current roster data
        rank1_row = next(
            (
                r
                for r in roster_rows
                if _to_int(r.get("ComputedAwardedRank") or r.get("AwardedRank"), 0) == 1
            ),
            None,
        )
        if rank1_row is None or rank1_row.get("TargetScore") is None:
            logger.warning(
                "mge_target_regen_skipped reason=no_rank1_target event_id=%s",
                event_id,
            )
            return False

        rank1_score = _to_int(rank1_row.get("TargetScore"), 0)
        if rank1_score <= 0:
            logger.warning(
                "mge_target_regen_skipped reason=rank1_target_zero event_id=%s",
                event_id,
            )
            return False

        roster_targets: dict[int, dict[str, Any]] = {}
        for row in roster_rows:
            award_id = _to_int(row.get("AwardId"), 0)
            rank = _to_int(row.get("ComputedAwardedRank") or row.get("AwardedRank"), 0)
            if award_id <= 0 or rank <= 0:
                continue
            target = max(rank1_score - ((rank - 1) * DEFAULT_TARGET_DECREMENT_SCORE), 0)
            roster_targets[award_id] = {"target_score": target, "awarded_rank": rank}

        if not roster_targets:
            return False

        # Non-roster award IDs to clear
        clear_award_ids: list[int] = []
        for key in ("waitlist_rows", "rejected_rows", "unassigned_rows"):
            for row in dataset.get(key, []):
                aid = _to_int(row.get("AwardId"), 0)
                if aid > 0:
                    clear_award_ids.append(aid)

        count = mge_publish_dal.apply_generated_targets(
            event_id=event_id,
            roster_targets=roster_targets,
            clear_award_ids=clear_award_ids,
            actor_discord_id=actor_discord_id,
            now_utc=now,
        )
        if count <= 0:
            logger.warning(
                "mge_target_regen_failed reason=apply_returned_zero event_id=%s",
                event_id,
            )
            return False

        logger.info(
            "mge_target_regen_success event_id=%s actor_discord_id=%s rows_updated=%s",
            event_id,
            actor_discord_id,
            count,
        )
        return True

    except Exception:
        logger.exception(
            "mge_target_regen_exception manual_regeneration_required event_id=%s actor_discord_id=%s",
            event_id,
            actor_discord_id,
        )
        return False


def get_leadership_board_payload(event_id: int) -> dict[str, Any]:
    """Return leadership embed/view payload using simplified-flow service outputs."""
    dataset = get_ordered_leadership_rows(event_id)
    readiness = evaluate_publish_readiness(event_id)
    counts = dict(dataset.get("counts", {}))

    ordered_rows: list[dict[str, Any]] = (
        list(dataset.get("roster_rows", []))
        + list(dataset.get("waitlist_rows", []))
        + list(dataset.get("unassigned_rows", []))
        + list(dataset.get("rejected_rows", []))
    )
    display_lines = [build_leadership_display_row(row) for row in ordered_rows[:_ROW_LIMIT]]
    extra_count = max(0, len(ordered_rows) - len(display_lines))
    if extra_count > 0:
        display_lines.append(f"...and {extra_count} more")

    roster_count = int(counts.get("roster_count", 0))
    waitlist_count = int(counts.get("waitlist_count", 0))
    roster_rows = list(dataset.get("roster_rows", []))
    waitlist_rows = list(dataset.get("waitlist_rows", []))

    payload = {
        "event_id": int(event_id),
        "rows": ordered_rows,
        "display_lines": display_lines,
        "display_chunks": _chunk_lines(display_lines),
        "counts": {
            "total_signups": int(counts.get("total_signups", len(ordered_rows))),
            "roster_count": roster_count,
            "waitlist_count": waitlist_count,
            "rejected_count": int(counts.get("rejected_count", 0)),
        },
        "publish": readiness,
        "guidance_lines": [
            "Step 1: Review order and reduce roster to 15 if needed",
            "Step 2: Generate targets",
            "Step 3: Publish awards",
        ],
        "actions": {
            # keep original requested gate semantics
            "can_move_to_waitlist": roster_count > 15,
            "can_move_to_roster": waitlist_count > 0 and roster_count < 15,
            "can_reject_signup": True,
            "can_reset_ranks": True,
            "roster_full": roster_count >= 15,
            # for swap flow when full
            "can_promote_with_swap": waitlist_count > 0 and roster_count >= 15,
        },
        "selection_data": {
            "roster_rows": roster_rows,
            "waitlist_rows": waitlist_rows,
            "unassigned_rows": list(dataset.get("unassigned_rows", [])),
        },
    }
    logger.info(
        "mge_simplified_leadership_payload_ready event_id=%s total=%s roster=%s waitlist=%s rejected=%s publish_ready=%s",
        event_id,
        payload["counts"]["total_signups"],
        payload["counts"]["roster_count"],
        payload["counts"]["waitlist_count"],
        payload["counts"]["rejected_count"],
        readiness.get("publish_ready"),
    )
    return payload


def move_waitlist_to_roster_with_optional_demote(
    *,
    event_id: int,
    promote_award_id: int,
    actor_discord_id: int,
    demote_award_id: int | None = None,
    notes: str | None = None,
) -> mge_roster_service.RosterResult:
    """
    Promote selected waitlist row to roster.
    If roster is full (>=15), requires demote_award_id and performs one-step swap:
      - demoted roster row appended to waitlist end.
    """
    dataset = get_ordered_leadership_rows(event_id)
    roster_rows = list(dataset.get("roster_rows", []))
    waitlist_rows = list(dataset.get("waitlist_rows", []))

    promote_row = next(
        (r for r in waitlist_rows if _to_int(r.get("AwardId")) == int(promote_award_id)), None
    )
    if not promote_row:
        return mge_roster_service.RosterResult(False, "Selected waitlist player not found.")

    now = datetime.now(UTC)
    roster_count = len(roster_rows)

    if roster_count >= 15:
        if not demote_award_id:
            return mge_roster_service.RosterResult(
                False,
                "Roster is full. Select a roster player to demote.",
            )

        demote_row = next(
            (r for r in roster_rows if _to_int(r.get("AwardId")) == int(demote_award_id)), None
        )
        if not demote_row:
            return mge_roster_service.RosterResult(
                False, "Selected roster player to demote was not found."
            )
        if int(demote_award_id) == int(promote_award_id):
            return mge_roster_service.RosterResult(
                False, "Promote and demote players must be different."
            )

        # append to end of remaining waitlist after promoted row leaves waitlist
        remaining_wait_orders = [
            _to_int(r.get("WaitlistOrder") or r.get("ComputedWaitlistOrder"), 0)
            for r in waitlist_rows
            if _to_int(r.get("AwardId"), 0) != int(promote_award_id)
        ]
        next_waitlist_order = max([o for o in remaining_wait_orders if o > 0], default=0) + 1

        demote_ok = mge_roster_dal.update_award(
            award_id=int(demote_award_id),
            awarded_rank=None,
            award_status="waitlist",
            waitlist_order=next_waitlist_order,
            internal_notes=(notes or None),
            manual_order_override=False,
            assigned_by_discord_id=actor_discord_id,
            now_utc=now,
        )
        if not demote_ok:
            return mge_roster_service.RosterResult(
                False, "Failed to demote selected roster player."
            )

        promote_target_rank = (
            _to_int(demote_row.get("ComputedAwardedRank") or demote_row.get("AwardedRank"), 0) or 1
        )

        promote_ok = mge_roster_dal.update_award(
            award_id=int(promote_award_id),
            awarded_rank=promote_target_rank,
            award_status="awarded",
            waitlist_order=None,
            internal_notes=(notes or None),
            manual_order_override=False,
            assigned_by_discord_id=actor_discord_id,
            now_utc=now,
        )
        if not promote_ok:
            return mge_roster_service.RosterResult(
                False, "Failed to promote selected waitlist player."
            )

        mge_roster_dal.insert_award_audit(
            award_id=int(demote_award_id),
            event_id=int(event_id),
            governor_id=_to_int(demote_row.get("GovernorId")),
            action_type="demote_to_waitlist",
            actor_discord_id=actor_discord_id,
            old_rank=(
                _to_int(demote_row.get("AwardedRank"))
                if demote_row.get("AwardedRank") is not None
                else None
            ),
            new_rank=None,
            old_status=str(
                demote_row.get("AwardStatusRaw") or demote_row.get("AwardStatus") or "awarded"
            ),
            new_status="waitlist",
            old_target_score=(
                _to_int(demote_row.get("TargetScore"))
                if demote_row.get("TargetScore") is not None
                else None
            ),
            new_target_score=(
                _to_int(demote_row.get("TargetScore"))
                if demote_row.get("TargetScore") is not None
                else None
            ),
            details={
                "waitlist_order": next_waitlist_order,
                "swap_promote_award_id": int(promote_award_id),
            },
            now_utc=now,
        )
        mge_roster_dal.insert_award_audit(
            award_id=int(promote_award_id),
            event_id=int(event_id),
            governor_id=_to_int(promote_row.get("GovernorId")),
            action_type="promote_from_waitlist_swap",
            actor_discord_id=actor_discord_id,
            old_rank=None,
            new_rank=promote_target_rank,
            old_status="waitlist",
            new_status="awarded",
            old_target_score=(
                _to_int(promote_row.get("TargetScore"))
                if promote_row.get("TargetScore") is not None
                else None
            ),
            new_target_score=(
                _to_int(promote_row.get("TargetScore"))
                if promote_row.get("TargetScore") is not None
                else None
            ),
            details={"demoted_award_id": int(demote_award_id)},
            now_utc=now,
        )
        _maybe_regenerate_targets(int(event_id), actor_discord_id, now)
        return mge_roster_service.RosterResult(
            True,
            "Promoted selected waitlist player and demoted selected roster player to end of waitlist.",
        )

    result = mge_roster_service.promote_waitlist_to_roster(
        award_id=int(promote_award_id),
        actor_discord_id=actor_discord_id,
        notes=notes,
    )
    if result.success:
        _maybe_regenerate_targets(int(event_id), actor_discord_id, datetime.now(UTC))
    return result


def reset_active_ranks(*, event_id: int, actor_discord_id: int) -> mge_roster_service.RosterResult:
    """Reset active roster/waitlist ordering to simplified-flow order and clear manual overrides."""
    dataset = get_ordered_leadership_rows(event_id)
    now = datetime.now(UTC)

    affected = 0
    for row in dataset.get("roster_rows", []):
        award_id = _to_int(row.get("AwardId"))
        if award_id <= 0:
            continue
        ok = mge_roster_dal.update_award(
            award_id=award_id,
            awarded_rank=_to_int(row.get("ComputedAwardedRank")),
            award_status=str(row.get("AwardStatusRaw") or row.get("AwardStatus") or "awarded"),
            waitlist_order=None,
            internal_notes=str(row.get("InternalNotes") or "") or None,
            manual_order_override=False,
            assigned_by_discord_id=actor_discord_id,
            now_utc=now,
        )
        if not ok:
            return mge_roster_service.RosterResult(False, "Failed to reset roster ranks.")
        affected += 1

    for row in dataset.get("waitlist_rows", []):
        award_id = _to_int(row.get("AwardId"))
        if award_id <= 0:
            continue
        ok = mge_roster_dal.update_award(
            award_id=award_id,
            awarded_rank=None,
            award_status="waitlist",
            waitlist_order=_to_int(row.get("ComputedWaitlistOrder")),
            internal_notes=str(row.get("InternalNotes") or "") or None,
            manual_order_override=False,
            assigned_by_discord_id=actor_discord_id,
            now_utc=now,
        )
        if not ok:
            return mge_roster_service.RosterResult(False, "Failed to reset waitlist order.")
        affected += 1

    logger.info(
        "mge_simplified_leadership_reset_ranks_success event_id=%s actor_discord_id=%s affected=%s",
        event_id,
        actor_discord_id,
        affected,
    )
    _maybe_regenerate_targets(event_id, actor_discord_id, now)
    return mge_roster_service.RosterResult(
        True,
        f"Reset ranks for {affected} active signup(s).",
    )
