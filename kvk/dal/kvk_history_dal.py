"""Data-access helpers for KVK history and KVK metadata queries."""

from __future__ import annotations

import logging
from typing import Any

from file_utils import fetch_one_dict, get_conn_with_retries

logger = logging.getLogger(__name__)


def resolve_current_kvk_no_from_cursor(cursor: Any, kvk_no: int | None = None) -> int:
    """Resolve an explicit/current KVK number using the provided DB cursor."""
    if kvk_no and kvk_no > 0:
        return int(kvk_no)

    cursor.execute("""
        SELECT TOP 1 KVK_NO
        FROM dbo.KVK_Details
        WHERE GETUTCDATE() BETWEEN KVK_REGISTRATION_DATE AND KVK_END_DATE
        ORDER BY KVK_NO DESC
    """)
    rowd = fetch_one_dict(cursor)
    if not rowd:
        raise ValueError("Could not resolve the current KVK window.")
    return int(next(iter(rowd.values())))


def resolve_current_kvk_no(kvk_no: int | None = None) -> int:
    """Resolve an explicit/current KVK number with a short-lived connection."""
    if kvk_no and kvk_no > 0:
        return int(kvk_no)
    with get_conn_with_retries() as cn:
        with cn.cursor() as cur:
            return resolve_current_kvk_no_from_cursor(cur, kvk_no)


def get_started_kvks() -> list[int]:
    """
    Return a contiguous range of started KVKs from the earliest tracked KVK
    through the latest KVK whose start date has passed.
    """
    with get_conn_with_retries() as cn:
        with cn.cursor() as cur:
            cur.execute("""
                SELECT MAX(KVK_NO)
                FROM dbo.KVK_Details
                WHERE KVK_START_DATE IS NOT NULL
                  AND KVK_START_DATE <= SYSUTCDATETIME();
            """)
            row = fetch_one_dict(cur)
            max_started = int(next(iter(row.values())) or 0) if row else 0

            if max_started == 0:
                cur.execute("SELECT ISNULL(MAX([KVK_NO]), 0) FROM dbo.v_EXCEL_FOR_KVK_All;")
                fallback_row = fetch_one_dict(cur)
                max_started = int(next(iter(fallback_row.values())) or 0) if fallback_row else 0

            cur.execute("""
                SELECT MIN(TRY_CONVERT(int, REPLACE(name, 'EXCEL_FOR_KVK_', '')))
                FROM sys.tables
                WHERE name LIKE 'EXCEL_FOR_KVK[_]%';
            """)
            min_row = fetch_one_dict(cur)
            if min_row:
                raw_min = next(iter(min_row.values()))
                min_kvk = int(raw_min) if raw_min is not None else 3
            else:
                min_kvk = 3
            min_kvk = max(3, min_kvk)

    if max_started < min_kvk:
        return [min_kvk]
    return list(range(min_kvk, max_started + 1))


def fetch_history_rows_for_governors(governor_ids: list[int]) -> list[dict[str, Any]]:
    """Fetch raw KVK history rows for concrete governor IDs."""
    if not governor_ids:
        return []

    placeholders = ",".join(["?"] * len(governor_ids))
    sql = f"""
        SELECT
            CAST([Gov_ID] AS BIGINT)      AS Gov_ID,
            [Governor_Name],
            CAST([KVK_NO] AS INT)         AS KVK_NO,
            CAST([T4_KILLS] AS BIGINT)    AS T4_KILLS,
            CAST([T5_KILLS] AS BIGINT)    AS T5_KILLS,
            CAST([T4&T5_Kills] AS BIGINT) AS T4T5_Kills,
            CAST([% of Kill target] AS DECIMAL(9,2)) AS KillPct,
            CAST([Deads_Delta] AS BIGINT)       AS Deads,
            CAST([% of Dead Target] AS DECIMAL(9,2)) AS DeadPct,
            CAST([DKP_SCORE] AS BIGINT)   AS DKP_SCORE,
            CAST([% of DKP Target] AS DECIMAL(9,2)) AS DKPPct,
            CAST([Pass 4 Kills] AS BIGINT) AS P4_Kills,
            CAST([Pass 6 Kills] AS BIGINT) AS P6_Kills,
            CAST([Pass 7 Kills] AS BIGINT) AS P7_Kills,
            CAST([Pass 8 Kills] AS BIGINT) AS P8_Kills,
            CAST([Pass 4 Deads] AS BIGINT) AS P4_Deads,
            CAST([Pass 6 Deads] AS BIGINT) AS P6_Deads,
            CAST([Pass 7 Deads] AS BIGINT) AS P7_Deads,
            CAST([Pass 8 Deads] AS BIGINT) AS P8_Deads
        FROM dbo.v_EXCEL_FOR_KVK_Started
        WHERE [Gov_ID] IN ({placeholders})
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, governor_ids)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in rows]
