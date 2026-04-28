from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from server_activity.activity_models import ActivityEvent, ActivityUserSummary
from stats_alerts.db import execute, execute_async, run_query, run_query_async

logger = logging.getLogger(__name__)

ACTIVITY_TABLE = "dbo.DiscordServerActivityEvents"


SCHEMA_SQL = """
IF OBJECT_ID(N'dbo.DiscordServerActivityEvents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DiscordServerActivityEvents
    (
        ActivityEventId BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DiscordServerActivityEvents PRIMARY KEY,
        OccurredAtUtc DATETIME2(0) NOT NULL,
        GuildId BIGINT NOT NULL,
        ChannelId BIGINT NULL,
        UserId BIGINT NOT NULL,
        EventType NVARCHAR(32) NOT NULL,
        MetadataJson NVARCHAR(MAX) NULL,
        CreatedAtUtc DATETIME2(0) NOT NULL
            CONSTRAINT DF_DiscordServerActivityEvents_CreatedAtUtc
            DEFAULT SYSUTCDATETIME()
    );
END;

IF OBJECT_ID(N'dbo.DiscordServerActivityEvents', N'U') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = N'IX_DiscordServerActivityEvents_Window'
          AND object_id = OBJECT_ID(N'dbo.DiscordServerActivityEvents')
    )
    BEGIN
        DROP INDEX IX_DiscordServerActivityEvents_Window
            ON dbo.DiscordServerActivityEvents;
    END;

    CREATE INDEX IX_DiscordServerActivityEvents_Window
        ON dbo.DiscordServerActivityEvents (GuildId, OccurredAtUtc, UserId, EventType)
        INCLUDE (ChannelId);
END;
"""


def _sql_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(tzinfo=None, microsecond=0)


def ensure_activity_schema() -> None:
    """Create the activity table if it is missing."""
    from file_utils import get_conn_with_retries

    conn = get_conn_with_retries()
    cur = None
    try:
        try:
            with conn:
                cur = conn.cursor()
                cur.execute(SCHEMA_SQL)
                conn.commit()
            logger.info("activity_schema_ensured")
        except Exception:
            logger.exception("activity_schema_ensure_failed")
            raise
        finally:
            if cur is not None:
                cur.close()
    finally:
        conn.close()


def _build_insert_params(event: ActivityEvent) -> tuple:
    metadata_json = None
    if event.metadata:
        metadata_json = json.dumps(event.metadata, ensure_ascii=False, separators=(",", ":"))
    return (
        _sql_datetime(event.occurred_at_utc),
        int(event.guild_id),
        int(event.channel_id) if event.channel_id is not None else None,
        int(event.user_id),
        str(event.event_type.value),
        metadata_json,
    )


_INSERT_SQL = """
    INSERT INTO {table}
        (OccurredAtUtc, GuildId, ChannelId, UserId, EventType, MetadataJson)
    VALUES (?, ?, ?, ?, ?, ?);
"""


def insert_activity_event(event: ActivityEvent) -> int:
    sql = _INSERT_SQL.format(table=ACTIVITY_TABLE)
    return execute(sql, _build_insert_params(event))


async def insert_activity_event_async(event: ActivityEvent) -> int:
    sql = _INSERT_SQL.format(table=ACTIVITY_TABLE)
    return await execute_async(sql, _build_insert_params(event))


def fetch_activity_top(
    *,
    guild_id: int,
    since_utc: datetime,
    limit: int = 10,
) -> list[ActivityUserSummary]:
    safe_limit = max(1, min(int(limit), 50))
    sql = f"""
        SELECT TOP {safe_limit}
            UserId,
            COUNT(*) AS Score,
            SUM(CASE WHEN EventType = 'message' THEN 1 ELSE 0 END) AS Messages,
            SUM(CASE WHEN EventType = 'reaction_add' THEN 1 ELSE 0 END) AS Reactions,
            SUM(CASE WHEN EventType IN ('voice_join', 'voice_leave', 'voice_move') THEN 1 ELSE 0 END) AS VoiceEvents
        FROM {ACTIVITY_TABLE}
        WHERE GuildId = ?
          AND OccurredAtUtc >= ?
        GROUP BY UserId
        ORDER BY Score DESC, Messages DESC, Reactions DESC, VoiceEvents DESC, UserId ASC;
    """
    rows = run_query(sql, (int(guild_id), _sql_datetime(since_utc)))
    return [_summary_from_row(row) for row in rows]


async def fetch_activity_top_async(
    *,
    guild_id: int,
    since_utc: datetime,
    limit: int = 10,
) -> list[ActivityUserSummary]:
    safe_limit = max(1, min(int(limit), 50))
    sql = f"""
        SELECT TOP {safe_limit}
            UserId,
            COUNT(*) AS Score,
            SUM(CASE WHEN EventType = 'message' THEN 1 ELSE 0 END) AS Messages,
            SUM(CASE WHEN EventType = 'reaction_add' THEN 1 ELSE 0 END) AS Reactions,
            SUM(CASE WHEN EventType IN ('voice_join', 'voice_leave', 'voice_move') THEN 1 ELSE 0 END) AS VoiceEvents
        FROM {ACTIVITY_TABLE}
        WHERE GuildId = ?
          AND OccurredAtUtc >= ?
        GROUP BY UserId
        ORDER BY Score DESC, Messages DESC, Reactions DESC, VoiceEvents DESC, UserId ASC;
    """
    rows = await run_query_async(sql, (int(guild_id), _sql_datetime(since_utc)))
    return [_summary_from_row(row) for row in rows]


def _summary_from_row(row: dict[str, Any]) -> ActivityUserSummary:
    return ActivityUserSummary(
        user_id=int(row.get("UserId") or 0),
        score=int(row.get("Score") or 0),
        messages=int(row.get("Messages") or 0),
        reactions=int(row.get("Reactions") or 0),
        voice_events=int(row.get("VoiceEvents") or 0),
    )
