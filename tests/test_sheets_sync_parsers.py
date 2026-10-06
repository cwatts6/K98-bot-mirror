from __future__ import annotations

import pytest

from event_calendar.sheets_sync import (
    parse_oneoff_events,
    parse_overrides,
    parse_recurring_rules,
)


def test_parse_recurring_rules_ok():
    rows = [
        {
            "active": "TRUE",
            "rule_id": "mge_archer",
            "emoji": "👑",
            "title": "MGE",
            "type": "mge",
            "variant": "archer",
            "recurrence_type": "every_n_days",
            "interval_days": "56",
            "first_start_utc": "2026-03-23 00:00:00",
            "duration_days": "6",
            "repeat_until_utc": "2028-03-23 00:00:00",
            "max_occurrences": "",
            "all_day": "TRUE",
            "importance": "major",
            "description": "desc",
            "link_url": "",
            "channel_id": "",
            "signup_url": "",
            "tags": "alliance, pve,alliance",
            "sort_order": "1",
            "notes_internal": "",
        }
    ]
    out = parse_recurring_rules(rows)
    assert len(out) == 1
    assert out[0]["RuleID"] == "mge_archer"
    assert out[0]["Tags"] == "alliance,pve"
    assert isinstance(out[0]["SourceRowHash"], (bytes, bytearray))
    assert len(out[0]["SourceRowHash"]) == 32


def test_parse_oneoff_events_rejects_invalid_range():
    rows = [
        {
            "active": "TRUE",
            "event_id": "bad",
            "title": "Bad",
            "type": "x",
            "variant": "",
            "start_utc": "2026-03-06 20:00:00",
            "end_utc": "2026-03-06 19:00:00",
            "all_day": "FALSE",
            "importance": "",
            "description": "",
            "link_url": "",
            "channel_id": "",
            "signup_url": "",
            "tags": "",
            "sort_order": "",
            "notes_internal": "",
        }
    ]
    with pytest.raises(ValueError, match="end_utc must be > start_utc"):
        parse_oneoff_events(rows)


def test_parse_overrides_requires_valid_action():
    rows = [
        {
            "active": "TRUE",
            "override_id": "ov1",
            "target_kind": "rule",
            "target_id": "x",
            "target_occurrence_start_utc": "2026-03-21 00:00:00",
            "action": "noop",
            "new_start_utc": "",
            "new_end_utc": "",
            "new_title": "",
            "new_variant": "",
            "new_emoji": "",
            "new_importance": "",
            "new_description": "",
            "new_link_url": "",
            "new_channel_id": "",
            "new_signup_url": "",
            "new_tags": "",
            "notes_internal": "",
        }
    ]
    with pytest.raises(ValueError, match="action must be cancel\\|modify"):
        parse_overrides(rows)
