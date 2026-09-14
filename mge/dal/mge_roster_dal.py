"""DAL for MGE roster builder persistence and audit."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query

logger = logging.getLogger(__name__)

SQL_SELECT_EVENT_AWARDS = """
SELECT
    AwardId, EventId, SignupId, GovernorId, GovernorNameSnapshot,
    RequestedCommanderId, RequestedCommanderName, AwardedRank, TargetScore,
    AwardStatus, WaitlistOrder, ManualOrderOverride, InternalNotes, PublishVersion,
    AssignedByDiscordId, CreatedUtc, UpdatedUtc
FROM dbo.MGE_Awards
WHERE EventId = ?
ORDER BY
    CASE WHEN AwardStatus = 'awarded' THEN 0
         WHEN AwardStatus = 'waitlist' THEN 1
         ELSE 2 END,
    AwardedRank ASC,
    WaitlistOrder ASC,
    AwardId ASC;
"""

SQL_SELECT_SIGNUP_SNAPSHOT = """
SELECT TOP (1)
    SignupId, EventId, GovernorId, GovernorNameSnapshot,
    RequestedCommanderId, RequestedCommanderName, IsActive
FROM dbo.MGE_Signups
WHERE SignupId = ? AND EventId = ?;
"""

SQL_SELECT_AWARD_BY_ID = """
SELECT TOP (1)
    AwardId,
    EventId,
    SignupId,
    GovernorId,
    GovernorNameSnapshot,
    RequestedCommanderId,
    RequestedCommanderName,
    AwardedRank,
    TargetScore,
    AwardStatus,
    WaitlistOrder,
    ManualOrderOverride,
    InternalNotes,
    PublishVersion,
    AssignedByDiscordId,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
WHERE AwardId = ?;
"""

SQL_SELECT_AWARD_BY_EVENT_GOVERNOR = """
SELECT TOP (1)
    AwardId,
    EventId,
    SignupId,
    GovernorId,
    GovernorNameSnapshot,
    RequestedCommanderId,
    RequestedCommanderName,
    AwardedRank,
    TargetScore,
    AwardStatus,
    WaitlistOrder,
    ManualOrderOverride,
    InternalNotes,
    PublishVersion,
    AssignedByDiscordId,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
WHERE EventId = ?
  AND GovernorId = ?;
"""


SQL_SELECT_AWARD_BY_EVENT_SIGNUP = """
SELECT TOP (1)
    AwardId,
    EventId,
    SignupId,
    GovernorId,
    GovernorNameSnapshot,
    RequestedCommanderId,
    RequestedCommanderName,
    AwardedRank,
    TargetScore,
    AwardStatus,
    WaitlistOrder,
    ManualOrderOverride,
    InternalNotes,
    PublishVersion,
    AssignedByDiscordId,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Awards
WHERE EventId = ?
  AND SignupId = ?;
"""


SQL_INSERT_AWARD = """
INSERT INTO dbo.MGE_Awards
(
    EventId, SignupId, GovernorId, GovernorNameSnapshot,
    RequestedCommanderId, RequestedCommanderName, AwardedRank,
    TargetScore, AwardStatus, WaitlistOrder, ManualOrderOverride, InternalNotes,
    PublishVersion, AssignedByDiscordId, CreatedUtc, UpdatedUtc
)
OUTPUT INSERTED.AwardId
VALUES
(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?);
"""

SQL_UPDATE_AWARD = """
UPDATE dbo.MGE_Awards
SET AwardedRank = ?, AwardStatus = ?, WaitlistOrder = ?, InternalNotes = ?,
    ManualOrderOverride = COALESCE(?, ManualOrderOverride),
    AssignedByDiscordId = ?, UpdatedUtc = ?
