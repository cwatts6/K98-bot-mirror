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
    finalized_kvk_nos: list[int],
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return finalized single-KVK records for a validated Hall of Fame metric."""
    finalized = sorted({int(value) for value in finalized_kvk_nos if int(value) > 0})[:20]
    if not finalized:
        return []
    padded: list[int | None] = [*finalized, *([None] * (20 - len(finalized)))]
    metric_expr = _HALL_OF_FAME_SQL_EXPRESSIONS[metric]
    normalized_limit = max(1, int(limit))
    healed_metric = metric is HallOfFameMetric.HEALED
    value_predicate = ">= 0" if healed_metric else "> 0"
    direction = "ASC" if healed_metric else "DESC"
    engaged_filter = (
        """
              AND TRY_CONVERT(float, src.[KillPointsDelta]) > 0
              AND (
                    TRY_CONVERT(float, src.[T4&T5_Kills]) > 0
                 OR TRY_CONVERT(float, src.[Deads_Delta]) > 0
                 OR TRY_CONVERT(float, src.[HealedTroopsDelta]) > 0
              )
    """
        if healed_metric
        else ""
    )
    sql = f"""
        DECLARE @FinalizedKvkNos dbo.IntList;
        INSERT INTO @FinalizedKvkNos (ID)
        SELECT DISTINCT ID
        FROM (VALUES (?), (?), (?), (?), (?), (?), (?), (?), (?), (?),
                     (?), (?), (?), (?), (?), (?), (?), (?), (?), (?)) AS input(ID)
        WHERE ID IS NOT NULL;

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
            JOIN dbo.KVKFinalReportHeader AS final_header
              ON final_header.KVK_NO = src.KVK_NO
             AND final_header.State = N'OUTPUT_COMPLETE'
            JOIN @FinalizedKvkNos AS finalized
              ON finalized.ID = src.KVK_NO
            WHERE src.[Gov_ID] IS NOT NULL
              AND TRY_CONVERT(float, {metric_expr}) {value_predicate}
              {engaged_filter}
        ),
        Ranked AS (
            SELECT
                RANK() OVER (
                    ORDER BY MetricValue {direction}
                ) AS RecordRank,
                GovernorID,
                GovernorName,
                KVK_NO,
                KVK_NAME,
                MetricValue,
                COUNT_BIG(*) OVER() AS TotalRecordsCount
            FROM RecordRows
        )
        SELECT TOP (?)
            RecordRank,
            GovernorID,
            GovernorName,
            KVK_NO,
            KVK_NAME,
            MetricValue,
            TotalRecordsCount
        FROM Ranked
        ORDER BY RecordRank ASC, MetricValue {direction}, KVK_NO DESC, GovernorID ASC;
    """
    with get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(sql, [*padded, normalized_limit])
        return [cursor_row_to_dict(cur, row) for row in cur.fetchall()]
