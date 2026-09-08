from __future__ import annotations

from typing import Any

from stats_alerts.db import run_query


def fetch_event_header(event_id: int) -> dict[str, Any] | None:
    rows = (
        run_query(
            """
        SELECT TOP 1
            EventId,
            EventName,
            EventMode,
            Status,
            VariantId,
            StartUtc,
            EndUtc,
            PublishVersion,
            LastPublishedUtc
        FROM dbo.MGE_Events
        WHERE EventId = ?
        """,
            [event_id],
        )
        or []
    )
    return rows[0] if rows else None


def fetch_signup_totals(event_id: int) -> list[dict[str, Any]]:
    return (
        run_query(
            """
        SELECT
            COUNT(1) AS TotalSignups
        FROM dbo.MGE_Signups
        WHERE EventId = ?
          AND IsActive = 1
        """,
            [event_id],
        )
        or []
    )


def fetch_signups_by_commander(event_id: int) -> list[dict[str, Any]]:
    return (
        run_query(
            """
        SELECT
            RequestedCommanderName,
            COUNT(1) AS SignupCount
        FROM dbo.MGE_Signups
        WHERE EventId = ?
          AND IsActive = 1
        GROUP BY RequestedCommanderName
        ORDER BY RequestedCommanderName
        """,
            [event_id],
        )
        or []
    )


def fetch_signups_by_priority(event_id: int) -> list[dict[str, Any]]:
    return (
        run_query(
            """
        SELECT
            RequestPriority,
            COUNT(1) AS SignupCount
        FROM dbo.MGE_Signups
        WHERE EventId = ?
          AND IsActive = 1
        GROUP BY RequestPriority
        """,
            [event_id],
        )
        or []
    )


def fetch_award_counts(event_id: int) -> list[dict[str, Any]]:
    return (
        run_query(
            """
        SELECT
            SUM(CASE WHEN AwardStatus = 'awarded' THEN 1 ELSE 0 END) AS AwardedCount,
            SUM(CASE WHEN AwardStatus = 'waitlist' THEN 1 ELSE 0 END) AS WaitlistCount
        FROM dbo.MGE_Awards
        WHERE EventId = ?
        """,
            [event_id],
        )
        or []
    )


def fetch_publish_change_count(event_id: int) -> list[dict[str, Any]]:
    return (
        run_query(
            """
        SELECT COUNT(1) AS ChangeCount
        FROM dbo.MGE_AwardAudit
        WHERE EventId = ?
          AND ActionType IN (
            'publish',
            'republish',
            'set_target',
            'set_rank',
            'move_rank',
            'move_waitlist',
            'remove',
            'undo_remove'
          )
        """,
            [event_id],
        )
        or []
    )


def fetch_fairness_metrics(event_id: int) -> list[dict[str, Any]]:
    return (
        run_query(
            """
        SELECT
            SUM(CASE WHEN WarningMissingKVKData = 1 THEN 1 ELSE 0 END) AS WarningMissingKVKDataCount,
            SUM(CASE WHEN WarningHeadsOutOfRange = 1 THEN 1 ELSE 0 END) AS WarningHeadsOutOfRangeCount,
            SUM(CASE WHEN WarningNoAttachments = 1 THEN 1 ELSE 0 END) AS WarningNoAttachmentsCount,
            SUM(CASE WHEN WarningNoGearOrArmamentText = 1 THEN 1 ELSE 0 END) AS WarningNoGearOrArmamentTextCount
        FROM dbo.v_MGE_SignupReview
        WHERE EventId = ?
        """,
            [event_id],
        )
        or []
    )
