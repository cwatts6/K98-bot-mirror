# stats_alerts/prekvk_stats.py
"""
Helpers to load Pre-KVK top lists (overall + per-phase deltas).

Provides:
- load_prekvk_top3(kvk_no: int, limit: int = 3) -> dict[str, list[dict]]
  returns dict with keys 'overall','p1','p2','p3', each a list of dicts with keys Name, Points.
"""

import logging
from typing import Any

from file_utils import cursor_row_to_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def _fetch_all_as_dicts(cur) -> list[dict[str, Any]]:
    rows = cur.fetchall()
    if not rows:
        return []
    return [cursor_row_to_dict(cur, r) for r in rows]


def load_prekvk_top3(kvk_no: int, limit: int = 3) -> dict:
    out = {"overall": [], "p1": [], "p2": [], "p3": []}
    try:
        if not kvk_no:
            return out
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()

            lim = int(limit) if limit is not None else 3
            if lim <= 0:
                lim = 1

            # Overall (latest scan per KVK, top N)
            cur.execute(
                f"""
                WITH latest AS (
                  SELECT s.KVK_NO, s.ScanID
                  FROM dbo.PreKvk_Scan s
                  WHERE s.KVK_NO = ?
                    AND s.ScanID = (
                      SELECT MAX(s2.ScanID) FROM dbo.PreKvk_Scan s2 WHERE s2.KVK_NO = s.KVK_NO
                    )
                )
                SELECT TOP ({lim}) sc.GovernorID, MAX(sc.GovernorName) AS Name, MAX(sc.Points) AS Points
                FROM dbo.PreKvk_Scores sc
                JOIN latest l ON l.KVK_NO = sc.KVK_NO AND l.ScanID = sc.ScanID
                GROUP BY sc.GovernorID
                ORDER BY MAX(sc.Points) DESC, MAX(sc.GovernorName);
                """,
                (kvk_no,),
            )
            rows = _fetch_all_as_dicts(cur)
            # Enforce limit again in Python in case mocks return more than expected.
            rows = rows[:lim]
            out["overall"] = [
                {
                    "Name": r.get("Name") or r.get("GovernorName") or "",
                    "Points": int(r.get("Points") or 0),
                }
                for r in rows
            ]

            # Phase helper
            def _phase_top(phase: int, lim_phase: int) -> list[dict[str, Any]]:
                lim_p = int(lim_phase) if lim_phase is not None else 1
                if lim_p <= 0:
                    lim_p = 1
                # compute delta points for the phase (Baseline vs InWindow) and return top lim_p
                cur.execute(
                    f"""
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
                    SELECT TOP ({lim_p}) COALESCE(p.GovernorID, b.GovernorID) AS GovernorID,
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
                rows_p = _fetch_all_as_dicts(cur)
                rows_p = rows_p[:lim_p]
                return [
                    {"Name": r.get("Name") or "", "Points": int(r.get("Points") or 0)}
                    for r in rows_p
                ]

            out["p1"] = _phase_top(1, lim)
            out["p2"] = _phase_top(2, lim)
            out["p3"] = _phase_top(3, lim)

    except Exception:
        logger.exception("[PREKVK] Failed to load Pre-KVK Top lists")
    return out
