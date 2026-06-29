"""Data access helpers for fallback stats imports."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

import pandas as pd

from constants import _conn_trusted
from file_utils import fetch_one_dict
from services.fallback_import_schema import INTERIM_AUTO_PARTIAL_SNAPSHOT

logger = logging.getLogger(__name__)

TASK_NAME = "UPDATE_ALL2"


def fetch_latest_fallback_snapshot(
    connection_factory: Callable[[], Any] = _conn_trusted,
) -> pd.DataFrame:
    """Read the latest full stats snapshot for interim partial fallback overlays."""
    query = """
        SELECT
            GovernorID AS [Governor ID],
            GovernorName AS [Name],
            [Power],
            Alliance,
            T1_Kills AS [T1-Kills],
            T2_Kills AS [T2-Kills],
            T3_Kills AS [T3-Kills],
            T4_Kills AS [T4-Kills],
            T5_Kills AS [T5-Kills],
            KillPoints AS [Total Kill Points],
            Deads AS [Dead Troops],
            HealedTroops AS [Healed Troops],
            RSSASSISTANCE AS [Rss Assistance],
            Helps AS [Alliance Helps],
            Rss_Gathered AS [Rss Gathered],
            [City Hall],
            [Troops Power],
            [Tech Power],
            [Building Power],
            [Commander Power],
            Civilization,
            AutarchTimes AS [Autarch Times],
            RangedPoints AS [Ranged Points],
            KvKPlayed AS [KvK Played],
            MostKvKKill AS [Most KvK Kill],
            MostKvKDead AS [Most KvK Dead],
            MostKvKHeal AS [Most KvK Heal],
            Acclaim,
            HighestAcclaim AS [Highest Acclaim],
            AOOJoined AS [AOO Joined],
            AOOWon AS [AOO Won],
            AOOAvgKill AS [AOO Avg Kill],
            AOOAvgDead AS [AOO Avg Dead],
            AOOAvgHeal AS [AOO Avg Heal],
            Conduct AS [Credit]
        FROM dbo.KingdomScanData4 WITH (NOLOCK)
        WHERE SCANORDER = (
            SELECT TOP (1) SCANORDER
            FROM dbo.KingdomScanData4 WITH (NOLOCK)
            ORDER BY SCANORDER DESC
        );
    """
    with connection_factory() as conn:
        cur = conn.cursor()
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame.from_records(cur.fetchall(), columns=cols)


def record_fallback_import_control(cur: Any, metadata: dict) -> None:
    """Persist the existing fallback import metadata row when the SQL object exists."""
    if not metadata:
        return

    source_type = str(metadata.get("source_type") or "")
    cur.execute("SELECT OBJECT_ID(N'dbo.FallbackImportBatchControl', N'U') AS ObjectId;")
    row = fetch_one_dict(cur)
    if not row or row.get("ObjectId") is None:
        if source_type == INTERIM_AUTO_PARTIAL_SNAPSHOT:
            raise RuntimeError(
                "dbo.FallbackImportBatchControl is required before interim partial imports."
            )
        logger.warning(
            "[EXCEL] FallbackImportBatchControl missing; continuing without SQL metadata."
        )
        return

    cur.execute(
        """
        INSERT INTO dbo.FallbackImportBatchControl
            (SourceType, SourceFilename, ScoreHeader, ColumnsPresentJson, RowsInSource, RowsWritten)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        source_type or None,
        metadata.get("source_filename"),
        metadata.get("score_header"),
        json.dumps(metadata.get("columns_present") or [], ensure_ascii=False),
        int(metadata.get("rows_in_source") or 0),
        int(metadata.get("rows_written") or 0),
    )


def fetch_update_all2_last_counter(cur: Any, task_name: str = TASK_NAME) -> int:
    cur.execute(
        "SELECT ISNULL(MAX(LastRunCounter), 0) AS LastRunCounter "
        "FROM SP_TaskStatus WHERE TaskName = ?",
        task_name,
    )
    row = fetch_one_dict(cur)
    return int(row.get("LastRunCounter", 0) if row else 0) or 0


def fetch_update_all2_status(
    connection_factory: Callable[[], Any] = _conn_trusted,
    task_name: str = TASK_NAME,
) -> dict | None:
    with connection_factory() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT "
            "MAX(LastRunCounter) AS LastRunCounter, "
            "MAX(LastRunTime)    AS LastRunTime, "
            "MAX(DurationSeconds) AS DurationSeconds "
            "FROM SP_TaskStatus WHERE TaskName = ?",
            task_name,
        )
        return fetch_one_dict(cur)
