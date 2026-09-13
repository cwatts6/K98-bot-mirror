"""SQL access for Discord-user-level profile preferences."""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

ProfileField = Literal["timezone", "country", "language"]

_PROFILE_COLUMN_BY_FIELD: dict[ProfileField, str] = {
    "timezone": "TimezoneName",
    "country": "LocationCountryCode",
    "language": "PreferredLanguageTag",
}


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def fetch_profile_preference(discord_user_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1
                   DiscordUserID,
                   TimezoneName,
                   LocationCountryCode,
                   PreferredLanguageTag,
                   CreatedAtUtc,
                   UpdatedAtUtc,
                   UpdatedByDiscordUserID
            FROM dbo.DiscordUserProfilePreference
            WHERE DiscordUserID = ?
            """,
            (int(discord_user_id),),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [item[0] for item in cur.description]
        return dict(zip(cols, row, strict=True))
    finally:
        conn.close()


def upsert_profile_preference_field(
    *,
    discord_user_id: int,
    field: ProfileField,
    value: str | None,
    updated_by_discord_user_id: int | None = None,
) -> dict[str, Any]:
    try:
        column_name = _PROFILE_COLUMN_BY_FIELD[field]
    except KeyError as exc:
        raise ValueError(f"Unsupported profile preference field: {field}") from exc

    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SET NOCOUNT ON;
            SET XACT_ABORT ON;
            SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

            UPDATE dbo.DiscordUserProfilePreference WITH (UPDLOCK, HOLDLOCK)
            SET {column_name} = ?,
                UpdatedAtUtc = SYSUTCDATETIME(),
                UpdatedByDiscordUserID = ?
            WHERE DiscordUserID = ?;

            IF @@ROWCOUNT = 0
            BEGIN
                INSERT dbo.DiscordUserProfilePreference (
                    DiscordUserID,
                    {column_name},
                    CreatedAtUtc,
                    UpdatedAtUtc,
                    UpdatedByDiscordUserID
                )
                VALUES (?, ?, SYSUTCDATETIME(), SYSUTCDATETIME(), ?);
            END;

            SELECT TOP 1
                   DiscordUserID,
                   TimezoneName,
                   LocationCountryCode,
                   PreferredLanguageTag,
                   CreatedAtUtc,
                   UpdatedAtUtc,
                   UpdatedByDiscordUserID
            FROM dbo.DiscordUserProfilePreference
            WHERE DiscordUserID = ?;
            """,
            (
                value,
                updated_by_discord_user_id,
                int(discord_user_id),
                int(discord_user_id),
                value,
                updated_by_discord_user_id,
                int(discord_user_id),
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("Profile preference write completed without a readable row")
        cols = [item[0] for item in cur.description]
        mapped = dict(zip(cols, row, strict=True))
        conn.commit()
        return mapped
    except Exception:
        try:
            conn.rollback()
        except Exception:
            logger.debug("profile_preference_rollback_failed", exc_info=True)
        logger.exception(
            "profile_preference_field_upsert_failed user_id=%s field=%s",
            discord_user_id,
            field,
        )
        raise
    finally:
        conn.close()
