from __future__ import annotations

import logging
from typing import Any

from mge.dal import mge_report_dal

logger = logging.getLogger(__name__)


def build_post_event_summary(event_id: int) -> dict[str, Any]:
    """Build internal post-event summary payload for leadership/admin use."""
    event = mge_report_dal.fetch_event_header(event_id)
    if not event:
        raise ValueError(f"MGE event {event_id} not found")

    total_rows = mge_report_dal.fetch_signup_totals(event_id)
    by_commander = mge_report_dal.fetch_signups_by_commander(event_id)
    by_priority = mge_report_dal.fetch_signups_by_priority(event_id)
    award_rows = mge_report_dal.fetch_award_counts(event_id)
    change_rows = mge_report_dal.fetch_publish_change_count(event_id)
    fairness_rows = mge_report_dal.fetch_fairness_metrics(event_id)

    totals = total_rows[0] if total_rows else {"TotalSignups": 0}
    awards = award_rows[0] if award_rows else {"AwardedCount": 0, "WaitlistCount": 0}
    changes = change_rows[0] if change_rows else {"ChangeCount": 0}
    fairness = (
        fairness_rows[0]
        if fairness_rows
        else {
            "WarningMissingKVKDataCount": 0,
            "WarningHeadsOutOfRangeCount": 0,
            "WarningNoAttachmentsCount": 0,
            "WarningNoGearOrArmamentTextCount": 0,
        }
    )

    summary = {
        "Event": event,
        "Totals": {"TotalSignups": int(totals.get("TotalSignups") or 0)},
        "SignupsByCommander": [
            {
                "RequestedCommanderName": str(r.get("RequestedCommanderName") or "Unknown"),
                "SignupCount": int(r.get("SignupCount") or 0),
            }
            for r in by_commander
        ],
        "SignupsByPriority": [
            {
                "RequestPriority": str(r.get("RequestPriority") or "Unknown"),
                "SignupCount": int(r.get("SignupCount") or 0),
            }
            for r in by_priority
        ],
        "Awards": {
            "AwardedCount": int(awards.get("AwardedCount") or 0),
            "WaitlistCount": int(awards.get("WaitlistCount") or 0),
        },
        "RepublishMetrics": {
            "PublishVersion": int(event.get("PublishVersion") or 0),
            "ChangeCount": int(changes.get("ChangeCount") or 0),
        },
        "FairnessIndicators": {
            "WarningMissingKVKDataCount": int(fairness.get("WarningMissingKVKDataCount") or 0),
            "WarningHeadsOutOfRangeCount": int(fairness.get("WarningHeadsOutOfRangeCount") or 0),
            "WarningNoAttachmentsCount": int(fairness.get("WarningNoAttachmentsCount") or 0),
            "WarningNoGearOrArmamentTextCount": int(
                fairness.get("WarningNoGearOrArmamentTextCount") or 0
            ),
        },
    }

    logger.info("mge_post_event_summary_built", extra={"event_id": event_id})
    return summary
