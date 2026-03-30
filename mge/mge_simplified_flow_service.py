"""Simplified-flow ordering and publish-readiness logic for MGE."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from mge.dal import mge_review_dal, mge_roster_dal

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_ACTIVE_STATUSES = {"roster", "waitlist"}
_ROSTER_STATUSES = {"roster", "awarded"}
_WAITLIST_STATUSES = {"waitlist"}
_REJECTED_STATUSES = {"rejected"}
_UNASSIGNED_STATUSES = {"unassigned"}
_PERSISTED_AWARDED_STATUSES = {"awarded", "roster"}
_MAX_ROSTER = 15


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_datetime_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return datetime.max.replace(tzinfo=UTC)


def normalize_priority(value: Any) -> str:
    """Normalize MGE request priority for sorting and display."""
    text = _as_text(value).lower()
    if text in _PRIORITY_ORDER:
        return text
    return "unknown"


def _persisted_award_status(value: Any) -> str:
    """Return the raw persisted award status or 'unassigned' when missing."""
    text = _as_text(value).lower()
    if not text:
        return "unassigned"
    return text


def normalize_status(value: Any) -> str:
    """Normalize award/signup status to simplified-flow semantics."""
    text = _persisted_award_status(value)
    if text in _ROSTER_STATUSES:
        return "roster"
    if text in _WAITLIST_STATUSES:
        return "waitlist"
    if text in _REJECTED_STATUSES:
        return "rejected"
    if text in _UNASSIGNED_STATUSES:
        return "unassigned"
    return "unassigned"


def is_active_status(value: Any) -> bool:
    """Return whether the provided status participates in active ordering."""
    return normalize_status(value) in _ACTIVE_STATUSES


def kvk_rank_value(row: dict[str, Any]) -> int | None:
    """Return the best available KVK rank for simplified ordering."""
    for key in ("LatestKVKRank", "LastKVKRank"):
        parsed = _as_int(row.get(key))
        if parsed is not None and parsed > 0:
            return parsed
    return None


def signup_auto_sort_key(row: dict[str, Any]) -> tuple[int, int, int, datetime, int]:
    """Build the simplified-flow auto ordering key for signup/review rows."""
    rank = kvk_rank_value(row)
    return (
        _PRIORITY_ORDER.get(normalize_priority(row.get("RequestPriority")), 99),
        1 if rank is None else 0,
        rank if rank is not None else 999_999_999,
        _as_datetime_utc(row.get("SignupCreatedUtc")),
        _as_int(row.get("SignupId")) or 999_999_999,
    )


def sort_review_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return review rows ordered by simplified-flow signup rules."""
    ordered = sorted((dict(row) for row in rows), key=signup_auto_sort_key)
    logger.info("mge_simplified_flow_sort_review_rows count=%s", len(ordered))
    return ordered


