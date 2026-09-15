"""Service layer for Task-I leadership roster builder (Option B)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
import threading
from typing import Any

from mge.dal import mge_roster_dal

logger = logging.getLogger(__name__)

_MAX_AWARDED = 15
_UNDO_TTL = timedelta(minutes=20)
_UNDO_MAX = 200
_UNDO_LOCK = threading.Lock()


@dataclass(slots=True)
class RosterResult:
    success: bool
    message: str
    award_id: int | None = None


@dataclass(slots=True)
class RosterState:
    awarded: list[dict[str, Any]]
    waitlist: list[dict[str, Any]]
    other: list[dict[str, Any]]


@dataclass(slots=True)
class UndoEntry:
    snapshot: dict[str, Any]
    created_at: datetime


_UNDO_BUFFER: dict[tuple[int, int], UndoEntry] = {}


def _now_utc(now_utc: datetime | None = None) -> datetime:
    if now_utc is None:
        return datetime.now(UTC)
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=UTC)
    return now_utc.astimezone(UTC)


def clear_undo_session(event_id: int, actor_discord_id: int) -> None:
    key = (int(event_id), int(actor_discord_id))
    with _UNDO_LOCK:
        _UNDO_BUFFER.pop(key, None)


def _restore_undo_if_absent(key: tuple[int, int], entry: UndoEntry) -> None:
    with _UNDO_LOCK:
        if key not in _UNDO_BUFFER:
            _UNDO_BUFFER[key] = entry


def prune_undo_buffer(now_utc: datetime | None = None) -> None:
    now = _now_utc(now_utc)
    with _UNDO_LOCK:
        expired = [k for k, v in _UNDO_BUFFER.items() if now - v.created_at > _UNDO_TTL]
        for k in expired:
            _UNDO_BUFFER.pop(k, None)

        if len(_UNDO_BUFFER) > _UNDO_MAX:
            oldest = sorted(_UNDO_BUFFER.items(), key=lambda x: x[1].created_at)[
                : len(_UNDO_BUFFER) - _UNDO_MAX
            ]
            for k, _ in oldest:
                _UNDO_BUFFER.pop(k, None)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _merge_notes(existing: str | None, extra: str | None) -> str | None:
    existing_text = str(existing or "").strip()
    extra_text = str(extra or "").strip()
    if existing_text and extra_text:
        return f"{existing_text}\n{extra_text}"
    if existing_text:
        return existing_text
    if extra_text:
        return extra_text
    return None


def load_roster_state(event_id: int) -> RosterState:
    rows = mge_roster_dal.fetch_event_awards(event_id)
    awarded = [r for r in rows if _status(r.get("AwardStatus")) == "awarded"]
    waitlist = [r for r in rows if _status(r.get("AwardStatus")) == "waitlist"]
    other = [r for r in rows if _status(r.get("AwardStatus")) not in {"awarded", "waitlist"}]
    awarded.sort(key=lambda r: (_to_int(r.get("AwardedRank"), 999), _to_int(r.get("AwardId"), 0)))
    waitlist.sort(
        key=lambda r: (_to_int(r.get("WaitlistOrder"), 999), _to_int(r.get("AwardId"), 0))
    )
    return RosterState(awarded=awarded, waitlist=waitlist, other=other)


def _ensure_no_duplicate_governor(event_id: int, governor_id: int) -> bool:
    rows = mge_roster_dal.fetch_event_awards(event_id)
    return all(_to_int(r.get("GovernorId")) != governor_id for r in rows)


def _next_awarded_rank(event_id: int) -> int | None:
    state = load_roster_state(event_id)
    if len(state.awarded) >= _MAX_AWARDED:
        return None
    used = {_to_int(r.get("AwardedRank")) for r in state.awarded}
    for n in range(1, _MAX_AWARDED + 1):
        if n not in used:
            return n
    return None


def _next_waitlist_order(event_id: int) -> int:
    state = load_roster_state(event_id)
    if not state.waitlist:
        return 1
    return max(_to_int(r.get("WaitlistOrder")) for r in state.waitlist) + 1


def add_signup_to_roster(
    *,
    event_id: int,
    signup_id: int,
    actor_discord_id: int,
    internal_notes: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    now = _now_utc(now_utc)
    signup = mge_roster_dal.fetch_signup_snapshot(signup_id, event_id)
    if not signup:
        return RosterResult(False, "Signup not found for event.")
    if _to_int(signup.get("IsActive")) != 1:
        return RosterResult(False, "Signup is not active.")

    governor_id = _to_int(signup.get("GovernorId"))
    if not _ensure_no_duplicate_governor(event_id, governor_id):
        return RosterResult(False, "Governor already exists in roster/waitlist.")

    rank = _next_awarded_rank(event_id)
    if rank is None:
        return RosterResult(False, "Cannot add: awarded roster is full (15).")

    aid = mge_roster_dal.insert_award(
        event_id=event_id,
        signup_id=signup_id,
        governor_id=governor_id,
        governor_name_snapshot=str(signup.get("GovernorNameSnapshot") or "Unknown"),
        requested_commander_id=_to_int(signup.get("RequestedCommanderId")),
        requested_commander_name=str(signup.get("RequestedCommanderName") or ""),
        awarded_rank=rank,
        award_status="awarded",
        waitlist_order=None,
        internal_notes=internal_notes,
        assigned_by_discord_id=actor_discord_id,
        now_utc=now,
    )
    if aid is None:
        return RosterResult(False, "Failed to add signup to awarded roster.")

    mge_roster_dal.insert_award_audit(
        award_id=aid,
        event_id=event_id,
        governor_id=governor_id,
        action_type="add_awarded",
        actor_discord_id=actor_discord_id,
        old_rank=None,
        new_rank=rank,
        old_status=None,
        new_status="awarded",
        old_target_score=None,
        new_target_score=None,
        details={"signup_id": signup_id},
        now_utc=now,
    )
    logger.info(
        "mge_roster_service_add_signup_success event_id=%s signup_id=%s award_id=%s rank=%s",
        event_id,
        signup_id,
        aid,
        rank,
    )
    return RosterResult(True, "Added to awarded roster.", award_id=aid)


def add_signup_with_rank(
    *,
    event_id: int,
    signup_id: int,
    target_rank: int,
    actor_discord_id: int,
    internal_notes: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    if target_rank < 1 or target_rank > _MAX_AWARDED:
        return RosterResult(False, "Rank must be between 1 and 15.")

    now = _now_utc(now_utc)
    signup = mge_roster_dal.fetch_signup_snapshot(signup_id, event_id)
    if not signup:
        return RosterResult(False, "Signup not found for event.")
    if _to_int(signup.get("IsActive")) != 1:
        return RosterResult(False, "Signup is not active.")

    governor_id = _to_int(signup.get("GovernorId"))
    if not _ensure_no_duplicate_governor(event_id, governor_id):
        return RosterResult(False, "Governor already exists in roster/waitlist.")

    state = load_roster_state(event_id)
    used_ranks = {_to_int(r.get("AwardedRank")) for r in state.awarded}
    if len(state.awarded) >= _MAX_AWARDED:
        return RosterResult(False, "Cannot add: awarded roster is full (15).")
    if target_rank in used_ranks:
        return RosterResult(False, "That rank is already occupied.")

    aid = mge_roster_dal.insert_award(
        event_id=event_id,
        signup_id=signup_id,
        governor_id=governor_id,
        governor_name_snapshot=str(signup.get("GovernorNameSnapshot") or "Unknown"),
        requested_commander_id=_to_int(signup.get("RequestedCommanderId")),
        requested_commander_name=str(signup.get("RequestedCommanderName") or ""),
        awarded_rank=int(target_rank),
        award_status="awarded",
        waitlist_order=None,
        internal_notes=internal_notes,
        assigned_by_discord_id=actor_discord_id,
        now_utc=now,
    )
    if aid is None:
        return RosterResult(False, "Failed to add signup to awarded roster.")

    mge_roster_dal.insert_award_audit(
        award_id=aid,
        event_id=event_id,
        governor_id=governor_id,
        action_type="add_awarded",
        actor_discord_id=actor_discord_id,
        old_rank=None,
        new_rank=int(target_rank),
        old_status=None,
        new_status="awarded",
        old_target_score=None,
        new_target_score=None,
        details={"signup_id": signup_id, "requested_rank": int(target_rank)},
        now_utc=now,
    )
    logger.info(
        "mge_roster_service_add_signup_with_rank_success event_id=%s signup_id=%s award_id=%s rank=%s",
        event_id,
        signup_id,
        aid,
        target_rank,
    )
    return RosterResult(True, "Added to awarded roster.", award_id=aid)


def set_rank(
    *, award_id: int, new_rank: int, actor_discord_id: int, now_utc: datetime | None = None
) -> RosterResult:
    if new_rank < 1 or new_rank > _MAX_AWARDED:
        return RosterResult(False, "Rank must be between 1 and 15.")
    now = _now_utc(now_utc)
    result = mge_roster_dal.apply_set_rank_atomic(
        award_id=award_id,
        new_rank=new_rank,
        actor_discord_id=actor_discord_id,
        now_utc=now,
    )
    if not result:
        return RosterResult(False, "Failed to set rank.")
    if result.get("error") == "rank_collision_without_current_rank":
        return RosterResult(False, "Cannot take occupied rank from waitlist/pending row.")
    if result.get("error"):
        return RosterResult(False, "Failed to set rank.")
    return RosterResult(True, "Rank updated.", award_id=award_id)


def move_rank_up(
    *,
    award_id: int,
    actor_discord_id: int,
    now_utc: datetime | None = None,
) -> RosterResult:
    row = mge_roster_dal.fetch_award_by_id(award_id)
    if not row:
        return RosterResult(False, "Award row not found.")
    current = _to_int(row.get("AwardedRank"), 0)
    if current <= 1:
        return RosterResult(False, "Cannot move up.")
    return set_rank(
        award_id=award_id,
        new_rank=current - 1,
        actor_discord_id=actor_discord_id,
        now_utc=now_utc,
    )


def move_rank_down(
    *,
    award_id: int,
    actor_discord_id: int,
    now_utc: datetime | None = None,
) -> RosterResult:
    row = mge_roster_dal.fetch_award_by_id(award_id)
    if not row:
        return RosterResult(False, "Award row not found.")
    current = _to_int(row.get("AwardedRank"), 0)
    if current <= 0 or current >= _MAX_AWARDED:
        return RosterResult(False, "Cannot move down.")
    return set_rank(
        award_id=award_id,
        new_rank=current + 1,
        actor_discord_id=actor_discord_id,
        now_utc=now_utc,
    )


def move_to_waitlist(
    *,
    award_id: int,
    actor_discord_id: int,
    waitlist_order: int | None = None,
    notes: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    now = _now_utc(now_utc)
    row = mge_roster_dal.fetch_award_by_id(award_id)
    if not row:
        return RosterResult(False, "Award row not found.")
    event_id = _to_int(row.get("EventId"))
    order = waitlist_order if waitlist_order is not None else _next_waitlist_order(event_id)
    merged_notes = _merge_notes(row.get("InternalNotes"), notes)
    ok = mge_roster_dal.update_award(
        award_id=award_id,
        awarded_rank=None,
        award_status="waitlist",
        waitlist_order=int(order),
        internal_notes=merged_notes,
        manual_order_override=True,
        assigned_by_discord_id=actor_discord_id,
        now_utc=now,
    )
    if not ok:
        return RosterResult(False, "Failed to move to waitlist.")
    mge_roster_dal.insert_award_audit(
        award_id=award_id,
        event_id=event_id,
        governor_id=_to_int(row.get("GovernorId")),
        action_type="move_waitlist",
        actor_discord_id=actor_discord_id,
        old_rank=row.get("AwardedRank"),
        new_rank=None,
        old_status=str(row.get("AwardStatus") or ""),
        new_status="waitlist",
        old_target_score=row.get("TargetScore"),
        new_target_score=row.get("TargetScore"),
        details={"waitlist_order": int(order)},
        now_utc=now,
    )
    return RosterResult(True, "Moved to waitlist.", award_id=award_id)


def set_waitlist_order(
    *, award_id: int, waitlist_order: int, actor_discord_id: int, now_utc: datetime | None = None
) -> RosterResult:
    if waitlist_order <= 0:
        return RosterResult(False, "Waitlist order must be >= 1.")
    now = _now_utc(now_utc)
    row = mge_roster_dal.fetch_award_by_id(award_id)
    if not row:
        return RosterResult(False, "Award row not found.")
    if _status(row.get("AwardStatus")) != "waitlist":
        return RosterResult(False, "Only waitlist rows can set waitlist order.")
    ok = mge_roster_dal.update_award(
        award_id=award_id,
        awarded_rank=None,
        award_status="waitlist",
        waitlist_order=int(waitlist_order),
        internal_notes=str(row.get("InternalNotes") or "") or None,
        manual_order_override=True,
        assigned_by_discord_id=actor_discord_id,
        now_utc=now,
    )
    if not ok:
        return RosterResult(False, "Failed to set waitlist order.")
    return RosterResult(True, "Waitlist order updated.", award_id=award_id)


def update_internal_notes(
    *, award_id: int, notes: str | None, actor_discord_id: int, now_utc: datetime | None = None
) -> RosterResult:
    now = _now_utc(now_utc)
    row = mge_roster_dal.fetch_award_by_id(award_id)
    if not row:
        return RosterResult(False, "Award row not found.")
    ok = mge_roster_dal.update_award(
        award_id=award_id,
        awarded_rank=(
            _to_int(row.get("AwardedRank")) if row.get("AwardedRank") is not None else None
        ),
        award_status=str(row.get("AwardStatus") or "pending"),
        waitlist_order=(
            _to_int(row.get("WaitlistOrder")) if row.get("WaitlistOrder") is not None else None
        ),
        internal_notes=notes,
        manual_order_override=bool(_to_int(row.get("ManualOrderOverride"), 0)),
        assigned_by_discord_id=actor_discord_id,
        now_utc=now,
    )
    if not ok:
        return RosterResult(False, "Failed to update internal notes.")
    return RosterResult(True, "Internal notes updated.", award_id=award_id)


def promote_waitlist_to_roster(
    *,
    award_id: int,
    actor_discord_id: int,
    notes: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    now = _now_utc(now_utc)
    row = mge_roster_dal.fetch_award_by_id(award_id)
    if not row:
        return RosterResult(False, "Award row not found.")
    if _status(row.get("AwardStatus")) != "waitlist":
        return RosterResult(False, "Only waitlist rows can be promoted to roster.")

    result = mge_roster_dal.promote_waitlist_to_awarded_atomic(
        award_id=award_id,
        actor_discord_id=actor_discord_id,
        now_utc=now,
        extra_notes=notes,
    )
    if not result:
        return RosterResult(False, "Failed to promote waitlist row to roster.")
    if result.get("error") == "not_waitlist":
        return RosterResult(False, "Only waitlist rows can be promoted to roster.")
    if result.get("error") == "roster_full":
        return RosterResult(False, "Cannot promote: awarded roster is full (15).")
    if result.get("error"):
        return RosterResult(False, "Failed to promote waitlist row to roster.")

    return RosterResult(True, "Moved from waitlist to roster.", award_id=award_id)


def remove_award_hard_delete(
    *,
    award_id: int,
    actor_discord_id: int,
    event_id: int,
    session_key: tuple[int, int] | None = None,
    removal_reason: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    now = _now_utc(now_utc)
    prune_undo_buffer(now)
    deleted = mge_roster_dal.delete_award_with_audit_atomic(
        award_id=award_id,
        actor_discord_id=actor_discord_id,
        action_type="remove",
        details={"hard_delete": True, "reason": removal_reason or ""},
        now_utc=now,
    )
    if not deleted:
        return RosterResult(False, "Failed to remove row from roster/waitlist.")
    if session_key:
        with _UNDO_LOCK:
            _UNDO_BUFFER[session_key] = UndoEntry(snapshot=deleted, created_at=now)
    return RosterResult(True, "Entry removed.", award_id=award_id)


def undo_last_removal_in_session(
    *, event_id: int, actor_discord_id: int, now_utc: datetime | None = None
) -> RosterResult:
    now = _now_utc(now_utc)
    prune_undo_buffer(now)
    key = (int(event_id), int(actor_discord_id))

    with _UNDO_LOCK:
        entry = _UNDO_BUFFER.pop(key, None)
    if not entry:
        return RosterResult(False, "No removal to undo in this session.")

    snap = entry.snapshot
    governor_id = _to_int(snap.get("GovernorId"))
    if not _ensure_no_duplicate_governor(event_id, governor_id):
        _restore_undo_if_absent(key, entry)
        return RosterResult(False, "Cannot undo: governor already re-added.")

    aid = mge_roster_dal.insert_award(
        event_id=event_id,
        signup_id=_to_int(snap.get("SignupId")),
        governor_id=governor_id,
        governor_name_snapshot=str(snap.get("GovernorNameSnapshot") or "Unknown"),
        requested_commander_id=_to_int(snap.get("RequestedCommanderId")),
        requested_commander_name=str(snap.get("RequestedCommanderName") or ""),
        awarded_rank=(
            _to_int(snap.get("AwardedRank")) if snap.get("AwardedRank") is not None else None
        ),
        award_status=str(snap.get("AwardStatus") or "pending"),
        waitlist_order=(
            _to_int(snap.get("WaitlistOrder")) if snap.get("WaitlistOrder") is not None else None
        ),
        manual_order_override=bool(_to_int(snap.get("ManualOrderOverride"), 0)),
        internal_notes=str(snap.get("InternalNotes") or "") or None,
        assigned_by_discord_id=actor_discord_id,
        now_utc=now,
    )
    if aid is None:
        _restore_undo_if_absent(key, entry)
        return RosterResult(False, "Failed to undo removal.")

    return RosterResult(True, "Undo complete; entry re-added.", award_id=aid)


def reject_signup_audit_only(
    *,
    event_id: int,
    signup_id: int,
    actor_discord_id: int,
    reason: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    now = _now_utc(now_utc)
    signup = mge_roster_dal.fetch_signup_snapshot(signup_id, event_id)
    if not signup:
        return RosterResult(False, "Signup not found for event.")
    ok = mge_roster_dal.insert_award_audit(
        award_id=0,
        event_id=event_id,
        governor_id=_to_int(signup.get("GovernorId")),
        action_type="reject",
        actor_discord_id=actor_discord_id,
        old_rank=None,
        new_rank=None,
        old_status=None,
        new_status="rejected",
        old_target_score=None,
        new_target_score=None,
        details={"signup_id": int(signup_id), "reason": reason or ""},
        now_utc=now,
    )
    if not ok:
        return RosterResult(False, "Failed to audit rejection.")
    return RosterResult(True, "Applicant rejected (audit-only).")


def reject_signup(
    *,
    event_id: int,
    signup_id: int,
    actor_discord_id: int,
    reason: str | None = None,
    now_utc: datetime | None = None,
) -> RosterResult:
    """Persist a rejected signup using the award-side state model."""
    now = _now_utc(now_utc)
    signup = mge_roster_dal.fetch_signup_snapshot(signup_id, event_id)
    if not signup:
        return RosterResult(False, "Signup not found for event.")

    existing = mge_roster_dal.fetch_award_by_event_signup(event_id, signup_id)
    if existing:
        ok = mge_roster_dal.update_award(
            award_id=_to_int(existing.get("AwardId")),
            awarded_rank=None,
            award_status="rejected",
            waitlist_order=None,
            internal_notes=_merge_notes(existing.get("InternalNotes"), reason),
            manual_order_override=False,
            assigned_by_discord_id=actor_discord_id,
            now_utc=now,
        )
        if not ok:
            return RosterResult(False, "Failed to reject signup.")
        award_id = _to_int(existing.get("AwardId"))
        old_rank = (
            _to_int(existing.get("AwardedRank"))
            if existing.get("AwardedRank") is not None
            else None
        )
        old_status = str(existing.get("AwardStatus") or "")
    else:
        award_id = mge_roster_dal.insert_award(
            event_id=event_id,
            signup_id=signup_id,
            governor_id=_to_int(signup.get("GovernorId")),
            governor_name_snapshot=str(signup.get("GovernorNameSnapshot") or "Unknown"),
            requested_commander_id=_to_int(signup.get("RequestedCommanderId")),
            requested_commander_name=str(signup.get("RequestedCommanderName") or ""),
            awarded_rank=None,
            award_status="rejected",
            waitlist_order=None,
            manual_order_override=False,
            internal_notes=str(reason or "").strip() or None,
            assigned_by_discord_id=actor_discord_id,
            now_utc=now,
        )
        if award_id is None:
            return RosterResult(False, "Failed to reject signup.")
        old_rank = None
        old_status = None

    audited = mge_roster_dal.insert_award_audit(
        award_id=award_id,
        event_id=event_id,
        governor_id=_to_int(signup.get("GovernorId")),
        action_type="reject",
        actor_discord_id=actor_discord_id,
        old_rank=old_rank,
        new_rank=None,
        old_status=old_status,
        new_status="rejected",
        old_target_score=existing.get("TargetScore") if existing else None,
        new_target_score=existing.get("TargetScore") if existing else None,
        details={"signup_id": int(signup_id), "reason": reason or ""},
        now_utc=now,
    )
    if not audited:
        return RosterResult(False, "Failed to audit rejection.")

    logger.info(
        "mge_roster_service_reject_signup_success event_id=%s signup_id=%s award_id=%s actor_discord_id=%s",
        event_id,
        signup_id,
        award_id,
        actor_discord_id,
    )
    return RosterResult(True, "Signup rejected.", award_id=award_id)
