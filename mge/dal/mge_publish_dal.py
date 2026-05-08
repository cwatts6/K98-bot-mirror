"""DAL for MGE target generation, publish/republish, and unpublish operations."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from stats_alerts.db import exec_with_cursor, execute, run_query

logger = logging.getLogger(__name__)


def _naive_utc(dt: datetime) -> datetime:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


SQL_SELECT_EVENT_PUBLISH_CONTEXT = """
SELECT
    e.EventId,
    e.EventName,
    e.Status,
    e.RuleMode,
    e.PublishVersion,
    e.LastPublishedUtc,
    e.AwardEmbedMessageId,
    e.AwardEmbedChannelId,
    e.AwardRemindersText,
    e.AwardRemindersSentUtc,
    e.AwardRemindersSentByDiscordId,
    v.VariantName
FROM dbo.MGE_Events e
JOIN dbo.MGE_Variants v ON e.VariantId = v.VariantId
WHERE e.EventId = ?;
"""

SQL_SELECT_AWARDS_WITH_SIGNUP_USER = """
SELECT
    a.AwardId,
    a.EventId,
    a.SignupId,
    a.GovernorId,
    a.GovernorNameSnapshot,
    a.RequestedCommanderName,
    a.AwardedRank,
    a.TargetScore,
    a.AwardStatus,
    a.WaitlistOrder,
    a.PublishVersion,
    s.DiscordUserId
FROM dbo.MGE_Awards a
LEFT JOIN dbo.MGE_Signups s ON s.SignupId = a.SignupId
WHERE a.EventId = ?
ORDER BY
    CASE WHEN a.AwardStatus = 'awarded' THEN 0
         WHEN a.AwardStatus = 'waitlist' THEN 1
         ELSE 2 END,
    a.AwardedRank ASC,
    a.WaitlistOrder ASC,
    a.AwardId ASC;
"""

SQL_SELECT_PUBLISHED_SNAPSHOT = """
SELECT
    AwardId,
    GovernorId,
    GovernorNameSnapshot,
    RequestedCommanderName,
    AwardedRank,
    TargetScore,
    AwardStatus,
    WaitlistOrder,
    PublishVersion
FROM dbo.MGE_Awards
WHERE EventId = ?
  AND PublishVersion = ?;
"""

SQL_SELECT_AWARD_ROW_BY_ID = """
SELECT TOP (1)
    AwardId,
    EventId,
    GovernorId,
    GovernorNameSnapshot,
    AwardStatus,
    AwardedRank,
    WaitlistOrder,
    TargetScore,
    PublishVersion
FROM dbo.MGE_Awards
WHERE AwardId = ?;
"""

SQL_SELECT_DEFAULT_REMINDERS_TEXT = """
SELECT TOP 1 RuleText
FROM dbo.MGE_DefaultRules
WHERE RuleMode = ?
  AND IsActive = 1
  AND (
      LOWER(RuleKey) LIKE '%award_reminder%'
      OR LOWER(RuleKey) LIKE '%award_reminders%'
  )