def _self_heal_assign_unassigned(
    review_rows: list[dict[str, Any]],
    award_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Ensure active non-rejected signups are persisted as roster/waitlist rows.

    Policy:
    - existing roster/waitlist/rejected rows are preserved
    - unassigned rows are auto-placed by sorted priority:
        first 15 -> roster
        16+ -> waitlist
    """
    existing_by_signup: dict[int, dict[str, Any]] = {}
    roster_count = 0
    waitlist_max = 0
    used_ranks: set[int] = set()
    used_waitlist: set[int] = set()

    for row in award_rows:
        sid = _as_int(row.get("SignupId"))
        if sid is None:
            continue
        if sid not in existing_by_signup:
            existing_by_signup[sid] = row
        status = _persisted_award_status(row.get("AwardStatus"))
        if status in _PERSISTED_AWARDED_STATUSES:
            roster_count += 1
            r = _as_int(row.get("AwardedRank")) or 0
            if r > 0:
                used_ranks.add(r)
        elif status == "waitlist":
            w = _as_int(row.get("WaitlistOrder")) or 0
            if w > 0:
                used_waitlist.add(w)
                waitlist_max = max(waitlist_max, w)

    def _next_roster_rank() -> int | None:
        if roster_count >= _MAX_ROSTER:
            return None
        for n in range(1, _MAX_ROSTER + 1):
            if n not in used_ranks:
                return n
        return None

    def _next_waitlist_order() -> int:
        nonlocal waitlist_max
        waitlist_max += 1
        while waitlist_max in used_waitlist:
            waitlist_max += 1
        used_waitlist.add(waitlist_max)
        return waitlist_max

    now = datetime.now(UTC)

    for rr in sort_review_rows(review_rows):
        sid = _as_int(rr.get("SignupId"))
        gid = _as_int(rr.get("GovernorId"))
        if sid is None or gid is None or sid <= 0 or gid <= 0:
            continue

        existing = existing_by_signup.get(sid)
        if existing:
            existing_status = _persisted_award_status(existing.get("AwardStatus"))
            if existing_status == "rejected":
                continue
            if existing_status in _PERSISTED_AWARDED_STATUSES or existing_status == "waitlist":
                continue

        if roster_count < _MAX_ROSTER:
            rank = _next_roster_rank()
            if rank is None:
                rank = 1
            aid = mge_roster_dal.insert_award(
                event_id=_as_int(rr.get("EventId")) or _as_int(rr.get("MGEEventId")) or 0,
                signup_id=sid,
                governor_id=gid,
                governor_name_snapshot=str(
                    rr.get("GovernorNameSnapshot") or rr.get("GovernorName") or "Unknown"
                ),
                requested_commander_id=_as_int(rr.get("RequestedCommanderId")) or 0,
                requested_commander_name=str(rr.get("RequestedCommanderName") or ""),
                awarded_rank=rank,
                award_status="awarded",
                waitlist_order=None,
                manual_order_override=False,
                internal_notes=None,
                assigned_by_discord_id=0,
                now_utc=now,
            )
            if aid is not None:
                roster_count += 1
                used_ranks.add(rank)
        else:
            order = _next_waitlist_order()
            aid = mge_roster_dal.insert_award(
                event_id=_as_int(rr.get("EventId")) or _as_int(rr.get("MGEEventId")) or 0,
                signup_id=sid,
                governor_id=gid,
                governor_name_snapshot=str(
                    rr.get("GovernorNameSnapshot") or rr.get("GovernorName") or "Unknown"
                ),
                requested_commander_id=_as_int(rr.get("RequestedCommanderId")) or 0,
                requested_commander_name=str(rr.get("RequestedCommanderName") or ""),
                awarded_rank=None,
                award_status="waitlist",
                waitlist_order=order,
                manual_order_override=False,
                internal_notes=None,
                assigned_by_discord_id=0,
                now_utc=now,
            )
            if aid is not None:
                used_waitlist.add(order)

    return mge_roster_dal.fetch_event_awards(
        _as_int(review_rows[0].get("EventId")) if review_rows else 0
    )


def merge_review_and_award_rows(
    review_rows: list[dict[str, Any]], award_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    award_by_signup_id: dict[int, dict[str, Any]] = {}
    for row in award_rows:
        signup_id = _as_int(row.get("SignupId"))
        if signup_id is not None and signup_id not in award_by_signup_id:
            award_by_signup_id[signup_id] = row

    merged: list[dict[str, Any]] = []
    for review_row in review_rows:
        combined = dict(review_row)
        signup_id = _as_int(review_row.get("SignupId")) or -1
        award_row = award_by_signup_id.get(signup_id)
        raw_award_status = award_row.get("AwardStatus") if award_row else "unassigned"
        status = normalize_status(raw_award_status)

        combined["AwardStatus"] = _persisted_award_status(raw_award_status)
        combined["SimplifiedStatus"] = status
        combined["AwardStatusNormalized"] = status
        combined["AwardStatusRaw"] = _persisted_award_status(raw_award_status)
        combined["ManualOrderOverride"] = bool(
            _as_int(award_row.get("ManualOrderOverride")) if award_row else 0
        )
        combined["AwardId"] = award_row.get("AwardId") if award_row else None
        combined["AwardedRank"] = award_row.get("AwardedRank") if award_row else None
        combined["WaitlistOrder"] = award_row.get("WaitlistOrder") if award_row else None
        combined["TargetScore"] = award_row.get("TargetScore") if award_row else None
        combined["AssignedByDiscordId"] = (
            award_row.get("AssignedByDiscordId") if award_row else None
        )
        merged.append(combined)
    return merged


def _assign_roster_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manual_rows = [
        dict(row)
        for row in rows
        if bool(row.get("ManualOrderOverride")) and (_as_int(row.get("AwardedRank")) or 0) > 0
    ]
    auto_rows = [
        dict(row)
        for row in rows
        if not (bool(row.get("ManualOrderOverride")) and (_as_int(row.get("AwardedRank")) or 0) > 0)
    ]

    manual_rows.sort(
        key=lambda row: (
            (_as_int(row.get("AwardedRank")) or 999_999_999),
            signup_auto_sort_key(row),
        )
    )
    occupied = {
        _as_int(row.get("AwardedRank"))
        for row in manual_rows
        if (_as_int(row.get("AwardedRank")) or 0) > 0
    }

    auto_rows.sort(key=signup_auto_sort_key)
    next_rank = 1
    for row in auto_rows:
        while next_rank in occupied:
            next_rank += 1
        row["ComputedAwardedRank"] = next_rank
        occupied.add(next_rank)
        next_rank += 1

    out = []
    for row in manual_rows:
        row["ComputedAwardedRank"] = _as_int(row.get("AwardedRank"))
        out.append(row)
    out.extend(auto_rows)
    out.sort(
        key=lambda row: (
            _as_int(row.get("ComputedAwardedRank")) or 999_999_999,
            signup_auto_sort_key(row),
        )
    )
    return out


def _assign_waitlist_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = [dict(row) for row in rows]
    ordered.sort(
        key=lambda row: (
            (
                0
                if bool(row.get("ManualOrderOverride"))
                and (_as_int(row.get("WaitlistOrder")) or 0) > 0
                else 1
            ),
            (_as_int(row.get("WaitlistOrder")) or 999_999_999),
            signup_auto_sort_key(row),
        )
    )
    next_order = 1
    occupied = set()
    for row in ordered:
        explicit = _as_int(row.get("WaitlistOrder"))
        if (
            bool(row.get("ManualOrderOverride"))
            and (explicit or 0) > 0
            and explicit not in occupied
        ):
            row["ComputedWaitlistOrder"] = explicit
            occupied.add(explicit)
            continue
        while next_order in occupied:
            next_order += 1
        row["ComputedWaitlistOrder"] = next_order
        occupied.add(next_order)
        next_order += 1
    ordered.sort(
        key=lambda row: (
            _as_int(row.get("ComputedWaitlistOrder")) or 999_999_999,
            signup_auto_sort_key(row),
        )
    )
    return ordered


def build_leadership_ordered_dataset(
    review_rows: list[dict[str, Any]], award_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    if review_rows:
        healed_awards = _self_heal_assign_unassigned(review_rows, award_rows)
    else:
        healed_awards = award_rows

    merged = merge_review_and_award_rows(review_rows, healed_awards)

    roster_rows = _assign_roster_positions(
        [row for row in merged if normalize_status(row.get("SimplifiedStatus")) == "roster"]
    )
    waitlist_rows = _assign_waitlist_positions(
        [row for row in merged if normalize_status(row.get("SimplifiedStatus")) == "waitlist"]
    )
    unassigned_rows = sorted(
        [row for row in merged if normalize_status(row.get("SimplifiedStatus")) == "unassigned"],
        key=signup_auto_sort_key,
    )
    rejected_rows = sorted(
        [row for row in merged if normalize_status(row.get("SimplifiedStatus")) == "rejected"],
        key=signup_auto_sort_key,
    )
    active_rows = roster_rows + waitlist_rows

    return {
        "rows": merged,
        "active_rows": active_rows,
        "roster_rows": roster_rows,
        "waitlist_rows": waitlist_rows,
        "unassigned_rows": unassigned_rows,
        "rejected_rows": rejected_rows,
        "counts": {
            "total_signups": len(merged),
            "roster_count": len(roster_rows),
            "waitlist_count": len(waitlist_rows),
            "unassigned_count": len(unassigned_rows),
            "rejected_count": len(rejected_rows),
        },
    }


def _is_persisted_awarded_row(row: dict[str, Any]) -> bool:
    raw_status = _persisted_award_status(row.get("AwardStatusRaw", row.get("AwardStatus")))
    return raw_status in _PERSISTED_AWARDED_STATUSES


def _is_persisted_waitlist_row(row: dict[str, Any]) -> bool:
    return (
        _persisted_award_status(row.get("AwardStatusRaw") or row.get("AwardStatus")) == "waitlist"
    )


def _is_persisted_rejected_row(row: dict[str, Any]) -> bool:
    return (
        _persisted_award_status(row.get("AwardStatusRaw") or row.get("AwardStatus")) == "rejected"
    )


def get_ordered_signup_rows(event_id: int) -> list[dict[str, Any]]:
    rows = mge_review_dal.fetch_signup_review_rows(event_id)
    return sort_review_rows(rows)


def get_public_signup_rows(event_id: int) -> list[dict[str, Any]]:
    review_rows = sort_review_rows(mge_review_dal.fetch_signup_review_rows(event_id))
    award_rows = mge_roster_dal.fetch_event_awards(event_id)
    merged = merge_review_and_award_rows(review_rows, award_rows)
    return [row for row in merged if not _is_persisted_rejected_row(row)]


def get_ordered_leadership_rows(event_id: int) -> dict[str, Any]:
    review_rows = mge_review_dal.fetch_signup_review_rows(event_id)
    award_rows = mge_roster_dal.fetch_event_awards(event_id)
    return build_leadership_ordered_dataset(review_rows, award_rows)


def evaluate_publish_readiness(event_id: int) -> dict[str, Any]:
    dataset = get_ordered_leadership_rows(event_id)

    rows = dataset.get("rows") or dataset.get("roster_rows", [])
    published_roster_rows = [row for row in rows if _is_persisted_awarded_row(row)]
    persisted_waitlist_rows = [row for row in rows if _is_persisted_waitlist_row(row)]
    persisted_rejected_rows = [row for row in rows if _is_persisted_rejected_row(row)]

    counts = {
        "total_signups": int(dataset.get("counts", {}).get("total_signups", len(rows))),
        "roster_count": len(published_roster_rows),
        "waitlist_count": len(persisted_waitlist_rows),
        "rejected_count": len(persisted_rejected_rows),
    }

    reasons: list[str] = []
    if counts["roster_count"] > 15:
        reasons.append("roster_count_exceeds_limit")

    missing_target_count = 0
    for row in published_roster_rows:
        value = row.get("TargetScore")
        if value is None or _as_text(value) == "":
            missing_target_count += 1

    if missing_target_count > 0:
        reasons.append("missing_roster_targets")

    publish_ready = not reasons
    status_text = (
        "Ready to publish."
        if publish_ready
        else "Publish blocked: "
        + " ".join(
            [
                (
                    "Roster has more than 15 entries."
                    if "roster_count_exceeds_limit" in reasons
                    else ""
                ),
                (
                    "Every rostered signup must have a target value."
                    if "missing_roster_targets" in reasons
                    else ""
                ),
            ]
        ).strip()
    )

    return {
        **counts,
        "publish_ready": publish_ready,
        "publish_status_text": status_text,
        "publish_block_reason_codes": reasons,
        "missing_roster_target_count": missing_target_count,
    }
