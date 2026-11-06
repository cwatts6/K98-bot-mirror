"""
DAL for audit/reporting queries that span the full active registry.
Separated from registry_dal.py to keep the primary DAL focused on CRUD stored procedures.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_SQL_ACTIVE_PLAYERS: str = """
SELECT [PowerRank],
       [GovernorName],
       [GovernorID],
       [Alliance],
       [Power],
       [KillPoints],
       [Deads],
       [T1_Kills],
       [T2_Kills],
       [T3_Kills],
       [T4_Kills],
       [T5_Kills],
       [T4&T5_KILLS],
       [TOTAL_KILLS],
       [RSS_Gathered],
       [RSSAssistance],
       [Helps],
       [ScanDate],
       [Troops Power],
       [City Hall],
       [Tech Power],
       [Building Power],
       [Commander Power],
       [LOCATION]
FROM [ROK_TRACKER].[dbo].[v_Active_Players]
WITH (NOLOCK);
"""


def get_active_players() -> list[dict[str, Any]]:
    """
    Fetch all active player rows from the stats view for audit purposes.

    Uses stats_alerts.db.run_query_strict() — raises on failure.
    Callers must handle exceptions explicitly.

    Returns list[dict] where each dict maps column names to values.
    """
    from stats_alerts.db import run_query_strict

    return run_query_strict(_SQL_ACTIVE_PLAYERS)
