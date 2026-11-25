from datetime import UTC, datetime

from event_utils import events_from_persisted, events_to_persisted, serialize_event


def test_events_from_persisted_iso_z():
    raw = [
        {"name": "Test", "type": "ruins", "start_time": "2025-11-19T10:00:00Z", "description": "d"}
    ]
    out = events_from_persisted(raw)
    assert len(out) == 1
    ev = out[0]
    assert isinstance(ev["start_time"], datetime)
    assert ev["start_time"].tzinfo is not None
    assert ev["name"] == "Test"


def test_events_from_persisted_naive_dt():
    naive = datetime(2025, 11, 19, 10, 0, 0)  # naive -> should be treated as UTC
    raw = [{"name": "N", "type": "altar", "start_time": naive}]
    out = events_from_persisted(raw)
    assert out[0]["start_time"].tzinfo is not None
    assert out[0]["start_time"].astimezone(UTC).hour == 10


def test_events_to_persisted_and_serialize_event():

    dt = datetime(2025, 11, 19, 10, 0, 0, tzinfo=UTC)
    ev = {"name": "S", "type": "major", "start_time": dt, "description": "desc"}
    persisted = events_to_persisted([ev])
    assert (
        persisted[0]["start_time"].endswith("+00:00")
        or persisted[0]["start_time"].endswith("Z")
        or "00:00" in persisted[0]["start_time"]
    )
    ser = serialize_event(ev)
    assert "start_time" in ser
