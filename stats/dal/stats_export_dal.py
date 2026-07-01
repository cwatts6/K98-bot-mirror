"""Data access for personal stats exports."""

from __future__ import annotations

from collections.abc import Sequence
import logging

import pandas as pd

from file_utils import get_conn_with_retries

logger = logging.getLogger(__name__)

EXPORT_COLUMNS = [
    "GovernorID",
    "GovernorName",
    "Alliance",
    "AsOfDate",
    "Power",
    "PowerDelta",
    "TroopPower",
    "TroopPowerDelta",
    "KillPoints",
    "KillPointsDelta",
    "Deads",
    "DeadsDelta",
    "RSS_Gathered",
    "RSS_GatheredDelta",
    "RSSAssist",
    "RSSAssistDelta",
    "Helps",
    "HelpsDelta",
    "BuildingMinutes",
    "TechDonations",
    "FortsTotal",
    "FortsLaunched",
    "FortsJoined",
    "AOOJoined",
    "AOOJoinedDelta",
    "AOOWon",
    "AOOWonDelta",
    "AOOAvgKill",
    "AOOAvgKillDelta",
    "AOOAvgDead",
    "AOOAvgDeadDelta",
    "AOOAvgHeal",
    "AOOAvgHealDelta",
    "T4_Kills",
    "T4_KillsDelta",
    "T5_Kills",
    "T5_KillsDelta",
    "T4T5_Kills",
    "T4T5_KillsDelta",
    "HealedTroops",
    "HealedTroopsDelta",
    "RangedPoints",
    "RangedPointsDelta",
    "HighestAcclaim",
    "HighestAcclaimDelta",
    "AutarchTimes",
    "AutarchTimesDelta",
]


def empty_export_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=EXPORT_COLUMNS)


def fetch_daily_player_export(governor_ids: Sequence[int]) -> pd.DataFrame:
    """Return personal daily export rows for the supplied governor IDs."""
    ids = [int(gid) for gid in governor_ids if int(gid) > 0]
    if not ids:
        return empty_export_frame()

    placeholders = ",".join("?" for _ in ids)
    columns_sql = ", ".join(EXPORT_COLUMNS)
    query = f"""
    SELECT {columns_sql}
    FROM dbo.vDaily_PlayerExport
    WHERE GovernorID IN ({placeholders})
    ORDER BY GovernorID, AsOfDate DESC;
    """

    logger.debug("stats_export_fetch governor_count=%s", len(ids))
    conn = get_conn_with_retries()
    try:
        cursor = conn.cursor()
        cursor.execute(query, ids)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else EXPORT_COLUMNS
        return pd.DataFrame.from_records(rows, columns=columns)
    finally:
        conn.close()
