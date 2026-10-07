# tests/test_event_utils_roundtrip.py
"""
Unit tests for event_utils persistence round-trip:
 - events_to_persisted -> JSON-safe persisted representation (ISO timestamps)
 - events_from_persisted -> canonical in-memory events with timezone-aware UTC datetimes
"""

from datetime import UTC, datetime, timedelta

from event_utils import events_from_persisted, events_to_persisted
from utils import ensure_aware_utc


def test_events_roundtrip_with_datetime_and_iso():
    # Build two events:
    #  - one with a timezone-aware datetime
    #  - one with an ISO string (use 'Z' style)
    now = datetime.now(UTC).replace(microsecond=0)
    later = now + timedelta(hours=2)

    events = [
        {"name": "AwareEvent", "type": "ruins", "start_time": now, "description": "aware dt"},
        {
            "name": "ISOBased",
            "type": "altar",
            "start_time": later.isoformat().replace("+00:00", "Z"),
            "description": "iso str",
        },
    ]

    # Persist to JSON-serializable form
    persisted = events_to_persisted(events)
    assert isinstance(persisted, list)
    assert len(persisted) == 2
    # Each persisted item must have an ISO string start_time
    for item in persisted:
        assert isinstance(item.get("start_time"), str)
        assert item.get("name") in {"AwareEvent", "ISOBased"}

    # Re-load into canonical in-memory events (datetimes should be timezone-aware UTC)
    loaded = events_from_persisted(persisted)
    assert isinstance(loaded, list)
    assert len(loaded) == 2

    # Validate types and UTC awareness
    for idx, ev in enumerate(loaded):
        st = ev.get("start_time")
        assert isinstance(st, datetime)
        assert st.tzinfo is not None
        # Ensure normalized to UTC
        assert st.utcoffset() == timedelta(0)

    # Check that the datetime values match original normalized values
    assert loaded[0]["name"] == "AwareEvent"
    assert loaded[0]["start_time"] == ensure_aware_utc(now)

    assert loaded[1]["name"] == "ISOBased"
    assert loaded[1]["start_time"] == ensure_aware_utc(later)