WHERE AwardId = ?;
"""

SQL_DELETE_AWARD = "DELETE FROM dbo.MGE_Awards WHERE AwardId = ?;"

SQL_INSERT_AWARD_AUDIT = """
INSERT INTO dbo.MGE_AwardAudit
(
    AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
    OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
    DetailsJson, CreatedUtc
)
VALUES
(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def _naive_utc(dt: datetime) -> datetime:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


def fetch_event_awards(event_id: int) -> list[dict[str, Any]]:
    try:
        return run_query(SQL_SELECT_EVENT_AWARDS, (event_id,))
    except Exception:
        logger.exception("mge_roster_dal_fetch_event_awards_failed event_id=%s", event_id)
        return []


def fetch_signup_snapshot(signup_id: int, event_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_SIGNUP_SNAPSHOT, (signup_id, event_id))
        return rows[0] if rows else None
    except Exception:
        logger.exception(
            "mge_roster_dal_fetch_signup_snapshot_failed event_id=%s signup_id=%s",
            event_id,
            signup_id,
        )
        return None


def fetch_award_by_id(award_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_AWARD_BY_ID, (award_id,))
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_roster_dal_fetch_award_by_id_failed award_id=%s", award_id)
        return None


def fetch_award_by_event_governor(event_id: int, governor_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_AWARD_BY_EVENT_GOVERNOR, (event_id, governor_id))
        return rows[0] if rows else None
    except Exception:
        logger.exception(
            "mge_roster_dal_fetch_award_by_event_governor_failed event_id=%s governor_id=%s",
            event_id,
            governor_id,
        )
        return None


def fetch_award_by_event_signup(event_id: int, signup_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_AWARD_BY_EVENT_SIGNUP, (event_id, signup_id))
        return rows[0] if rows else None
    except Exception:
        logger.exception(
            "mge_roster_dal_fetch_award_by_event_signup_failed event_id=%s signup_id=%s",
            event_id,
            signup_id,
        )
        return None


def insert_award(
    *,
    event_id: int,
    signup_id: int,
    governor_id: int,
    governor_name_snapshot: str,
    requested_commander_id: int,
    requested_commander_name: str,
    awarded_rank: int | None,
    award_status: str,
    waitlist_order: int | None,
    manual_order_override: bool = False,
    internal_notes: str | None,
    assigned_by_discord_id: int | None,
    now_utc: datetime,
) -> int | None:
    def _callback(cur):
        cur.execute(
            SQL_INSERT_AWARD,
            (
                int(event_id),
                int(signup_id),
                int(governor_id),
                str(governor_name_snapshot),
                int(requested_commander_id),
                str(requested_commander_name),
                awarded_rank,
                None,
                str(award_status),
                waitlist_order,
                1 if manual_order_override else 0,
                internal_notes,
                int(assigned_by_discord_id) if assigned_by_discord_id is not None else None,
                _naive_utc(now_utc),
                _naive_utc(now_utc),
            ),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None

    result = exec_with_cursor(_callback)
    if result is None:
        logger.error(
            "mge_roster_dal_insert_award_failed event_id=%s signup_id=%s governor_id=%s",
            event_id,
            signup_id,
            governor_id,
        )
        return None
    return int(result)


def update_award(
    *,
    award_id: int,
    awarded_rank: int | None,
    award_status: str,
    waitlist_order: int | None,
    manual_order_override: bool | None,
    internal_notes: str | None,
    assigned_by_discord_id: int | None,
    now_utc: datetime,
) -> bool:
    def _callback(cur):
        cur.execute(
            SQL_UPDATE_AWARD,
            (
                awarded_rank,
                award_status,
                waitlist_order,
                internal_notes,
                None if manual_order_override is None else (1 if manual_order_override else 0),
                assigned_by_discord_id,
                _naive_utc(now_utc),
                award_id,
            ),
        )
        return int(cur.rowcount or 0)

    affected = exec_with_cursor(_callback)
    if affected is None:
        logger.error("mge_roster_dal_update_award_failed award_id=%s", award_id)
        return False
    return True


def update_manual_order_override(
    *,
    award_id: int,
    manual_order_override: bool,
    actor_discord_id: int | None,
    now_utc: datetime,
) -> bool:
    """Persist the manual-order override flag for an award row."""

    def _callback(cur):
        cur.execute(
            """
            UPDATE dbo.MGE_Awards
            SET ManualOrderOverride = ?, AssignedByDiscordId = ?, UpdatedUtc = ?
            WHERE AwardId = ?;
            """,
            (
                1 if manual_order_override else 0,
                actor_discord_id,
                _naive_utc(now_utc),
                award_id,
            ),
        )
        return int(cur.rowcount or 0)

    affected = exec_with_cursor(_callback)
    if affected is None:
        logger.error(
            "mge_roster_dal_update_manual_order_override_failed award_id=%s manual_order_override=%s",
            award_id,
            manual_order_override,
        )
        return False
    return True


def insert_award_audit(
    *,
    award_id: int,
    event_id: int,
    governor_id: int,
    action_type: str,
    actor_discord_id: int | None,
    old_rank: int | None,
    new_rank: int | None,
    old_status: str | None,
    new_status: str | None,
    old_target_score: int | None,
    new_target_score: int | None,
    details: dict[str, Any] | None,
    now_utc: datetime,
) -> bool:
    details_json = json.dumps(details or {}, ensure_ascii=False)

    def _callback(cur):
        cur.execute(
            SQL_INSERT_AWARD_AUDIT,
            (
                award_id,
                event_id,
                governor_id,
                action_type,
                actor_discord_id,
                old_rank,
                new_rank,
                old_status,
                new_status,
                old_target_score,
                new_target_score,
                details_json,
                _naive_utc(now_utc),
            ),
        )
        return int(cur.rowcount or 0)

    affected = exec_with_cursor(_callback)
    if affected is None:
        logger.error(
            "mge_roster_dal_insert_award_audit_failed award_id=%s action_type=%s",
            award_id,
            action_type,
        )
        return False
    return True


def delete_award_with_audit_atomic(
    *,
    award_id: int,
    actor_discord_id: int,
    action_type: str,
    details: dict[str, Any] | None,
    now_utc: datetime,
) -> dict[str, Any] | None:
    def _callback(cur):
        cur.execute(SQL_SELECT_AWARD_BY_ID, (award_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        snapshot = dict(zip(cols, row, strict=False))

        cur.execute(SQL_DELETE_AWARD, (award_id,))
        if int(cur.rowcount or 0) <= 0:
            return None

        details_json = json.dumps(details or {}, ensure_ascii=False)
        cur.execute(
            SQL_INSERT_AWARD_AUDIT,
            (
                int(snapshot["AwardId"]),
                int(snapshot["EventId"]),
                int(snapshot["GovernorId"]),
                action_type,
                actor_discord_id,
                snapshot.get("AwardedRank"),
                None,
                snapshot.get("AwardStatus"),
                "removed",
                snapshot.get("TargetScore"),
                snapshot.get("TargetScore"),
                details_json,
                _naive_utc(now_utc),
            ),
        )
        return snapshot

    return exec_with_cursor(_callback)


def delete_award_by_event_governor_with_audit_atomic(
    *,
    event_id: int,
    governor_id: int,
    actor_discord_id: int,
    action_type: str,
    details: dict[str, Any] | None,
    now_utc: datetime,
) -> dict[str, Any] | None:
    def _callback(cur):
        cur.execute(SQL_SELECT_AWARD_BY_EVENT_GOVERNOR, (event_id, governor_id))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        snapshot = dict(zip(cols, row, strict=False))

        cur.execute(SQL_DELETE_AWARD, (int(snapshot["AwardId"]),))
        if int(cur.rowcount or 0) <= 0:
            return None

        details_json = json.dumps(details or {}, ensure_ascii=False)
        cur.execute(
            SQL_INSERT_AWARD_AUDIT,
            (
                int(snapshot["AwardId"]),
                int(snapshot["EventId"]),
                int(snapshot["GovernorId"]),
                action_type,
                actor_discord_id,
                snapshot.get("AwardedRank"),
                None,
                snapshot.get("AwardStatus"),
                "removed",
                snapshot.get("TargetScore"),
                snapshot.get("TargetScore"),
                details_json,
                _naive_utc(now_utc),
            ),
        )
        return snapshot

    return exec_with_cursor(_callback)


def apply_set_rank_atomic(
    *,
    award_id: int,
    new_rank: int,
    actor_discord_id: int,
    now_utc: datetime,
) -> dict[str, Any] | None:
    """
    Atomically set target row to awarded/new_rank and resolve collisions safely.
    Guarantees all 'awarded' rows retain valid rank (1-15).
    """

    def _callback(cur):
        cur.execute(
            """
            SELECT TOP (1)
                AwardId, EventId, SignupId, GovernorId, GovernorNameSnapshot,
                RequestedCommanderId, RequestedCommanderName, AwardedRank, TargetScore,
                AwardStatus, WaitlistOrder, ManualOrderOverride, InternalNotes, PublishVersion,
                AssignedByDiscordId, CreatedUtc, UpdatedUtc
            FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
            WHERE AwardId = ?;
            """,
            (award_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        target = dict(zip(cols, row, strict=False))

        event_id = int(target["EventId"])
        old_rank = target.get("AwardedRank")
        old_status = str(target.get("AwardStatus") or "")

        if str(old_status).lower() == "awarded" and old_rank == int(new_rank):
            return {
                "ok": True,
                "event_id": event_id,
                "award_id": int(target["AwardId"]),
                "noop": True,
            }

        cur.execute(
            """
            SELECT AwardId, AwardedRank, AwardStatus, InternalNotes, TargetScore, GovernorId
            FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
            WHERE EventId = ?
              AND AwardStatus = 'awarded'
              AND AwardedRank = ?
              AND AwardId <> ?
            ORDER BY AwardId ASC;
            """,
            (event_id, new_rank, award_id),
        )
        conflicts = cur.fetchall()
        c_cols = [d[0] for d in cur.description] if cur.description else []

        if len(conflicts) > 1:
            return {"error": "multiple_rank_conflicts"}

        conflict = dict(zip(c_cols, conflicts[0], strict=False)) if conflicts else None

        if conflict is not None and old_rank is None:
            return {"error": "rank_collision_without_current_rank"}

        if conflict is not None:
            cur.execute(
                SQL_UPDATE_AWARD,
                (
                    int(old_rank),
                    "awarded",
                    None,
                    conflict.get("InternalNotes"),
                    conflict.get("ManualOrderOverride"),
                    actor_discord_id,
                    _naive_utc(now_utc),
                    int(conflict["AwardId"]),
                ),
            )
            if int(cur.rowcount or 0) <= 0:
                return {"error": "conflict_update_failed"}

        cur.execute(
            SQL_UPDATE_AWARD,
            (
                int(new_rank),
                "awarded",
                None,
                target.get("InternalNotes"),
                1,
                actor_discord_id,
                _naive_utc(now_utc),
                award_id,
            ),
        )
        if int(cur.rowcount or 0) <= 0:
            return {"error": "target_update_failed"}

        details_json = json.dumps({"new_rank": int(new_rank)}, ensure_ascii=False)
        cur.execute(
            SQL_INSERT_AWARD_AUDIT,
            (
                int(target["AwardId"]),
                event_id,
                int(target["GovernorId"]),
                "set_rank",
                actor_discord_id,
                int(old_rank) if old_rank is not None else None,
                int(new_rank),
                old_status,
                "awarded",
                target.get("TargetScore"),
                target.get("TargetScore"),
                details_json,
                _naive_utc(now_utc),
            ),
        )
        return {"ok": True, "event_id": event_id, "award_id": int(target["AwardId"])}

    return exec_with_cursor(_callback)


def promote_waitlist_to_awarded_atomic(
    *,
    award_id: int,
    actor_discord_id: int,
    now_utc: datetime,
    extra_notes: str | None = None,
) -> dict[str, Any] | None:
    """
    Promote a waitlist row to awarded status using the next available rank.
    Appends extra_notes to the existing internal notes and writes the audit record
    in the same transaction.
    """

    def _callback(cur):
        cur.execute(
            """
            SELECT TOP (1)
                AwardId, EventId, SignupId, GovernorId, GovernorNameSnapshot,
                RequestedCommanderId, RequestedCommanderName, AwardedRank, TargetScore,
                AwardStatus, WaitlistOrder, ManualOrderOverride, InternalNotes, PublishVersion,
                AssignedByDiscordId, CreatedUtc, UpdatedUtc
            FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
            WHERE AwardId = ?;
            """,
            (award_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        target = dict(zip(cols, row, strict=False))

        if str(target.get("AwardStatus") or "").lower() != "waitlist":
            return {"error": "not_waitlist"}

        event_id = int(target["EventId"])

        cur.execute(
            """
            SELECT AwardId, AwardedRank
            FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
            WHERE EventId = ?
              AND AwardStatus = 'awarded'
              AND AwardedRank IS NOT NULL
            ORDER BY AwardedRank ASC, AwardId ASC;
            """,
            (event_id,),
        )
        rows = cur.fetchall()
        used = {int(r[1]) for r in rows if r and r[1] is not None}
        new_rank = None
        for n in range(1, 16):
            if n not in used:
                new_rank = n
                break

        if new_rank is None:
            return {"error": "roster_full"}

        existing_notes = str(target.get("InternalNotes") or "").strip()
        extra_text = str(extra_notes or "").strip()
        merged_notes = existing_notes
        if extra_text:
            merged_notes = f"{existing_notes}\n{extra_text}" if existing_notes else extra_text

        cur.execute(
            SQL_UPDATE_AWARD,
            (
                int(new_rank),
                "awarded",
                None,
                merged_notes or None,
                1,
                actor_discord_id,
                _naive_utc(now_utc),
                award_id,
            ),
        )
        if int(cur.rowcount or 0) <= 0:
            return {"error": "target_update_failed"}

        details_json = json.dumps(
            {"promoted_from": "waitlist", "new_rank": int(new_rank)},
            ensure_ascii=False,
        )
        cur.execute(
            SQL_INSERT_AWARD_AUDIT,
            (
                int(target["AwardId"]),
                event_id,
                int(target["GovernorId"]),
                "promote_to_awarded",
                actor_discord_id,
                None,
                int(new_rank),
                "waitlist",
                "awarded",
                target.get("TargetScore"),
                target.get("TargetScore"),
                details_json,
                _naive_utc(now_utc),
            ),
        )
        return {
            "ok": True,
            "event_id": event_id,
            "award_id": int(target["AwardId"]),
            "new_rank": int(new_rank),
        }

    return exec_with_cursor(_callback)
