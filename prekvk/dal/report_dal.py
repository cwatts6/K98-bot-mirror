from __future__ import annotations

import logging
from typing import Any

from file_utils import cursor_row_to_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def _fetch_all(cursor: Any) -> list[dict[str, Any]]:
    return [cursor_row_to_dict(cursor, row) for row in cursor.fetchall()]


def fetch_latest_prekvk_report_rows(kvk_no: int) -> list[dict[str, Any]]:
    """Return latest direct-stage PreKvK rows enriched with player power when available."""
    conn = get_conn_with_retries()
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            WITH Latest AS (
                SELECT TOP (1)
                    ScanID,
                    ScanTimestampUTC,
                    SourceFileName
                FROM dbo.PreKvk_Scan
                WHERE KVK_NO = ?
                ORDER BY ScanID DESC
            ),
            PowerRows AS (
                SELECT
                    CAST(Gov_ID AS bigint) AS GovernorID,
                    MAX(CAST([Starting Power] AS bigint)) AS Power
                FROM dbo.ALL_STATS_FOR_DASHBAORD
                WHERE KVK_NO = ?
                  AND Gov_ID IS NOT NULL
                GROUP BY CAST(Gov_ID AS bigint)
            )
            SELECT
                sc.GovernorID,
                COALESCE(NULLIF(LTRIM(RTRIM(sc.GovernorName)), ''), CONVERT(varchar(20), sc.GovernorID)) AS GovernorName,
                pr.Power,
                sc.Stage1Points,
                sc.Stage2Points,
                sc.Stage3Points,
                COALESCE(sc.TotalPoints, sc.Points, 0) AS OverallPoints,
                l.ScanID,
                l.ScanTimestampUTC,
                l.SourceFileName
            FROM dbo.PreKvk_Scores sc
            JOIN Latest l
              ON l.ScanID = sc.ScanID
            LEFT JOIN PowerRows pr
              ON pr.GovernorID = sc.GovernorID
            WHERE sc.KVK_NO = ?
            ORDER BY COALESCE(sc.TotalPoints, sc.Points, 0) DESC, sc.GovernorID ASC;
            """,
            (int(kvk_no), int(kvk_no), int(kvk_no)),
        )
        return _fetch_all(cursor)
