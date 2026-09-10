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


def fetch_source_report_metadata(connect, envelope):
    """Enrich S3B's pinned read using immutable IDs only; never reselect inputs.

    The selection/desired-config snapshot is owned by S3B. These subsequent reads
    cannot mix generations because configuration and accepted revisions are immutable.
    """
    from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction

    publication = envelope.get("publication")
    if not publication:
        return {}
    with transaction(connect) as cursor:
        configs = {}
        for key, config_id in (
            ("selected", publication["ConfigVersionID"]),
            ("requested", envelope["desired_config_id"]),
        ):
            cursor.execute(
                "SELECT w.*,p.PeriodKind FROM KVK.SourceWindowConfig w "
                "JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO "
                "AND p.PeriodKey=w.PeriodKey WHERE w.ConfigVersionID=? AND p.PeriodID=?",
                config_id,
                envelope["period_id"],
            )
            configs[key] = one(cursor)
            if not configs[key]:
                raise SourceConflict("Pinned report configuration is unavailable.")
        endpoints = {}
        for key in ("Start", "End"):
            revision = publication[key + "RevisionID"]
            if revision is None:
                endpoints[key.lower()] = None
                continue
            cursor.execute(
                "SELECT o.ObservationID,o.ScanStartUTC,o.TimePrecision FROM "
                "KVK.SourceObservationRevision r JOIN KVK.SourceObservation o "
                "ON o.ObservationID=r.ObservationID WHERE r.RevisionID=?",
                revision,
            )
            endpoints[key.lower()] = one(cursor)
            if not endpoints[key.lower()]:
                raise SourceConflict("Pinned report endpoint is unavailable.")
        cursor.execute(
            "SELECT Kingdom,CampID,CampName FROM KVK.SourceCampConfig WHERE ConfigVersionID=?",
            publication["ConfigVersionID"],
        )
        camps = rows(cursor)
        aggregate = None
        if publication["AggregateRevisionID"] is not None:
            cursor.execute(
                "SELECT CoverageStartUTC,CoverageEndUTC,AsOfUTC,ReportState "
                "FROM KVK.SourceAggregateRevision WHERE RevisionID=?",
                publication["AggregateRevisionID"],
            )
            aggregate = one(cursor)
            if not aggregate:
                raise SourceConflict("Pinned aggregate metadata is unavailable.")
    return dict(configs=configs, endpoints=endpoints, camps=camps, aggregate=aggregate)


def fetch_source_recent_scans(connect, kvk_no, limit):
    """Private source registry diagnostics; aggregates never allocate these IDs."""
    from kvk.dal.new_source_import_dal import rows, transaction
    from kvk.schemas.new_source_schema import SOURCE_KEY

    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT TOP (?) s.LogicalScanID AS ScanID,o.ScanStartUTC AS ScanTimestampUTC,"
            "o.TimePrecision,o.ObservationID FROM KVK.SourceLogicalScan s "
            "JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID "
            "WHERE s.SourceKey=? AND s.KVK_NO=? ORDER BY s.LogicalScanID DESC",
            limit,
            SOURCE_KEY,
            kvk_no,
        )
        return rows(cursor)


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
