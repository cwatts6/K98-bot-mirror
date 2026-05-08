# stats_alerts/prekvk_stats.py
"""
Helpers to load Pre-KVK top lists (overall + direct stage values).

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

            # Overall (latest scan per KVK, top N).
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
                SELECT TOP ({lim})
                       sc.GovernorID,
                       MAX(sc.GovernorName) AS Name,
                       MAX(COALESCE(sc.TotalPoints, sc.Points)) AS Points
                FROM dbo.PreKvk_Scores sc
                JOIN latest l ON l.KVK_NO = sc.KVK_NO AND l.ScanID = sc.ScanID
                GROUP BY sc.GovernorID
                ORDER BY MAX(COALESCE(sc.TotalPoints, sc.Points)) DESC, sc.GovernorID ASC;
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

            def _stage_top(stage_column: str, lim_phase: int) -> list[dict[str, Any]]:
                lim_p = int(lim_phase) if lim_phase is not None else 1
                if lim_p <= 0:
                    lim_p = 1
                if stage_column not in {"Stage1Points", "Stage2Points", "Stage3Points"}:
                    return []

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
                    SELECT TOP ({lim_p})
                           sc.GovernorID,
                           MAX(sc.GovernorName) AS Name,
                           MAX(sc.{stage_column}) AS Points
                    FROM dbo.PreKvk_Scores sc
                    JOIN latest l ON l.KVK_NO = sc.KVK_NO AND l.ScanID = sc.ScanID
                    WHERE sc.{stage_column} IS NOT NULL
                    GROUP BY sc.GovernorID
                    ORDER BY MAX(sc.{stage_column}) DESC, sc.GovernorID ASC;
                    """,
                    (kvk_no,),
                )
                rows_p = _fetch_all_as_dicts(cur)
                rows_p = rows_p[:lim_p]
                return [
                    {"Name": r.get("Name") or "", "Points": int(r.get("Points") or 0)}
                    for r in rows_p
                ]

            out["p1"] = _stage_top("Stage1Points", lim)
            out["p2"] = _stage_top("Stage2Points", lim)
            out["p3"] = _stage_top("Stage3Points", lim)

    except Exception:
        logger.exception("[PREKVK] Failed to load Pre-KVK Top lists")
    return out
