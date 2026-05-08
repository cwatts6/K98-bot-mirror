# kvk/dal/kvk_stats_dal.py
"""
Data-access layer for KVK stats queries.
No Discord types; all SQL lives here.
Pattern follows telemetry/dal/command_usage_dal.py and mge/dal/mge_review_dal.py.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


def fetch_prekvk_phase_list(kvk_no: int, phase: int) -> list[dict[str, Any]]:
    """
    Return list of dicts with keys GovernorID, Name, Points for the given KVK and phase.
    Uses direct PreKvK stage columns from the latest scan.
    """
    stage_columns = {1: "Stage1Points", 2: "Stage2Points", 3: "Stage3Points"}
    stage_column = stage_columns.get(int(phase or 0))
    if stage_column is None:
        logger.warning("[PREKVK] Unsupported phase requested for KVK %s phase %s", kvk_no, phase)
        return []

    try:
        from file_utils import cursor_row_to_dict

        conn = _get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                WITH Latest AS (
                  SELECT TOP (1) ScanID
                  FROM dbo.PreKvk_Scan
                  WHERE KVK_NO = ?
                  ORDER BY ScanID DESC
                )
                SELECT
                    sc.GovernorID,
                    COALESCE(MAX(sc.GovernorName), CONVERT(varchar(20), sc.GovernorID)) AS Name,
                    MAX(sc.{stage_column}) AS Points
                FROM dbo.PreKvk_Scores sc
                JOIN Latest l ON l.ScanID = sc.ScanID
                WHERE sc.KVK_NO = ?
                  AND sc.{stage_column} IS NOT NULL
                GROUP BY sc.GovernorID
                ORDER BY MAX(sc.{stage_column}) DESC, sc.GovernorID ASC;
                """,
                (kvk_no, kvk_no),
            )
            rows = cur.fetchall()
            if not rows:
                return []
            return [cursor_row_to_dict(cur, r) for r in rows]
    except Exception:
        logger.exception("[PREKVK] Failed to fetch phase list for KVK %s phase %s", kvk_no, phase)
        return []


def fetch_latest_honor_list() -> list[dict[str, Any]]:
    """
    Return the full latest honor list (GovernorName, GovernorID, HonorPoints) ordered desc.
    """
    try:
        from file_utils import cursor_row_to_dict

        conn = _get_conn()
        with conn:
            cur = conn.cursor()
            sql = """
            ;WITH latest_kvk AS (
                SELECT MAX(KVK_NO) AS KVK_NO
                FROM dbo.KVK_Honor_Scan
            ),
            last_scan AS (
                SELECT s.KVK_NO, MAX(s.ScanID) AS ScanID
                FROM dbo.KVK_Honor_Scan s
                JOIN latest_kvk k ON k.KVK_NO = s.KVK_NO
                GROUP BY s.KVK_NO
            )
            SELECT a.GovernorName, a.GovernorID, a.HonorPoints
            FROM dbo.KVK_Honor_AllPlayers_Raw a
            JOIN last_scan l ON l.KVK_NO = a.KVK_NO AND l.ScanID = a.ScanID
            ORDER BY a.HonorPoints DESC, a.GovernorID ASC;
            """
            cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                return []
            return [cursor_row_to_dict(cur, r) for r in rows]
    except Exception:
        logger.exception("[HONOR] Failed to fetch latest honor list")
        return []
