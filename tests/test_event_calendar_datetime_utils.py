from event_calendar.datetime_utils import parse_iso_utc_nullable


def test_parse_iso_nullable_ok():
    dt = parse_iso_utc_nullable("2026-03-07T10:00:00Z")
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_iso_nullable_bad():
    assert parse_iso_utc_nullable("bad-date") is None
