"""DAL for leadership MGE signup review dataset."""

from __future__ import annotations

import logging
from typing import Any

from stats_alerts.db import run_query

logger = logging.getLogger(__name__)

SQL_SELECT_SIGNUP_REVIEW_ROWS = """
SELECT
    EventId,
    SignupId,
    GovernorId,
    GovernorNameSnapshot,
    RequestedCommanderId,
    RequestedCommanderName,
    RequestPriority,
    PreferredRankBand,
    CurrentHeads,
    KingdomRole,
    HasGearText,
    HasArmamentText,
    HasGearOrArmamentText,
    HasGearAttachment,
    HasArmamentAttachment,
    HasAnyAttachment,
    SignupCreatedUtc,
    Source,
    LatestPower,
    LatestKVKRank,
    LastKVKRank,
    LatestT4T5Kills,
    LastT4T5Kills,
    LatestPercentOfKillTarget,
    LastPercentOfKillTarget,
    PriorAwardsRequestedCommanderCount,
    PriorAwardsOverallCount,
    PriorAwardsOverallLast2YearsCount,
    WarningMissingKVKData,
    WarningHeadsOutOfRange,
    WarningNoAttachments,
    WarningNoGearOrArmamentText
FROM dbo.v_MGE_SignupReview
WHERE EventId = ?;
"""


def fetch_signup_review_rows(event_id: int) -> list[dict[str, Any]]:
    """Fetch raw leadership review rows for a specific MGE event."""
    try:
        rows = run_query(SQL_SELECT_SIGNUP_REVIEW_ROWS, (event_id,))
        logger.info("mge_review_dal_fetch_success event_id=%s count=%s", event_id, len(rows))
        return rows
    except Exception:
        logger.exception("mge_review_dal_fetch_failed event_id=%s", event_id)
        return []
