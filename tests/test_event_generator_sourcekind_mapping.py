from __future__ import annotations

from datetime import UTC, datetime

from event_calendar.event_generator import apply_overrides, generate_recurring_instances


def test_recurring_sourcekind_is_recurring():
    rules = [
        {
            "RuleID": "R1",
            "IntervalDays": 7,
            "FirstStartUTC": datetime(2026, 3, 1, tzinfo=UTC),
            "DurationDays": 1,
            "AllDay": True,
            "Title": "x",
            "EventType": "y",
        }
    ]
    out = generate_recurring_instances(
        rules=rules,
        horizon_start_utc=datetime(2026, 3, 1, tzinfo=UTC),
        horizon_end_utc=datetime(2026, 3, 20, tzinfo=UTC),
    )
    assert out
    assert all(i["SourceKind"] == "recurring" for i in out)


def test_override_rule_maps_to_recurring():
    instances = [
        {
            "SourceKind": "recurring",
            "SourceID": "R1",
            "StartUTC": datetime(2026, 3, 1, tzinfo=UTC),
            "EndUTC": datetime(2026, 3, 2, tzinfo=UTC),
            "IsCancelled": False,
        }
    ]
    overrides = [
        {
            "OverrideID": "O1",
            "TargetKind": "rule",
            "TargetID": "R1",
            "TargetOccurrenceStartUTC": datetime(2026, 3, 1, tzinfo=UTC),
            "ActionType": "cancel",
        }
    ]
    final, cancelled, _ = apply_overrides(instances=instances, overrides=overrides)
    assert cancelled == 1
    assert final[0]["IsCancelled"] is True
