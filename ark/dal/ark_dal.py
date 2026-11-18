from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
import logging
from typing import Any

from ark.ark_constants import ARK_MATCH_STATUS_SCHEDULED, ARK_MATCH_STATUSES_OPEN
from ark.db_reminder_prefs import (
    get_reminder_prefs as _get_reminder_prefs_sync,
    upsert_reminder_prefs as _upsert_reminder_prefs_sync,
)
from file_utils import run_blocking_in_thread
from stats_alerts.db import (
    execute_async,
    run_one_async,
    run_one_strict_async,
    run_query_async,
    run_query_strict_async,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArkMatchCreateRequest:
    alliance: str
    ark_weekend_date: date
    match_day: str
    match_time_utc: time
    registration_starts_at_utc: datetime
    signup_close_utc: datetime
    notes: str | None
    actor_discord_id: int
    calendar_instance_id: int | None = None
    created_source: str | None = None


async def list_alliances(active_only: bool = True) -> list[dict[str, Any]]:
    sql = """
        SELECT Alliance, RegistrationChannelId, ConfirmationChannelId, IsActive
        FROM dbo.ArkAlliances
        WHERE (? = 0 OR IsActive = 1)
        ORDER BY Alliance ASC;
    """
    return await run_query_async(sql, (1 if active_only else 0,))


async def get_alliance(alliance: str) -> dict[str, Any] | None:
    sql = """
        SELECT Alliance, RegistrationChannelId, ConfirmationChannelId, IsActive
        FROM dbo.ArkAlliances
        WHERE Alliance = ?;
    """
    return await run_one_async(sql, (alliance,))


async def get_config() -> dict[str, Any] | None:
    sql = "SELECT TOP 1 * FROM dbo.ArkConfig ORDER BY ConfigId DESC;"
    return await run_one_async(sql)


async def fetch_ark_calendar_candidates(
    window_start: datetime,
    window_end: datetime,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            InstanceID,
            SourceKind,
            SourceID,
            StartUTC,
            EndUTC,
            Title,
            EventType,
            IsCancelled
        FROM dbo.EventInstances
        WHERE EventType = 'ark'
          AND IsCancelled = 0
          AND StartUTC >= ?
          AND StartUTC < ?
        ORDER BY StartUTC ASC, InstanceID ASC;
    """
    return await run_query_async(sql, (window_start, window_end))


async def match_exists(alliance: str, ark_weekend_date: date) -> bool:
    sql = """
        SELECT COUNT(1) AS Cnt
        FROM dbo.ArkMatches
        WHERE Alliance = ? AND ArkWeekendDate = ?;
    """
    row = await run_one_async(sql, (alliance, ark_weekend_date))
    return int((row or {}).get("Cnt") or 0) > 0


async def create_match(req: ArkMatchCreateRequest) -> int:
    sql = """
        INSERT INTO dbo.ArkMatches
            (
                Alliance,
                ArkWeekendDate,
                MatchDay,
                MatchTimeUtc,
                RegistrationStartsAtUtc,
                SignupCloseUtc,
                Status,
                Notes,
                CalendarInstanceId,
                CreatedSource
            )
        OUTPUT INSERTED.MatchId
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    row = await run_one_async(
        sql,
        (
            req.alliance,
            req.ark_weekend_date,
            req.match_day,
            req.match_time_utc,
            req.registration_starts_at_utc,
            req.signup_close_utc,
            ARK_MATCH_STATUS_SCHEDULED,
            req.notes,
            req.calendar_instance_id,
            req.created_source,
        ),
    )
    return int((row or {}).get("MatchId") or 0)


async def list_matches_pending_registration_open(now_utc: datetime) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM dbo.ArkMatches
        WHERE Status = 'Scheduled'
          AND RegistrationStartsAtUtc IS NOT NULL
          AND RegistrationStartsAtUtc <= ?
          AND SignupCloseUtc > ?
          AND (
                RegistrationMessageId IS NULL
                OR RegistrationChannelId IS NULL
          )
        ORDER BY RegistrationStartsAtUtc ASC, MatchId ASC;
    """
    return await run_query_async(sql, (now_utc, now_utc))


async def amend_match(
    match_id: int,
    alliance: str,
    match_day: str,
    match_time_utc: time,
    signup_close_utc: datetime,
    notes: str | None,
    actor_discord_id: int,
) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET Alliance = ?,
            MatchDay = ?,
            MatchTimeUtc = ?,
            SignupCloseUtc = ?,
            Notes = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(
        sql,
        (alliance, match_day, match_time_utc, signup_close_utc, notes, match_id),
    )
    return int((row or {}).get("MatchId") or 0) > 0


async def cancel_match(match_id: int, actor_discord_id: int) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET Status = 'Cancelled',
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (match_id,))
    return int((row or {}).get("MatchId") or 0) > 0


async def get_match(match_id: int) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM dbo.ArkMatches
        WHERE MatchId = ?;
    """
    return await run_one_async(sql, (match_id,))


async def get_match_by_alliance_weekend(
    alliance: str,
    ark_weekend_date: date,
) -> dict[str, Any] | None:
    sql = """
        SELECT *
        FROM dbo.ArkMatches
        WHERE Alliance = ? AND ArkWeekendDate = ?;
    """
    return await run_one_async(sql, (alliance, ark_weekend_date))


async def clear_match_signups(match_id: int, status: str = "Removed") -> int:
    sql = """
        UPDATE dbo.ArkSignups
        SET Status = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND Status = 'Active';
    """
    rows = await run_query_async(sql, (status, match_id))
    return len(rows or [])


async def reopen_cancelled_match(
    match_id: int,
    match_day: str,
    match_time_utc: time,
    signup_close_utc: datetime,
    notes: str | None,
) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET MatchDay = ?,
            MatchTimeUtc = ?,
            SignupCloseUtc = ?,
            Notes = ?,
            Status = 'Scheduled',
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ? AND Status = 'Cancelled';
    """
    row = await run_one_async(
        sql,
        (match_day, match_time_utc, signup_close_utc, notes, match_id),
    )
    return int((row or {}).get("MatchId") or 0) > 0


async def list_open_matches(alliance: str | None = None) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM dbo.ArkMatches
        WHERE Status IN ('Scheduled', 'Locked')
          AND (? IS NULL OR Alliance = ?)
        ORDER BY ArkWeekendDate ASC, MatchTimeUtc ASC;
    """
    return await run_query_async(sql, (alliance, alliance))


async def get_roster(match_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT MatchId, GovernorId, GovernorNameSnapshot, DiscordUserId, SlotType, Status, CreatedAtUtc,
               CheckedIn, CheckedInAtUtc, NoShow, NoShowAtUtc
        FROM dbo.ArkSignups
        WHERE MatchId = ? AND Status = 'Active'
        ORDER BY CreatedAtUtc ASC;
    """
    return await run_query_async(sql, (match_id,))


async def lock_match(match_id: int, actor_discord_id: int | None = None) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET Status = 'Locked',
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ? AND Status <> 'Locked';
    """
    row = await run_one_async(sql, (match_id,))
    return int((row or {}).get("MatchId") or 0) > 0


async def update_match_confirmation_message(
    match_id: int, confirmation_channel_id: int, confirmation_message_id: int
) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET ConfirmationChannelId = ?,
            ConfirmationMessageId = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (confirmation_channel_id, confirmation_message_id, match_id))
    return int((row or {}).get("MatchId") or 0) > 0


async def update_match_registration_message(
    match_id: int,
    registration_channel_id: int,
    registration_message_id: int,
) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET RegistrationChannelId = ?,
            RegistrationMessageId = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (registration_channel_id, registration_message_id, match_id))
    return int((row or {}).get("MatchId") or 0) > 0


async def mark_registration_announcement(
    match_id: int,
    *,
    announcement_sent: bool,
    announcement_sent_at_utc: datetime | None,
) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET AnnouncementSent = ?,
            AnnouncementSentAtUtc = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(
        sql,
        (1 if announcement_sent else 0, announcement_sent_at_utc, match_id),
    )
    return int((row or {}).get("MatchId") or 0) > 0


async def touch_registration_refresh(match_id: int, refreshed_at_utc: datetime) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET LastRegistrationRefreshAtUtc = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (refreshed_at_utc, match_id))
    return int((row or {}).get("MatchId") or 0) > 0


