"""DAL for leadership MGE signup review dataset."""

from __future__ import annotations

import logging
from typing import Any

from core.operation_timing import timed_stage
from mge.dal.qualified_read import qualified_read
from mge.dataset_errors import MgeDatasetError
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


def fetch_signup_review_rows(event_id: int, *, strict: bool = False) -> list[dict[str, Any]]:
    """Fetch raw leadership review rows for a specific MGE event."""
    try:
        with timed_stage("mge_review_read"):
            rows = (
                qualified_read(
                    SQL_SELECT_SIGNUP_REVIEW_ROWS,
                    (event_id,),
                    stage="review_read",
                    columns=(
                        "EventId",
                        "SignupId",
                        "GovernorId",
                        "GovernorNameSnapshot",
                        "RequestedCommanderId",
                        "RequestedCommanderName",
                        "RequestPriority",
                        "PreferredRankBand",
                        "SignupCreatedUtc",
                        "CurrentHeads",
                        "KingdomRole",
                        "HasGearText",
                        "HasArmamentText",
                        "HasGearOrArmamentText",
                        "HasGearAttachment",
                        "HasArmamentAttachment",
                        "HasAnyAttachment",
                        "Source",
                        "LatestPower",
                        "LatestKVKRank",
                        "LastKVKRank",
                        "LatestT4T5Kills",
                        "LastT4T5Kills",
                        "LatestPercentOfKillTarget",
                        "LastPercentOfKillTarget",
                        "PriorAwardsRequestedCommanderCount",
                        "PriorAwardsOverallCount",
                        "PriorAwardsOverallLast2YearsCount",
                        "WarningMissingKVKData",
                        "WarningHeadsOutOfRange",
                        "WarningNoAttachments",
                        "WarningNoGearOrArmamentText",
                    ),
                )
                if strict
                else run_query(SQL_SELECT_SIGNUP_REVIEW_ROWS, (event_id,))
            )
        logger.info("mge_review_dal_fetch_success event_id=%s count=%s", event_id, len(rows))
        return rows
    except MgeDatasetError:
        raise
    except Exception:
        if strict:
            raise MgeDatasetError("unavailable", "review_read") from None
        logger.exception("mge_review_dal_fetch_failed event_id=%s", event_id)
        return []
