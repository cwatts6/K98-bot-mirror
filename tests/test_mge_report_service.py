from __future__ import annotations

from unittest.mock import patch

from mge import mge_report_service


def test_build_post_event_summary() -> None:
    with (
        patch(
            "mge.dal.mge_report_dal.fetch_event_header",
            return_value={"EventId": 1, "PublishVersion": 3},
        ),
        patch(
            "mge.dal.mge_report_dal.fetch_signup_totals",
            return_value=[{"TotalSignups": 20}],
        ),
        patch(
            "mge.dal.mge_report_dal.fetch_signups_by_commander",
            return_value=[{"RequestedCommanderName": "Nevsky", "SignupCount": 5}],
        ),
        patch(
            "mge.dal.mge_report_dal.fetch_signups_by_priority",
            return_value=[{"RequestPriority": "High", "SignupCount": 7}],
        ),
        patch(
            "mge.dal.mge_report_dal.fetch_award_counts",
            return_value=[{"AwardedCount": 15, "WaitlistCount": 4}],
        ),
        patch(
            "mge.dal.mge_report_dal.fetch_publish_change_count",
            return_value=[{"ChangeCount": 9}],
        ),
        patch(
            "mge.dal.mge_report_dal.fetch_fairness_metrics",
            return_value=[
                {
                    "WarningMissingKVKDataCount": 1,
                    "WarningHeadsOutOfRangeCount": 0,
                    "WarningNoAttachmentsCount": 2,
                    "WarningNoGearOrArmamentTextCount": 3,
                }
            ],
        ),
    ):
        summary = mge_report_service.build_post_event_summary(1)
        assert summary["Totals"]["TotalSignups"] == 20
        assert summary["Awards"]["AwardedCount"] == 15
        assert summary["RepublishMetrics"]["PublishVersion"] == 3