async def find_active_signup_for_weekend(
    governor_id: int,
    ark_weekend_date: date,
    exclude_match_id: int | None = None,
) -> dict[str, Any] | None:
    sql = """
        SELECT s.MatchId, m.Alliance, m.ArkWeekendDate, m.MatchDay, m.MatchTimeUtc
        FROM dbo.ArkSignups s
        JOIN dbo.ArkMatches m ON m.MatchId = s.MatchId
        WHERE s.GovernorId = ?
          AND s.Status = 'Active'
          AND m.ArkWeekendDate = ?
          AND m.Status IN (?, ?)
          AND (? IS NULL OR s.MatchId <> ?);
    """
    return await run_one_async(
        sql,
        (
            governor_id,
            ark_weekend_date,
            *sorted(ARK_MATCH_STATUSES_OPEN),
            exclude_match_id,
            exclude_match_id,
        ),
    )


async def add_signup(
    match_id: int,
    governor_id: int,
    governor_name: str,
    discord_user_id: int | None,
    slot_type: str,
    source: str,
    actor_discord_id: int | None,
) -> int:
    sql = """
        INSERT INTO dbo.ArkSignups
            (MatchId, GovernorId, GovernorNameSnapshot, DiscordUserId, SlotType, Status, Source)
        OUTPUT INSERTED.SignupId
        VALUES (?, ?, ?, ?, ?, 'Active', ?);
    """
    row = await run_one_async(
        sql,
        (
            match_id,
            governor_id,
            governor_name,
            discord_user_id,
            slot_type,
            source,
        ),
    )
    return int((row or {}).get("SignupId") or 0)


