from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from event_calendar.event_generator import (
    apply_overrides,
    generate_recurring_instances,
    merge_events,
)
from event_calendar.sheets_sync import (
    parse_oneoff_events,
    parse_overrides,
    parse_recurring_rules,
)


def test_parse_recurring_duplicate_rule_id_rejected():
    rows = [
        {
            "active": "1",
            "rule_id": "R1",
            "title": "A",
            "type": "raid",
            "recurrence_type": "interval_days",
            "interval_days": "7",
            "first_start_utc": "2026-01-01T00:00:00Z",
            "duration_days": "1",
        },
        {
            "active": "1",
            "rule_id": "R1",
            "title": "B",
            "type": "raid",
            "recurrence_type": "interval_days",
            "interval_days": "7",
            "first_start_utc": "2026-01-08T00:00:00Z",
            "duration_days": "1",
        },
    ]
    with pytest.raises(ValueError):
        parse_recurring_rules(rows)


def test_parse_oneoff_end_before_start_rejected():
    rows = [
        {
            "active": "1",
            "event_id": "E1",
            "title": "Bad",
            "type": "raid",
            "start_utc": "2026-02-01T10:00:00Z",
            "end_utc": "2026-02-01T09:00:00Z",
        }
    ]
    with pytest.raises(ValueError):
        parse_oneoff_events(rows)


def test_parse_overrides_duplicate_override_id_rejected():
    rows = [
        {
            "active": "1",
            "override_id": "O1",
            "target_kind": "rule",
            "target_id": "R1",
            "action": "cancel",
        },
        {
            "active": "1",
            "override_id": "O1",
            "target_kind": "rule",
            "target_id": "R2",
            "action": "cancel",
        },
    ]
    with pytest.raises(ValueError):
        parse_overrides(rows)


def test_generate_recurring_instances_basics():
    rules = [
        {
            "RuleID": "R1",
            "IntervalDays": 7,
            "FirstStartUTC": datetime(2026, 1, 1, tzinfo=UTC),
            "DurationDays": 1,
            "AllDay": False,
            "Title": "Weekly",
            "EventType": "raid",
        }
    ]
    out = generate_recurring_instances(
        rules=rules,
        horizon_start_utc=datetime(2026, 1, 1, tzinfo=UTC),
        horizon_end_utc=datetime(2026, 1, 31, tzinfo=UTC),
    )
    assert len(out) >= 4


def test_apply_overrides_cancel_and_modify():
    base_start = datetime(2026, 1, 1, tzinfo=UTC)
    instances = [
        {
            "SourceKind": "recurring",
            "SourceID": "R1",
            "StartUTC": base_start,
            "EndUTC": base_start + timedelta(hours=2),
            "Title": "Original",
            "IsCancelled": False,
        }
    ]
    overrides = [
        {
            "OverrideID": "O1",
            "ActionType": "modify",
            "TargetKind": "rule",
            "TargetID": "R1",
            "NewTitle": "Updated",
        },
        {
            "OverrideID": "O2",
            "ActionType": "cancel",
            "TargetKind": "rule",
            "TargetID": "R1",
        },
    ]
    final_instances, cancelled, modified = apply_overrides(instances=instances, overrides=overrides)
    assert final_instances[0]["Title"] == "Updated"
    assert final_instances[0]["IsCancelled"] is True
    assert cancelled == 1
    assert modified == 1


def test_merge_events_skips_invalid_oneoff():
    recurring = []
    oneoff = [
        {"EventID": "E1", "StartUTC": None, "EndUTC": None, "Title": "Bad"},
        {
            "EventID": "E2",
            "StartUTC": datetime(2026, 1, 1, tzinfo=UTC),
            "EndUTC": datetime(2026, 1, 1, tzinfo=UTC),
            "Title": "AlsoBad",
        },
        {
            "EventID": "E3",
            "StartUTC": datetime(2026, 1, 1, tzinfo=UTC),
            "EndUTC": datetime(2026, 1, 1, 1, tzinfo=UTC),
            "Title": "Good",
            "AllDay": False,
            "EventType": "raid",
        },
    ]
    out = merge_events(recurring_instances=recurring, oneoff_events=oneoff)
    assert len(out) == 1
    assert out[0]["SourceID"] == "E3"
