from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

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


def fetch_resource_export_rows(
    governor_ids: list[int], *, lookback_days: int = 366
) -> list[dict[str, Any]]:
    if not governor_ids:
        return []
    since_utc = datetime.now(UTC) - timedelta(days=int(lookback_days))
    placeholders = ",".join("?" for _ in governor_ids)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT b.ImportBatchID,
                   b.GovernorID,
                   b.DiscordUserID,
                   b.FlowType,
                   b.ApprovedAtUtc,
                   b.CreatedAtUtc,
                   r.ScanUtc,
                   r.ResourceType,
                   r.FromItemsValue,
                   r.TotalResourcesValue
            FROM dbo.GovernorResourceInventory AS r
            INNER JOIN dbo.InventoryImportBatch AS b
                ON b.ImportBatchID = r.ImportBatchID
            WHERE r.GovernorID IN ({placeholders})
              AND b.Status = N'approved'
              AND b.ImportType = N'resources'
              AND r.ScanUtc >= ?
            ORDER BY r.GovernorID ASC, r.ScanUtc DESC, r.ResourceType ASC
            """,
            (*[int(item) for item in governor_ids], since_utc),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()


def fetch_speedup_export_rows(
    governor_ids: list[int], *, lookback_days: int = 366
) -> list[dict[str, Any]]:
    if not governor_ids:
        return []
    since_utc = datetime.now(UTC) - timedelta(days=int(lookback_days))
    placeholders = ",".join("?" for _ in governor_ids)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT b.ImportBatchID,
                   b.GovernorID,
                   b.DiscordUserID,
                   b.FlowType,
                   b.ApprovedAtUtc,
                   b.CreatedAtUtc,
                   s.ScanUtc,
                   s.SpeedupType,
                   s.TotalMinutes,
                   s.TotalHours,
                   s.TotalDaysDecimal
            FROM dbo.GovernorSpeedupInventory AS s
            INNER JOIN dbo.InventoryImportBatch AS b
                ON b.ImportBatchID = s.ImportBatchID
            WHERE s.GovernorID IN ({placeholders})
              AND b.Status = N'approved'
              AND b.ImportType = N'speedups'
              AND s.ScanUtc >= ?
            ORDER BY s.GovernorID ASC, s.ScanUtc DESC, s.SpeedupType ASC
            """,
            (*[int(item) for item in governor_ids], since_utc),
        )
        return _rows_to_dicts(cur)
    finally:
        conn.close()
