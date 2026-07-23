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


def fetch_output_complete_kvk_candidates(limit: int = 20) -> list[dict[str, Any]]:
    """Return bounded resolver inputs for KVKs with completed report output."""
    bounded_limit = max(1, min(int(limit), 20))
    with get_conn_with_retries() as cn:
        with cn.cursor() as cur:
            cur.execute(
                """
                SELECT TOP (?)
                       details.KVK_NO,
                       details.PASS4_START_SCAN,
                       details.KVK_END_SCAN,
                       latest_scan.MaxScanOrder,
                       final_header.State AS FinalOutputState
                FROM dbo.KVK_Details AS details
                JOIN dbo.KVKFinalReportHeader AS final_header
                  ON final_header.KVK_NO = details.KVK_NO
                 AND final_header.State = N'OUTPUT_COMPLETE'
                CROSS JOIN
                (
                    SELECT MAX(ScanOrder) AS MaxScanOrder
                    FROM dbo.KingdomScanData4
                ) AS latest_scan
                ORDER BY details.KVK_NO DESC;
                """,
                [bounded_limit],
            )
            rows = cur.fetchall()
            cols = [column[0] for column in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in rows]


def _normalized_finalized_kvk_nos(values: list[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})[:20]


def fetch_history_rows_for_governors(
    governor_ids: list[int], finalized_kvk_nos: list[int]
) -> list[dict[str, Any]]:
    """Fetch raw KVK history rows for concrete governor IDs."""
    finalized = _normalized_finalized_kvk_nos(finalized_kvk_nos)
    if not governor_ids or not finalized:
        return []

    placeholders = ",".join(["?"] * len(governor_ids))
    finalized_placeholders = ",".join(["?"] * len(finalized))
    sql = f"""
        SELECT
            CAST([Gov_ID] AS BIGINT)      AS Gov_ID,
            LTRIM(RTRIM([Governor_Name])) AS Governor_Name,
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
        FROM dbo.v_EXCEL_FOR_KVK_Started AS history
        WHERE [Gov_ID] IN ({placeholders})
          AND history.KVK_NO IN ({finalized_placeholders})
          AND EXISTS
          (
              SELECT 1
              FROM dbo.KVKFinalReportHeader AS final_header
              WHERE final_header.KVK_NO = history.KVK_NO
                AND final_header.State = N'OUTPUT_COMPLETE'
          )
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, [*governor_ids, *finalized])
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in rows]


def fetch_modern_history_rows_for_governors(
    governor_ids: list[int], finalized_kvk_nos: list[int]
) -> list[dict[str, Any]]:
    """Fetch null-preserving KVK history rows for the modern history payload/export."""
    finalized = _normalized_finalized_kvk_nos(finalized_kvk_nos)
    if not governor_ids or not finalized:
        return []

    placeholders = ",".join(["?"] * len(governor_ids))
    finalized_placeholders = ",".join(["?"] * len(finalized))
    sql = f"""
        SELECT
            CAST([Rank] AS INT)          AS Kingdom_Rank,
            CAST([KVK_RANK] AS INT)      AS KVK_RANK,
            CAST([Gov_ID] AS BIGINT)     AS Gov_ID,
            LTRIM(RTRIM([Governor_Name])) AS Governor_Name,
            CAST([KVK_NO] AS INT)        AS KVK_NO,
            CAST([T4_KILLS] AS BIGINT)   AS T4_KILLS,
            CAST([T5_KILLS] AS BIGINT)   AS T5_KILLS,
            CAST([T4&T5_Kills] AS BIGINT) AS T4T5_Kills,
            CAST([Kill Target] AS BIGINT) AS Kill_Target,
            CAST([% of Kill target] AS DECIMAL(9,2)) AS KillPct,
            CAST([Deads_Delta] AS BIGINT) AS Deads,
            CAST([Dead_Target] AS BIGINT) AS Dead_Target,
            CAST([% of Dead Target] AS DECIMAL(9,2)) AS DeadPct,
            CAST([DKP_SCORE] AS BIGINT)  AS DKP_SCORE,
            CAST([DKP Target] AS BIGINT) AS DKP_Target,
            CAST([% of DKP Target] AS DECIMAL(9,2)) AS DKPPct,
            CAST([Acclaim] AS BIGINT)    AS Acclaim,
            CAST([HighestAcclaim] AS BIGINT) AS HighestAcclaim,
            CAST([AutarchTimes] AS BIGINT) AS AutarchTimes,
            CAST([KvKPlayed] AS INT)     AS KvKPlayed,
            CAST([MostKvKKill] AS BIGINT) AS MostKvKKill,
            CAST([MostKvKDead] AS BIGINT) AS MostKvKDead,
            CAST([MostKvKHeal] AS BIGINT) AS MostKvKHeal,
            CAST([HealedTroopsDelta] AS BIGINT) AS HealedTroopsDelta,
            CAST([KillPointsDelta] AS BIGINT) AS KillPointsDelta,
            CAST([Max_PreKvk_Points] AS BIGINT) AS Max_PreKvk_Points,
            CAST([Max_HonorPoints] AS BIGINT) AS Max_HonorPoints,
            CAST([Pass 4 Kills] AS BIGINT) AS P4_Kills,
            CAST([Pass 6 Kills] AS BIGINT) AS P6_Kills,
            CAST([Pass 7 Kills] AS BIGINT) AS P7_Kills,
            CAST([Pass 8 Kills] AS BIGINT) AS P8_Kills,
            CAST([Pass 4 Deads] AS BIGINT) AS P4_Deads,
            CAST([Pass 6 Deads] AS BIGINT) AS P6_Deads,
            CAST([Pass 7 Deads] AS BIGINT) AS P7_Deads,
            CAST([Pass 8 Deads] AS BIGINT) AS P8_Deads
        FROM dbo.v_EXCEL_FOR_KVK_Started AS history
        WHERE [Gov_ID] IN ({placeholders})
          AND history.KVK_NO IN ({finalized_placeholders})
          AND EXISTS
          (
              SELECT 1
              FROM dbo.KVKFinalReportHeader AS final_header
              WHERE final_header.KVK_NO = history.KVK_NO
                AND final_header.State = N'OUTPUT_COMPLETE'
          )
        ORDER BY [Gov_ID], [KVK_NO]
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, [*governor_ids, *finalized])
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in rows]


def fetch_history_summary_metric_ranks(
    governor_id: int, finalized_kvk_nos: list[int]
) -> list[dict[str, Any]]:
    """Fetch canonical ranks for a bounded set of finalized KVK outputs."""
    normalized = sorted({int(value) for value in finalized_kvk_nos if int(value) > 0})[:20]
    if not normalized:
        return []
    padded: list[int | None] = [*normalized, *([None] * (20 - len(normalized)))]
    sql = """
        DECLARE @FinalizedKvkNos dbo.IntList;
        INSERT INTO @FinalizedKvkNos (ID)
        SELECT DISTINCT ID
        FROM (VALUES (?), (?), (?), (?), (?), (?), (?), (?), (?), (?),
                     (?), (?), (?), (?), (?), (?), (?), (?), (?), (?)) AS input(ID)
        WHERE ID IS NOT NULL;
        EXEC dbo.usp_GetKvkHistorySummaryMetricRanks
             @GovernorID = ?,
             @FinalizedKvkNos = @FinalizedKvkNos;
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, [*padded, governor_id])
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in rows]