ORDER BY RuleKey;
"""


def fetch_event_publish_context(event_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_EVENT_PUBLISH_CONTEXT, (event_id,))
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_publish_dal_fetch_event_publish_context_failed event_id=%s", event_id)
        return None


def fetch_awards_with_signup_user(event_id: int) -> list[dict[str, Any]]:
    try:
        return run_query(SQL_SELECT_AWARDS_WITH_SIGNUP_USER, (event_id,))
    except Exception:
        logger.exception(
            "mge_publish_dal_fetch_awards_with_signup_user_failed event_id=%s", event_id
        )
        return []


def fetch_published_snapshot(event_id: int, publish_version: int) -> list[dict[str, Any]]:
    try:
        return run_query(SQL_SELECT_PUBLISHED_SNAPSHOT, (event_id, publish_version))
    except Exception:
        logger.exception(
            "mge_publish_dal_fetch_published_snapshot_failed event_id=%s publish_version=%s",
            event_id,
            publish_version,
        )
        return []


def fetch_award_target_row(award_id: int) -> dict[str, Any] | None:
    """Return the target-edit snapshot for a specific award row."""
    try:
        rows = run_query(SQL_SELECT_AWARD_ROW_BY_ID, (award_id,))
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_publish_dal_fetch_award_target_row_failed award_id=%s", award_id)
        return None


def fetch_default_award_reminders_text(rule_mode: str) -> str | None:
    mode = str(rule_mode or "").strip().lower()
    if mode not in {"fixed", "open"}:
        return None
    try:
        rows = run_query(SQL_SELECT_DEFAULT_REMINDERS_TEXT, (mode,))
        if not rows:
            return None
        return str(rows[0].get("RuleText") or "").strip() or None
    except Exception:
        logger.exception(
            "mge_publish_dal_fetch_default_award_reminders_text_failed rule_mode=%s",
            mode,
        )
        return None


def apply_generated_targets(
    *,
    event_id: int,
    roster_targets: dict[int, dict[str, Any]],
    clear_award_ids: list[int],
    actor_discord_id: int,
    now_utc: datetime,
) -> int:
    """Apply generated roster targets and clear non-roster targets for the event."""

    def _callback(cur):
        updated = 0
        touched_award_ids: set[int] = set()
        for award_id, payload in roster_targets.items():
            cur.execute(
                """
                SELECT TOP (1)
                    AwardId, EventId, GovernorId, AwardStatus, AwardedRank, WaitlistOrder, TargetScore
                FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
                WHERE AwardId = ? AND EventId = ?;
                """,
                (int(award_id), int(event_id)),
            )
            row = cur.fetchone()
            if row is None:
                continue
            cols = [d[0] for d in cur.description]
            snap = dict(zip(cols, row, strict=False))
            new_rank = payload.get("awarded_rank")
            new_target = payload.get("target_score")

            cur.execute(
                """
                UPDATE dbo.MGE_Awards
                SET AwardStatus = 'awarded',
                    AwardedRank = ?,
                    WaitlistOrder = NULL,
                    TargetScore = ?,
                    TargetsGeneratedAtUtc = ?,
                    TargetsGeneratedByDiscordId = ?,
                    TargetsOverrideLastAtUtc = NULL,
                    TargetsOverrideLastByDiscordId = NULL,
                    AssignedByDiscordId = ?,
                    UpdatedUtc = ?
                WHERE AwardId = ?;
                """,
                (
                    new_rank,
                    int(new_target),
                    _naive_utc(now_utc),
                    actor_discord_id,
                    actor_discord_id,
                    _naive_utc(now_utc),
                    int(award_id),
                ),
            )
            if int(cur.rowcount or 0) <= 0:
                continue
            touched_award_ids.add(int(award_id))
            details = json.dumps(
                {
                    "mode": "auto_generate_targets",
                    "award_id": int(award_id),
                    "computed_awarded_rank": new_rank,
                },
                ensure_ascii=False,
            )
            cur.execute(
                """
                INSERT INTO dbo.MGE_AwardAudit
                (
                    AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                    OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                    DetailsJson, CreatedUtc
                )
                VALUES
                (?, ?, ?, 'target_auto_generate', ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    int(snap["AwardId"]),
                    int(snap["EventId"]),
                    int(snap["GovernorId"]),
                    actor_discord_id,
                    snap.get("AwardedRank"),
                    new_rank,
                    snap.get("AwardStatus"),
                    "awarded",
                    snap.get("TargetScore"),
                    int(new_target),
                    details,
                    _naive_utc(now_utc),
                ),
            )
            updated += 1

        for award_id in clear_award_ids:
            if int(award_id) in touched_award_ids:
                continue
            cur.execute(
                """
                SELECT TOP (1)
                    AwardId, EventId, GovernorId, AwardStatus, AwardedRank, WaitlistOrder, TargetScore
                FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
                WHERE AwardId = ? AND EventId = ?;
                """,
                (int(award_id), int(event_id)),
            )
            row = cur.fetchone()
            if row is None:
                continue
            cols = [d[0] for d in cur.description]
            snap = dict(zip(cols, row, strict=False))
            cur.execute(
                """
                UPDATE dbo.MGE_Awards
                SET TargetScore = NULL,
                    TargetsGeneratedAtUtc = ?,
                    TargetsGeneratedByDiscordId = ?,
                    TargetsOverrideLastAtUtc = NULL,
                    TargetsOverrideLastByDiscordId = NULL,
                    AssignedByDiscordId = ?,
                    UpdatedUtc = ?
                WHERE AwardId = ?;
                """,
                (
                    _naive_utc(now_utc),
                    actor_discord_id,
                    actor_discord_id,
                    _naive_utc(now_utc),
                    int(award_id),
                ),
            )
            if int(cur.rowcount or 0) <= 0:
                continue

            details = json.dumps(
                {"mode": "auto_generate_targets_clear_non_roster", "award_id": int(award_id)},
                ensure_ascii=False,
            )
            cur.execute(
                """
                INSERT INTO dbo.MGE_AwardAudit
                (
                    AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                    OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                    DetailsJson, CreatedUtc
                )
                VALUES
                (?, ?, ?, 'target_auto_generate', ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    int(snap["AwardId"]),
                    int(snap["EventId"]),
                    int(snap["GovernorId"]),
                    actor_discord_id,
                    snap.get("AwardedRank"),
                    snap.get("AwardedRank"),
                    snap.get("AwardStatus"),
                    snap.get("AwardStatus"),
                    snap.get("TargetScore"),
                    None,
                    details,
                    _naive_utc(now_utc),
                ),
            )
        return updated

    result = exec_with_cursor(_callback)
    return int(result or 0)


def apply_manual_target_override(
    *,
    award_id: int,
    target_score: int,
    actor_discord_id: int,
    now_utc: datetime,
) -> bool:
    def _callback(cur):
        cur.execute(
            """
            SELECT TOP (1) AwardId, EventId, GovernorId, AwardStatus, AwardedRank, TargetScore
            FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
            WHERE AwardId = ?;
            """,
            (award_id,),
        )
        row = cur.fetchone()
        if row is None:
            return False
        cols = [d[0] for d in cur.description]
        snap = dict(zip(cols, row, strict=False))
        old_target = snap.get("TargetScore")

        cur.execute(
            """
            UPDATE dbo.MGE_Awards
            SET TargetScore = ?,
                TargetsOverrideLastAtUtc = ?,
                TargetsOverrideLastByDiscordId = ?,
                AssignedByDiscordId = ?,
                UpdatedUtc = ?
            WHERE AwardId = ?;
            """,
            (
                int(target_score),
                _naive_utc(now_utc),
                actor_discord_id,
                actor_discord_id,
                _naive_utc(now_utc),
                int(award_id),
            ),
        )
        if int(cur.rowcount or 0) <= 0:
            return False

        details = json.dumps({"mode": "manual_target_override"}, ensure_ascii=False)
        cur.execute(
            """
            INSERT INTO dbo.MGE_AwardAudit
            (
                AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                DetailsJson, CreatedUtc
            )
            VALUES
            (?, ?, ?, 'target_manual_override', ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                int(snap["AwardId"]),
                int(snap["EventId"]),
                int(snap["GovernorId"]),
                actor_discord_id,
                snap.get("AwardedRank"),
                snap.get("AwardedRank"),
                snap.get("AwardStatus"),
                snap.get("AwardStatus"),
                old_target,
                int(target_score),
                details,
                _naive_utc(now_utc),
            ),
        )
        return True

    result = exec_with_cursor(_callback)
    return bool(result)


