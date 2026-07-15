from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from inventory.models import InventoryReportVisibility

logger = logging.getLogger(__name__)

_BULK_GOVERNOR_CHUNK_SIZE = 500


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


def fetch_latest_resource_rows(governor_id: int) -> list[dict[str, Any]]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            WITH LatestBatch AS (
                SELECT TOP 1 ImportBatchID
                FROM dbo.InventoryImportBatch
                WHERE GovernorID = ?
                  AND ImportType = N'resources'
                  AND Status = N'approved'
                ORDER BY ApprovedAtUtc DESC, ImportBatchID DESC
            )
            SELECT r.ImportBatchID,
                   r.GovernorID,
                   r.ScanUtc,
                   r.ResourceType,
                   r.FromItemsValue,
                   r.TotalResourcesValue
            FROM dbo.GovernorResourceInventory AS r
            INNER JOIN LatestBatch AS b
                ON b.ImportBatchID = r.ImportBatchID
            ORDER BY r.ResourceType ASC
            """,
            (int(governor_id),),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()


def fetch_latest_resource_rows_bulk(
    governor_ids: list[int] | tuple[int, ...],
) -> list[dict[str, Any]]:
    """Fetch the latest approved complete-resource candidate batches in set-based chunks."""
    ids = tuple(dict.fromkeys(int(value) for value in governor_ids if int(value) > 0))
    if not ids:
        return []

    rows: list[dict[str, Any]] = []
    conn = _get_conn()
    try:
        for start in range(0, len(ids), _BULK_GOVERNOR_CHUNK_SIZE):
            chunk = ids[start : start + _BULK_GOVERNOR_CHUNK_SIZE]
            values_sql = ", ".join("(?)" for _ in chunk)
            cur = conn.cursor()
            cur.execute(
                f"""
                WITH Requested(GovernorID) AS (
                    SELECT CAST(v.GovernorID AS BIGINT)
                    FROM (VALUES {values_sql}) AS v(GovernorID)
                ),
                RankedBatch AS (
                    SELECT
                        b.GovernorID,
                        b.ImportBatchID,
                        ROW_NUMBER() OVER (
                            PARTITION BY b.GovernorID
                            ORDER BY b.ApprovedAtUtc DESC, b.ImportBatchID DESC
                        ) AS rn
                    FROM dbo.InventoryImportBatch AS b
                    INNER JOIN Requested AS requested
                        ON requested.GovernorID = b.GovernorID
                    WHERE b.ImportType = N'resources'
                      AND b.Status = N'approved'
                )
                SELECT r.ImportBatchID,
                       r.GovernorID,
                       r.ScanUtc,
                       r.ResourceType,
                       r.FromItemsValue,
                       r.TotalResourcesValue
                FROM dbo.GovernorResourceInventory AS r
                INNER JOIN RankedBatch AS latest
                    ON latest.ImportBatchID = r.ImportBatchID
                   AND latest.rn = 1
                ORDER BY r.GovernorID ASC, r.ResourceType ASC
                """,
                tuple(chunk),
            )
            rows.extend(_rows_to_dicts(cur))
        return rows
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


def fetch_latest_speedup_rows(governor_id: int) -> list[dict[str, Any]]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            WITH LatestBatch AS (
                SELECT TOP 1 ImportBatchID
                FROM dbo.InventoryImportBatch
                WHERE GovernorID = ?
                  AND ImportType = N'speedups'
                  AND Status = N'approved'
                ORDER BY ApprovedAtUtc DESC, ImportBatchID DESC
            )
            SELECT s.ImportBatchID,
                   s.GovernorID,
                   s.ScanUtc,
                   s.SpeedupType,
                   s.TotalMinutes,
                   s.TotalHours,
                   s.TotalDaysDecimal
            FROM dbo.GovernorSpeedupInventory AS s
            INNER JOIN LatestBatch AS b
                ON b.ImportBatchID = s.ImportBatchID
            ORDER BY s.SpeedupType ASC
            """,
            (int(governor_id),),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()
