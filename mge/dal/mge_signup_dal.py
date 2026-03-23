"""DAL for MGE signup CRUD and validation context."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query

logger = logging.getLogger(__name__)

SQL_SELECT_EVENT_SIGNUP_CONTEXT = """
SELECT
    e.EventId,
    e.EventName,
    e.EventMode,
    e.Status,
    e.SignupCloseUtc,
    e.StartUtc,
    e.EndUtc,
    e.RulesText,
    v.VariantId,
    v.VariantName
FROM dbo.MGE_Events e
JOIN dbo.MGE_Variants v ON e.VariantId = v.VariantId
WHERE e.EventId = ?;
"""

SQL_SELECT_ACTIVE_SIGNUP_BY_EVENT_GOV = """
SELECT TOP (1)
    SignupId,
    EventId,
    GovernorId,
    GovernorNameSnapshot,
    DiscordUserId,
    RequestPriority,
    PreferredRankBand,
    RequestedCommanderId,
    RequestedCommanderName,
    CurrentHeads,
    KingdomRole,
    GearText,
    ArmamentText,
    IsActive,
    Source,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Signups
WHERE EventId = ?
  AND GovernorId = ?
  AND IsActive = 1
ORDER BY SignupId DESC;
"""

SQL_SELECT_ACTIVE_SIGNUP_BY_EVENT_DISCORD = """
SELECT TOP (1)
    SignupId,
    EventId,
    GovernorId,
    GovernorNameSnapshot,
    DiscordUserId,
    RequestPriority,
    PreferredRankBand,
    RequestedCommanderId,
    RequestedCommanderName,
    CurrentHeads,
    KingdomRole,
    GearText,
    ArmamentText,
    IsActive,
    Source,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Signups
WHERE EventId = ?
  AND DiscordUserId = ?
  AND IsActive = 1
ORDER BY UpdatedUtc DESC, SignupId DESC;
"""

SQL_SELECT_ACTIVE_SIGNUPS_BY_EVENT_DISCORD = """
SELECT
    SignupId,
    EventId,
    GovernorId,
    GovernorNameSnapshot,
    DiscordUserId,
    RequestPriority,
    PreferredRankBand,
    RequestedCommanderId,
    RequestedCommanderName,
    CurrentHeads,
    KingdomRole,
    GearText,
    ArmamentText,
    IsActive,
    Source,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Signups
WHERE EventId = ?
  AND DiscordUserId = ?
  AND IsActive = 1
ORDER BY UpdatedUtc DESC, SignupId DESC;
"""

SQL_SELECT_SIGNUP_BY_ID = """
SELECT TOP (1)
    SignupId,
    EventId,
    GovernorId,
    GovernorNameSnapshot,
    DiscordUserId,
    RequestPriority,
    PreferredRankBand,
    RequestedCommanderId,
    RequestedCommanderName,
    CurrentHeads,
    KingdomRole,
    GearText,
    ArmamentText,
    GearAttachmentUrl,
    GearAttachmentFilename,
    ArmamentAttachmentUrl,
    ArmamentAttachmentFilename,
    IsActive,
    Source,
    CreatedUtc,
    UpdatedUtc