def apply_publish_atomic(
    *,
    event_id: int,
    publish_rows: list[dict[str, Any]],
    waitlist_rows: list[dict[str, Any]],
    clear_rank_award_ids: list[int],
    actor_discord_id: int,
    now_utc: datetime,
) -> int | None:
    def _callback(cur):
        cur.execute(
            """
            SELECT TOP (1) EventId, PublishVersion
            FROM dbo.MGE_Events WITH (UPDLOCK, HOLDLOCK)
            WHERE EventId = ?;
            """,
            (event_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        event_row = dict(zip(cols, row, strict=False))
        old_version = int(event_row.get("PublishVersion") or 0)
        new_version = old_version + 1

        cur.execute(
            """
            UPDATE dbo.MGE_Events
            SET PublishVersion = ?,
                LastPublishedUtc = ?,
                Status = 'published',
                UpdatedUtc = ?
            WHERE EventId = ?;
            """,
            (new_version, _naive_utc(now_utc), _naive_utc(now_utc), event_id),
        )

        publish_ids = {int(row.get("AwardId") or 0) for row in publish_rows}
        waitlist_ids = {int(row.get("AwardId") or 0) for row in waitlist_rows}
        clear_ids = {int(value) for value in clear_rank_award_ids}

        for row in publish_rows:
            award_id = int(row.get("AwardId") or 0)
            if award_id <= 0:
                continue
            rank = row.get("FinalAwardedRank")
            target_score = row.get("TargetScore")
            cur.execute(
                """
                SELECT TOP (1) AwardId, EventId, GovernorId, AwardStatus, AwardedRank, TargetScore
                FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
                WHERE AwardId = ? AND EventId = ?;
                """,
                (award_id, event_id),
            )
            snap_row = cur.fetchone()
            if snap_row is None:
                continue
            cols = [d[0] for d in cur.description]
            snap = dict(zip(cols, snap_row, strict=False))

            cur.execute(
                """
                UPDATE dbo.MGE_Awards
                SET AwardStatus = 'awarded',
                    AwardedRank = ?,
                    WaitlistOrder = NULL,
                    PublishVersion = ?,
                    AssignedByDiscordId = ?,
                    UpdatedUtc = ?
                WHERE AwardId = ?;
                """,
                (
                    rank,
                    new_version,
                    actor_discord_id,
                    _naive_utc(now_utc),
                    award_id,
                ),
            )
            details = json.dumps(
                {"publish_version": new_version, "final_award_rank": rank}, ensure_ascii=False
            )
            cur.execute(
                """
                INSERT INTO dbo.MGE_AwardAudit
                (
                    AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                    OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                    DetailsJson, CreatedUtc
                )
                VALUES
                (?, ?, ?, 'publish', ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    award_id,
                    int(snap["EventId"]),
                    int(snap["GovernorId"]),
                    actor_discord_id,
                    snap.get("AwardedRank"),
                    rank,
                    snap.get("AwardStatus"),
                    "awarded",
                    snap.get("TargetScore"),
                    target_score,
                    details,
                    _naive_utc(now_utc),
                ),
            )

        for row in waitlist_rows:
            award_id = int(row.get("AwardId") or 0)
            if award_id <= 0:
                continue
            waitlist_order = row.get("FinalWaitlistOrder")
            cur.execute(
                """
                SELECT TOP (1) AwardId, EventId, GovernorId, AwardStatus, AwardedRank, TargetScore, WaitlistOrder
                FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
                WHERE AwardId = ? AND EventId = ?;
                """,
                (award_id, event_id),
            )
            snap_row = cur.fetchone()
            if snap_row is None:
                continue
            cols = [d[0] for d in cur.description]
            snap = dict(zip(cols, snap_row, strict=False))
            cur.execute(
                """
                UPDATE dbo.MGE_Awards
                SET AwardStatus = 'waitlist',
                    AwardedRank = NULL,
                    WaitlistOrder = ?,
                    PublishVersion = ?,
                    AssignedByDiscordId = ?,
                    UpdatedUtc = ?
                WHERE AwardId = ?;
                """,
                (
                    waitlist_order,
                    new_version,
                    actor_discord_id,
                    _naive_utc(now_utc),
                    award_id,
                ),
            )
            details = json.dumps(
                {"publish_version": new_version, "final_waitlist_order": waitlist_order},
                ensure_ascii=False,
            )
            cur.execute(
                """
                INSERT INTO dbo.MGE_AwardAudit
                (
                    AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                    OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                    DetailsJson, CreatedUtc
                )
                VALUES
                (?, ?, ?, 'publish', ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    award_id,
                    int(snap["EventId"]),
                    int(snap["GovernorId"]),
                    actor_discord_id,
                    snap.get("AwardedRank"),
                    None,
                    snap.get("AwardStatus"),
                    "waitlist",
                    snap.get("TargetScore"),
                    snap.get("TargetScore"),
                    details,
                    _naive_utc(now_utc),
                ),
            )

        for award_id in clear_ids - publish_ids - waitlist_ids:
            if award_id <= 0:
                continue
            cur.execute(
                """
                SELECT TOP (1) AwardId, EventId, GovernorId, AwardStatus, AwardedRank, TargetScore, WaitlistOrder
                FROM dbo.MGE_Awards WITH (UPDLOCK, HOLDLOCK)
                WHERE AwardId = ? AND EventId = ?;
                """,
                (award_id, event_id),
            )
            snap_row = cur.fetchone()
            if snap_row is None:
                continue
            cols = [d[0] for d in cur.description]
            snap = dict(zip(cols, snap_row, strict=False))
            cur.execute(
                """
                UPDATE dbo.MGE_Awards
                SET AwardedRank = NULL,
                    PublishVersion = CASE WHEN AwardStatus IN ('rejected', 'unassigned') THEN NULL ELSE ? END,
                    AssignedByDiscordId = ?,
                    UpdatedUtc = ?
                WHERE AwardId = ?;
                """,
                (new_version, actor_discord_id, _naive_utc(now_utc), award_id),
            )
            details = json.dumps(
                {"publish_version": new_version, "cleared_award_rank": True}, ensure_ascii=False
            )
            cur.execute(
                """
                INSERT INTO dbo.MGE_AwardAudit
                (
                    AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                    OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                    DetailsJson, CreatedUtc
                )
                VALUES
                (?, ?, ?, 'publish', ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    award_id,
                    int(snap["EventId"]),
                    int(snap["GovernorId"]),
                    actor_discord_id,
                    snap.get("AwardedRank"),
                    None,
                    snap.get("AwardStatus"),
                    snap.get("AwardStatus"),
                    snap.get("TargetScore"),
                    snap.get("TargetScore"),
                    details,
                    _naive_utc(now_utc),
                ),
            )

        return new_version

    try:
        result = exec_with_cursor(_callback)
        return int(result) if result is not None else None
    except Exception:
        logger.exception("mge_publish_dal_apply_publish_atomic_failed event_id=%s", event_id)
        return None


def apply_unpublish_atomic(
    *,
    event_id: int,
    actor_discord_id: int,
    now_utc: datetime,
    restore_status: str,
) -> dict[str, Any] | None:
    def _callback(cur):
        cur.execute(
            """
            SELECT TOP (1)
                EventId, EventName, Status, PublishVersion, LastPublishedUtc,
                AwardEmbedMessageId, AwardEmbedChannelId
            FROM dbo.MGE_Events WITH (UPDLOCK, HOLDLOCK)
            WHERE EventId = ?;
            """,
            (event_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        event_row = dict(zip(cols, row, strict=False))

        old_status = str(event_row.get("Status") or "")
        old_version = int(event_row.get("PublishVersion") or 0)
        if old_version <= 0 and old_status.strip().lower() not in {"published", "completed"}:
            return None

        cur.execute(
            """
            UPDATE dbo.MGE_Events
            SET
                Status = ?,
                PublishVersion = 0,
                LastPublishedUtc = NULL,
                AwardEmbedMessageId = NULL,
                AwardEmbedChannelId = NULL,
                UpdatedUtc = ?
            WHERE EventId = ?
              AND (PublishVersion > 0 OR LOWER(Status) IN ('published', 'completed'));
            """,
            (restore_status, _naive_utc(now_utc), event_id),
        )
        if int(cur.rowcount or 0) <= 0:
            return None

        cur.execute(
            """
            UPDATE dbo.MGE_Awards
            SET PublishVersion = NULL,
                AssignedByDiscordId = ?,
                UpdatedUtc = ?
            WHERE EventId = ?;
            """,
            (actor_discord_id, _naive_utc(now_utc), event_id),
        )

        details = json.dumps(
            {
                "old_status": old_status,
                "restore_status": restore_status,
                "old_publish_version": old_version,
                "unpublish": True,
            },
            ensure_ascii=False,
        )
        cur.execute(
            """
            INSERT INTO dbo.MGE_AwardAudit
            (
                AwardId, EventId, GovernorId, ActionType, ActorDiscordId,
                OldRank, NewRank, OldStatus, NewStatus, OldTargetScore, NewTargetScore,
                DetailsJson, CreatedUtc
            )
            VALUES
            (0, ?, 0, 'unpublish', ?, NULL, NULL, ?, ?, NULL, NULL, ?, ?);
            """,
            (
                int(event_id),
                actor_discord_id,
                old_status,
                restore_status,
                details,
                _naive_utc(now_utc),
            ),
        )

        return {
            "ok": True,
            "event_id": event_id,
            "old_status": old_status,
            "restore_status": restore_status,
            "old_publish_version": old_version,
            "embed_message_id": event_row.get("AwardEmbedMessageId"),
            "embed_channel_id": event_row.get("AwardEmbedChannelId"),
        }

    return exec_with_cursor(_callback)


def update_award_embed_ids(
    *,
    event_id: int,
    message_id: int,
    channel_id: int,
    now_utc: datetime,
) -> bool:
    try:
        execute(
            """
            UPDATE dbo.MGE_Events
            SET AwardEmbedMessageId = ?,
                AwardEmbedChannelId = ?,
                UpdatedUtc = ?
            WHERE EventId = ?;
            """,
            (int(message_id), int(channel_id), _naive_utc(now_utc), int(event_id)),
        )
        return True
    except Exception:
        logger.exception("mge_publish_dal_update_award_embed_ids_failed event_id=%s", event_id)
        return False


def update_event_award_reminders_text(
    *,
    event_id: int,
    reminders_text: str,
    now_utc: datetime,
) -> bool:
    try:
        updated = execute(
            """
            UPDATE dbo.MGE_Events
            SET AwardRemindersText = ?,
                UpdatedUtc = ?
            WHERE EventId = ?;
            """,
            (str(reminders_text), _naive_utc(now_utc), int(event_id)),
        )
        return int(updated or 0) > 0
    except Exception:
        logger.exception(
            "mge_publish_dal_update_event_award_reminders_text_failed event_id=%s",
            event_id,
        )
        return False


def mark_award_reminders_sent(
    *,
    event_id: int,
    actor_discord_id: int,
    now_utc: datetime,
) -> bool:
    try:
        updated = execute(
            """
            UPDATE dbo.MGE_Events
            SET AwardRemindersSentUtc = ?,
                AwardRemindersSentByDiscordId = ?,
                UpdatedUtc = ?
            WHERE EventId = ?
              AND AwardRemindersSentUtc IS NULL;
            """,
            (
                _naive_utc(now_utc),
                int(actor_discord_id),
                _naive_utc(now_utc),
                int(event_id),
            ),
        )
        return int(updated or 0) > 0
    except Exception:
        logger.exception("mge_publish_dal_mark_award_reminders_sent_failed event_id=%s", event_id)
        return False