async def remove_signup(
    match_id: int,
    governor_id: int,
    status: str,
    actor_discord_id: int | None,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET Status = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ? AND Status = 'Active';
    """
    row = await run_one_async(sql, (status, match_id, governor_id))
    return int((row or {}).get("SignupId") or 0) > 0


async def get_signup(
    match_id: int,
    governor_id: int,
) -> dict[str, Any] | None:
    sql = """
        SELECT TOP 1 *
        FROM dbo.ArkSignups
        WHERE MatchId = ? AND GovernorId = ?;
    """
    return await run_one_async(sql, (match_id, governor_id))


async def reactivate_signup(
    match_id: int,
    governor_id: int,
    governor_name: str,
    discord_user_id: int | None,
    slot_type: str,
    source: str,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET Status = 'Active',
            SlotType = ?,
            DiscordUserId = ?,
            GovernorNameSnapshot = ?,
            Source = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ?;
    """
    row = await run_one_async(
        sql,
        (slot_type, discord_user_id, governor_name, source, match_id, governor_id),
    )
    return int((row or {}).get("SignupId") or 0) > 0


async def switch_signup_governor(
    match_id: int,
    old_governor_id: int,
    new_governor_id: int,
    new_governor_name: str,
    discord_user_id: int,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET GovernorId = ?,
            GovernorNameSnapshot = ?,
            DiscordUserId = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ? AND Status = 'Active';
    """
    row = await run_one_async(
        sql,
        (new_governor_id, new_governor_name, discord_user_id, match_id, old_governor_id),
    )
    return int((row or {}).get("SignupId") or 0) > 0


async def move_signup_slot(
    match_id: int,
    governor_id: int,
    slot_type: str,
    actor_discord_id: int,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET SlotType = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ? AND Status = 'Active';
    """
    row = await run_one_async(sql, (slot_type, match_id, governor_id))
    return int((row or {}).get("SignupId") or 0) > 0


async def mark_checked_in(
    match_id: int,
    governor_id: int,
    checked_in_at_utc: datetime,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET CheckedIn = 1,
            CheckedInAtUtc = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ? AND Status = 'Active';
    """
    row = await run_one_async(sql, (checked_in_at_utc, match_id, governor_id))
    return int((row or {}).get("SignupId") or 0) > 0


async def mark_emergency_withdraw(
    match_id: int,
    governor_id: int,
    actor_discord_id: int,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET Status = 'Withdrawn',
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ? AND Status = 'Active';
    """
    row = await run_one_async(sql, (match_id, governor_id))
    return int((row or {}).get("SignupId") or 0) > 0


async def mark_no_show(
    match_id: int,
    governor_id: int,
    actor_discord_id: int,
) -> bool:
    sql = """
        UPDATE dbo.ArkSignups
        SET NoShow = 1,
            NoShowAtUtc = SYSUTCDATETIME(),
            NoShowByDiscordId = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.SignupId
        WHERE MatchId = ? AND GovernorId = ? AND Status = 'Active';
    """
    row = await run_one_async(sql, (actor_discord_id, match_id, governor_id))
    return int((row or {}).get("SignupId") or 0) > 0


async def add_ban(
    governor_id: int,
    governor_name: str,
    reason: str | None,
    actor_discord_id: int,
) -> int:
    sql = """
        INSERT INTO dbo.ArkBans
            (GovernorId, GovernorNameSnapshot, Reason, CreatedByDiscordId, IsActive)
        OUTPUT INSERTED.BanId
        VALUES (?, ?, ?, ?, 1);
    """
    row = await run_one_async(sql, (governor_id, governor_name, reason, actor_discord_id))
    return int((row or {}).get("BanId") or 0)


async def revoke_ban(ban_id: int, actor_discord_id: int) -> bool:
    sql = """
        UPDATE dbo.ArkBans
        SET IsActive = 0,
            RevokedByDiscordId = ?,
            RevokedAtUtc = SYSUTCDATETIME(),
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.BanId
        WHERE BanId = ? AND IsActive = 1;
    """
    row = await run_one_async(sql, (actor_discord_id, ban_id))
    return int((row or {}).get("BanId") or 0) > 0


async def list_bans(active_only: bool = True) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM dbo.ArkBans
        WHERE (? = 0 OR IsActive = 1)
        ORDER BY CreatedAtUtc DESC;
    """
    return await run_query_async(sql, (1 if active_only else 0,))


async def get_active_ban_for(
    discord_user_id: int | None,
    governor_id: int | None,
    ark_weekend_date: date,
) -> dict[str, Any] | None:
    """
    Return the first active ban that applies to this discord_user_id or governor_id
    on the given ark_weekend_date, or None if no ban applies.

    At least one of discord_user_id or governor_id must be provided.
    Ownership: ark/dal/ark_dal.py
    """
    if not discord_user_id and not governor_id:
        return None

    sql = """
        SELECT TOP 1
            BanId,
            DiscordUserId,
            GovernorId,
            Reason,
            BannedArkWeekends,
            StartArkWeekendDate,
            EndArkWeekendDate,
            CreatedAtUtc,
            CreatedByDiscordId,
            RevokedAtUtc,
            RevokedByDiscordId
        FROM dbo.ArkBans
        WHERE RevokedAtUtc IS NULL
          AND StartArkWeekendDate <= ?
          AND EndArkWeekendDate >= ?
          AND (
                (? IS NOT NULL AND DiscordUserId = ?)
             OR (? IS NOT NULL AND GovernorId = ?)
          )
        ORDER BY BanId DESC;
    """
    return await run_one_async(
        sql,
        (
            ark_weekend_date,
            ark_weekend_date,
            discord_user_id,
            discord_user_id,
            governor_id,
            governor_id,
        ),
    )


async def get_reminder_prefs(discord_user_id: int) -> dict | None:
    return await run_blocking_in_thread(
        _get_reminder_prefs_sync,
        discord_user_id,
        name="ark_get_reminder_prefs",
    )


async def upsert_reminder_prefs(
    discord_user_id: int,
    opt_out_all: int,
    opt_out_24h: int,
    opt_out_4h: int,
    opt_out_1h: int,
    opt_out_start: int,
    opt_out_checkin_12h: int,
) -> bool:
    return await run_blocking_in_thread(
        _upsert_reminder_prefs_sync,
        discord_user_id,
        opt_out_all=opt_out_all,
        opt_out_24h=opt_out_24h,
        opt_out_4h=opt_out_4h,
        opt_out_1h=opt_out_1h,
        opt_out_start=opt_out_start,
        opt_out_checkin_12h=opt_out_checkin_12h,
        name="ark_upsert_reminder_prefs",
    )


async def list_player_report_rows() -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM dbo.vw_ArkPlayerReport
        ORDER BY MatchesPlayed DESC, GovernorName ASC;
    """
    return await run_query_async(sql)


async def set_match_result(
    match_id: int,
    result: str,
    notes: str | None,
    actor_discord_id: int,
) -> bool:
    normalized = (result or "").strip().title()
    if normalized not in {"Win", "Loss"}:
        raise ValueError("Result must be Win or Loss.")

    sql = """
        UPDATE dbo.ArkMatches
        SET Result = ?,
            ResultNotes = ?,
            Status = 'Completed',
            CompletedAtUtc = SYSUTCDATETIME(),
            CompletedByDiscordId = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (normalized, notes, actor_discord_id, match_id))
    return int((row or {}).get("MatchId") or 0) > 0


async def mark_match_completed(
    match_id: int,
    actor_discord_id: int | None = None,
) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET Status = 'Completed',
            CompletedAtUtc = COALESCE(CompletedAtUtc, SYSUTCDATETIME()),
            CompletedByDiscordId = COALESCE(CompletedByDiscordId, ?),
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?
          AND Status IN ('Locked', 'Scheduled');
    """
    row = await run_one_async(sql, (actor_discord_id, match_id))
    return int((row or {}).get("MatchId") or 0) > 0


async def insert_audit_log(
    action_type: str,
    actor_discord_id: int,
    match_id: int | None,
    governor_id: int | None,
    details_json: dict[str, Any] | None,
) -> int:
    import json

    sql = """
        INSERT INTO dbo.ArkAuditLog
            (ActionType, ActorDiscordId, MatchId, GovernorId, DetailsJson)
        OUTPUT INSERTED.LogId
        VALUES (?, ?, ?, ?, ?);
    """
    details = json.dumps(details_json) if details_json else None
    row = await run_one_async(sql, (action_type, actor_discord_id, match_id, governor_id, details))
    return int((row or {}).get("LogId") or 0)


async def list_completed_matches_pending_completion(days_back: int = 7) -> list[dict[str, Any]]:
    sql = """
        SELECT *
        FROM dbo.ArkMatches
        WHERE Status = 'Completed'
          AND (
                CompletionEmbedPostedAtUtc IS NULL
                OR CompletionEmbedPostedAtUtc < UpdatedAtUtc
          )
          AND CompletedAtUtc >= DATEADD(day, -?, SYSUTCDATETIME())
        ORDER BY CompletedAtUtc DESC;
    """
    return await run_query_async(sql, (days_back,))


async def mark_match_completion_posted(match_id: int) -> bool:
    sql = """
        UPDATE dbo.ArkMatches
        SET CompletionEmbedPostedAtUtc = SYSUTCDATETIME(),
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (match_id,))
    return int((row or {}).get("MatchId") or 0) > 0


async def upsert_team_preference(
    governor_id: int,
    preferred_team: int,
    updated_by: str,
) -> dict[str, Any] | None:
    sql = """
        MERGE dbo.ArkTeamPreferences AS target
        USING (SELECT CAST(? AS bigint) AS GovernorID) AS source
          ON target.GovernorID = source.GovernorID
        WHEN MATCHED THEN
            UPDATE SET
                PreferredTeam = ?,
                IsActive = 1,
                UpdatedAtUTC = SYSUTCDATETIME(),
                UpdatedBy = ?
        WHEN NOT MATCHED THEN
            INSERT (GovernorID, PreferredTeam, IsActive, CreatedAtUTC, UpdatedAtUTC, UpdatedBy)
            VALUES (?, ?, 1, SYSUTCDATETIME(), SYSUTCDATETIME(), ?)
        OUTPUT
            inserted.GovernorID,
            inserted.PreferredTeam,
            inserted.IsActive,
            inserted.CreatedAtUTC,
            inserted.UpdatedAtUTC,
            inserted.UpdatedBy;
    """
    return await run_one_async(
        sql,
        (governor_id, preferred_team, updated_by, governor_id, preferred_team, updated_by),
    )


async def get_team_preference(governor_id: int, active_only: bool = True) -> dict[str, Any] | None:
    sql = """
        SELECT GovernorID, PreferredTeam, IsActive, CreatedAtUTC, UpdatedAtUTC, UpdatedBy
        FROM dbo.ArkTeamPreferences
        WHERE GovernorID = ?
          AND (? = 0 OR IsActive = 1);
    """
    return await run_one_async(sql, (governor_id, 1 if active_only else 0))


async def list_active_team_preferences() -> list[dict[str, Any]]:
    sql = """
        SELECT GovernorID, PreferredTeam, IsActive, CreatedAtUTC, UpdatedAtUTC, UpdatedBy
        FROM dbo.ArkTeamPreferences
        WHERE IsActive = 1
        ORDER BY GovernorID ASC;
    """
    return await run_query_async(sql)


async def clear_team_preference(governor_id: int, updated_by: str) -> dict[str, Any] | None:
    sql = """
        UPDATE dbo.ArkTeamPreferences
        SET IsActive = 0,
            UpdatedAtUTC = SYSUTCDATETIME(),
            UpdatedBy = ?
        OUTPUT inserted.GovernorID, inserted.PreferredTeam, inserted.IsActive,
               inserted.CreatedAtUTC, inserted.UpdatedAtUTC, inserted.UpdatedBy
        WHERE GovernorID = ?
          AND IsActive = 1;
    """
    return await run_one_async(sql, (updated_by, governor_id))


async def get_governor_power_bulk(governor_ids: list[int]) -> dict[int, int]:
    ids = sorted({int(gid) for gid in (governor_ids or [])})
    if not ids:
        return {}

    values = ", ".join(["(?)"] * len(ids))
    sql = f"""
        WITH input_ids (GovernorID) AS (
            SELECT CAST(v.GovernorID AS bigint)
            FROM (VALUES {values}) AS v(GovernorID)
        )
        SELECT i.GovernorID, p.Power
        FROM input_ids i
        LEFT JOIN dbo.v_PlayerProfile p WITH (NOLOCK)
          ON p.GovernorID = i.GovernorID;
    """
    rows = await run_query_async(sql, tuple(ids))
    out: dict[int, int] = {}
    for row in rows or []:
        gid = row.get("GovernorID")
        if gid is None:
            continue
        try:
            out[int(gid)] = int(row.get("Power") or 0)
        except Exception:
            out[int(gid)] = 0
    for gid in ids:
        out.setdefault(int(gid), 0)
    return out


async def list_match_team_rows(match_id: int, draft_only: bool = True) -> list[dict[str, Any]]:
    """
    Return ArkMatchTeams rows for a match.

    draft_only=True  → only draft rows  (IsDraft=1, IsFinal=0)
    draft_only=False → all rows         (both draft and final)
    """
    sql = """
        SELECT
            MatchId,
            GovernorId,
            TeamNumber,
            IsDraft,
            IsFinal,
            UpdatedAtUtc
        FROM dbo.ArkMatchTeams
        WHERE MatchId = ?
          AND (? = 0 OR IsDraft = 1)
        ORDER BY TeamNumber ASC, GovernorId ASC;
    """
    rows = await run_query_strict_async(sql, (int(match_id), 1 if draft_only else 0))
    logger.info(
        "[ARK_TEAM_DAL] list_match_team_rows match_id=%s draft_only=%s rows=%s",
        int(match_id),
        bool(draft_only),
        len(rows or []),
    )
    return rows


async def replace_match_draft_rows(
    *,
    match_id: int,
    assignments: list[tuple[int, int]],
    actor_discord_id: int,
    source: str,
    check_finalized_only: bool = False,
) -> bool:
    """
    Atomically replace all draft rows for a match with the provided assignments.

    Ownership: ark/dal/ark_dal.py
    State model:
      - Draft rows: IsDraft=1, IsFinal=0
      - Final rows: IsDraft=0, IsFinal=1
      - A match is blocked from draft mutation while IsFinal=1 rows exist.

    Steps (sequential single-statement calls — no multi-statement batch):
      1. Check for finalized rows. Return False if blocked.
      2. If check_finalized_only=True, return True/False without mutation.
      3. DELETE existing draft rows for the match.
      4. INSERT new draft rows (skipped if assignments is empty — reset path).
      5. Return True.

    Returns:
      True  — draft rows replaced (or cleared) successfully.
      False — blocked because IsFinal=1 rows exist for this match.
    """
    match_id_i = int(match_id)
    actor_i = int(actor_discord_id)
    source_s = str(source)

    # Deduplicate and validate assignments.
    normalized: list[tuple[int, int]] = []
    seen: set[int] = set()
    for governor_id, team_number in assignments or []:
        gid = int(governor_id)
        team = int(team_number)
        if team not in (1, 2) or gid in seen:
            continue
        seen.add(gid)
        normalized.append((gid, team))

    logger.info(
        "[ARK_TEAM_DAL] replace_draft_start match_id=%s assignments_raw=%s assignments_normalized=%s "
        "source=%s actor_discord_id=%s check_finalized_only=%s",
        match_id_i,
        len(assignments or []),
        len(normalized),
        source_s,
        actor_i,
        bool(check_finalized_only),
    )

    # ── Step 1: Check for existing final rows (single SELECT — no multi-result-set risk). ──
    guard_row = await run_one_strict_async(
        """
        SELECT COUNT(1) AS FinalCount
        FROM dbo.ArkMatchTeams
        WHERE MatchId = ?
          AND IsFinal = 1;
        """,
        (match_id_i,),
    )
    final_count_existing = int((guard_row or {}).get("FinalCount") or 0)
    is_finalized = final_count_existing > 0

    logger.info(
        "[ARK_TEAM_DAL] replace_draft_finalized_check match_id=%s final_rows_existing=%s blocked=%s",
        match_id_i,
        final_count_existing,
        is_finalized,
    )

    # ── Step 2: check_finalized_only path — return without mutation. ──
    if check_finalized_only:
        # Returns True if we CAN mutate (not finalized), False if blocked.
        return not is_finalized

    if is_finalized:
        logger.warning(
            "[ARK_TEAM_DAL] replace_draft_blocked match_id=%s reason=finalized_rows_exist "
            "final_rows=%s source=%s",
            match_id_i,
            final_count_existing,
            source_s,
        )
        return False

    # ── Step 3: DELETE existing draft rows (single DELETE statement). ──
    deleted_count = await execute_async(
        """
        DELETE FROM dbo.ArkMatchTeams
        WHERE MatchId = ?
          AND IsDraft = 1
          AND IsFinal = 0;
        """,
        (match_id_i,),
    )
    logger.info(
        "[ARK_TEAM_DAL] replace_draft_deleted match_id=%s deleted_rows=%s",
        match_id_i,
        int(deleted_count),
    )

    # ── Step 4: INSERT new draft rows (skipped on reset/empty path). ──
    inserted_count = 0
    if normalized:
        # Build a parameterised VALUES list — one row per assignment.
        # Each row: (MatchId, GovernorId, TeamNumber, IsDraft, IsFinal, Source,
        #            CreatedByDiscordId, UpdatedByDiscordId)
        placeholders = ", ".join(["(?, ?, ?, 1, 0, ?, ?, ?)"] * len(normalized))
        params: list[Any] = []
        for gid, team in normalized:
            params.extend([match_id_i, gid, team, source_s, actor_i, actor_i])

        inserted_count = await execute_async(
            f"""
            INSERT INTO dbo.ArkMatchTeams
                (MatchId, GovernorId, TeamNumber, IsDraft, IsFinal,
                 Source, CreatedByDiscordId, UpdatedByDiscordId)
            VALUES {placeholders};
            """,
            tuple(params),
        )

    logger.info(
        "[ARK_TEAM_DAL] replace_draft_done match_id=%s inserted_rows=%s source=%s ok=True",
        match_id_i,
        int(inserted_count),
        source_s,
    )
    return True


async def promote_match_draft_to_final(
    *,
    match_id: int,
    actor_discord_id: int,
    source: str,
) -> bool:
    """
    Promote persisted draft rows to final rows for a match.

    Ownership: ark/dal/ark_dal.py
    State model:
      - Reads IsDraft=1, IsFinal=0 rows as source.
      - Deletes any existing IsFinal=1 rows first.
      - Inserts new IsDraft=0, IsFinal=1 rows from draft source.
      - Returns True if final_count >= draft_count after promotion.

    All steps are separate single-statement calls — no multi-statement batch.
    """
    match_id_i = int(match_id)
    actor_i = int(actor_discord_id)
    source_s = str(source)

    # ── Step 1: Count draft rows. Abort if none exist. ──
    draft_row = await run_one_strict_async(
        """
        SELECT COUNT(1) AS DraftCount
        FROM (
            SELECT GovernorId
            FROM dbo.ArkMatchTeams
            WHERE MatchId = ?
              AND IsDraft = 1
              AND IsFinal = 0
            GROUP BY GovernorId
        ) d;
        """,
        (match_id_i,),
    )
    draft_target = int((draft_row or {}).get("DraftCount") or 0)

    if draft_target < 1:
        logger.warning(
            "[ARK_TEAM_DAL] promote_to_final_blocked match_id=%s reason=no_draft_rows source=%s",
            match_id_i,
            source_s,
        )
        return False

    logger.info(
        "[ARK_TEAM_DAL] promote_to_final_start match_id=%s draft_target=%s source=%s "
        "actor_discord_id=%s",
        match_id_i,
        draft_target,
        source_s,
        actor_i,
    )

    # ── Step 2: Delete existing final rows. ──
    deleted_final = await execute_async(
        """
        DELETE FROM dbo.ArkMatchTeams
        WHERE MatchId = ?
          AND IsFinal = 1;
        """,
        (match_id_i,),
    )
    logger.info(
        "[ARK_TEAM_DAL] promote_to_final_cleared_existing match_id=%s deleted_final_rows=%s",
        match_id_i,
        int(deleted_final),
    )

    # ── Step 3: Insert final rows from draft source. ──
    inserted_final = await execute_async(
        """
        ;WITH draft AS (
            SELECT
                MatchId,
                GovernorId,
                TeamNumber,
                CreatedByDiscordId,
                ROW_NUMBER() OVER (
                    PARTITION BY GovernorId
                    ORDER BY UpdatedAtUtc DESC, ArkMatchTeamId DESC
                ) AS rn
            FROM dbo.ArkMatchTeams WITH (UPDLOCK, HOLDLOCK)
            WHERE MatchId = ?
              AND IsDraft = 1
              AND IsFinal = 0
        )
        INSERT INTO dbo.ArkMatchTeams
            (
                MatchId,
                GovernorId,
                TeamNumber,
                IsDraft,
                IsFinal,
                Source,
                CreatedByDiscordId,
                UpdatedByDiscordId,
                FinalizedAtUtc,
                FinalizedByDiscordId
            )
        SELECT
            d.MatchId,
            d.GovernorId,
            d.TeamNumber,
            0,
            1,
            ?,
            COALESCE(d.CreatedByDiscordId, ?),
            ?,
            SYSUTCDATETIME(),
            ?
        FROM draft d
        WHERE d.rn = 1
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.ArkMatchTeams f
                WHERE f.MatchId = d.MatchId
                  AND f.GovernorId = d.GovernorId
                  AND f.IsFinal = 1
            );
        """,
        (match_id_i, source_s, actor_i, actor_i, actor_i),
    )

    # ── Step 4: Verify final row count. ──
    final_verify_row = await run_one_strict_async(
        """
        SELECT COUNT(1) AS FinalCount
        FROM dbo.ArkMatchTeams
        WHERE MatchId = ?
          AND IsFinal = 1;
        """,
        (match_id_i,),
    )
    final_count = int((final_verify_row or {}).get("FinalCount") or 0)
    ok = final_count > 0 and final_count >= draft_target

    logger.info(
        "[ARK_TEAM_DAL] promote_to_final_done match_id=%s draft_target=%s "
        "prior_final_deleted=%s inserted_final=%s final_count_verified=%s ok=%s "
        "source=%s actor_discord_id=%s",
        match_id_i,
        draft_target,
        int(deleted_final),
        int(inserted_final),
        final_count,
        ok,
        source_s,
        actor_i,
    )
    return ok


async def clear_match_final_rows(
    *,
    match_id: int,
) -> int:
    """
    Delete all IsFinal=1 rows for a match (unpublish).

    Returns the count of rows deleted.
    Ownership: ark/dal/ark_dal.py
    """
    match_id_i = int(match_id)
    removed = await execute_async(
        """
        DELETE FROM dbo.ArkMatchTeams
        WHERE MatchId = ?
          AND IsFinal = 1;
        """,
        (match_id_i,),
    )
    removed_i = int(removed)
    logger.info(
        "[ARK_TEAM_DAL] clear_final_rows match_id=%s removed_rows=%s",
        match_id_i,
        removed_i,
    )
    return removed_i


async def get_teams_first_published_at(match_id: int) -> datetime | None:
    """Return TeamsFirstPublishedAtUtc for *match_id*, or None if not yet set.

    Used by team_publish.py to determine whether this is the first publish of
    team assignments for a match, replacing the in-memory `published_at_utc`
    check so the flag survives bot restarts.
    """
    sql = """
        SELECT TeamsFirstPublishedAtUtc
        FROM dbo.ArkMatches
        WHERE MatchId = ?;
    """
    row = await run_one_async(sql, (match_id,))
    if row is None:
        return None
    raw = row.get("TeamsFirstPublishedAtUtc")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    # Handle string form (some ODBC drivers return strings)
    from utils import ensure_aware_utc

    try:
        return ensure_aware_utc(raw)
    except Exception:
        return None


async def mark_teams_first_published(match_id: int) -> bool:
    """Set TeamsFirstPublishedAtUtc = SYSUTCDATETIME() if it is currently NULL.

    Idempotent: if the column is already set the UPDATE touches 0 rows and
    returns False, which is the correct signal for "not first publish".
    Returns True only when the row was actually updated (first publish).
    """
    sql = """
        UPDATE dbo.ArkMatches
        SET TeamsFirstPublishedAtUtc = SYSUTCDATETIME(),
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.MatchId
        WHERE MatchId = ?
          AND TeamsFirstPublishedAtUtc IS NULL;
    """
    row = await run_one_async(sql, (match_id,))
    return int((row or {}).get("MatchId") or 0) > 0