FROM dbo.MGE_Signups
WHERE SignupId = ?;
"""


def _naive_utc(dt: datetime) -> datetime:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


def fetch_event_signup_context(event_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_EVENT_SIGNUP_CONTEXT, (event_id,))
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_signup_dal_fetch_event_signup_context_failed event_id=%s", event_id)
        return None


def fetch_active_signup_by_event_governor(event_id: int, governor_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_ACTIVE_SIGNUP_BY_EVENT_GOV, (event_id, governor_id))
        return rows[0] if rows else None
    except Exception:
        logger.exception(
            "mge_signup_dal_fetch_active_signup_by_event_governor_failed event_id=%s governor_id=%s",
            event_id,
            governor_id,
        )
        return None


def fetch_active_signup_by_event_discord(
    event_id: int, discord_user_id: int
) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_ACTIVE_SIGNUP_BY_EVENT_DISCORD, (event_id, discord_user_id))
        return rows[0] if rows else None
    except Exception:
        logger.exception(
            "mge_signup_dal_fetch_active_signup_by_event_discord_failed event_id=%s discord_user_id=%s",
            event_id,
            discord_user_id,
        )
        return None


def fetch_active_signups_by_event_discord(
    event_id: int, discord_user_id: int
) -> list[dict[str, Any]]:
    try:
        return run_query(SQL_SELECT_ACTIVE_SIGNUPS_BY_EVENT_DISCORD, (event_id, discord_user_id))
    except Exception:
        logger.exception(
            "mge_signup_dal_fetch_active_signups_by_event_discord_failed event_id=%s discord_user_id=%s",
            event_id,
            discord_user_id,
        )
        return []


def fetch_signup_by_id(signup_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_SIGNUP_BY_ID, (signup_id,))
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_signup_dal_fetch_signup_by_id_failed signup_id=%s", signup_id)
        return None


def insert_signup(
    *,
    event_id: int,
    governor_id: int,
    governor_name_snapshot: str,
    discord_user_id: int | None,
    request_priority: str,
    preferred_rank_band: str | None,
    requested_commander_id: int,
    requested_commander_name: str,
    current_heads: int,
    kingdom_role: str | None,
    gear_text: str | None,
    armament_text: str | None,
    source: str,
    now_utc: datetime,
) -> int | None:
    def _callback(cur):
        cur.execute(
            """
            INSERT INTO dbo.MGE_Signups
            (
                EventId,
                GovernorId,
                GovernorNameSnapshot,
                DiscordUserId,
                RequestPriority,
                PreferredRankBand,
                RequestedCommanderId,
                RequestedCommanderName,
                CurrentHeads,
                KingdomRole,
                GearText,
                ArmamentText,
                GearAttachmentUrl,
                GearAttachmentFilename,
                ArmamentAttachmentUrl,
                ArmamentAttachmentFilename,
                IsActive,
                Source,
                CreatedUtc,
                UpdatedUtc
            )
            OUTPUT INSERTED.SignupId
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, 1, ?, ?, ?);
            """,
            (
                event_id,
                governor_id,
                governor_name_snapshot,
                discord_user_id,
                request_priority,
                preferred_rank_band,
                requested_commander_id,
                requested_commander_name,
                current_heads,
                kingdom_role,
                gear_text,
                armament_text,
                source,
                _naive_utc(now_utc),
                _naive_utc(now_utc),
            ),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None

    try:
        return exec_with_cursor(_callback)
    except Exception:
        logger.exception(
            "mge_signup_dal_insert_signup_failed event_id=%s governor_id=%s",
            event_id,
            governor_id,
        )
        return None


def update_signup(
    *,
    signup_id: int,
    request_priority: str,
    preferred_rank_band: str | None,
    requested_commander_id: int,
    requested_commander_name: str,
    current_heads: int,
    kingdom_role: str | None,
    gear_text: str | None,
    armament_text: str | None,
    now_utc: datetime,
) -> bool:
    def _callback(cur):
        cur.execute(
            """
            UPDATE dbo.MGE_Signups
            SET
                RequestPriority = ?,
                PreferredRankBand = ?,
                RequestedCommanderId = ?,
                RequestedCommanderName = ?,
                CurrentHeads = ?,
                KingdomRole = ?,
                GearText = ?,
                ArmamentText = ?,
                UpdatedUtc = ?
            WHERE SignupId = ?;
            """,
            (
                request_priority,
                preferred_rank_band,
                requested_commander_id,
                requested_commander_name,
                current_heads,
                kingdom_role,
                gear_text,
                armament_text,
                _naive_utc(now_utc),
                signup_id,
            ),
        )
        return int(cur.rowcount or 0) > 0

    try:
        result = exec_with_cursor(_callback)
        return bool(result)
    except Exception:
        logger.exception("mge_signup_dal_update_signup_failed signup_id=%s", signup_id)
        return False


def update_signup_gear_attachment(
    *,
    signup_id: int,
    gear_attachment_url: str,
    gear_attachment_filename: str | None,
    now_utc: datetime,
) -> bool:
    def _callback(cur):
        cur.execute(
            """
            UPDATE dbo.MGE_Signups
            SET
                GearAttachmentUrl = ?,
                GearAttachmentFilename = ?,
                UpdatedUtc = ?
            WHERE SignupId = ?;
            """,
            (
                gear_attachment_url,
                gear_attachment_filename,
                _naive_utc(now_utc),
                signup_id,
            ),
        )
        return int(cur.rowcount or 0) > 0

    try:
        result = exec_with_cursor(_callback)
        return bool(result)
    except Exception:
        logger.exception(
            "mge_signup_dal_update_signup_gear_attachment_failed signup_id=%s", signup_id
        )
        return False


def update_signup_armament_attachment(
    *,
    signup_id: int,
    armament_attachment_url: str,
    armament_attachment_filename: str | None,
    now_utc: datetime,
) -> bool:
    def _callback(cur):
        cur.execute(
            """
            UPDATE dbo.MGE_Signups
            SET
                ArmamentAttachmentUrl = ?,
                ArmamentAttachmentFilename = ?,
                UpdatedUtc = ?
            WHERE SignupId = ?;
            """,
            (
                armament_attachment_url,
                armament_attachment_filename,
                _naive_utc(now_utc),
                signup_id,
            ),
        )
        return int(cur.rowcount or 0) > 0

    try:
        result = exec_with_cursor(_callback)
        return bool(result)
    except Exception:
        logger.exception(
            "mge_signup_dal_update_signup_armament_attachment_failed signup_id=%s", signup_id
        )
        return False


def withdraw_signup(*, signup_id: int, now_utc: datetime) -> bool:
    def _callback(cur):
        cur.execute(
            """
            UPDATE dbo.MGE_Signups
            SET IsActive = 0,
                UpdatedUtc = ?
            WHERE SignupId = ?;
            """,
            (_naive_utc(now_utc), signup_id),
        )
        return int(cur.rowcount or 0) > 0

    try:
        result = exec_with_cursor(_callback)
        return bool(result)
    except Exception:
        logger.exception("mge_signup_dal_withdraw_signup_failed signup_id=%s", signup_id)
        return False


def insert_signup_audit(
    *,
    signup_id: int,
    event_id: int,
    governor_id: int,
    action_type: str,
    actor_discord_id: int | None,
    details: dict[str, Any] | None,
    now_utc: datetime,
) -> bool:
    def _callback(cur):
        details_json = json.dumps(details or {}, ensure_ascii=False)
        cur.execute(
            """
            INSERT INTO dbo.MGE_SignupAudit
            (
                SignupId,
                EventId,
                GovernorId,
                ActionType,
                ActorDiscordId,
                DetailsJson,
                CreatedUtc
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                signup_id,
                event_id,
                governor_id,
                action_type,
                actor_discord_id,
                details_json,
                _naive_utc(now_utc),
            ),
        )
        return True

    try:
        result = exec_with_cursor(_callback)
        return bool(result)
    except Exception:
        logger.exception(
            "mge_signup_dal_insert_signup_audit_failed signup_id=%s action_type=%s",
            signup_id,
            action_type,
        )
        return False
