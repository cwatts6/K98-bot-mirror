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
    Uses the same delta computation logic as stats_alerts/prekvk_stats._phase_top but returns all rows.
    """
    try:
        from file_utils import cursor_row_to_dict

        conn = _get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                WITH W AS (
                  SELECT StartUTC, EndUTC
                  FROM dbo.PreKvk_Phases
                  WHERE KVK_NO = ? AND Phase = ?
                ),
                B AS (
                  SELECT sc.GovernorID,
                         MAX(sc.Points) AS Baseline
                  FROM dbo.PreKvk_Scores sc
                  JOIN dbo.PreKvk_Scan s ON s.KVK_NO = sc.KVK_NO AND s.ScanID = sc.ScanID
                  CROSS JOIN W
                  WHERE sc.KVK_NO = ? AND s.ScanTimestampUTC < W.StartUTC
                  GROUP BY sc.GovernorID
                ),
                P AS (
                  SELECT sc.GovernorID,
                         MAX(sc.Points) AS InWindow
                  FROM dbo.PreKvk_Scores sc
                  JOIN dbo.PreKvk_Scan s ON s.KVK_NO = sc.KVK_NO AND s.ScanID = sc.ScanID
                  CROSS JOIN W
                  WHERE sc.KVK_NO = ? AND s.ScanTimestampUTC BETWEEN W.StartUTC AND W.EndUTC
                  GROUP BY sc.GovernorID
                ),
                Names AS (
                  SELECT sc.GovernorID, MAX(sc.GovernorName) AS GovernorName
                  FROM dbo.PreKvk_Scores sc
                  JOIN dbo.PreKvk_Scan s ON s.KVK_NO = sc.KVK_NO AND s.ScanID = sc.ScanID
                  WHERE sc.KVK_NO = ?
                  GROUP BY sc.GovernorID
                )
                SELECT COALESCE(p.GovernorID, b.GovernorID) AS GovernorID,
                       COALESCE(n.GovernorName, CONVERT(varchar(20), COALESCE(p.GovernorID, b.GovernorID))) AS Name,
                       MAX(COALESCE(p.InWindow, b.Baseline, 0)) - MAX(COALESCE(b.Baseline, 0)) AS Points
                FROM B b
                FULL JOIN P p ON p.GovernorID = b.GovernorID
                LEFT JOIN Names n ON n.GovernorID = COALESCE(p.GovernorID, b.GovernorID)
                GROUP BY COALESCE(p.GovernorID, b.GovernorID), COALESCE(n.GovernorName, CONVERT(varchar(20), COALESCE(p.GovernorID, b.GovernorID)))
                ORDER BY Points DESC, Name;
                """,
                (kvk_no, phase, kvk_no, kvk_no, kvk_no),
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
