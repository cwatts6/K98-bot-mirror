"""SQL access for Discord-user-level profile preferences."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


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


def upsert_profile_preference(
    *,
    discord_user_id: int,
    timezone_name: str | None,
    location_country_code: str | None,
    preferred_language_tag: str | None,
    updated_by_discord_user_id: int | None = None,
) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            MERGE dbo.DiscordUserProfilePreference AS target
            USING (
                SELECT ? AS DiscordUserID,
                       ? AS TimezoneName,
                       ? AS LocationCountryCode,
                       ? AS PreferredLanguageTag,
                       ? AS UpdatedByDiscordUserID
            ) AS source
               ON target.DiscordUserID = source.DiscordUserID
            WHEN MATCHED THEN
                UPDATE SET TimezoneName = source.TimezoneName,
                           LocationCountryCode = source.LocationCountryCode,
                           PreferredLanguageTag = source.PreferredLanguageTag,
                           UpdatedAtUtc = SYSUTCDATETIME(),
                           UpdatedByDiscordUserID = source.UpdatedByDiscordUserID
            WHEN NOT MATCHED THEN
                INSERT (
                    DiscordUserID,
                    TimezoneName,
                    LocationCountryCode,
                    PreferredLanguageTag,
                    CreatedAtUtc,
                    UpdatedAtUtc,
                    UpdatedByDiscordUserID
                )
                VALUES (
                    source.DiscordUserID,
                    source.TimezoneName,
                    source.LocationCountryCode,
                    source.PreferredLanguageTag,
                    SYSUTCDATETIME(),
                    SYSUTCDATETIME(),
                    source.UpdatedByDiscordUserID
                );
            """,
            (
                int(discord_user_id),
                timezone_name,
                location_country_code,
                preferred_language_tag,
                updated_by_discord_user_id,
            ),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            logger.debug("profile_preference_rollback_failed", exc_info=True)
        logger.exception("profile_preference_upsert_failed user_id=%s", discord_user_id)
        raise
    finally:
        conn.close()
