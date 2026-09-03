"""Data-access helpers for KVK admin commands."""

from __future__ import annotations

import logging
from typing import Any

from file_utils import cursor_row_to_dict, fetch_one_dict, get_conn_with_retries
from kvk.dal.kvk_history_dal import resolve_current_kvk_no_from_cursor

logger = logging.getLogger(__name__)


RECENT_SCANS_SQL = """
SELECT TOP (?)
       ScanID, ScanTimestampUTC, Row_Count, SourceFileName, ImportedAtUTC
FROM KVK.KVK_Scan
WHERE KVK_NO = ?
ORDER BY ScanID DESC;
"""

MAX_SCAN_SQL = "SELECT MAX(ScanID) AS MaxScanID FROM KVK.KVK_Scan WHERE KVK_NO=?;"

WINDOW_PREVIEW_SQL = """
WITH MaxScan AS (
  SELECT ? AS KVK_NO, ? AS MaxScanID
)
SELECT
  w.WindowName,
  w.StartScanID,
  w.EndScanID,
  s1.ScanTimestampUTC AS StartTS,
  s2.ScanTimestampUTC AS EndTS,
  CASE
    WHEN w.StartScanID IS NULL THEN NULL
    ELSE (
      SELECT COUNT(*) FROM KVK.KVK_Scan s
      WHERE s.KVK_NO=w.KVK_NO
        AND s.ScanID BETWEEN w.StartScanID AND COALESCE(w.EndScanID, m.MaxScanID)
    )
  END AS NumScans,
  (SELECT COUNT(*) FROM KVK.KVK_Player_Windowed p
     WHERE p.KVK_NO=w.KVK_NO AND p.WindowName=w.WindowName) AS [RowCount]
FROM KVK.KVK_Windows w
JOIN MaxScan m ON m.KVK_NO=w.KVK_NO
LEFT JOIN KVK.KVK_Scan s1 ON s1.KVK_NO=w.KVK_NO AND s1.ScanID=w.StartScanID
LEFT JOIN KVK.KVK_Scan s2 ON s2.KVK_NO=w.KVK_NO AND s2.ScanID=COALESCE(w.EndScanID, m.MaxScanID)
WHERE w.KVK_NO=?
ORDER BY CASE WHEN w.StartScanID IS NULL THEN 1 ELSE 0 END, w.WindowName;
"""

RECOMPUTE_SQL = "EXEC KVK.sp_KVK_Recompute_Windows @KVK_NO=?;"


def resolve_kvk_no(kvk_no: int | None = None) -> int:
    """Resolve an explicit/current KVK number using the shared metadata contract."""
    with get_conn_with_retries() as conn:
        with conn.cursor() as cursor:
            return resolve_current_kvk_no_from_cursor(cursor, kvk_no)


def recompute_windows(kvk_no: int | None = None) -> int:
    """Run the KVK window recompute procedure and return the resolved KVK number."""
    with get_conn_with_retries() as conn:
        with conn.cursor() as cursor:
            resolved_kvk = resolve_current_kvk_no_from_cursor(cursor, kvk_no)
            logger.info("[KVK ADMIN] recomputing windows kvk_no=%s", resolved_kvk)
            cursor.execute(RECOMPUTE_SQL, (resolved_kvk,))
            conn.commit()
            return resolved_kvk


def fetch_recent_scans(kvk_no: int | None, limit: int) -> tuple[int, list[dict[str, Any]]]:
    """Fetch recent KVK scan metadata for admin display."""
    with get_conn_with_retries() as conn:
        with conn.cursor() as cursor:
            resolved_kvk = resolve_current_kvk_no_from_cursor(cursor, kvk_no)
            cursor.execute(RECENT_SCANS_SQL, (limit, resolved_kvk))
            rows = [cursor_row_to_dict(cursor, row) for row in cursor.fetchall()]
            return resolved_kvk, rows


def fetch_window_preview(kvk_no: int | None) -> tuple[int, list[dict[str, Any]]]:
    """Fetch KVK window edge, scan-count, and row-count metadata."""
    with get_conn_with_retries() as conn:
        with conn.cursor() as cursor:
            resolved_kvk = resolve_current_kvk_no_from_cursor(cursor, kvk_no)

            cursor.execute(MAX_SCAN_SQL, (resolved_kvk,))
            max_scan_row = fetch_one_dict(cursor)
            max_scan = int(next(iter(max_scan_row.values())) or 0) if max_scan_row else 0

            cursor.execute(WINDOW_PREVIEW_SQL, (resolved_kvk, max_scan, resolved_kvk))
            rows = [cursor_row_to_dict(cursor, row) for row in cursor.fetchall()]
            return resolved_kvk, rows
