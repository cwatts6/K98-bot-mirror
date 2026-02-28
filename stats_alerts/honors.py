# stats_alerts/honors.py
"""
Honor helpers (migrated from legacy stats_alert_utils).

Provides:
- get_latest_honor_top(n) -> list[dict] (async-friendly)
- purge_latest_honor_scan() -> int (sync; can be run in thread)
"""

import logging
from typing import Any

from file_utils import fetch_one_dict
from stats_alerts.db import exec_with_cursor, run_query_async

logger = logging.getLogger(__name__)


async def get_latest_honor_top(n: int = 3) -> list[dict[str, Any]]:
    """
    Return latest overall honor Top-N for the most recent scan of latest KVK.
    Runs in a thread via run_query_async (which prefers run_blocking_in_thread internally).
    """
    # Validate n
    try:
        n_i = int(n)
        if n_i <= 0:
            return []
    except Exception:
        return []

    sql = f"""
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
    SELECT TOP ({n_i}) a.GovernorName, a.GovernorID, a.HonorPoints
    FROM dbo.KVK_Honor_AllPlayers_Raw a
    JOIN last_scan l ON l.KVK_NO = a.KVK_NO AND l.ScanID = a.ScanID
    ORDER BY a.HonorPoints DESC, a.GovernorID ASC;
    """

    try:
        rows = await run_query_async(sql)
        # Normalize to the expected dict keys (some drivers may produce column names different)
        out = []
        for r in rows:
            # r is already a dict from cursor_row_to_dict via run_query_async
            try:
                if isinstance(r, dict):
                    name = r.get("GovernorName") or r.get("Governor") or r.get("governorname") or ""
                    gid = int(r.get("GovernorID", 0))
                    pts = int(r.get("HonorPoints", 0))
                else:
                    # tuple-like fallback
                    name = r[0]
                    gid = int(r[1])
                    pts = int(r[2])
                out.append({"GovernorName": name, "GovernorID": gid, "HonorPoints": pts})
            except Exception:
                # Best-effort fallback
                try:
                    out.append(
                        {
                            "GovernorName": (
                                r.get("GovernorName", "Unknown")
                                if isinstance(r, dict)
                                else "Unknown"
                            ),
                            "GovernorID": int(r.get("GovernorID", 0)) if isinstance(r, dict) else 0,
                            "HonorPoints": (
                                int(r.get("HonorPoints", 0)) if isinstance(r, dict) else 0
                            ),
                        }
                    )
                except Exception:
                    continue
        if not out or (out and out[0].get("HonorPoints", 0) <= 0):
            return []
        return out
    except Exception:
        logger.exception("[HONOR] Failed loading latest Top-%s", n)
        return []


def purge_latest_honor_scan() -> int:
    """
    Deletes the most recent honor scan rows for the latest KVK.
    Returns number of rows deleted from KVK_Honor_AllPlayers_Raw.

    This is synchronous (disk/DB) and should be called via file_utils.run_blocking_in_thread
    (preferable) or asyncio.to_thread if necessary.
    """
    try:
        # Use exec_with_cursor to ensure consistency across multiple queries
        def cb(cur):
            # find latest kvk + scan
            cur.execute("SELECT MAX(KVK_NO) FROM dbo.KVK_Honor_Scan")
            row = fetch_one_dict(cur)
            if not row:
                return 0
            kvk = next(iter(row.values()))

            if kvk is None:
                return 0

            cur.execute("SELECT MAX(ScanID) FROM dbo.KVK_Honor_Scan WHERE KVK_NO=?", (kvk,))
            row = fetch_one_dict(cur)
            if not row:
                return 0
            sid = next(iter(row.values()))
            if sid is None:
                return 0

            cur.execute(
                "SELECT COUNT(*) FROM dbo.KVK_Honor_AllPlayers_Raw WHERE KVK_NO=? AND ScanID=?",
                (kvk, sid),
            )
            row = fetch_one_dict(cur)
            cnt = int(next(iter(row.values())) or 0) if row else 0

            cur.execute(
                "DELETE FROM dbo.KVK_Honor_AllPlayers_Raw WHERE KVK_NO=? AND ScanID=?", (kvk, sid)
            )
            cur.execute("DELETE FROM dbo.KVK_Honor_Scan WHERE KVK_NO=? AND ScanID=?", (kvk, sid))
            cur.connection.commit()
            return cnt

        res = exec_with_cursor(cb)
        logger.info("[HONOR] Purged latest scan (rows=%s)", res)
        return int(res or 0)
    except Exception:
        logger.exception("[HONOR] Purge latest scan failed")
        return 0
