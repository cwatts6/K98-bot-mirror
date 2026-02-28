from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

from ark.ark_constants import ARK_MATCH_STATUS_SCHEDULED, ARK_MATCH_STATUSES_OPEN
from ark.db_reminder_prefs import (
    get_reminder_prefs as _get_reminder_prefs_sync,
    upsert_reminder_prefs as _upsert_reminder_prefs_sync,
)
from file_utils import run_blocking_in_thread
from stats_alerts.db import run_one_async, run_query_async


@dataclass(frozen=True)
class ArkMatchCreateRequest:
    alliance: str
    ark_weekend_date: date
    match_day: str
    match_time_utc: time
    signup_close_utc: datetime
    notes: str | None
    actor_discord_id: int


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
            (Alliance, ArkWeekendDate, MatchDay, MatchTimeUtc, SignupCloseUtc, Status, Notes)
        OUTPUT INSERTED.MatchId
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    row = await run_one_async(
        sql,
        (
            req.alliance,
            req.ark_weekend_date,
            req.match_day,
            req.match_time_utc,
            req.signup_close_utc,
            ARK_MATCH_STATUS_SCHEDULED,
            req.notes,
        ),
    )
    return int((row or {}).get("MatchId") or 0)


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
        WHERE Status IN (?, ?)
          AND (? IS NULL OR Alliance = ?)
        ORDER BY ArkWeekendDate ASC, MatchTimeUtc ASC;
    """
    return await run_query_async(
        sql,
        (
            *sorted(ARK_MATCH_STATUSES_OPEN),
            alliance,
            alliance,
        ),
    )


async def get_roster(match_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT MatchId, GovernorId, GovernorNameSnapshot, DiscordUserId, SlotType, Status, CreatedAtUtc,
               CheckedIn, CheckedInAtUtc
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


async def add_ban(
    discord_user_id: int | None,
    governor_id: int | None,
    banned_ark_weekends: int,
    start_ark_weekend_date: date,
    reason: str | None,
    actor_discord_id: int,
) -> int:
    raise NotImplementedError


async def revoke_ban(ban_id: int, actor_discord_id: int) -> bool:
    raise NotImplementedError


async def list_bans(active_only: bool = True) -> list[dict[str, Any]]:
    raise NotImplementedError


async def get_active_ban_for(
    discord_user_id: int | None,
    governor_id: int | None,
    ark_weekend_date: date,
) -> dict[str, Any] | None:
    raise NotImplementedError


async def get_reminder_prefs(discord_user_id: int) -> dict | None:
    return await run_blocking_in_thread(
        _get_reminder_prefs_sync,
        discord_user_id,
        name="ark_get_reminder_prefs",
    )


async def upsert_reminder_prefs(
    discord_user_id: int,
    *,
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


async def set_match_result(
    match_id: int,
    result: str,
    notes: str | None,
    actor_discord_id: int,
) -> bool:
    raise NotImplementedError


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
