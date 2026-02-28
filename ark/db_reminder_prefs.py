from __future__ import annotations

from stats_alerts.db import run_query


def get_reminder_prefs(discord_user_id: int) -> dict | None:
    rows = run_query(
        """
        SELECT TOP 1
            DiscordUserId,
            OptOutAll,
            OptOut24h,
            OptOut4h,
            OptOut1h,
            OptOutStart,
            OptOutCheckIn12h,
            UpdatedAtUtc,
            CreatedAtUtc
        FROM dbo.ArkReminderPrefs
        WHERE DiscordUserId = ?
        """,
        (discord_user_id,),
        fetch_all=True,
    )
    return rows[0] if rows else None


def upsert_reminder_prefs(
    discord_user_id: int,
    *,
    opt_out_all: int,
    opt_out_24h: int,
    opt_out_4h: int,
    opt_out_1h: int,
    opt_out_start: int,
    opt_out_checkin_12h: int,
) -> bool:
    run_query(
        """
        MERGE dbo.ArkReminderPrefs AS target
        USING (SELECT ? AS DiscordUserId) AS source
        ON target.DiscordUserId = source.DiscordUserId
        WHEN MATCHED THEN
            UPDATE SET
                OptOutAll = ?,
                OptOut24h = ?,
                OptOut4h = ?,
                OptOut1h = ?,
                OptOutStart = ?,
                OptOutCheckIn12h = ?,
                UpdatedAtUtc = SYSUTCDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (
                DiscordUserId, OptOutAll, OptOut24h, OptOut4h, OptOut1h, OptOutStart, OptOutCheckIn12h,
                CreatedAtUtc, UpdatedAtUtc
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME()
            );
        """,
        (
            discord_user_id,
            opt_out_all,
            opt_out_24h,
            opt_out_4h,
            opt_out_1h,
            opt_out_start,
            opt_out_checkin_12h,
            discord_user_id,
            opt_out_all,
            opt_out_24h,
            opt_out_4h,
            opt_out_1h,
            opt_out_start,
            opt_out_checkin_12h,
        ),
        fetch_all=False,
    )
    return True
