from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from inventory.models import InventoryReportVisibility

logger = logging.getLogger(__name__)


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [item[0] for item in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in rows]


def fetch_visibility_preference(discord_user_id: int) -> InventoryReportVisibility | None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1 Visibility
            FROM dbo.InventoryReportPreference
            WHERE DiscordUserID = ?
            """,
            (int(discord_user_id),),
        )
        row = cur.fetchone()
        if not row:
            return None
        try:
            return InventoryReportVisibility(str(row[0]))
        except ValueError:
            logger.warning(
                "inventory_report_unknown_visibility_pref user_id=%s visibility=%s",
                discord_user_id,
                row[0],
            )
            return None
    finally:
        conn.close()


def upsert_visibility_preference(
    discord_user_id: int, visibility: InventoryReportVisibility
) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            MERGE dbo.InventoryReportPreference AS target
            USING (SELECT ? AS DiscordUserID, ? AS Visibility) AS source
               ON target.DiscordUserID = source.DiscordUserID
            WHEN MATCHED THEN
                UPDATE SET Visibility = source.Visibility,
                           UpdatedAtUtc = SYSUTCDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (DiscordUserID, Visibility, CreatedAtUtc, UpdatedAtUtc)
                VALUES (source.DiscordUserID, source.Visibility, SYSUTCDATETIME(), SYSUTCDATETIME());
            """,
            (int(discord_user_id), str(visibility.value)),
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("inventory_report_pref_upsert_failed user_id=%s", discord_user_id)
        raise
    finally:
        conn.close()


def fetch_resource_rows(governor_id: int, *, lookback_days: int = 370) -> list[dict[str, Any]]:
    since_utc = datetime.now(UTC) - timedelta(days=int(lookback_days))
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.ImportBatchID,
                   r.GovernorID,
                   r.ScanUtc,
                   r.ResourceType,
                   r.FromItemsValue,
                   r.TotalResourcesValue
            FROM dbo.GovernorResourceInventory AS r
            INNER JOIN dbo.InventoryImportBatch AS b
                ON b.ImportBatchID = r.ImportBatchID
            WHERE r.GovernorID = ?
              AND b.Status = N'approved'
              AND b.ImportType = N'resources'
              AND r.ScanUtc >= ?
            ORDER BY r.ScanUtc ASC, r.ResourceType ASC
            """,
            (int(governor_id), since_utc),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()


def fetch_speedup_rows(governor_id: int, *, lookback_days: int = 370) -> list[dict[str, Any]]:
    since_utc = datetime.now(UTC) - timedelta(days=int(lookback_days))
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.ImportBatchID,
                   s.GovernorID,
                   s.ScanUtc,
                   s.SpeedupType,
                   s.TotalMinutes,
                   s.TotalHours,
                   s.TotalDaysDecimal
            FROM dbo.GovernorSpeedupInventory AS s
            INNER JOIN dbo.InventoryImportBatch AS b
                ON b.ImportBatchID = s.ImportBatchID
            WHERE s.GovernorID = ?
              AND b.Status = N'approved'
              AND b.ImportType = N'speedups'
              AND s.ScanUtc >= ?
            ORDER BY s.ScanUtc ASC, s.SpeedupType ASC
            """,
            (int(governor_id), since_utc),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()
