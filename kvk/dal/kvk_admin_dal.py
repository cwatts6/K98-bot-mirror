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


def read_admin_source(kvk_no, *, connect=None):
    from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, transaction
    from kvk.dal.season_source_dal import lock_season

    with transaction(connect or get_conn_with_retries) as cursor:
        resolved = resolve_current_kvk_no_from_cursor(cursor, kvk_no)
        lock_scope(cursor, resolved)
        choice = lock_season(cursor, resolved)
        if not choice:
            raise SourceConflict("Season source setup is unavailable.")
        return choice


def fetch_source_windows(kvk_no, *, connect=None):
    """Private metadata snapshot only; no results, calculation or selection writes."""
    from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, rows, transaction
    from kvk.dal.season_source_dal import lock_season

    with transaction(connect or get_conn_with_retries) as cursor:
        lock_scope(cursor, kvk_no)
        choice = lock_season(cursor, kvk_no)
        if not choice or choice["SourceKey"] != "snapshot_report_v1":
            raise SourceConflict("Source diagnostic scope changed.")
        cursor.execute(
            "SELECT p.PeriodID,p.PeriodKey,p.PeriodKind,w.WindowName,w.StartScanID,w.EndScanID,"
            "c.UpdateID,c.PublicationID,c.PublicSelectionVersion,"
            "pub.StartScanID AS SelectedStartScanID,pub.EndScanID AS SelectedEndScanID,"
            "pub.ConfigVersionID AS SelectedConfigVersionID,w.ConfigVersionID AS DesiredConfigVersionID,"
            "pub.PeriodState,pub.BuildState,pub.EligibleCount AS RowCount,"
            "pending.UpdateID AS PendingUpdateID,pending.UpdateState AS PendingUpdateState,"
            "o1.ScanStartUTC AS StartTS,o2.ScanStartUTC AS EndTS "
            "FROM KVK.SourcePeriod p "
            "LEFT JOIN KVK.SourceCompleteSelection c ON c.SourceKey=p.SourceKey AND c.KVK_NO=p.KVK_NO AND c.PeriodID=p.PeriodID "
            "LEFT JOIN KVK.SourcePublication pub ON pub.PublicationID=c.PublicationID "
            "LEFT JOIN KVK.SourceConfigVersion selected_config ON selected_config.ConfigVersionID=pub.ConfigVersionID "
            "OUTER APPLY (SELECT TOP(1) r.DesiredConfigVersionID FROM KVK.SourceConfigRequest r "
            "JOIN KVK.SourceConfigVersion v ON v.ConfigVersionID=r.DesiredConfigVersionID "
            "WHERE r.SourceKey=p.SourceKey AND r.KVK_NO=p.KVK_NO AND r.PeriodID=p.PeriodID "
            "AND r.RequestState<>'rejected' AND v.ConfigVersion>COALESCE(selected_config.ConfigVersion,0) "
            "ORDER BY v.ConfigVersion DESC) desired "
            "LEFT JOIN KVK.SourceWindowConfig w ON w.SourceKey=p.SourceKey AND w.KVK_NO=p.KVK_NO "
            "AND w.PeriodKey=p.PeriodKey AND w.ConfigVersionID=COALESCE(desired.DesiredConfigVersionID,pub.ConfigVersionID) "
            "OUTER APPLY (SELECT TOP(1) u.UpdateID,u.UpdateState FROM KVK.SourceUpdate u "
            "WHERE u.SourceKey=p.SourceKey AND u.KVK_NO=p.KVK_NO AND u.PeriodID=p.PeriodID "
            "AND u.UpdateState IN ('waiting_player','waiting_aggregate','ready') "
            "AND (w.ConfigVersionID IS NULL OR u.ConfigVersionID=w.ConfigVersionID) "
            "AND ((c.UpdateID IS NULL AND u.BaseUpdateID IS NULL) OR u.BaseUpdateID=c.UpdateID) "
            "ORDER BY u.ConfirmedUTC DESC,u.UpdateID) pending "
            "LEFT JOIN KVK.SourceObservationRevision r1 ON r1.RevisionID=pub.StartRevisionID "
            "LEFT JOIN KVK.SourceObservation o1 ON o1.ObservationID=r1.ObservationID "
            "LEFT JOIN KVK.SourceObservationRevision r2 ON r2.RevisionID=pub.EndRevisionID "
            "LEFT JOIN KVK.SourceObservation o2 ON o2.ObservationID=r2.ObservationID "
            "WHERE p.SourceKey=? AND p.KVK_NO=? ORDER BY p.PeriodKey",
            choice["SourceKey"],
            kvk_no,
        )
        return rows(cursor)


def fetch_source_report_metadata(connect, envelope):
    """Enrich S3B's pinned read using immutable IDs only; never reselect inputs.

    The selection/desired-config snapshot is owned by S3B. These subsequent reads
    cannot mix generations because configuration and accepted revisions are immutable.
    """
    from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction

    publication = envelope.get("publication")
    if not publication:
        with transaction(connect) as cursor:
            cursor.execute(
                "SELECT p.SourceKey,p.KVK_NO,p.PeriodKey,p.PeriodKind,"
                "w.ConfigVersionID,w.WindowName,w.StartScanID,w.EndScanID "
                "FROM KVK.SourcePeriod p LEFT JOIN KVK.SourceWindowConfig w "
                "ON w.SourceKey=p.SourceKey AND w.KVK_NO=p.KVK_NO "
                "AND w.PeriodKey=p.PeriodKey AND w.ConfigVersionID=? "
                "WHERE p.PeriodID=? AND p.SourceKey=? AND p.KVK_NO=?",
                envelope.get("desired_config_id"),
                envelope["period_id"],
                envelope["source_key"],
                envelope["kvk_no"],
            )
            requested = one(cursor)
            if not requested or (
                envelope.get("desired_config_id") and not requested["ConfigVersionID"]
            ):
                raise SourceConflict("Requested report configuration or period is unavailable.")
            return {"configs": {"requested": requested}}
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
    """Keep fixed legacy admission locked through EXEC and its single commit."""
    from kvk.dal.new_source_import_dal import lock_scope, transaction
    from kvk.dal.season_source_dal import require_source

    with transaction(get_conn_with_retries) as cursor:
        resolved_kvk = resolve_current_kvk_no_from_cursor(cursor, kvk_no)
        lock_scope(cursor, resolved_kvk)
        require_source(cursor, resolved_kvk, "legacy_full_data")
        logger.info("[KVK ADMIN] recomputing windows kvk_no=%s", resolved_kvk)
        cursor.execute(RECOMPUTE_SQL, (resolved_kvk,))
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
