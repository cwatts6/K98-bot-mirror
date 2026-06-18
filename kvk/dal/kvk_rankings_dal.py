"""Data-access helpers for KVK ranking browser and Hall of Fame records."""

from __future__ import annotations

from typing import Any

from file_utils import cursor_row_to_dict, get_conn_with_retries
from kvk.models.kvk_rankings import HallOfFameMetric

_HALL_OF_FAME_SQL_EXPRESSIONS: dict[HallOfFameMetric, str] = {
    HallOfFameMetric.KILLS: "src.[T4&T5_Kills]",
    HallOfFameMetric.KILL_POINTS: "src.[KillPointsDelta]",
    HallOfFameMetric.DEADS: "src.[Deads_Delta]",
    HallOfFameMetric.DKP: "src.[DKP_SCORE]",
    HallOfFameMetric.HEALED: "src.[HealedTroopsDelta]",
    HallOfFameMetric.ACCLAIM: "src.[Acclaim]",
    HallOfFameMetric.HONOR: "src.[Max_HonorPoints]",
    HallOfFameMetric.PREKVK: "src.[Max_PreKvk_Points]",
}


def fetch_hall_of_fame_records(
    metric: HallOfFameMetric,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top single-KVK performances for a validated Hall of Fame metric."""
    metric_expr = _HALL_OF_FAME_SQL_EXPRESSIONS[metric]
    normalized_limit = max(1, int(limit))
    sql = f"""
        WITH RecordRows AS (
            SELECT
                CAST(src.[Gov_ID] AS BIGINT) AS GovernorID,
                COALESCE(
                    NULLIF(LTRIM(RTRIM(src.[Governor_Name])), ''),
                    CONVERT(varchar(20), src.[Gov_ID])
                ) AS GovernorName,
                CAST(src.[KVK_NO] AS INT) AS KVK_NO,
                NULLIF(LTRIM(RTRIM(details.[KVK_NAME])), '') AS KVK_NAME,
                TRY_CONVERT(decimal(38, 2), {metric_expr}) AS MetricValue
            FROM dbo.v_EXCEL_FOR_KVK_Started AS src
            LEFT JOIN dbo.KVK_Details AS details
              ON details.KVK_NO = src.KVK_NO
            WHERE src.[Gov_ID] IS NOT NULL
              AND TRY_CONVERT(float, {metric_expr}) > 0
        ),
        Ranked AS (
            SELECT
                RANK() OVER (
                    ORDER BY MetricValue DESC, KVK_NO DESC, GovernorID ASC
                ) AS RecordRank,
                GovernorID,
                GovernorName,
                KVK_NO,
                KVK_NAME,
                MetricValue
            FROM RecordRows
        )
        SELECT TOP (?)
            RecordRank,
            GovernorID,
            GovernorName,
            KVK_NO,
            KVK_NAME,
            MetricValue
        FROM Ranked
        ORDER BY RecordRank ASC, MetricValue DESC, KVK_NO DESC, GovernorID ASC;
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, [normalized_limit])
        return [cursor_row_to_dict(cur, row) for row in cur.fetchall()]
