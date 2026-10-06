from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query


def _naive_utc(dt: datetime) -> datetime:
    # Align with existing MGE DAL pattern: treat naive dt as UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(tzinfo=None)


def fetch_due_event_ids_for_completion(as_of_utc: datetime) -> list[int]:
    as_of = _naive_utc(as_of_utc)
    query = """
        SELECT E.EventId
        FROM dbo.MGE_Events E
        WHERE E.Status IN ('published', 'reopened', 'signup_closed', 'signup_open')
          AND DATEADD(DAY, 6, E.StartUtc) <= ?
    """
    rows = run_query(query, [as_of]) or []
    return [int(r["EventId"]) for r in rows if r.get("EventId") is not None]


def fetch_event_completion_context(event_id: int) -> dict[str, Any] | None:
    query = """
        SELECT TOP 1
            EventId,
            EventMode,
            Status,
            StartUtc,
            EndUtc,
            PublishVersion,
            CompletedAtUtc,
            CompletedByDiscordId,
            ReopenedAtUtc,
            ReopenedByDiscordId
        FROM dbo.MGE_Events
        WHERE EventId = ?
    """
    rows = run_query(query, [event_id]) or []
    return rows[0] if rows else None


def mark_event_completed(
    event_id: int,
    actor_discord_id: int | None,
    completed_at_utc: datetime,
) -> bool:
    completed_at = _naive_utc(completed_at_utc)

    def _op(cur: Any) -> bool:
        cur.execute(
            """
            UPDATE dbo.MGE_Events
            SET
                Status = 'completed',
                CompletedAtUtc = ?,
                CompletedByDiscordId = ?,
                UpdatedUtc = ?
            WHERE EventId = ?
              AND Status <> 'completed'
            """,
            completed_at,
            actor_discord_id,
            completed_at,
            event_id,
        )
        return cur.rowcount > 0

    return bool(exec_with_cursor(_op))


def reopen_event(
    event_id: int,
    actor_discord_id: int,
    reopened_at_utc: datetime,
) -> bool:
    reopened_at = _naive_utc(reopened_at_utc)

    def _op(cur: Any) -> bool:
        cur.execute(
            """
            UPDATE dbo.MGE_Events
            SET
                Status = 'reopened',
                ReopenedAtUtc = ?,
                ReopenedByDiscordId = ?,
                UpdatedUtc = ?
            WHERE EventId = ?
              AND Status = 'completed'
            """,
            reopened_at,
            actor_discord_id,
            reopened_at,
            event_id,
        )
        return cur.rowcount > 0

    return bool(exec_with_cursor(_op))
