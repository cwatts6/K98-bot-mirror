from __future__ import annotations

from mge import mge_summary_service


def test_summary_counts():
    rows = [
        {
            "RequestPriority": "High",
            "RequestedCommanderName": "Scipio",
            "KingdomRole": "R4",
            "WarningMissingKVKData": 1,
            "WarningHeadsOutOfRange": 0,
            "WarningNoAttachments": 1,
            "WarningNoGearOrArmamentText": 1,
        },
        {
            "RequestPriority": "Medium",
            "RequestedCommanderName": "Scipio",
            "KingdomRole": "R4",
            "WarningMissingKVKData": 0,
            "WarningHeadsOutOfRange": 1,
            "WarningNoAttachments": 0,
            "WarningNoGearOrArmamentText": 0,
        },
        {
            "RequestPriority": "High",
            "RequestedCommanderName": "Mehmed",
            "KingdomRole": None,
            "WarningMissingKVKData": 0,
            "WarningHeadsOutOfRange": 0,
            "WarningNoAttachments": 1,
            "WarningNoGearOrArmamentText": 1,
        },
    ]

    by_priority = mge_summary_service.summarize_by_priority(rows)
    assert by_priority == {"High": 2, "Medium": 1}

    by_commander = mge_summary_service.summarize_by_commander(rows)
    assert by_commander == {"Scipio": 2, "Mehmed": 1}

    by_role = mge_summary_service.summarize_by_role(rows)
    assert by_role == {"R4": 2, "Unknown": 1}

    warnings = mge_summary_service.summarize_warnings(rows)
    assert warnings["missing_kvk_data"] == 1
    assert warnings["heads_out_of_range"] == 1
    assert warnings["no_attachments"] == 2
    assert warnings["no_gear_or_armament_text"] == 2


def test_summary_null_safe():
    rows = [{}]
    summary = mge_summary_service.build_review_summary(rows)
    assert summary["total_rows"] == 1
    assert summary["by_priority"]["Unknown"] == 1
    assert summary["by_commander"]["Unknown"] == 1
    assert summary["by_role"]["Unknown"] == 1
