"""DAL for MGE commander administration."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query

logger = logging.getLogger(__name__)


def _naive_utc(dt: datetime) -> datetime:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


def fetch_active_variants() -> list[dict[str, Any]]:
    try:
        return run_query("""
            SELECT VariantId, VariantName
            FROM dbo.MGE_Variants
            WHERE IsActive = 1
            ORDER BY VariantName;
            """)
    except Exception:
        logger.exception("mge_commander_dal_fetch_active_variants_failed")
        return []


def fetch_commanders_for_variant(
    variant_id: int, *, include_inactive: bool = True
) -> list[dict[str, Any]]:
    try:
        active_filter = "" if include_inactive else "AND c.IsActive = 1 AND vc.IsActive = 1"
        return run_query(
            f"""
            SELECT
                c.CommanderId,
                c.CommanderName,
                c.IsActive AS CommanderIsActive,
                c.ReleaseStartUtc,
                c.ReleaseEndUtc,
                c.ImageUrl,
                vc.VariantCommanderId,
                vc.VariantId,
                vc.IsActive AS VariantCommanderIsActive,
                v.VariantName
            FROM dbo.MGE_VariantCommanders vc
            JOIN dbo.MGE_Commanders c ON c.CommanderId = vc.CommanderId
            JOIN dbo.MGE_Variants v ON v.VariantId = vc.VariantId
            WHERE vc.VariantId = ?
              {active_filter}
            ORDER BY c.CommanderName;
            """,
            (int(variant_id),),
        )
    except Exception:
        logger.exception(
            "mge_commander_dal_fetch_commanders_for_variant_failed variant_id=%s",
            variant_id,
        )
        return []


def fetch_commander_by_id(commander_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(
            """
            SELECT CommanderId, CommanderName, IsActive, ReleaseStartUtc, ReleaseEndUtc, ImageUrl
            FROM dbo.MGE_Commanders
            WHERE CommanderId = ?;
            """,
            (int(commander_id),),
        )
        return rows[0] if rows else None
    except Exception:
        logger.exception(
            "mge_commander_dal_fetch_commander_by_id_failed commander_id=%s", commander_id
        )
        return None


def fetch_commander_by_name(commander_name: str) -> dict[str, Any] | None:
    try:
        rows = run_query(
            """
            SELECT CommanderId, CommanderName, IsActive, ReleaseStartUtc, ReleaseEndUtc, ImageUrl
            FROM dbo.MGE_Commanders
            WHERE CommanderName = ?;
            """,
            (str(commander_name).strip(),),
        )
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_commander_dal_fetch_commander_by_name_failed")
        return None


def commander_has_history(commander_id: int) -> bool:
    try:
        rows = run_query(
            """
            SELECT TOP (1) 1 AS HasHistory
            WHERE EXISTS (SELECT 1 FROM dbo.MGE_Signups WHERE RequestedCommanderId = ?)
               OR EXISTS (SELECT 1 FROM dbo.MGE_Awards WHERE RequestedCommanderId = ?)
               OR EXISTS (SELECT 1 FROM dbo.MGE_EventCommanderOverrides WHERE CommanderId = ?);
            """,
            (int(commander_id), int(commander_id), int(commander_id)),
        )
        return bool(rows)
    except Exception:
        logger.exception(
            "mge_commander_dal_commander_has_history_failed commander_id=%s",
            commander_id,
        )
        return True


def upsert_commander_assignment(
    *,
    commander_id: int | None,
    commander_name: str,
    variant_id: int,
    is_active: bool,
    now_utc: datetime,
) -> dict[str, Any] | None:
    """Create/update a commander and upsert the requested variant mapping."""

    def _op(cur: Any) -> dict[str, Any] | None:
        effective_commander_id = int(commander_id or 0)
        if effective_commander_id <= 0:
            cur.execute(
                """
                SELECT TOP (1) CommanderId
                FROM dbo.MGE_Commanders WITH (UPDLOCK, HOLDLOCK)
                WHERE CommanderName = ?;
                """,
                (commander_name,),
            )
            row = cur.fetchone()
            if row:
                effective_commander_id = int(row[0])
            else:
                cur.execute(
                    """
                    INSERT INTO dbo.MGE_Commanders
                        (CommanderName, IsActive, ReleaseStartUtc, ReleaseEndUtc, ImageUrl, CreatedUtc, UpdatedUtc)
                    OUTPUT INSERTED.CommanderId
                    VALUES (?, ?, NULL, NULL, NULL, ?, ?);
                    """,
                    (
                        commander_name,
                        1 if is_active else 0,
                        _naive_utc(now_utc),
                        _naive_utc(now_utc),
                    ),
                )
                inserted = cur.fetchone()
                if not inserted:
                    return None
                effective_commander_id = int(inserted[0])

        cur.execute(
            """
            UPDATE dbo.MGE_Commanders
            SET CommanderName = ?,
                IsActive = ?,
                UpdatedUtc = ?
            WHERE CommanderId = ?;
            """,
            (
                commander_name,
                1 if is_active else 0,
                _naive_utc(now_utc),
                effective_commander_id,
            ),
        )

        cur.execute(
            """
            SELECT TOP (1) VariantCommanderId
            FROM dbo.MGE_VariantCommanders WITH (UPDLOCK, HOLDLOCK)
            WHERE CommanderId = ?
              AND VariantId = ?;
            """,
            (effective_commander_id, int(variant_id)),
        )
        mapping = cur.fetchone()
        if mapping:
            cur.execute(
                """
                UPDATE dbo.MGE_VariantCommanders
                SET IsActive = ?
                WHERE VariantCommanderId = ?;
                """,
                (1 if is_active else 0, int(mapping[0])),
            )
        else:
            cur.execute(
                """
                INSERT INTO dbo.MGE_VariantCommanders
                    (VariantId, CommanderId, IsActive, CreatedUtc)
                VALUES (?, ?, ?, ?);
                """,
                (
                    int(variant_id),
                    effective_commander_id,
                    1 if is_active else 0,
                    _naive_utc(now_utc),
                ),
            )

        return {
            "CommanderId": effective_commander_id,
            "CommanderName": commander_name,
            "VariantId": int(variant_id),
            "IsActive": bool(is_active),
        }

    try:
        return exec_with_cursor(_op)
    except Exception:
        logger.exception(
            "mge_commander_dal_upsert_assignment_failed commander_id=%s variant_id=%s",
            commander_id,
            variant_id,
        )
        return None
